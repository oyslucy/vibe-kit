"""Install global settings: CLAUDE.md, git hooks, Claude settings, skills.

Each step inspects the current state and returns the actions still needed,
so running the installer twice is a no-op the second time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Protocol

from .errors import VibeError
from .shell import Runner

# Attribution off. The object form is understood by every Claude Code version
# that supports `attribution` (the bare `false` form needs v2.1.281+).
ATTRIBUTION_OFF = {"commit": "", "pr": "", "sessionUrl": False}

Clock = Callable[[], datetime]
Confirm = Callable[[str], bool]


@dataclass
class Action:
    description: str
    apply: Callable[[], None]
    confirm: str | None = None  # question to ask before applying


class Step(Protocol):
    name: str

    def plan(self) -> list[Action]: ...


def backup_path(path: Path, clock: Clock) -> Path:
    stamp = clock().strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(f"{path.name}.bak-{stamp}")
    n = 1
    while candidate.exists() or candidate.is_symlink():
        candidate = path.with_name(f"{path.name}.bak-{stamp}-{n}")
        n += 1
    return candidate


@dataclass
class SymlinkStep:
    name: str
    link: Path
    target: Path
    clock: Clock = datetime.now

    def plan(self) -> list[Action]:
        if not self.target.exists():
            raise VibeError(f"원본이 없습니다: {self.target}")
        if self.link.is_symlink() and self.link.resolve() == self.target.resolve():
            return []
        actions: list[Action] = []
        if self.link.exists() or self.link.is_symlink():
            backup = backup_path(self.link, self.clock)
            actions.append(
                Action(f"백업: {self.link} -> {backup}", lambda: self.link.rename(backup))
            )
        actions.append(Action(f"링크: {self.link} -> {self.target}", self._link))
        return actions

    def _link(self) -> None:
        self.link.parent.mkdir(parents=True, exist_ok=True)
        self.link.symlink_to(self.target, target_is_directory=self.target.is_dir())


@dataclass
class HooksPathStep:
    hooks_dir: Path
    runner: Runner
    name: str = "git core.hooksPath"

    def plan(self) -> list[Action]:
        current = self._current()
        wanted = str(self.hooks_dir)
        if current == wanted:
            return []
        action = Action(
            f"git config --global core.hooksPath {wanted}",
            lambda: self.runner.run(["git", "config", "--global", "core.hooksPath", wanted]),
        )
        if current:
            action.description = f"core.hooksPath 변경: {current} -> {wanted}"
            action.confirm = f"core.hooksPath가 이미 '{current}'로 설정되어 있습니다. 덮어쓸까요?"
        return [action]

    def _current(self) -> str:
        proc = self.runner.run(
            ["git", "config", "--global", "--get", "core.hooksPath"], check=False
        )
        return proc.stdout.strip() if proc.returncode == 0 else ""


@dataclass
class SettingsStep:
    """Merge attribution-off into settings.json without touching other keys."""

    path: Path
    name: str = "Claude settings.json"
    patch: dict = field(default_factory=lambda: dict(ATTRIBUTION_OFF))

    def plan(self) -> list[Action]:
        data = self._load()
        current = data.get("attribution")
        if current is False:
            return []
        if isinstance(current, dict) and all(current.get(k) == v for k, v in self.patch.items()):
            return []
        merged = dict(current) if isinstance(current, dict) else {}
        merged.update(self.patch)
        data["attribution"] = merged
        return [Action(f"{self.path}: attribution 끄기", lambda: self._write(data))]

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text() or "{}")
        except json.JSONDecodeError as e:
            raise VibeError(
                f"{self.path}가 올바른 JSON이 아닙니다 ({e}).",
                hint="파일을 고친 뒤 다시 실행하세요. 파일은 변경하지 않았습니다.",
            ) from e
        if not isinstance(data, dict):
            raise VibeError(f"{self.path}의 최상위 값이 객체가 아닙니다.")
        return data

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(self.path)


def default_steps(kit: Path, home: Path, runner: Runner, clock: Clock = datetime.now) -> list[Step]:
    claude = home / ".claude"
    return [
        SymlinkStep("전역 CLAUDE.md", claude / "CLAUDE.md", kit / "global" / "CLAUDE.md", clock),
        HooksPathStep(kit / "hooks", runner),
        SettingsStep(claude / "settings.json"),
        SymlinkStep(
            "bootstrap 스킬", claude / "skills" / "bootstrap", kit / "skills" / "bootstrap", clock
        ),
    ]


@dataclass
class Installer:
    steps: list[Step]
    confirm: Confirm
    echo: Callable[[str], None] = print

    def run(self, dry_run: bool = False) -> int:
        """Apply (or, with dry_run, only print) pending actions. Returns their count."""
        count = 0
        for step in self.steps:
            actions = step.plan()
            if not actions:
                self.echo(f"✓ {step.name}: 이미 설정됨")
                continue
            for action in actions:
                if dry_run:
                    note = " (확인 필요)" if action.confirm else ""
                    self.echo(f"[dry-run] {action.description}{note}")
                    count += 1
                    continue
                if action.confirm and not self.confirm(action.confirm):
                    self.echo(f"- 건너뜀: {action.description}")
                    break
                action.apply()
                self.echo(f"✓ {action.description}")
                count += 1
        return count


def ensure_hooks_executable(kit: Path) -> None:
    for hook in (kit / "hooks").iterdir():
        if hook.is_file():
            hook.chmod(hook.stat().st_mode | 0o111)
