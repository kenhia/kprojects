# Sprint 002 — installable anywhere, stack-aware

2026-08-11 · korg proposal 912 · covers #699, #725 · slice 1 of program 1103

## Goal

Make the harness applicable from any machine — Windows or Linux — with one
command and no hand-placed clone, and make what it applies depend on the
project's stack instead of always being Python.

The two are one sprint because both rewrite the installer. Landing #699
first and #725 later means rewriting `install.sh`, then immediately
reopening it.

## What was actually broken

Verified against the tree at the start of the sprint, not assumed:

- `install.sh:15` resolved `KPROJECTS_DIR` from `BASH_SOURCE` and read
  `$KPROJECTS_DIR/harness/`. "Run the installer" structurally meant "have a
  clone" — the direct cause of the temp-clone ritual.
- `harness/instructions.md` hard-coded the Python/uv/ruff/ty stanza *inside*
  the managed block, which by convention may not be hand-edited. A Rust
  kproject carried Python guidance it was not allowed to correct. Existing
  victim: `agent-wiki-tooling` (the Rust `kwiki` server).
- `harness/instructions.md:3-4` — a **third** kai-absolute path, this one
  inside the managed block, so it had already shipped to every kproject
  repo: "This project uses the kproject minimal harness
  (`~/src/ai-agents/kprojects`)."
- `harness/justfile` seeded a Python-flavoured TODO echo for every stack.
  The papercut #725 originally focused on; real, but the smallest of these.

Blocker #1 from #699 (no remote) was already resolved on 2026-07-27 —
`github.com/kenhia/kprojects` is public.

## Decisions

