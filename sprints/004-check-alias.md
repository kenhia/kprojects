# Sprint 004 — The installer makes `just check` true

2026-08-14 · korg proposal 1255 · covers #1254

## Goal

Stop the managed block from asserting something false.

The block tells every agent that **`just check` runs the CI gates**. But
`_seed()` returns early when a justfile already exists — correct behaviour, and
what makes "extend, don't replace" safe — so in a repo whose gate goes by
another name the installer wrote a promise it did not keep, *inside a region
the repo is not allowed to hand-correct*. Same class as #725: guidance
hard-coded in a managed block, discoverable only by running the command and
watching `just` fail.

Hit for real by **klams** (sprint 044, PR #48), whose gate is `just gate` and
which had no `check` at all — its work item had said "extend the seeded
`just check`" and there was nothing to extend. **klams-mind** (korg:1251) is
the same shape and is queued. The rollout's standing rule was "file a work item
if a second repo hits it"; this was the second, and roughly ten repos remain in
korg #737's batches 3–6.

## Decisions

- **Append a `check: <gate>` alias — fix (a), not fix (b).** #1254 deliberately
  left this open, and the choice is really about what `check` *is*. Taking (a)
  settles it: `check` is a **convention every repo adopts**, not a label for
  whatever the repo already does. The consequence is the reason to prefer it —
  the managed block's text stays **byte-identical across the fleet**, so
  re-apply remains a pure replace and `render_block()` stays a function of the
  stack alone. Fix (b) — rendering each repo's detected gate name into the
  block — is more faithful per repo but makes the block's content a function of
  the target, weakening the property that makes it safe to regenerate.
  Confirmed in practice: `just apply-self` after this change produced **no diff
  at all** in either agent file.
- **An alias, not a second recipe.** `check: gate` with an empty body, matching
  what klams arrived at by hand. The gate keeps a single definition and the
  name CI already invokes stays authoritative — duplicating the recipe body
  would create two things to keep in step.
- **`GATE_RECIPES = ("gate", "ci", "all")`, first match wins.** These are the
  three #1254 named. **`test` is deliberately excluded**: it is one *component*
  of a gate, not the aggregate, so aliasing `check` to it would keep the
  block's promise in the letter while making `just check` skip lint and
  typecheck — a worse failure than the honest one, because it looks like it
  passed.
- **No recognisable gate → warn and write nothing.** Guessing at an unknown
  recipe, or emitting a `check` that points at nothing, both break the repo.
  The warning names the candidates it looked for. This also preserves the
  existing `test_never_overwrites_an_existing_justfile_or_roadmap` contract for
  a justfile with no recipes at all.
- **Recipe detection is shallow and hand-rolled, not a justfile parser.** We
  only need "is `check` taken, and which gate name is present". The two things
  that read as recipes if you only look for a colon are assignments (`x := y`,
  `set shell := [...]`) and indented recipe bodies, so both are excluded
  explicitly. `alias check := gate` counts as taken — a recipe colliding with
  an alias is a hard error in `just`, so appending there would break the
  justfile outright.
- **The blank line above the alias's doc comment is load-bearing.** Caught by
  the smoke test, not by reasoning: `just --list` shows the comment line
  *directly above* a recipe, so the first draft's three-line rationale block
  rendered as `check  # definition and just gate stays authoritative.` in the
  listing — in every migrated repo, in the place people look first. The
  rationale now sits above a blank line, with a one-line doc comment beneath
  it.

## Shipped

- `src/kprojects/cli.py` — `GATE_RECIPES`, `CHECK_ALIAS`, `_recipe_names()`,
  `ensure_check_recipe()`, called from `apply()` immediately after `_seed()`
  (order matters: a freshly seeded justfile already defines `check`, so the new
  path only ever fires on a justfile the repo brought itself).
- `tests/test_install.py` — 52 tests, up from 38.
- `CLAUDE.md`, `.github/copilot-instructions.md` — the new invariant, in both,
  outside the managed block.

## Verification

Written test-first: 13 new tests red before implementation, green after.
`just check` passes — ruff format, ruff check, ty, 52 tests.

The new tests cover the alias landing while preserving the original file, an
existing `check` recipe being left alone, an existing `check` *alias* being
respected, idempotence across re-runs, `gate` > `ci` > `all` priority, `test`
not counting as a gate, the warn-and-write-nothing path, every shipped
`justfile.<stack>` template needing no alias, no justfile at all, CRLF
preservation, the `just --list` doc comment, and `_recipe_names()` against
assignments, `set` directives, comments, indented bodies, parameterised
recipes and aliases.

End to end against a throwaway repo reproducing klams-mind's documented shape
(`default`, `fmt`, `test`, `gate`, no `check`): the installer reported
``justfile : added `check: gate` alias``, real `just` parsed the result, and
`just --list` showed ``check   # Run CI gates (alias for `gate`)``. Re-running
the installer left exactly one alias. A second throwaway repo with a
recipe-less justfile produced the warning and a byte-identical file.

## Follow-ups

- **Repos already migrated need no revisit** — klams (and klams-mind when it
  lands) carry a hand-written alias that is what the installer would now
  produce anyway. Explicitly out of scope per #1254.
- **The remaining rollout batches are the payoff.** Every repo in korg #737's
  batches 3–6 with a pre-existing justfile is a candidate; they now get the
  alias without whoever runs that sprint noticing the problem first.
- **Ambiguity is currently resolved silently.** A repo defining both `gate` and
  `ci` gets `gate` with no comment on the road not taken. #1254 floated
  emitting a TODO naming the candidates instead; the plain priority list was
  taken as the smaller change. Worth revisiting only if a real repo turns up
  where the priority picks wrong.
