# Sprint 011 — Fleet re-apply of the 008 block

2026-11-09 · korg proposal 4453 · covers #1409 · program korg:4368 (backlog
drawdown) · karc leg `kprojects-6185b3` on kai

## Goal

Sprint 008 re-applied its cross-project-plan pointer to only the three repos
where it fires, which left the block **differing by repo**. That breaks #1254's
"byte-identical everywhere" property, the one that makes "this block looks
different" a reliable drift signal. #1409 is the sweep that restores it. The
installer it runs is the post-010 one (`b42a4f2`), so the block it hands out is
also prettier-clean (#2509).

## Decisions

- **Per-repo rule from the overseer, followed exactly.** Branch
  `chore/kproject-reapply`, the installer run as documented
  (`uvx --from git+https://github.com/kenhia/kprojects kproject-install .`),
  only the installer's own files staged by name, that repo's `just check` run,
  and one PR opened per repo. Merges happen on the ship turn, because karc
  blocks them before that. No per-repo sprint record, following 007 and 008.
- **Two stack overrides, not one.** The brief named `--stack cmake` for
  kdeskdash. **hv-simulator needs `--stack python` too.** It has no root
  marker, so detection says `other`, and that would have swapped its python
  stanza for the `other` one. This is sprint 007's trap, recorded in its
  closing audit. Before running anything, each repo's existing stanza was
  checked against its root markers. Those two are the only repos where the
  two disagree, and kdeskdash's override matches what detection gives anyway.
- **kyac's untracked `.env.pre-3534.bak` was not treated as a dirty tree.**
  The brief says to skip dirty trees because they are another session's work
  in flight. A stray, secret-bearing backup file is not work in flight, and
  selective staging means it can never enter the commit, which 007 already
  showed with kaed. It is still untracked and untouched. The overseer may rule
  the other way.
- **Two kubs0 repos the triage missed were added: k-homelab and
  agent-skills.** k-homelab lives at `~/k-homelab`, outside `~/src`, so an
  audit rooted at `~/src` cannot see it. agent-skills' `CLAUDE.md` already
  carried the pointer, but its `.github/copilot-instructions.md` did not. Both
  fall under #1409's own scope, which is every repo still pre-pointer. kubs0
  had no karc legs (`karc list --json` → `legs: []`), and both were clean and
  synced with no open PRs. The operation was the same mechanical one. This
  extends the brief, and it is flagged to the overseer.
- **The post-pointer, pre-010 repos were folded in on a second turn.** At
  first they were left alone, as outside "pre-pointer" and unlocked by this
  leg. The overseer ruled that a block differing from what the installer
  writes today is not re-applied, so the twelve got the same mechanical pass.
  See *Second pass*. The overseer also ruled k-homelab, agent-skills and
  kyac's backup file as in scope / correct to leave.
- **kdashdata kept its `other` stanza (`--stack other`).** Its root has had a
  `CMakeLists.txt` since `a291ba1`. But the `other` block was scaffolded at
  `34fad8f`, before the C library existed, so that was never an override.
  Plain detection would now swap it to the `cmake` stanza. For a polyglot
  repo (docs, Python, Rust and C, with one `just check` over all four), that
  changes the guidance agents get, so it is a decision, not a refresh. This
  pass keeps the block's text and flags the stanza question instead.

## The re-apply pass

Every repo started on a clean `main` synced with `origin/main`, with no karc
lock other than this leg's (kai) and no leg at all (kubs0). On every repo, a
second installer run left the diff byte-for-byte unchanged. On every repo, the
block above the per-stack stanza is md5-identical to kprojects' own
(`aabd7ef8`). All diffs are insertions only.

### kai — 14 repos, all locked by this leg

| Repo | Stack | PR | Diff | Gate |
|---|---|---|---|---|
| homelab-ai-plan | other | [#3](https://github.com/kenhia/homelab-ai-plan/pull/3) | +53, 3 files | green |
| kaed | rust | [#34](https://github.com/kenhia/kaed/pull/34) | +23, 3 files | green |
| kmon | python | [#50](https://github.com/kenhia/kmon/pull/50) | +35, 3 files | green |
| kvllm | python | [#15](https://github.com/kenhia/kvllm/pull/15) | +34, 2 files | green |
| kyac | python | [#29](https://github.com/kenhia/kyac/pull/29) | +35, 3 files | green |
| hv-simulator | python (`--stack`) | [#46](https://github.com/kenhia/hv-simulator/pull/46) | +35, 3 files | green |
| mortars | other | [#4](https://github.com/kenhia/mortars/pull/4) | +23, 3 files | green |
| apt-temps | python | [#7](https://github.com/kenhia/apt-temps/pull/7) | +35, 3 files | green |
| kdeskdash | cmake (`--stack`) | [#55](https://github.com/kenhia/kdeskdash/pull/55) | +29, 3 files | green |
| kmuster | rust | [#4](https://github.com/kenhia/kmuster/pull/4) | +23, 3 files | green |
| knarr | go | [#8](https://github.com/kenhia/knarr/pull/8) | +34, 2 files | green |
| korg-dash | other | [#2](https://github.com/kenhia/korg-dash/pull/2) | +24, 3 files | green |
| krot | rust | [#29](https://github.com/kenhia/krot/pull/29) | +23, 3 files | green |
| kwebi | other | [#9](https://github.com/kenhia/kwebi/pull/9) | +23, 3 files | green |

### kubs0 — 5 repos, none locked, no legs running

| Repo | Stack | PR | Diff | Gate |
|---|---|---|---|---|
| klams | rust | [#63](https://github.com/kenhia/klams/pull/63) | +35, 3 files | green |
| klams-mind | python | [#15](https://github.com/kenhia/klams-mind/pull/15) | +35, 3 files | green |
| klams-view | rust | [#7](https://github.com/kenhia/klams-view/pull/7) | +23, 3 files | green |
| k-homelab | other | [#182](https://github.com/kenhia/k-homelab/pull/182) | +22, 2 files | green |
| agent-skills | other | [#71](https://github.com/kenhia/agent-skills/pull/71) | +22, 2 files | green |

The size of each diff shows how far behind that copy was. +22/+23 is the
pointer plus 010's two blank lines. +34/+35 adds the 007 `Deployed` bullet and
the resolve-as-you-go bullet. homelab-ai-plan's +53 also picks up the `other`
stanza, which its block predated entirely. Every `.gitignore` change is the
installer's own harness-file ignore: `.sprint-defaults` everywhere, plus
`.korg-sprint-proposal` in korg-dash. No justfile was touched and no
`NO_GATE_WARNING` fired.

Merge readiness, checked before the ship: no branch is protected, no repo has
`CODEOWNERS`, and no repo's `CLAUDE.md` says its PRs need Ken.

### Second pass — 12 repos with the pointer but not sprint 010's block

The same rules applied. `karc list --json` was checked on each host first:
kai held only `kloom-900340` and kubs0 held nothing. All twelve were clean,
synced, unlocked and had no open PRs, so none was skipped. Every diff is
010's two blank lines, +2 per agent file, plus the installer's ignore lines
where a repo lacked them. Insertions only. Second run a no-op.

| Repo | Host | Stack | PR | Diff | Gate |
|---|---|---|---|---|---|
| kfdc | kai | other | [#35](https://github.com/kenhia/kfdc/pull/35) | +4, 2 files | green |
| ktail | kai | go | [#1](https://github.com/kenhia/ktail/pull/1) | +6, 3 files | green |
| kfo | kai | other | [#7](https://github.com/kenhia/kfo/pull/7) | +5, 3 files | green |
| kpolice | kai | rust | [#5](https://github.com/kenhia/kpolice/pull/5) | +5, 3 files | green |
| kdashdata | kai | other (`--stack`) | [#21](https://github.com/kenhia/kdashdata/pull/21) | +5, 3 files | green |
| klaude-top | kai | go | [#6](https://github.com/kenhia/klaude-top/pull/6) | +4, 2 files | green |
| korg | kai | rust | [#108](https://github.com/kenhia/korg/pull/108) | +4, 2 files | green |
| kapollo | kai | rust | [#14](https://github.com/kenhia/kapollo/pull/14) | +5, 3 files | green |
| kpidash | kai | cmake (`--stack`) | [#31](https://github.com/kenhia/kpidash/pull/31) | +4, 2 files | green |
| karc | kai | rust | [#14](https://github.com/kenhia/karc/pull/14) | +4, 2 files | green |
| kagviz | kai | rust | [#17](https://github.com/kenhia/kagviz/pull/17) | +4, 2 files | green |
| khlenv | kubs0 | rust | [#5](https://github.com/kenhia/khlenv/pull/5) | +5, 3 files | green |

karc's `check` recipe is `cargo fmt --check`, `clippy` and `test`. Nothing
was installed, redeployed or restarted.

**A trap the first pass did not hit:** kfdc, kfo and korg still had
`chore/kproject-reapply` on origin from sprint 008. Each tip was exactly the
head of the already-merged #13 / #2 / #66. The push was rejected, and
`gh pr create` then attached to the stale remote branch, opening kfdc#34,
kfo#6 and korg#107. Each of those re-proposed 008's commit and would have
duplicated the pointer if merged. All three were closed with a comment. The
stale ref was replaced with `--force-with-lease` pinned to that exact SHA,
and fresh PRs (#35, #7, #108) were opened. This is a reason for the ship turn
to delete each branch after merging.

### Before / after

| Host | Before (pre-pointer / pointer but pre-010) | After the ship (if all 31 merge) |
|---|---|---|
| kai | 14 / 11 (+ harness-eval, skipped by brief) | 0 / 0 — all 76 agent files across 38 repos identical (+ harness-eval) |
| kubs0 | 5 / 1 (+ khound, skipped — stopped) | 0 / 0 — 14 of 16 agent files identical; the other two are khound |
| cleo | not audited | not audited — the overseer checks it from cleo |

The "after" column was measured on the PR branches with the same block-hash
audit, over `~/src` plus `~/k-homelab`, excluding `.scratch/`, harness-eval
fixtures and the vendored `lib/kdashdata` submodules.

## What the pass found

- **The `lib/kdashdata` submodules in kdeskdash and kpidash** are pinned at
  `4837473` and carry kdashdata's pre-010 block. They will stay that way
  until each repo bumps its submodule pin. That is a dependency change for
  those repos, so it was not done here. They are vendored copies, not repos
  agents work in.
- **kdashdata's stanza** — whether its `other` stanza should become `cmake`.
  See Decisions. This is a question for whoever owns kdashdata's guidance,
  not a re-apply.
- **The triage audit's root misses `~/k-homelab`** on kubs0. Any future
  closing audit should search `~/src` *and* `~/k-homelab` (kaed's
  `kubs0:k-homelab` root names it).
- **Stale local branches** in kmon (`korg-cut-status`, PR #49 merged), kvllm
  (15 merged sprint branches), krot (three, PRs merged or closed) and klams
  (two). None was in flight. They were noted and left alone, because pruning
  another session's branches is not a repair this sprint owns.
- **`.scratch` copies carry old blocks** (krot `proof-017`, korg `097`,
  k-homelab `.scratch/kmon`). They are ignored and ephemeral, so not a
  defect, but an audit that does not exclude `.scratch` will count them.
- **cleo was not audited** (out of scope; the overseer checks it from cleo).
  korg-vs is likely pre-pointer: its last re-apply was sprint 007's, which
  came before 008.

## Verification

Each repo's own `just check` was run on the branch, after the change, and all
31 were green. The Rust and CMake gates finished in seconds, so their logs
were read to confirm that real test runs had happened against warm caches.
kprojects' own `just check` is green with this record added. No installer
change was needed.
