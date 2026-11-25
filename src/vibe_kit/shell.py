"""Thin subprocess wrapper so callers can be tested with a fake runner."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Protocol, Sequence


class Runner(Protocol):
    def run(
        self,
        args: Sequence[str],
        cwd: Path | None = None,
        check: bool = True,
        interactive: bool = False,
    ) -> subprocess.CompletedProcess[str]: ...


class SubprocessRunner:
    """Runs real commands. Captures output unless `interactive` is set."""

    def run(
        self,
        args: Sequence[str],
        cwd: Path | None = None,
        check: bool = True,
        interactive: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args),
            cwd=cwd,
            check=check,
            text=True,
            capture_output=not interactive,
        )
