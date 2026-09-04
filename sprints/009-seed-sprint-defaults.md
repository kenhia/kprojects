# Sprint 009 — Seeding `.sprint-defaults`, and the first sprint run end to end through karc

2026-09-04 · korg proposal 1883 · covers #1855

## Goal

Ken's ask, from karc on 2026-09-03: a project stood up by
`new-homelab-project` should start with a `.sprint-defaults`, so a bare
`/sprint-ship` does the whole ship instead of each repo discovering the file
later — knarr, kstudiodash and agent-skills each added theirs by hand
mid-sprint. The mechanics belong here, because `new-homelab-project` runs
`kproject-init`, which runs `kproject-install`, which already owns the
`.gitignore` stanza.

This sprint is also the **live test of karc program 1853's skills slice**
(korg:1851): it ran headless as karc leg `kprojects-e9d72c`, launched from a
cleo overseer, and everything the run taught about the skills goes back to
1851 before that ships. Deliberately small work, chosen for that reason.

## Decisions

- **Gitignore always, seed only on greenfield.** #1855 asks for both, and they
  split on the same reasoning sprint 006 used to decline a seeded TODO `check`
  recipe. The ignore line is right in every repo unconditionally. The
  *contents* are not: one line that becomes sprint-ship's entire `$ARGUMENTS`,
  so seeding `PR, merge, local clean` into a repo that already ships
  differently configures its ship behaviour from a guess — silently, and in a
  file nobody is watching. A migration target gets the ignore line and nothing
  else.
- **The greenfield signal is an explicit `--greenfield` flag.** The installer
  had no notion of greenfield, and both plausible cheap alternatives were
  rejected. Detecting it (no history, no harness, empty tree) is exactly the
  guess sprint 006 declined. Riding on `--stack`, which kproject-init
  documents as "greenfield only" (§4), would be a real signal but an *implicit*
  one — a human overriding a wrong detection on a migration would silently
  seed a ship config. A flag says what it means and costs one line at the call
  site.
- **So the flag has no caller yet, and that is stated rather than papered
  over.** `kproject-init`'s greenfield path has to pass `--greenfield` for
  this to fire, and that file lives in agent-skills, which this leg was
  explicitly scoped out of (proposal 1883's notes: agent-skills has one
  checkout, on kubs0, holding 1851's branch and its lock). #1855 already
  splits its skill half off for the 1851 session — this enlarges that half
  from "one line each" to "one line each, plus pass the flag". Flagged to the
  overseer rather than decided here.
- **`SPRINT_DEFAULTS` is a module constant, not a harness template.** The
  seeded body and the report line that echoes it (`defaults : seeded
  .sprint-defaults (PR, merge, local clean)`) are the same string, so one
  constant makes drift between them unrepresentable. It also sits with
  `BASE_IGNORES` rather than in `harness/`, which is where #1855 puts it
  conceptually: this is the installer's ignore-stanza family, not the managed
  block whose content `harness/` owns.
- **`.sprint-deploy` is not seeded, and there is a test pinning that.**
  Whether a repo deploys is a property of the repo, declared when its deploy
  skill exists. It is a deliberate non-behaviour, so it gets an assertion
  rather than a silence.
- **"Kept existing" is reported on migration targets too.** The seeder returns
  `"kept"` whenever the file is present, greenfield or not, so the operator
  sees that the installer looked and left it alone. Only the genuinely silent
  case — migration, no file — prints nothing.

## Shipped

- `src/kprojects/cli.py` — `SPRINT_DEFAULTS`; `.sprint-defaults` added to
  `BASE_IGNORES`; `ensure_sprint_defaults()`; the `--greenfield` flag threaded
  through `apply()`; two report lines.
- `tests/test_install.py` — nine tests: the gitignore entry, the greenfield
  seed, the migration non-seed, never-overwrite, idempotency across reruns,
  both report lines, the one-line `$ARGUMENTS` contract, and `.sprint-deploy`
  staying unseeded.
- `.gitignore`, via `just apply-self` — this repo takes its own new ignore
  line, and correctly gets no seed, being no one's greenfield target.
- `CLAUDE.md`, `.github/copilot-instructions.md` — the behaviour and its
  reasoning, identical in both.

## Verification

`just check` green — ruff format, ruff check, ty, 83 tests (74 before).

All nine tests were watched failing first: `--greenfield` unrecognised by
argparse, `.sprint-defaults` absent from the gitignore stanza.

`just apply-self` on this repo printed `gitignore: added .sprint-defaults`,
wrote no `.sprint-defaults`, and left both managed blocks byte-identical —
no template changed, so #1254's property is not disturbed.

## Follow-ups

- **agent-skills, for the 1851 session** (#1855's second half): `kproject-init`
  §7 Verify gains "`.sprint-defaults` present and gitignored"; §4 gains
  `--greenfield` on the greenfield invocation, alongside the existing
  greenfield-only `--stack`; `new-homelab-project` §5 step 1 notes the
  installer seeded it. Until §4 passes the flag, greenfield installs get the
  ignore line only.
- **A skills finding for korg:1851**, from being the live test:
  `overseen-sprint`'s karc section lists "a branch-name confirmation" among
  the things a leg must park on. In a repo with a deterministic `NNN-slug`
  convention there is nothing to confirm — `sprints/008-*` fixes the number
  and the proposal fixes the slug — so parking there would strand every leg on
  turn 1 for a renameable string, and this leg proceeded instead. Suggested
  wording: derive the name from the repo's convention and state it; park only
  when the convention is absent or genuinely ambiguous.
