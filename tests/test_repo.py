import subprocess
from pathlib import Path

import pytest

from vibe_kit.errors import VibeError
from vibe_kit.repo import GitHub


class FakeRunner:
    """Returns canned results keyed by command prefix; records every call."""

    def __init__(self, results=None):
        self.results = results or {}
        self.calls: list[tuple[list[str], Path | None]] = []

    def run(self, args, cwd=None, check=True, interactive=False):
        args = list(args)
        self.calls.append((args, cwd))
        for prefix, (code, out) in self.results.items():
            if args[: len(prefix)] == list(prefix):
                return subprocess.CompletedProcess(args, code, out, "err")
        return subprocess.CompletedProcess(args, 0, "", "")

    def commands(self):
        return [c for c, _ in self.calls]


def all_tools(_name):
    return "/usr/bin/x"


OUTSIDE_REPO = {("git", "-C"): (128, "")}


def test_missing_gh(tmp_path):
    gh = GitHub(FakeRunner(OUTSIDE_REPO), which=lambda n: None if n == "gh" else "/x")
    with pytest.raises(VibeError, match="gh"):
        gh.preflight("demo", tmp_path)


def test_not_logged_in(tmp_path):
    runner = FakeRunner({("gh", "auth"): (1, ""), **OUTSIDE_REPO})
    with pytest.raises(VibeError) as e:
        GitHub(runner, which=all_tools).preflight("demo", tmp_path)
    assert e.value.hint == "gh auth login"


def test_inside_other_repo(tmp_path):
    runner = FakeRunner({("git", "-C"): (0, "/work/big\n")})
    with pytest.raises(VibeError, match="/work/big"):
        GitHub(runner, which=all_tools).preflight("demo", tmp_path)


def test_missing_parent(tmp_path):
    with pytest.raises(VibeError, match="폴더가 없습니다"):
        GitHub(FakeRunner(OUTSIDE_REPO), which=all_tools).preflight("demo", tmp_path / "nope")


def test_existing_local_dir(tmp_path):
    (tmp_path / "demo").mkdir()
    with pytest.raises(VibeError, match="이미 존재"):
        GitHub(FakeRunner(OUTSIDE_REPO), which=all_tools).preflight("demo", tmp_path)


def test_preflight_ok_with_owner(tmp_path):
    path = GitHub(FakeRunner(OUTSIDE_REPO), which=all_tools).preflight("me/demo", tmp_path)
    assert path == tmp_path / "demo"


def test_creates_when_remote_missing(tmp_path):
    runner = FakeRunner({("gh", "repo", "view"): (1, "")})
    path, created = GitHub(runner).create_or_clone("demo", tmp_path, private=True)
    assert created and path == tmp_path / "demo"
    assert ["gh", "repo", "create", "demo", "--private", "--add-readme", "--clone"] in runner.commands()
    assert runner.calls[-1][1] == tmp_path


def test_public_flag(tmp_path):
    runner = FakeRunner({("gh", "repo", "view"): (1, "")})
    GitHub(runner).create_or_clone("demo", tmp_path, private=False)
    assert "--public" in runner.commands()[-1]


def test_clones_when_remote_exists(tmp_path):
    runner = FakeRunner()
    path, created = GitHub(runner).create_or_clone("me/demo", tmp_path)
    assert not created and path == tmp_path / "demo"
    assert ["gh", "repo", "clone", "me/demo"] in runner.commands()
    assert not any(c[:3] == ["gh", "repo", "create"] for c in runner.commands())


def test_create_failure_shows_stderr(tmp_path):
    runner = FakeRunner({("gh", "repo", "view"): (1, ""), ("gh", "repo", "create"): (1, "")})
    with pytest.raises(VibeError) as e:
        GitHub(runner).create_or_clone("demo", tmp_path)
    assert e.value.hint == "err"


def test_commit_and_push(tmp_path):
    runner = FakeRunner({("git", "diff", "--cached"): (1, "")})
    assert GitHub(runner).commit_and_push(tmp_path, "chore: initial setup")
    cmds = runner.commands()
    assert ["git", "commit", "-m", "chore: initial setup"] in cmds
    assert cmds[-1] == ["git", "push", "-u", "origin", "HEAD"]


def test_nothing_to_commit_skips_push(tmp_path):
    runner = FakeRunner({("git", "diff", "--cached"): (0, "")})
    assert not GitHub(runner).commit_and_push(tmp_path, "chore: initial setup")
    assert not any(c[:2] == ["git", "push"] for c in runner.commands())
