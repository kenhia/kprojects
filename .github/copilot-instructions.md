<!-- kproject:begin — managed by kprojects/install.sh; do not edit inside this block -->
## kproject conventions

This project uses the kproject minimal harness
(`~/src/ai-agents/kprojects`). Keep context small; prefer doing over
ceremony.

### Layout

- `sprints/` — the project's evolution, one record per PR-sized unit of
  work (a "sprint")
  - `planning/` — planning docs; at minimum `roadmap.md` (the general plan)
  - `review/` — more formal reviews as the project matures
  - sprint records: `###-<short-name>.md` for small projects, or a
    `###-<short-name>/` directory of files for larger/more formal ones
  - a sprint record is one informal narrative: goal, decisions, what
    shipped, follow-ups — written during the sprint, not after
- `docs/` — project documentation, architecture, usage
- `.scratch/` — git-ignored scratch space for user or agent ephemera;
  use it instead of /tmp
- `justfile` — dev recipes; default recipe is `@just --list`; `just check`
  runs the CI gates; `just deploy` (or variants) if the project deploys
- `.env` — git-ignored; tokens and environment vars

### Workflow

- One sprint ≈ one PR. Sprint proposals and work items are managed in
  `korg`; durable cross-project knowledge goes in `klams`.
- If the korg or klams MCP tools are unavailable in your session, say so
  up front — don't silently work around missing infrastructure.
- TDD preferred: write the failing test first when practical.

### Tooling preferences

- Python managed by `uv`; lint/format with `ruff`; typecheck with `ty`
  (astral toolchain)
- License is MIT unless specifically directed otherwise
<!-- kproject:end -->

## Project

kprojects is the harness itself: single-source agent conventions plus the
tooling to apply them to other repos.

- `harness/instructions.md` is the only place shared conventions are
  edited. The managed blocks in this file and in downstream repos are
  regenerated from it by `./install.sh <repo>` — after editing, re-run
  `./install.sh .` here and on affected repos. Never edit inside a
  `kproject:begin`/`kproject:end` block by hand.
- `skills/kproject-init/SKILL.md` is the migration/init skill; deploy with
  `./install.sh --skill` (copies to `~/.claude/skills/`).
- Keep `CLAUDE.md` and `.github/copilot-instructions.md` equivalent —
  same facts in both, outside the managed block too.
- `just check` is the CI gate (`bash -n`, shellcheck when available).
