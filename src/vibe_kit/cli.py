"""Typer entry point: `vibe install`, `vibe new`. Wiring only; logic lives in modules."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer

from . import installer, repo, scaffold
from .errors import VibeError
from .resources import kit_root
from .shell import SubprocessRunner

INITIAL_COMMIT = "chore: initial setup"

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


@app.command()
def new(
    name: str = typer.Argument(..., help="레포 이름 (NAME 또는 OWNER/NAME)"),
    private: bool = typer.Option(True, "--private/--public", help="레포 공개 범위"),
    directory: Path = typer.Option(
        Path.home() / "Desktop", "--dir", help="레포를 만들 상위 폴더", show_default="~/Desktop"
    ),
    no_claude: bool = typer.Option(False, "--no-claude", help="마지막에 claude /bootstrap 실행 안 함"),
) -> None:
    """GitHub 레포를 만들고(이미 있으면 clone) 템플릿을 적용한 뒤 push."""
    runner = SubprocessRunner()
    gh = repo.GitHub(runner)
    parent = directory.expanduser().resolve()
    try:
        gh.preflight(name, parent)
        typer.echo(f"레포 준비 중: {name}")
        path, created = gh.create_or_clone(name, parent, private=private)
        typer.echo(("생성" if created else "기존 레포 clone") + f": {path}")
        scaffold.apply_template(kit_root() / "templates" / "project", path, repo.local_dir_name(name))
        pushed = gh.commit_and_push(path, INITIAL_COMMIT)
        typer.echo(f"커밋·push: {INITIAL_COMMIT}" if pushed else "커밋할 변경이 없습니다.")
    except VibeError as e:
        _fail(e)
    if no_claude:
        typer.echo(f"완료. cd {path}")
        return
    if not shutil.which("claude"):
        typer.secho("claude CLI가 없어 /bootstrap을 건너뜁니다.", fg=typer.colors.YELLOW)
        typer.echo(f"  → 설치 후: cd {path} && claude \"/bootstrap\"")
        return
    runner.run(["claude", "/bootstrap"], cwd=path, check=False, interactive=True)
