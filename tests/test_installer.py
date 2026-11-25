"""Installer tests run against a temporary HOME and git global config."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from vibe_kit import installer
from vibe_kit.errors import VibeError
from vibe_kit.shell import SubprocessRunner

FIXED = datetime(2026, 1, 2, 3, 4, 5)


@pytest.fixture
def home(tmp_path, monkeypatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(home / ".gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    return home


@pytest.fixture
def kit(tmp_path) -> Path:
    kit = tmp_path / "kit"
    (kit / "global").mkdir(parents=True)
    (kit / "global" / "CLAUDE.md").write_text("# rules\n")
    (kit / "hooks").mkdir()
    (kit / "hooks" / "commit-msg").write_text("#!/bin/sh\n")
    (kit / "skills" / "bootstrap").mkdir(parents=True)
    (kit / "skills" / "bootstrap" / "SKILL.md").write_text("skill\n")
    return kit


def make(kit, home, answers=None, log=None):
    asked = []

    def confirm(q):
        asked.append(q)
        return answers.pop(0) if answers else False

    steps = installer.default_steps(kit, home, SubprocessRunner(), clock=lambda: FIXED)
    inst = installer.Installer(steps, confirm, (log if log is not None else []).append)
    return inst, asked


def hooks_path() -> str:
    return subprocess.run(
        ["git", "config", "--global", "--get", "core.hooksPath"], capture_output=True, text=True
    ).stdout.strip()


def test_fresh_install(kit, home):
    inst, asked = make(kit, home)
    inst.run()
    claude = home / ".claude"
    assert (claude / "CLAUDE.md").resolve() == (kit / "global" / "CLAUDE.md").resolve()
    assert (claude / "skills" / "bootstrap").resolve() == (kit / "skills" / "bootstrap").resolve()
    assert hooks_path() == str(kit / "hooks")
    settings = json.loads((claude / "settings.json").read_text())
    assert settings["attribution"] == {"commit": "", "pr": "", "sessionUrl": False}
    assert asked == []


def test_idempotent(kit, home):
    make(kit, home)[0].run()
    snapshot = (home / ".claude" / "settings.json").read_text()
    inst, asked = make(kit, home)
    assert inst.run() == 0
    assert asked == []
    assert (home / ".claude" / "settings.json").read_text() == snapshot
    assert not list((home / ".claude").glob("*.bak-*"))


def test_backs_up_existing_claude_md(kit, home):
    claude = home / ".claude"
    claude.mkdir()
    (claude / "CLAUDE.md").write_text("old\n")
    make(kit, home)[0].run()
    backup = claude / "CLAUDE.md.bak-20260102-030405"
    assert backup.read_text() == "old\n"
    assert (claude / "CLAUDE.md").is_symlink()


def test_merges_settings_without_dropping_keys(kit, home):
    claude = home / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text(
        json.dumps({"model": "opus", "attribution": {"commit": "x", "extra": 1}})
    )
    make(kit, home)[0].run()
    data = json.loads((claude / "settings.json").read_text())
    assert data["model"] == "opus"
    assert data["attribution"] == {"commit": "", "pr": "", "sessionUrl": False, "extra": 1}


def test_attribution_false_is_left_alone(kit, home):
    claude = home / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text('{"attribution": false}')
    make(kit, home)[0].run()
    assert json.loads((claude / "settings.json").read_text()) == {"attribution": False}


def test_invalid_settings_json_raises_and_is_untouched(kit, home):
    claude = home / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text("{not json")
    with pytest.raises(VibeError):
        make(kit, home)[0].run()
    assert (claude / "settings.json").read_text() == "{not json"


def test_existing_hooks_path_declined(kit, home):
    subprocess.run(["git", "config", "--global", "core.hooksPath", "/other/hooks"], check=True)
    inst, asked = make(kit, home, answers=[False])
    inst.run()
    assert len(asked) == 1 and "/other/hooks" in asked[0]
    assert hooks_path() == "/other/hooks"


def test_existing_hooks_path_accepted(kit, home):
    subprocess.run(["git", "config", "--global", "core.hooksPath", "/other/hooks"], check=True)
    inst, _ = make(kit, home, answers=[True])
    inst.run()
    assert hooks_path() == str(kit / "hooks")


def test_dry_run_changes_nothing(kit, home):
    log = []
    inst, asked = make(kit, home, log=log)
    assert inst.run(dry_run=True) > 0
    assert not (home / ".claude").exists()
    assert hooks_path() == ""
    assert asked == []
    assert all(line.startswith(("[dry-run]", "✓")) for line in log)
