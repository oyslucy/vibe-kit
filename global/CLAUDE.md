# Global rules

## Commits
- Commit in meaningful units, one concern per commit.
- One-line English message, no body: `type: description` (feat|fix|chore|docs|refactor|test|style|perf).
- Never add `Co-Authored-By` or any line crediting Claude, in commits or PRs.

## Code
- Follow SOLID: one responsibility per module, depend on abstractions at I/O boundaries (shell, network, fs) so logic is testable.
- Prefer small modules with clear names over large files; no speculative abstractions.

## Tech stack decisions
- Split the user's conditions into:
  - **Hard constraint**: must follow, no debate.
  - **Soft preference**: the default, but push back with reasons if a better option exists.
- For anything unspecified, propose 2–3 options with trade-offs and a recommendation; let the user pick before writing code.

## New projects
- Create a project `CLAUDE.md` with: overview, directory structure, and decisions as ADRs (`decision — one-line reason`).
- Keep it current as the project changes; the next session should be able to start from it alone.
- Add `/CLAUDE.md` to the project's `.gitignore`.
