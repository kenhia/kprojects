---
name: kproject-init
description: Apply the kproject minimal harness to the current repo — clean up an old harness (Spec-Kit, ATV-Starter Kit, Phoenix, ...) if present, install the simple sprint layout and shared conventions, and create/refresh CLAUDE.md and/or .github/copilot-instructions.md. Use when asked to kproject-init a repo, migrate a project to the simpler sprint layout, or set up agent instructions for a new project.
---

# kproject-init

Convert the current repo to the kproject minimal harness. Work in the repo
root. Source of truth is the `kprojects` checkout at
`~/src/ai-agents/kprojects` (ask where it is if not found; consider
`git -C ~/src/ai-agents/kprojects pull --ff-only` to freshen it first).

## 1. Survey before touching anything

Look for what's already here and report it to the user:

- Existing agent instructions: `CLAUDE.md`, `.github/copilot-instructions.md`,
  `AGENTS.md`, `.claude/` project skills/commands.
- Old harness footprints (non-exhaustive — anything that looks like harness
  machinery rather than project content counts):
  - **Spec-Kit**: `.specify/`, `specs/`, `memory/constitution.md`,
    `.github/prompts/speckit*.prompt.md`
  - **ATV-Starter Kit**: its starter directories/prompt files
  - **Phoenix**: `docs/brainstorms/`, `/ce-*` prompt/command files
- Existing planning/sprint material worth keeping: plans, specs, roadmaps,
  sprint logs, wherever they live.

## 2. Propose the migration, get confirmation

Present one plan covering, and **wait for the user's go-ahead before
deleting anything**:

- What gets **removed** (harness machinery: prompt files, `.specify/`,
  constitutions, harness configs).
- What gets **migrated** — content has value even when the harness doesn't:
  - spec/plan/tasks documents for completed work → collapse into sprint
    records `sprints/###-<short-name>.md` (or a `###-<name>/` dir if large),
    keeping the original numbering where sensible
  - roadmap-ish documents → fold into `sprints/planning/roadmap.md`
  - real architecture/usage docs → `docs/`
- What gets **kept as-is** (anything genuinely project content).

## 3. Apply the harness

Run the installer (it is idempotent):

```sh
~/src/ai-agents/kprojects/install.sh --agent <claude|ghcp|both> .
```

Pick the agent target by asking or by what's already in the repo; default
`both`. This creates `sprints/{planning,review}`, `docs/`, `.scratch/`,
seeds `roadmap.md` and a `justfile` if missing, adds `.scratch/` and `.env`
to `.gitignore`, and writes the shared-conventions managed block
(`kproject:begin`/`kproject:end`) into the agent instruction file(s).

## 4. Write the project-specific section

The managed block holds only shared conventions. Everything project-specific
goes **outside** the block (the `## Project` section), in each generated
file. Explore the repo and write it — short, current, no ceremony:

- one-paragraph what-this-is
- how to build / run / test (wire the real commands into `just check`
  while you're at it, replacing the seeded TODO)
- architecture pointers: the 3–6 files/dirs an agent should read first
- any project-specific gotchas or conventions that aren't derivable from
  the code

Keep `CLAUDE.md` and `.github/copilot-instructions.md` equivalent in
content — same facts, both maintained; neither is generated from the other
(yet).

## 5. Fill the roadmap and verify

- Put whatever is actually planned into `sprints/planning/roadmap.md`
  (from migrated docs, korg work items for this project, or the user).
- Verify: managed block present in the chosen agent file(s), `.gitignore`
  entries in place, `just` runs, old-harness paths gone or migrated.
- Summarize what changed. Suggest a commit; don't push or open a PR unless
  asked (shipping is `/sprint-ship`'s job).
