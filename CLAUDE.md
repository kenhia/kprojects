<!-- kproject:begin — managed by kprojects; do not edit inside this block -->
## kproject conventions

This project uses the kproject minimal harness
(<https://github.com/kenhia/kprojects>). Keep context small; prefer doing
over ceremony.

### Layout

- `sprints/` — the project's evolution, one record per PR-sized unit of
  work (a "sprint")
  - `planning/` — planning docs; at minimum `roadmap.md` (the general plan)
  - `review/` — more formal reviews as the project matures
  - sprint records: `###-<short-name>.md` for small projects, or a
    `###-<short-name>/` directory of files for larger/more formal ones
  - a sprint record is one informal narrative: goal, decisions, what
    shipped, follow-ups — written during the sprint, not after
  - projects that deploy end the record with a `## Deployed` section:
    what shipped, where, when, and what was verified live — appended
    after the deploy, not predicted before it
- `docs/` — project documentation, architecture, usage
- `.scratch/` — git-ignored scratch space for user or agent ephemera;
  use it instead of /tmp
- `justfile` — dev recipes; default recipe is `@just --list`; `just check`
  runs the CI gates; `just deploy` (or variants) if the project deploys
- `.env` — git-ignored; tokens and environment vars

### Workflow

- One sprint ≈ one PR. Sprint proposals and work items are managed in
  `korg`; durable cross-project knowledge goes in `klams`.
- Mark each work item resolved as its work completes — don't batch the
  resolutions into sprint-ship. A proposal's progress should be readable
  while the sprint is running, which is the only time it is useful.
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
`kproject-install` CLI that applies them to other repos.

- `src/kprojects/harness/` holds the templates and is the only place shared
  conventions are edited — `instructions.md` for what every project gets,
  `tooling/<stack>.md` for the per-stack stanza composed in at the
  `{{TOOLING}}` placeholder, `justfile.<stack>` for the seeded gate. The
  managed blocks in this file and in downstream repos are regenerated from
  them; after editing, run `just apply-self` here and re-run
  `kproject-install` on affected repos. Never edit inside a
  `kproject:begin`/`kproject:end` block by hand.
- The harness ships as **package data**, which is what lets the installer run
  from any machine with no clone:
  `uvx --from git+https://github.com/kenhia/kprojects kproject-install .`
  Never resolve templates relative to `__file__` — that adjacency assumption
  was the bug (#699) that made the old bash installer non-portable.
- Stack is **detected** from the target repo (`Cargo.toml` → rust, `go.mod` →
  go, `CMakeLists.txt` → cmake, `pyproject.toml` → python, else other);
  `--stack` overrides. It is not defaulted, deliberately: see sprint 002.
  `STACK_MARKERS` order decides a polyglot repo — `pyproject.toml` is
  deliberately last, since it also appears carrying nothing but ruff config,
  and `CMakeLists.txt` sits below cargo/go because CMake is often a vendored
  dependency's build system inside those.
- Every seeded gate must fail when it has nothing to assert. Each stack has
  its own way of not doing that: `gofmt -l` exits 0 and prints (003), `clippy`
  skips test targets without `--all-targets`, and `ctest` exits 0 on "No tests
  were found!!!" unless given `--no-tests=error` (006). The `other`
  placeholder exits 1 for the same reason — a TODO gate that succeeds makes
  the block's `just check` promise true in the letter and false in substance.
- Adding a stack is one `STACKS` value, one `STACK_MARKERS` entry, one
  `STACK_IGNORES` entry (`()` is valid) and two files —
  `harness/tooling/<stack>.md` + `harness/justfile.<stack>`. The
  `test_harness_ships_with_the_package` test iterates `STACKS`, so it fails
  until both files exist: that test is the registration check.
- Block markers are matched on the `<!-- kproject:begin` **prefix**, never
  the full line, so repos carrying a block from the retired `install.sh`
  re-apply cleanly with no migration step.
- An existing justfile is never overwritten, but the managed block promises
  `just check` — so when a repo's gate goes by another name the installer
  appends a `check: <gate>` alias, picking by `GATE_RECIPES` priority
  (`gate`, `ci`, `all`) and warning when it recognises none. `test` is
  excluded on purpose: it is one component of a gate, not the aggregate.
  Sprint 004 chose this over rendering each repo's real gate name into the
  block, so the block stays **byte-identical everywhere** (#1254). The blank
  line above the alias's doc comment is load-bearing — `just --list` shows
  the comment directly above a recipe.
- When no gate exists under any name there is nothing to alias, so the
  installer still writes nothing and `NO_GATE_WARNING` carries the
  consequence instead — that the block's promise is now false here (#1259).
  Seeding a TODO `check` into someone's justfile was declined in sprint 006:
  kpidash showed a seeded guess configures the wrong thing, since its real
  gate was readable only from its own `CMakeLists.txt`.
- The `/kproject-init` skill does not live here. `agent-skills` owns skill
  content, kprojects owns the harness, k-homelab delivers both.
- Keep `CLAUDE.md` and `.github/copilot-instructions.md` equivalent —
  same facts in both, outside the managed block too.
- `just check` is the CI gate (`ruff format --check`, `ruff check`, `ty`,
  `pytest`).
