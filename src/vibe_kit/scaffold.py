"""Apply templates/project to a project directory."""

from __future__ import annotations

from pathlib import Path

# Stored without the dot so the template's ignore rules don't apply to vibe-kit itself.
RENAMES = {"gitignore": ".gitignore"}
CLAUDE_IGNORE = "/CLAUDE.md"


def apply_template(template_dir: Path, dest: Path, name: str) -> list[Path]:
    """Copy template files into dest. Existing files are kept; .gitignore is merged.

    Returns the files created or changed.
    """
    changed: list[Path] = []
    for src in sorted(template_dir.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(template_dir)
        target = dest / rel.parent / RENAMES.get(rel.name, rel.name)
        text = src.read_text().replace("{{name}}", name)
        if target.name == ".gitignore":
            if merge_lines(target, text.splitlines()):
                changed.append(target)
        elif not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
            changed.append(target)
    gitignore = dest / ".gitignore"
    if merge_lines(gitignore, [CLAUDE_IGNORE]) and gitignore not in changed:
        changed.append(gitignore)
    return changed


def merge_lines(path: Path, lines: list[str]) -> bool:
    """Append lines missing from path (comments/blank lines only if the file is new)."""
    if not path.exists():
        path.write_text("\n".join(lines).rstrip("\n") + "\n")
        return True
    existing = path.read_text()
    present = {line.strip() for line in existing.splitlines()}
    missing = [ln for ln in lines if ln.strip() and not ln.startswith("#") and ln.strip() not in present]
    if not missing:
        return False
    prefix = "" if existing.endswith("\n") or not existing else "\n"
    path.write_text(existing + prefix + "\n".join(missing) + "\n")
    return True
