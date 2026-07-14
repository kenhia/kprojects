# Sprint 001 — first cut

2026-07-13

## Goal

Turn the README's "simpler sprint" idea into something installable: a
minimal harness that can be applied to any personal project, targeting both
Claude and GHCP, plus a skill to drive migrations.

## Decisions

- **Single source, managed block.** Shared conventions live once in
  `harness/instructions.md`. `install.sh` injects them into `CLAUDE.md`
  and/or `.github/copilot-instructions.md` between
  `<!-- kproject:begin -->` / `<!-- kproject:end -->` markers, replacing
  the block on re-run. Project-specific content lives outside the block and
  is never touched — so re-applying the harness after a conventions edit is
  safe and cheap. This is deliberately lighter than kagent-harness's
  generator approach; both agent files are inlined (GHCP doesn't follow
  links/imports reliably).
- **Script does the mechanical, skill does the judgment.** `install.sh` is
  dumb and idempotent (layout, seeds, gitignore, block injection; warns on
  old-harness paths). `/kproject-init` is the interactive front-end: survey,
  propose cleanup/migration, confirm before deleting, run the installer,
  then write the project-specific section by actually reading the repo.
- **Old-harness cleanup is migrate-first.** Spec-Kit `specs/` etc. get
  collapsed into `sprints/###-*.md` records rather than deleted — the
  content has value even when the machinery doesn't.
- **Stay in-repo for now.** Skill source and conventions live in kprojects;
  `install.sh --skill` copies the skill to `~/.claude/skills/`. Global/user
  promotion is a Later item.

## Shipped

- `harness/` — `instructions.md` (shared conventions), `roadmap.md` and
  `justfile` seed templates
- `install.sh` — idempotent installer, `--agent claude|ghcp|both`,
  `--skill`
- `skills/kproject-init/SKILL.md` — the migration/init skill
- `justfile` (`apply`, `install-skill`, `check`), README usage section
- Dogfooded on kprojects itself: this repo now carries its own `CLAUDE.md`,
  `.github/copilot-instructions.md`, `sprints/`, `docs/`, `.scratch/`

## Follow-ups

- Exact ATV-Starter Kit / Phoenix footprints for the skill's survey step
  (currently named but vague — will firm up during first real migrations)
- Run `/kproject-init` against a real project and record what chafes
