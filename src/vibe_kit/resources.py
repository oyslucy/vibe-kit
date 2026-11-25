"""Locate kit assets (global/, hooks/, skills/, templates/)."""

from __future__ import annotations

import os
from pathlib import Path

from .errors import VibeError

_PKG_DIR = Path(__file__).resolve().parent


def kit_root() -> Path:
    """Return the directory holding kit assets.

    Order: $VIBE_KIT_HOME, the source checkout (editable install), bundled assets.
    """
    env = os.environ.get("VIBE_KIT_HOME")
    if env:
        return Path(env).expanduser().resolve()
    checkout = _PKG_DIR.parent.parent
    if (checkout / "global" / "CLAUDE.md").is_file():
        return checkout
    bundled = _PKG_DIR / "_assets"
    if bundled.is_dir():
        return bundled
    raise VibeError(
        "vibe-kit 자산(global/, hooks/ 등)을 찾을 수 없습니다.",
        hint="레포 경로를 VIBE_KIT_HOME 환경변수로 지정하세요.",
    )
