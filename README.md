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

From **any machine, Windows or Linux, with no clone of this repo**:

```sh
uvx --from git+https://github.com/kenhia/kprojects kproject-install ~/src/x
```

Flags: `--agent claude|ghcp|both` (default `both`) and `--stack
python|rust|go|cmake|other`. Leave `--stack` off and the target repo is
inspected — `Cargo.toml` means rust, `go.mod` means go, `CMakeLists.txt` means
cmake, `pyproject.toml` means python, anything else is other (checked in that
order, so a repo carrying more than one marker gets the toolchain that owns
its build). From a clone of this repo, `just apply ~/src/x` does the same.

- `src/kprojects/harness/` — the single source for shared conventions.
  `instructions.md` is what every project gets; `tooling/<stack>.md` is the
  stanza composed into it per stack; `justfile.<stack>` is the seeded gate.
  The installer injects the result into `CLAUDE.md` /
  `.github/copilot-instructions.md` as a managed block (`kproject:begin`/`end`
  markers) and replaces that block on re-run; anything outside the block is
  project-specific and never touched. After editing conventions, re-run the
  installer on affected repos.
- The harness travels *inside the package*, which is what makes the one-command
  install true — there is no cached clone to manage and nothing to place by
  hand.
- The installer is idempotent and mechanical: layout dirs, seed
  `roadmap.md`/`justfile`, `.gitignore` entries, block injection, and warnings
  when old-harness paths (`.specify/`, `specs/`, ...) are present. It preserves
  CRLF line endings, so a Windows checkout survives re-application.
- An existing `justfile` is never overwritten. Since the managed block tells
  every agent that `just check` runs the gates, a repo whose gate is named
  `gate`, `ci` or `all` instead gets a one-line `check: <gate>` alias appended
  — so the block is true without the block's text differing between repos. If
  no gate is recognisable the installer writes nothing and says why, naming
  the consequence: the block's `just check` promise is not true in that repo
  until someone adds one. Guessing a gate would ship one that passes by not
  looking, which is the failure every seeded gate here is shaped to avoid —
  `--no-tests=error` for `ctest`, capturing `gofmt -l`'s output rather than
  its exit status, `--all-targets` for clippy, and an `other` placeholder that
  exits 1 until it is written.
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
