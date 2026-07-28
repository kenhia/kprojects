# kprojects - low touch agent instructions for managing personal projects

Agents have evolved, a lot, in a short time. Some of the heavier harnesses
like "Spec Kit" now slow down development and, per some studies, actually
reduce how well the frontier models work.

This is my, as simple as I can make it instructions for managing my personal
projects.

## Goals

- Keep token context as small as practical
- Share with agents how I like to run my projects
- Ensure agents have access to my infrastructure, telling me when this is not
  the case

## Project Management

> I use the term "sprint" somewhat incorrectly, but it's a handy term that
doesn't conflict with Phase, Step, etc. I use it to refer to a PR's worth of
work and the term is used within `korg` for "sprint proposal" and common
skills `sprint-start` and `ship-sprint`

Various projects currently use different sprint management along with
Spec-Kit, ATV-Starter Kit, Phoenix, etc. I am trying to consolidate so that
all my projects use a simplified approach:

- `sprints` directory containing:
    - planning - formal and/or ad-hoc planning documents
        - should at minimum contain `roadmap.md` with the general plan for
          the project
    - review - generally more formal reviews as projects mature
    - sprint documents - contains a record of how the project evolved over
      time
        - smaller projects, files with `###-<short-name>.md`, e.g.
          "007-consolidation.md"
        - larger or more formal projects, directories named `###-<short-name>"
          within directory one or more (usually markdown) files
- `docs` directory containing project documentation/architecture/etc
- `.scratch` directory, git ignored, place for output data and other
  ephemeral items that either user or agent needs for a while
- `README.md`, `LICENSE` (MIT unless specifically directed otherwise)
- `justfile` - recipes to aid in development and use of the project. Should
  have `@just --list` as default recipe and recipes for checking CI gates
  (usually as `just check`). If deployment is needed for the project
  `just deploy` (or variants as needed).
- `.env` - git ignored, any tokens or other environment vars needed by the
  project

### User Preferences

- Python, managed by `uv`, `ruff`, `ty` (astral tools)
- TDD preferred

### Infrastructure MVP
- Sprint proposals and WI's managed by `korg`
- Memories that should be shared cross project/cross agent recorded in `klams`


## Using this repo

```sh
./install.sh --agent both ~/src/x    # apply harness to a repo (claude|ghcp|both)
just apply ~/src/x                   # same, via just
```

- `harness/instructions.md` — the single source for shared conventions.
  `install.sh` injects it into `CLAUDE.md` / `.github/copilot-instructions.md`
  as a managed block (`kproject:begin`/`end` markers) and replaces that block
  on re-run; anything outside the block is project-specific and never touched.
  After editing conventions, re-run `./install.sh <repo>` on affected repos.
- `install.sh` is idempotent and mechanical: layout dirs, seed
  `roadmap.md`/`justfile`, `.gitignore` entries, block injection, and warnings
  when old-harness paths (`.specify/`, `specs/`, ...) are present.
- `/kproject-init` is the judgment layer: run it inside a repo (or point it at
  a new one) to scaffold from scratch or survey an old harness, migrate its
  content into `sprints/`, apply the installer, and write the project-specific
  section of the agent files.

  **The skill does not live here.** Its source is the `agent-skills` repo, and
  it reaches machines through k-homelab's `claude-skills` recipe on managed
  hosts or `bin/deploy-skill` on unmanaged ones. This repo owns the *harness*;
  that repo owns the *skill*. Keeping a second copy here is what let the two
  drift apart before.

## License

MIT — see [LICENSE](LICENSE).
