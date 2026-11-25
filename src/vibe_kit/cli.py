"""Typer entry point: `vibe install`, `vibe new`."""

from __future__ import annotations

import typer

app = typer.Typer(help="바이브코딩 프로젝트 초기 세팅 자동화", no_args_is_help=True)


@app.callback()
def main() -> None:
    """vibe-kit CLI."""
