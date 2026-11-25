---
name: bootstrap
description: Start a new project in two phases — decide the stack with the user, then scaffold a minimal runnable skeleton. Use right after `vibe new`, or when the user says /bootstrap.
---

# Bootstrap

Run the phases in order. Do not write project code during Phase 1.

## Phase 1 — Decision

1. Ask, in one message:
   - What is the project for, and who uses it?
   - Any required language, framework, platform, hosting, or budget?
   - Any preferences (familiar tools, style), and deadlines?
2. Sort every answer into a short table:
   - **Hard constraint** — must follow.
   - **Soft preference** — default; challenge it with reasons if something is clearly better.
   - **Open** — not specified.
3. For the open/soft parts, propose 2–3 stack options. For each: one-line summary, why it fits, main trade-off. Mark one as recommended.
4. Wait for the user to choose (or adjust). Repeat 3 if needed. **No code until a choice is made.**

## Phase 2 — Scaffold

1. Fill the project `CLAUDE.md` (keep it short):
   - Overview, constraints (hard/soft), structure, commands.
   - ADRs, one line each: `YYYY-MM-DD decision — reason`, including rejected options worth remembering.
   - Make sure `/CLAUDE.md` is in `.gitignore`.
2. Create the directory structure and the smallest skeleton that runs: entry point, one passing test, run/test commands.
3. Verify it actually runs and the test passes; report the exact commands used.
4. Commit in meaningful units (e.g. `chore: add project skeleton`, `test: add smoke test`), one-line English messages, no co-author lines. Push.
5. End with: what was created, how to run it, and the suggested next step.
