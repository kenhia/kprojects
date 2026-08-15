# Sprint 006 — The harness debt the rollout surfaced

2026-08-15 · korg proposal 1270 · covers #1258, #1259, #1260, #1166

## Goal

Clear four items in one pass. Three of them were filed by the #737 rollout as
it hit them — a dozen repos through the installer is a decent sample, and what
it surfaced is a single theme with three faces: **what does `just check` mean
where the harness cannot supply one?** The fourth (#1166) is unrelated and
touches `instructions.md` rather than the installer.

Two premises in the proposal notes had already moved by the time this started,
both recorded in same-day comments: kpidash migrated in sprint 014 as `other`
with a real hand-written gate, which removed the sequencing pressure on #1260
and took kpidash off #1259's list. Worth re-reading the comments before
trusting proposal notes written a day earlier.

## Decisions

- **C/CMake earns the fifth stack** (#1260, Ken's call). The research comment
  argued the other way — kpidash's gate came from its own documented
  `-DTESTS_ONLY=ON` convention, which no generic template could have produced,
  and the population is still one. The counter is the one 1195 already
  settled for Go: the enum is cheap to change *now*, and adding a stack is data
  plus two files by design. `CMakeLists.txt` is a real build definition; the
  harness should be able to name it.
- **`CMakeLists.txt` ranks below cargo/go and above `pyproject.toml`.** Above
  pyproject because it defines a build and pyproject doubles as tool config —
  kpidash is exactly that shape (C at the root, Python only in
  `clients/kpidash-client/`). Below cargo and go because CMake commonly appears
  as a *vendored dependency's* build system inside a Rust or Go repo, where it
  is not what owns the build.
- **The cmake gate's trap is `ctest`.** Every stack added so far has had one —
  `clippy` skipping test targets, `gofmt -l` exiting 0 while printing offenders
  (003's trap). CMake's is that **bare `ctest` exits 0 on "No tests were
  found!!!"**, so the gate passes loudest when there is least to check.
  `--no-tests=error` is the fix and it is the load-bearing flag in the
  template. Measured, not assumed: bare `ctest` returned 0 on an empty suite,
  the seeded gate returned 8.
- **The gate builds in `build-check/`, its own tree.** A cross-compiled repo
  already keeps one build tree per target and two configurations cannot share a
  `CMakeCache.txt`. kpidash has `build-native/` and `build-pi5/`; the gate must
  not fight either.
- **No formatter in the cmake gate.** `clang-format` asserts nothing without a
  committed `.clang-format`, and #1258's own rule is to add no dependency to
  make a gate. `just fmt` is noted in the stanza as something to add once the
  repo has the config — an honest omission over a recipe that fails on a
  missing tool.
- **No gate under any name → still write nothing, but say what broke** (#1259,
  option 3). Seeding a TODO `check` into someone's justfile was the considered
  alternative and was declined: kpidash is the evidence, where a seeded TODO
  would have been one more thing to delete and a seeded guess
  (`cmake -B build && ctest`) would have configured the wrong thing entirely.
  What changes is that `NO_GATE_WARNING` names the **consequence** — that the
  block's promise is now false in this repo — rather than only the missing
  recipe. The lever is already evidenced to work: kpidash's gap was noticed and
  closed in one sitting off the weaker warning.
- **`tooling/other.md` stops being empty** (#1258). It was empty *by design*,
  and the design was wrong: it is the per-stack guidance slot and the file an
  agent in an `other` repo actually reads. It now carries the four points
  homelab-ai-plan derived unaided (PR #1) — ask what the repo can actually get
  wrong, add no dependency, skip what isn't yours to verify, and negative-test
  it. The last is the one most likely to be skipped under time pressure and the
  one that matters most.
- **The seeded `other` gate now exits 1.** This is the sprint's one behaviour
  change beyond guidance, and it follows from the sprint's own argument: a TODO
  gate that exits 0 satisfies the block's `just check` promise in the letter
  while asserting nothing — the exact "passes by not looking" gate this project
  keeps refusing to ship, and worse than #1259's case because no warning
  accompanies it. Failing until written is the honest state. It reaches only
  **freshly seeded** `other` repos: `_seed()` never touches an existing
  justfile, so no migrated repo changes on re-apply.
- **#1166 is one bullet in `instructions.md`.** Mark each work item resolved as
  its work completes rather than batching into sprint-ship. The evidence is
  kfdc's Fire Missions card reading 1/10 on a sprint nearly done — a progress
  bar that says nothing while it would be useful, then jumps to 10/10.

## Shipped

- `src/kprojects/cli.py` — `cmake` in `STACKS`, `STACK_MARKERS` (reordered and
  re-commented), `STACK_IGNORES`; `NO_GATE_WARNING` hoisted to a constant and
  emitted as three lines.
- `src/kprojects/harness/justfile.cmake`, `harness/tooling/cmake.md` — new.
- `src/kprojects/harness/tooling/other.md` — filled, was empty.
- `src/kprojects/harness/justfile.other` — placeholder gate exits 1, with the
  reasoning above it.
- `src/kprojects/harness/instructions.md` — the #1166 bullet.
- `tests/test_install.py` — 68 tests, up from 55.
- `CLAUDE.md`, `.github/copilot-instructions.md` — cmake in the detection list,
  a new "every seeded gate must fail when it has nothing to assert" invariant
  collecting all four traps, and the #1259 rule. Same facts in both.

## Verification

Written test-first: 11 new tests red before implementation, green after.
`just check` passes — ruff format, ruff check, ty, 68 tests.

`just apply-self` regenerated both agent files; the only managed-block diff is
the #1166 bullet, as expected.

**The cmake gate was negative-tested** — the requirement this sprint is
shipping for `other`, applied to itself. Against throwaway CMake projects with
real `cmake`/`ctest`:

| Case | Expected | Got |
|---|---|---|
| no tests registered | fail | exit 8 |
| bare `ctest`, same tree | *(the trap)* | **exit 0**, "No tests were found!!!" |
| one passing test | pass | exit 0 |
| one failing test | fail | exit 8 |

`just --list` on the seeded cmake justfile shows clean doc comments — the
multi-line rationale block does not leak in, because the blank line above the
doc comment (004's lesson) is there. `just clean` removes the tree.

A throwaway repo reproducing kpidash's pre-migration shape (`_default` and
`publish`, no gate) produced the three-line warning and a byte-identical
justfile. A fresh `other` install failed `just check` with the placeholder's
message, as intended.

## Follow-ups

- **kpidash can re-apply with `--stack cmake`** whenever convenient. It is
  cheap — the tooling stanza and gitignore are the only changes, and its
  hand-written gate is better than the template's and should stay. Its
  `build-native/`/`build-pi5/` trees are what `build-*/` in `STACK_IGNORES` was
  written for.
- **The cmake stanza's advice is untested against a second C repo**, because
  there isn't one. If one arrives and the generic configure/build/ctest gate
  turns out not to fit, that is the signal that #1260's research comment was
  right and the stack should collapse back into `other`.
- **`STACK_MARKERS` now has a real precedence question in it.** A repo with
  `CMakeLists.txt` and `pyproject.toml` at the root gets cmake; that is pinned
  by test and is right for kpidash, but it is the first ordering call made
  about a marker that is not the weakest signal. Revisit if a polyglot repo
  picks wrong.
- **#1254's own known follow-up is still untriggered** — a repo defining both
  `gate` and `ci` gets `gate` silently.
