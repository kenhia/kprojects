# 005 — say the Windows `sh` prerequisite out loud

korg #1257. Small: four template files, one comment block each.

## Goal

On Windows, `just` runs every recipe through `sh`, and Windows does not ship
one. Git for Windows puts `C:\Program Files\Git\cmd` on PATH but not
`usr\bin`, where `sh.exe` actually lives — so on a stock Windows shell every
recipe in every kproject fails with *"could not find the shell `sh`"*, while
`just --list` works fine and makes it look like a broken repo instead of a
missing dependency.

kvscf and krot both have this today; kpidashclient-win joins them in rollout
batch 5.

## The decision, and why it is only a comment

Ken, 2026-08-14, after reading just's own install notes: **"After installation,
sh must be available in the PATH of the shell you want to invoke just from."**

That reframes the whole thing. This was filed as a harness bug; it is actually
a **documented prerequisite of a dependency that the harness never states**.
The fix is therefore to state it, not to work around it — put
`C:\Program Files\Git\usr\bin` on PATH (Ken's machine), and have every
generated justfile say so at the top.

## What was measured before deciding

Several cleverer options were tested on cleo against `just 1.49.0` and rejected
on evidence rather than taste:

- **`.env` + `SH_PATH`** — the machine-specific value in the machine-specific
  place. Impossible: `set windows-shell := [sh_path, ...]` fails with *"Cannot
  access non-const variable in const context"*, and the function form fails with
  *"Cannot call functions in const context"*. Settings take const expressions
  only — literal `+` concatenation works, nothing that could vary does.
- **`.env` setting `PATH`** — also fails. just resolves the shell binary against
  the *parent process's* PATH; dotenv is loaded into the recipe environment,
  after that decision is made.
- **`set windows-shell := ["C:/Program Files/Git/usr/bin/sh.exe", "-cu"]`** —
  works, but hard-codes an absolute path into every generated justfile, which is
  the shape #699 spent a sprint removing from `/kproject-init`.
- **`just --shell <path>`** — works, and is the only way the `.env` idea could
  be made to function (a wrapper reading `.env` at invocation time). Rejected
  for now as a new moving part that only helps callers who use the wrapper.

The PATH-shadowing worry against the simple answer turned out not to apply:
Windows searches the **Machine** PATH before the **User** PATH, `System32` is
first in Machine, and only 8 of the 246 executables in `Git\usr\bin` collide by
name (`expand`, `find`, `hostname`, `reset`, `sort`, `tar`, `timeout`,
`whoami`). Appending to the User PATH leaves all 8 resolving to the Windows
versions. Prepending would be a different story.

## Shipped

A three-line comment at the top of `justfile.{go,other,python,rust}`, above a
blank line so it does not become `default`'s doc comment in `just --list` —
the same trap #1254 pinned a test for, and one that had already bitten kvscf's
hand-written justfile.

## Follow-ups

- **Existing kprojects do not get this**, because `_seed()` never overwrites an
  existing justfile. krot and kvscf need the line added by hand if it is wanted
  there; kvscf already documents the requirement in its `CLAUDE.md`.
- **`JUST_SHELL` upstream.** Nearly every `just` flag advertises an env var —
  `JUST_CHOOSER`, `JUST_CYGPATH`, `JUST_JUSTFILE`, `JUST_TEMPDIR` — and
  `--shell` / `--shell-arg` have none. If it existed, one user-environment
  variable would fix every kproject on a Windows box at once, with no per-repo
  line at all. just is Rust and CC0-1.0; Ken's plan is a local fork to dogfood
  it, then a PR upstream. Tracked on korg #1257, not scheduled.