- **Python installer shipped via `uvx`** (#699's option B). `harness/` is
  package data, so the adjacency blocker dies by construction rather than by
  a cache-clone convention that could drift. `uv` is already the homelab
  toolchain, and it makes path handling (`~`, separators, CRLF) explicit
  instead of accidental.
- **`harness/` moves inside the package**, to `src/kprojects/harness/`.
  First attempt was to keep it at the repo root for discoverability — this
  repo *is* the harness, so someone browsing it on GitHub should trip over
  `instructions.md` immediately — and ship it with hatchling `force-include`.
  Rejected: `force-include` does not materialise files for an *editable*
  install, so dev and test runs would need a "look next to `__file__`"
  fallback. That is the same shape as the `BASH_SOURCE` bug being removed,
  and worse, it means the tests never exercise the resource-loading path that
  actually runs under `uvx`. One `importlib.resources` path, used identically
  in dev, test, and production, is worth more than a shorter repo-root path.
  README and both agent files now point at the real location.
- **Stack is detected, not defaulted.** #725 proposed `--stack` defaulting to
  `other`; #699's comment proposed `--lang` defaulting to `python`. Both are
  wrong for the same reason: the nine existing kproject repos are mostly
  Python, so an `other` default silently strips their tooling stanza on the
  next re-run, and a `python` default recreates exactly the bug that made
  `agent-wiki-tooling` wrong on day one. So `--stack` is optional and
  overriding; when omitted, the target repo is inspected (`Cargo.toml` →
  rust, `pyproject.toml` → python, else `other`). Re-running on an existing
  repo now does the right thing with no flag at all, which matters because
  re-running is the documented way to pick up a conventions edit.
- **The tooling stanza leaves `instructions.md`.** It becomes
  `harness/tooling/{python,rust,other}.md`, composed into the managed block
  at a `{{TOOLING}}` placeholder. `instructions.md` remains the single source
  for everything that is genuinely shared; the per-stack files are the single
  source for what is not.
- **Marker text changed, marker prefix did not.** Both the old awk and the
  new parser match on the `<!-- kproject:begin` prefix, so re-running over a
  repo installed by `install.sh` replaces its block cleanly. No migration
  step, and that is deliberate — nine repos would have needed one.

## Gate fragments

Settled in #725's comment and carried in as-is, because the reasoning is
already recorded there:

- `ruff format --check` in `check`, never the mutating form — a gate that
  rewrites your tree is a bad gate. The mutating form goes in `just fmt`.
- No `--fix` in `check`, same argument.
- Keep `ty`. Type-checking is the point of the homelab's uv toolchain.
- `cargo clippy --all-targets` deliberately: clippy has passed without it and
  CI has failed with it, on kvscf.

## Shipped

- `src/kprojects/cli.py` — the installer, entry point `kproject-install`.
  Same job as the old script (layout, seeds, `.gitignore`, block injection,
  old-harness warnings) plus stack selection, and CRLF-preserving file i/o.
- `src/kprojects/harness/` — `instructions.md` (with the `{{TOOLING}}`
  placeholder and the kai path gone), `tooling/{python,rust,other}.md`,
  `justfile.{python,rust,other}`, `roadmap.md`.
- `pyproject.toml` — hatchling, `requires-python >=3.10`, dev group of
  pytest/ruff/ty. The harness is inside the package, so it ships in the wheel.
- `tests/test_install.py` — 32 tests. The load-bearing ones are block
  replacement (idempotency, content outside the block, **old-marker
  compatibility**, CRLF) because nine repos already carry a block written by
  the retired script.
- `justfile` — `apply`, `apply-self`, `check` (now ruff format --check / ruff
  check / ty / pytest), `fmt`, `build`. `install.sh` deleted.
- README usage section, and the `## Project` section of both agent files,
  rewritten. Those still described `./install.sh --skill`, which commit
  `e3fe180` retired — stale in both files, fixed here.

## Verification

Both halves of #699's definition of done, run rather than assumed.

**Linux (kai).** Installer run from a built wheel with the cwd outside this
repo, and again from source, against throwaway git repos. Rust detection
produced the cargo stanza, the cargo justfile and `target/` in `.gitignore` —
the `agent-wiki-tooling` bug, fixed. Dogfooded on kprojects itself: detection
picked `python` with no flag, and the diff to `CLAUDE.md` was exactly two
hunks — the marker line and the kai path — with every other line byte
identical. That is the nine-repo migration demonstrated on a real file.

**Windows (cleo).** Both hazards #699 told us to check turned out to be
real:

- `bash` resolves to `C:\Users\kenhi\AppData\Local\Microsoft\WindowsApps\bash.exe`
  — the **WSL launcher**, not Git Bash. The old `install.sh` would have run
  inside WSL against a different filesystem view, with `~` pointing at the WSL
  home rather than `C:\Users\kenhi`.
- `python` is the **MSIX Store stub** from the same directory.

`uv`/`uvx` (`C:\Users\kenhi\.local\bin`) and `git` (Git for Windows) are
genuine, so the uvx route steps around both by needing neither bash nor a
system Python. Ran against a throwaway repo with `core.autocrlf true`:
detection, layout with backslash separators, both agent files, gitignore all
correct. Re-applied over a CRLF copy carrying a hand-written note outside the
block — 45 CRLF in, 45 CRLF out, zero bare LF, note intact, exactly one
begin/end marker pair, and run 3 hashed identical to run 2.

**The literal one-command form, on both.** Once the branch was pushed, the
exact command from #699's definition of done was run against throwaway repos
on kai and on cleo:

```
uvx --from git+https://github.com/kenhia/kprojects kproject-install <repo>
```

Both cloned from GitHub, built, and applied the harness with no kprojects
checkout on the machine. cleo detected `rust` from a `Cargo.toml` and wrote
the cargo stanza and cargo justfile. That closes every line of #699's DoD
except the `/kproject-init` absolute path, which moved to agent-skills #1184
by design.

## Follow-ups

- Re-apply to the eight other repos already on the harness so they pick up the
  URL fix and the new marker text. That is rollout, which is proposal 749's
  job, not this sprint's.

## Follow-ups

- agent-skills #1184 / proposal 1185 (slice 2 of program 1103): point
  `/kproject-init` at the portable invocation, drop its clone-if-missing
  fallback, and add the greenfield stack question. The stack-aware installer
  is **inert until that lands** — nothing passes `--stack` until the skill
  asks for it. Filed rather than done here: one sprint ≈ one PR ≈ one repo.
