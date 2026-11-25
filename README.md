# vibe-kit

A CLI that automates the initial setup of vibe-coding projects.

- `vibe install`: installs global Claude Code and git settings in one go: rules, a commit hook, attribution turned off, and the `/bootstrap` skill.
- `vibe new <name>`: creates a GitHub repo, applies the project template, pushes it, then starts stack selection and scaffolding with `claude "/bootstrap"`.

## Requirements

- Python 3.10+, [pipx](https://pipx.pypa.io)
- git, [GitHub CLI](https://cli.github.com), logged in with `gh auth login`
- [Claude Code](https://code.claude.com): the `claude` command, used to run `/bootstrap`

## Install

```sh
git clone https://github.com/oyslucy/vibe-kit.git ~/Desktop/vibe-kit
pipx install -e ~/Desktop/vibe-kit   # editable recommended: repo edits apply immediately
vibe install                         # install global settings (preview with --dry-run)
```

With an editable (`-e`) install, the symlinks and `core.hooksPath` point at your clone. A regular install, such as `pipx install git+https://github.com/oyslucy/vibe-kit.git`, points them at the copy bundled in the package instead. To use assets from another location, set `VIBE_KIT_HOME=/path/to/vibe-kit`.

`vibe install` is idempotent: running it again gives the same result, and it skips anything already set up.

| Option | Description |
| --- | --- |
| `--dry-run` | Show what would change without changing anything |
| `-y`, `--yes` | Overwrite an existing `core.hooksPath` without asking |

## What gets installed where

| Item | Location | How |
| --- | --- | --- |
| Global rules | `~/.claude/CLAUDE.md` → `global/CLAUDE.md` | Symlink (an existing file is backed up as `CLAUDE.md.bak-YYYYmmdd-HHMMSS`) |
| Commit hook | `git config --global core.hooksPath` → `hooks/` | Global git config (asks before overwriting an existing value) |
| Attribution off | `attribution` in `~/.claude/settings.json` | Merges `{"commit": "", "pr": "", "sessionUrl": false}` and keeps all other keys |
| Bootstrap skill | `~/.claude/skills/bootstrap` → `skills/bootstrap` | Symlink |

### commit-msg hook rules

- Removes `Co-Authored-By:` lines automatically, in any letter case.
- Requires exactly one line once comments and blank lines are removed.
- The line must be `type: description` (feat|fix|chore|docs|refactor|test|style|perf; a scope and `!` are allowed) or an English sentence starting with a capital letter.
- Lets messages that git writes itself through: `Merge ...`, `Revert "..."`, `fixup!`, `squash!`, `amend!`.

> Setting `core.hooksPath` globally makes git ignore each repo's `.git/hooks/`. In projects with per-repo hooks such as husky, override it locally, for example `git config core.hooksPath .husky`.

## Usage

```sh
vibe new my-app                      # ~/Desktop/my-app, private repo
vibe new my-app --public --dir ~/code
vibe new my-org/my-app --no-claude   # organization repo, skip bootstrap
```

What it does:

1. Checks that gh is installed and logged in, that `--dir` exists and is not inside another git repo, and that no local folder of the same name exists.
2. Runs `gh repo create <name> --add-readme --clone` in `--dir`. If a remote repo of that name already exists, it only runs `gh repo clone`.
3. Copies `templates/project`. Existing files are kept, `.gitignore` is merged, and `/CLAUDE.md` is always added to it.
4. Commits with `chore: initial setup` and pushes.
5. Runs `claude "/bootstrap"` in the new folder, unless `--no-claude` is given.

| Option | Default |
| --- | --- |
| `--private` / `--public` | `--private` |
| `--dir` | `~/Desktop` |
| `--no-claude` | off |

## Uninstall

```sh
rm ~/.claude/CLAUDE.md ~/.claude/skills/bootstrap   # removes the symlinks only
# to restore a backup: mv ~/.claude/CLAUDE.md.bak-<timestamp> ~/.claude/CLAUDE.md
git config --global --unset core.hooksPath          # set the old value again if you had one
# to turn attribution back on, delete the "attribution" entry from ~/.claude/settings.json
pipx uninstall vibe-kit
```

## Development

```sh
uv venv && uv pip install -e '.[dev]'   # or: python -m venv .venv && pip install -e '.[dev]'
.venv/bin/pytest
```
