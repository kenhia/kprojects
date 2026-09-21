# Sprint 010 — Three installer papercuts: duplicate ignores, an invisible stack, a block prettier rejects

2026-09-21 · korg proposal 2976 · covers #1288, #1289, #2509

Run as karc leg `kprojects-e4a1b5` on kai, one slice of program korg:2981
("Low-hanging fruit — experiment 1"), under an overseer on cleo.

## Goal

Three small, long-open installer complaints, each with its call already made
by the overseer so this leg did not re-decide them:

- **#1288** — `cargo new` writes `/target`; the installer appended `target/`
  beside it on every Rust re-apply. Call: never add a second line, and leave
  cargo's own line alone.
- **#1289** — detection reads the repo root only, so hv-simulator's five
  `pyproject.toml` files (under `engine/` and `tools/*`, none at the top) are
  invisible and it silently gets `other`. Call: option 3 from the work item —
  report what was found and name the flag, still choose `other`.
- **#2509** — prettier wants a blank line inside each managed-block marker, so
  every kproject repo whose gate lints markdown went red at its last
  re-apply. Call: fix the template, not a `.prettierignore` contract.

## Premise check

All three still true on 2026-09-21, checked before any code changed:

- **#1288 holds.** Ran the work item's own repro against `ensure_gitignore`: a
  file containing `# Added by cargo` / `/target` came back with `target/`
  appended.
- **#1289 holds.** `detect_stack(~/src/fun/hv-simulator)` returns `other`; all
  five `pyproject.toml` files are still one and two levels down.
- **#2509 holds, and is not kwebi-local.** Formatting a file carrying the block
  with kwebi's own prettier (3.9.5) produced exactly two edits — after the
  begin marker, before the end marker — and the output was byte-identical
  under prettier's defaults and under kwebi's options. So the requirement is
  prettier's markdown formatter, not a repo setting.

kprojects is not in the cross-project-planning routing table, so no guiding
plan applies.

## Decisions

