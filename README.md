# vibe-kit

바이브코딩 프로젝트 초기 세팅을 자동화하는 CLI입니다.

- `vibe install`: Claude Code와 git 전역 설정(규칙, 커밋 훅, attribution 끄기, `/bootstrap` 스킬)을 한 번에 설치합니다.
- `vibe new <name>`: GitHub 레포를 만들고 템플릿을 적용해 push한 뒤 `claude "/bootstrap"`으로 스택 결정과 스캐폴딩을 시작합니다.

## 요구 사항

- Python 3.10+, [pipx](https://pipx.pypa.io)
- git, [GitHub CLI](https://cli.github.com) (`gh auth login` 완료)
- [Claude Code](https://code.claude.com) (`claude` 명령, `/bootstrap` 실행 시)

## 설치

```sh
git clone https://github.com/oyslucy/vibe-kit.git ~/Desktop/vibe-kit
pipx install -e ~/Desktop/vibe-kit   # editable 권장: 레포를 수정하면 바로 반영
vibe install                         # 전역 설정 설치 (--dry-run으로 미리보기)
```

editable(`-e`)로 설치하면 심볼릭 링크와 hooksPath가 clone한 레포를 가리킵니다. `pipx install git+https://github.com/oyslucy/vibe-kit.git`처럼 일반 설치를 하면 패키지에 번들된 사본을 가리킵니다. 다른 위치의 자산을 쓰려면 `VIBE_KIT_HOME=/path/to/vibe-kit`을 지정하세요.

`vibe install`은 여러 번 실행해도 결과가 같습니다. 이미 설정된 항목은 건너뜁니다.

| 옵션 | 설명 |
| --- | --- |
| `--dry-run` | 아무것도 바꾸지 않고 할 일만 출력 |
| `-y`, `--yes` | 기존 `core.hooksPath` 덮어쓰기 확인을 자동 승인 |

## 설치되는 위치

| 항목 | 위치 | 방식 |
| --- | --- | --- |
| 전역 규칙 | `~/.claude/CLAUDE.md` → `global/CLAUDE.md` | 심볼릭 링크 (기존 파일은 `CLAUDE.md.bak-YYYYmmdd-HHMMSS`로 백업) |
| 커밋 훅 | `git config --global core.hooksPath` → `hooks/` | 전역 git 설정 (기존 값이 있으면 확인 후 덮어씀) |
| attribution 끄기 | `~/.claude/settings.json`의 `attribution` | `{"commit": "", "pr": "", "sessionUrl": false}` 병합, 다른 키는 유지 |
| bootstrap 스킬 | `~/.claude/skills/bootstrap` → `skills/bootstrap` | 심볼릭 링크 |

### commit-msg 훅 규칙

- `Co-Authored-By:` 줄은 대소문자와 상관없이 자동으로 지웁니다.
- 주석과 빈 줄을 뺀 메시지가 정확히 한 줄이어야 합니다.
- `type: 설명`(feat|fix|chore|docs|refactor|test|style|perf, scope와 `!` 허용) 형식이거나 대문자로 시작하는 영어 문장이어야 합니다.
- git이 자동으로 만드는 메시지(`Merge ...`, `Revert "..."`, `fixup!`, `squash!`, `amend!`)는 통과합니다.

> `core.hooksPath`를 전역으로 설정하면 각 레포의 `.git/hooks/`는 무시됩니다. husky 등 레포별 훅을 쓰는 프로젝트에서는 `git config core.hooksPath .husky`처럼 로컬 설정으로 덮어쓰세요.

## 사용법

```sh
vibe new my-app                      # ~/Desktop/my-app, private 레포
vibe new my-app --public --dir ~/code
vibe new my-org/my-app --no-claude   # 조직 레포, bootstrap 생략
```

동작 순서:

1. 검사: gh 설치와 로그인 여부, `--dir` 존재 여부, `--dir`이 다른 git 레포 안에 있지 않은지, 같은 이름의 로컬 폴더가 없는지 확인합니다.
2. `--dir`에서 `gh repo create <name> --add-readme --clone`을 실행합니다. 같은 이름의 원격 레포가 이미 있으면 `gh repo clone`만 합니다.
3. `templates/project`를 복사합니다. 이미 있는 파일은 유지하고, `.gitignore`는 병합하며, `/CLAUDE.md`를 항상 포함합니다.
4. `chore: initial setup`으로 커밋하고 push합니다.
5. `--no-claude`가 아니면 그 폴더에서 `claude "/bootstrap"`을 실행합니다.

| 옵션 | 기본값 |
| --- | --- |
| `--private` / `--public` | `--private` |
| `--dir` | `~/Desktop` |
| `--no-claude` | 끔 |

## 제거

```sh
rm ~/.claude/CLAUDE.md ~/.claude/skills/bootstrap   # 심볼릭 링크만 삭제
# 백업을 되돌리려면: mv ~/.claude/CLAUDE.md.bak-<timestamp> ~/.claude/CLAUDE.md
git config --global --unset core.hooksPath          # 이전 값이 있었다면 다시 설정
# ~/.claude/settings.json에서 "attribution" 항목 삭제 (attribution을 다시 켜려면)
pipx uninstall vibe-kit
```

## 개발

```sh
uv venv && uv pip install -e '.[dev]'   # 또는 python -m venv .venv && pip install -e '.[dev]'
.venv/bin/pytest
```
