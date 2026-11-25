import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "commit-msg"


def run_hook(tmp_path: Path, message: str) -> tuple[int, str, str]:
    msg = tmp_path / "COMMIT_EDITMSG"
    msg.write_text(message)
    proc = subprocess.run(["sh", str(HOOK), str(msg)], capture_output=True, text=True)
    return proc.returncode, msg.read_text(), proc.stderr


def test_hook_is_executable():
    assert os.access(HOOK, os.X_OK)


@pytest.mark.parametrize(
    "message",
    [
        "feat: add login page\n",
        "fix(api): handle empty body\n",
        "chore!: drop python 3.9\n",
        "Add login page\n",
        "Initial commit",
        "docs: update readme\n\n# Please enter the commit message\n# Lines starting with '#' are ignored\n",
        "test: cover parser\n# ------------------------ >8 ------------------------\ndiff --git a/x b/x\n+line\n",
        "Merge branch 'dev' into main\n\n# Conflicts:\n#\tfoo.py\n",
        "Merge pull request #1 from a/b\n\nSome PR title\n",
        'Revert "feat: add x"\n\nThis reverts commit abc123.\n',
        "fixup! feat: add x\n",
        "squash! feat: add x\n",
    ],
)
def test_accepts(tmp_path, message):
    code, _, err = run_hook(tmp_path, message)
    assert code == 0, err


@pytest.mark.parametrize(
    "message",
    [
        "",
        "# only a comment\n",
        "feat: add x\n\nlonger body explaining things\n",
        "wip\n",
        "add login page\n",
        "feature: add x\n",
        "feat:add x\n",
        "feat: 로그인 추가\n",
        "로그인 추가\n",
    ],
)
def test_rejects(tmp_path, message):
    code, _, err = run_hook(tmp_path, message)
    assert code == 1
    assert "commit-msg:" in err


@pytest.mark.parametrize(
    "trailer",
    [
        "Co-Authored-By: Claude <noreply@anthropic.com>",
        "co-authored-by: Someone <a@b.c>",
        "CO-AUTHORED-BY: X <x@y.z>",
        "  Co-authored-by: Indented <i@j.k>",
    ],
)
def test_strips_co_author(tmp_path, trailer):
    code, text, err = run_hook(tmp_path, f"feat: add x\n\n{trailer}\n")
    assert code == 0, err
    assert "co-authored-by" not in text.lower()
    assert text.startswith("feat: add x")


def test_strips_co_author_then_rejects_remaining_body(tmp_path):
    code, text, _ = run_hook(tmp_path, "feat: add x\n\nbody\nCo-Authored-By: C <c@d.e>\n")
    assert code == 1
    assert "co-authored-by" not in text.lower()