- **Equivalence by stripping slashes, and nothing cleverer** (#1288).
  `_ignore_key` is `pattern.strip().strip("/")`, which folds the four
  spellings of one directory (`x`, `x/`, `/x`, `/x/`). A real gitignore
  semantics engine would be the wrong tool: the question is only ever "does a
  line already express this intent", and the cheapest comparison that answers
  it is the one a reader can also verify at a glance.
- **A `!x` negation is not a spelling of `x`.** It is the opposite rule, and
  folding it would make the installer *skip* an ignore the repo had explicitly
  un-ignored. Pinned by a test, alongside one proving `/targets` is still seen
  as a different directory — the comparison must not be so loose that it
  swallows a real gap.
- **Cargo's line is left exactly as cargo wrote it.** The work item floated
  replacing `/target` with the wider `target/` and saying so in the output.
  The overseer's call was not to, and it is the better one: rewriting a line
  the user's own toolchain authored, in a file edited on their behalf, buys a
  marginally wider pattern at the cost of a surprise.
- **#1289 is a report, and the scan is deliberately not a fallback.**
  `detect_stack` is untouched and there is a test pinning that hv-simulator's
  shape still yields `other`. Falling back a level was declined on #1260's
  standing reasoning: a vendored dependency's build system must not choose a
  stack, and from outside the repo a `Cargo.toml` in `third_party/` is
  indistinguishable from one in `engine/`. Only the repo knows. So this
  follows `NO_GATE_WARNING`'s precedent — name what was found and the lever
  that acts on it, write nothing.
- **Depth 2, with a skip list.** `tools/<name>/pyproject.toml` needs two
  levels to be visible at all. The skip list (`node_modules`, `target`,
  `build`, `dist`, `vendor`, `third_party`, virtualenvs, caches) exists
  because those are exactly where a foreign build system's markers live — the
  hint would be actively misleading without it. Dotted directories are skipped
  too, and an unreadable directory is stepped over rather than failing an
  install.
- **The hint fires only when it has something to say**: detection settled for
  `other` *and* no `--stack` was passed. A flag on the command line has
  already answered the question the hint asks. Three tests, one per silent
  case.
- **The blank lines go in the renderer, so the block stays byte-identical
  everywhere** (#2509, preserving #1254). The body is `strip("\n")`ed before
  the markers are added, so the result does not depend on a template's
  trailing newlines — a stack stanza gaining or losing one cannot move the
  markers.

## Shipped

- `src/kprojects/cli.py`
  - `render_block` emits a blank line after the begin marker and before the
    end marker (#2509).
  - `_ignore_key` and a rewritten `ensure_gitignore` comparing by it (#1288).
  - `SCAN_SKIP_DIRS`, `SCAN_DEPTH`, `find_subdirectory_markers`,
    `warn_subdirectory_markers`, called from `main` only when detection chose
    `other` unaided (#1289).
  - `.korg-sprint-proposal` added to `BASE_IGNORES` (#2990, see below).
- `tests/test_install.py` — 24 tests across three new sections: prettier-safe
  markers, subdirectory markers as report-not-decision, and gitignore
  equivalence (including the two for #2990). 107 tests, from 83.
- `CLAUDE.md`, `.github/copilot-instructions.md` — the managed block
  regenerated via `just apply-self`, plus four new Project bullets recording
  the behaviour and its reasoning, identical in both files.

## Verification

`just check` green — ruff format, ruff check, ty, 107 tests.

Every new test was watched failing first: 15 failures on the first run, with
`target/` (the byte-identical spelling) and the "detection is unchanged" test
correctly passing from the start.

**#2509's stated acceptance met.** `just apply-self` regenerated both agent
files, and `prettier --check` passes on both — under prettier's defaults and
under kwebi's options — with no `.prettierignore` entry anywhere. Before the
change, the same check reported exactly the two marker edits.

**#1289 verified against the repo that raised it**, read-only:
`warn_subdirectory_markers(~/src/fun/hv-simulator)` finds all five
`pyproject.toml` files, names `--stack python`, and `detect_stack` still
returns `other`. hv-simulator's working tree was confirmed untouched
afterwards.

Both checks ran **on kai**, which is where hv-simulator, kwebi and this repo
all live — the host that would do the work.

## Repaired in passing

**#2990 — `.korg-sprint-proposal` added to `BASE_IGNORES`.** `start-sprint`
writes that file at the root of every repo it starts a sprint in, and its own
instructions say it must never be committed — yet the installer did not ignore
it, so repos acquired the line by hand (this repo at `.gitignore:3`, and kaed's
as quoted in #1288).

Filed first, deliberately, because the repair test looked unsettled from here:
either `kproject-install` owns the ignore line for a file `start-sprint`
writes, or `start-sprint` does. **The overseer read it the other way and made
the call**, which is recorded for Ken in the program report: the installer
already owns the ignore set for harness-written files, and **#1855 settled
exactly this split for `.sprint-defaults`** — the ignore line is
unconditional, only a seeded file's *contents* are a per-repo decision. That
precedent removes the fork, so it is a repair and it landed here.

One constant and two tests: the marker appears for a fresh repo, and a repo
that already added it by hand gains nothing — the latter exercising #1288's
new comparison on the real case. `just apply-self` on this repo confirmed it:
no `gitignore: added` line, `.gitignore` byte-unchanged.

**The fleet-visible effect arrives with #1409's re-apply**, not now. That is
the same delivery path as the #2509 block fix in this sprint, and it is fine:
until a repo is re-applied it simply keeps whatever it has, which for the two
known cases is the correct line already.

Nothing else. The gate was green on `main` at branch time and no other
pre-existing defect surfaced while working these three.

## Follow-ups

- **#2990** — filed during this sprint, then **resolved in it** once the
  overseer made the call. See "Repaired in passing" above; it is not
  outstanding.
- **#1409** — the fleet re-apply pass was explicitly outside this sprint, and
  its prettier blocker is now cleared. Commented there to say so: repos
  re-applied before this sprint carry a block that reds a markdown-linting
  gate; repos re-applied after do not. kwebi's local `.prettierignore` entry
  was deliberately left in place — it is now harmless rather than
  load-bearing, and dropping it is kwebi's call once the new block reaches it.
