"""GitHub repository creation/cloning and git commits via the gh and git CLIs."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .errors import VibeError
from .shell import Runner

Which = Callable[[str], "str | None"]


def local_dir_name(name: str) -> str:
    """`owner/repo` -> `repo`."""
    return name.rstrip("/").split("/")[-1]


@dataclass
class GitHub:
    runner: Runner
    which: Which = shutil.which

    def preflight(self, name: str, parent: Path) -> Path:
        """Validate tools, auth, and location. Returns the project path."""
        if not name or not local_dir_name(name):
            raise VibeError("프로젝트 이름이 비어 있습니다.")
        if not self.which("git"):
            raise VibeError("git이 설치되어 있지 않습니다.", hint="brew install git")
        if not self.which("gh"):
            raise VibeError(
                "GitHub CLI(gh)가 설치되어 있지 않습니다.",
                hint="brew install gh  (https://cli.github.com)",
            )
        if self.runner.run(["gh", "auth", "status"], check=False).returncode != 0:
            raise VibeError("gh에 로그인되어 있지 않습니다.", hint="gh auth login")
        if not parent.is_dir():
            raise VibeError(f"폴더가 없습니다: {parent}", hint="--dir로 존재하는 폴더를 지정하세요.")
        top = self.runner.run(
            ["git", "-C", str(parent), "rev-parse", "--show-toplevel"], check=False
        )
        if top.returncode == 0:
            raise VibeError(
                f"{parent}는 이미 다른 git 레포({top.stdout.strip()}) 안에 있습니다.",
                hint="레포 밖의 폴더를 --dir로 지정하세요.",
            )
        path = parent / local_dir_name(name)
        if path.exists():
            raise VibeError(f"이미 존재하는 폴더입니다: {path}")
        return path

    def remote_exists(self, name: str) -> bool:
        return self.runner.run(["gh", "repo", "view", name, "--json", "name"], check=False).returncode == 0

    def create_or_clone(self, name: str, parent: Path, private: bool = True) -> tuple[Path, bool]:
        """Returns (path, created). Clones instead when the remote already exists."""
        if self.remote_exists(name):
            self._run(["gh", "repo", "clone", name], parent, "clone")
            return parent / local_dir_name(name), False
        visibility = "--private" if private else "--public"
        self._run(["gh", "repo", "create", name, visibility, "--add-readme", "--clone"], parent, "생성")
        return parent / local_dir_name(name), True

    def commit_and_push(self, path: Path, message: str) -> bool:
        """Commit everything and push. Returns False if there was nothing to commit."""
        self._run(["git", "add", "-A"], path, "git add")
        if self.runner.run(["git", "diff", "--cached", "--quiet"], cwd=path, check=False).returncode == 0:
            return False
        self._run(["git", "commit", "-m", message], path, "커밋")
        self._run(["git", "push", "-u", "origin", "HEAD"], path, "push")
        return True

    def _run(self, args: list[str], cwd: Path, what: str) -> None:
        proc = self.runner.run(args, cwd=cwd, check=False)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise VibeError(f"{what} 실패: {' '.join(args)}", hint=detail or None)
