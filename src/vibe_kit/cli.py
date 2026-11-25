"""Typer entry point: `vibe install`, `vibe new`. Wiring only; logic lives in modules."""

from __future__ import annotations

from pathlib import Path

import typer

from . import installer
from .errors import VibeError
from .resources import kit_root
from .shell import SubprocessRunner

app = typer.Typer(help="바이브코딩 프로젝트 초기 세팅 자동화", no_args_is_help=True)


def _fail(err: VibeError) -> None:
    typer.secho(f"오류: {err.message}", fg=typer.colors.RED, err=True)
    if err.hint:
        typer.echo(f"  → {err.hint}", err=True)
    raise typer.Exit(1)


@app.callback()
def main() -> None:
    """vibe-kit CLI."""


@app.command()
def install(
    dry_run: bool = typer.Option(False, "--dry-run", help="변경 없이 할 일만 출력"),
    yes: bool = typer.Option(False, "--yes", "-y", help="확인 질문에 모두 yes"),
) -> None:
    """전역 설정 설치: ~/.claude/CLAUDE.md, git hooks, attribution 끄기, bootstrap 스킬."""
    try:
        kit = kit_root()
        if not dry_run:
            installer.ensure_hooks_executable(kit)
        steps = installer.default_steps(kit, Path.home(), SubprocessRunner())
        confirm = (lambda _q: True) if yes else (lambda q: typer.confirm(q, default=False))
        count = installer.Installer(steps, confirm, typer.echo).run(dry_run=dry_run)
    except VibeError as e:
        _fail(e)
    if dry_run:
        typer.echo(f"dry-run: 변경 예정 {count}건" if count else "변경할 것이 없습니다.")
    else:
        typer.echo("완료.")
