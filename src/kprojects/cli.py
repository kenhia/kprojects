"""kproject-install — apply the kproject minimal harness to a target repo.

Run it from anywhere, with no clone of this repo on disk:

    uvx --from git+https://github.com/kenhia/kprojects kproject-install ~/src/x

The harness templates travel inside the package (`importlib.resources`), which
is what makes that true. Do not reintroduce a "look next to __file__" lookup —
that was the bug (#699) this replaced.

Idempotent: layout pieces are only created when missing, and the agent
instruction files carry a managed block between kproject:begin/end markers that
is replaced in place on re-run. Content outside the block is yours.

The /kproject-init skill is NOT installed from here. It lives in the
agent-skills repo and reaches machines via k-homelab's claude-skills recipe
(managed hosts) or bin/deploy-skill (unmanaged ones). One source, one path.
"""

from __future__ import annotations

import argparse
import sys
from importlib.resources import files
from pathlib import Path

BEGIN_MARK = "<!-- kproject:begin — managed by kprojects; do not edit inside this block -->"
END_MARK = "<!-- kproject:end -->"

# Matched on the prefix, never the full line: blocks written by the retired
# install.sh carry different marker *text* and must still be replaced cleanly.
BEGIN_PREFIX = "<!-- kproject:begin"
END_PREFIX = "<!-- kproject:end"

TOOLING_PLACEHOLDER = "{{TOOLING}}"

STACKS = ("python", "rust", "go", "other")
AGENTS = ("claude", "ghcp", "both")

AGENT_FILES = {
    "claude": ("CLAUDE.md",),
    "ghcp": (".github/copilot-instructions.md",),
    "both": ("CLAUDE.md", ".github/copilot-instructions.md"),
}

# Ordered: a repo carrying more than one is treated as the one whose toolchain
# owns the build. Cargo stays first — it is the stricter gate. `pyproject.toml`
# is last because it is the weakest signal of the three: `Cargo.toml` and
# `go.mod` define a build, `pyproject.toml` also shows up carrying nothing but
# ruff settings in repos that are not Python projects at all.
STACK_MARKERS = (("rust", "Cargo.toml"), ("go", "go.mod"), ("python", "pyproject.toml"))

BASE_IGNORES = (".scratch/", ".env")
STACK_IGNORES = {
    "python": (".venv/", "__pycache__/", ".pytest_cache/"),
    "rust": ("target/",),
    # `go.work` is per-machine by design (upstream guidance is not to commit it);
    # `*.test` and `*.out` are `go test -c` binaries and profile output.
    "go": ("*.exe", "*.test", "*.out", "go.work", "go.work.sum"),
    "other": (),
}

LAYOUT_DIRS = ("sprints/planning", "sprints/review", "docs", ".scratch")

# What "the recipe CI runs" is called when it is not called `check` (#1254).
# Ordered: the first one present wins. `test` is deliberately absent — it is one
# component of a gate, not the aggregate, so aliasing `check` to it would keep
# the managed block's promise in the letter only.
GATE_RECIPES = ("gate", "ci", "all")

# The blank line before the doc comment is load-bearing: `just --list` shows the
# comment line directly above a recipe, so without it the rationale's last line
# leaks into the listing as a sentence fragment.
CHECK_ALIAS = """\
# Added by kproject-install: the managed block tells every agent that
# `just check` runs the gates, so this repo needs that name. An alias rather
# than a second recipe, so `{gate}` stays the single definition CI invokes.

# Run CI gates (alias for `{gate}`)
check: {gate}
"""

OLD_HARNESS_PATHS = (
    ".specify",
    "specs",
    "memory/constitution.md",
    ".github/prompts",
    ".atv",
    "docs/brainstorms",
)

NEW_FILE_TAIL = """
## Project

<!-- project-specific instructions go here (outside the managed block).
     Run /kproject-init to survey the repo and fill this in. -->
"""


# --- harness resources -------------------------------------------------------


def harness_root():
    """The packaged harness templates. No clone required, by construction."""
    return files("kprojects") / "harness"


def _read_harness(*parts: str) -> str:
    node = harness_root()
    for part in parts:
        node = node / part
    return node.read_text(encoding="utf-8")


def render_block(stack: str) -> str:
    """The managed block for `stack`, marker to marker, newline-terminated."""
    instructions = _read_harness("instructions.md")
    tooling = _read_harness("tooling", f"{stack}.md").strip("\n")

    lines: list[str] = []
    for line in instructions.split("\n"):
        if line.strip() == TOOLING_PLACEHOLDER:
            # An empty stanza drops its line rather than leaving a blank hole.
            if tooling:
                lines.extend(tooling.split("\n"))
        else:
            lines.append(line)

    body = "\n".join(lines)
    return BEGIN_MARK + "\n" + body + END_MARK + "\n"


# --- text i/o that survives a Windows checkout -------------------------------


def _read(path: Path) -> tuple[str, bool]:
    """Read as text with newlines normalised; report whether the file was CRLF."""
    text = path.read_bytes().decode("utf-8")
    return text.replace("\r\n", "\n"), "\r\n" in text


def _write(path: Path, text: str, crlf: bool) -> None:
    if crlf:
        text = text.replace("\n", "\r\n")
    path.write_bytes(text.encode("utf-8"))


# --- the managed block -------------------------------------------------------


def inject_block(path: Path, block: str) -> str:
    """Replace, append, or create the managed block in one agent file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        _write(path, block + NEW_FILE_TAIL, crlf=False)
        return "created"

    text, crlf = _read(path)

    if BEGIN_PREFIX not in text:
        _write(path, text.rstrip("\n") + "\n\n" + block, crlf)
        return "appended"

    out: list[str] = []
    skipping = False
    for line in text.split("\n"):
        if line.startswith(BEGIN_PREFIX):
            skipping = True
            out.extend(block.rstrip("\n").split("\n"))
            continue
        if skipping:
            if line.startswith(END_PREFIX):
                skipping = False
            continue
        out.append(line)

    _write(path, "\n".join(out), crlf)
    return "updated"


# --- stack -------------------------------------------------------------------


def detect_stack(target: Path) -> str:
    """Infer the stack from the repo itself.

    Neither of the defaults proposed in #725 (`other`) or #699 (`python`) is
    safe: one silently strips the tooling stanza from the existing Python
    kprojects on their next re-run, the other recreates the wrong-guidance bug
    that made agent-wiki-tooling incorrect on day one.
    """
    for stack, marker in STACK_MARKERS:
        if (target / marker).exists():
            return stack
    return "other"


# --- layout, seeds, gitignore ------------------------------------------------


def ensure_gitignore(target: Path, stack: str) -> list[str]:
    path = target / ".gitignore"
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    added = [e for e in (*BASE_IGNORES, *STACK_IGNORES[stack]) if e not in existing]
    if added:
        body = "\n".join(existing + added) + "\n"
        path.write_text(body.lstrip("\n"), encoding="utf-8")
    return added


def _seed(path: Path, template: str, label: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_read_harness(template), encoding="utf-8")
    print(f"layout   : seeded {label}")


def _recipe_names(text: str) -> set[str]:
    """The names `just <name>` will accept in this justfile.

    Deliberately shallow — we only need to know whether `check` is taken and
    which known gate name is present. The two things that read as recipes if
    you only look for a colon are assignments (`x := y`, `set shell := [...]`)
    and indented recipe bodies, so both are excluded explicitly.
    """
    names: set[str] = set()
    for line in text.split("\n"):
        if not line[:1].strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("alias "):
            # `alias check := gate` already makes `just check` work, and a
            # recipe colliding with an alias is a hard error in just.
            name = line[len("alias ") :].split(":=")[0].strip()
            if name:
                names.add(name)
            continue
        colon = line.find(":")
        if colon == -1 or line[colon + 1 : colon + 2] == "=":
            continue
        head = line[:colon].split()
        if head and not head[0].startswith("["):
            names.add(head[0])
    return names


def ensure_check_recipe(target: Path) -> str | None:
    """Give a pre-existing justfile a `check` recipe when it lacks one (#1254).

    The managed block tells every agent that `just check` runs the gates, and
    `_seed()` deliberately never clobbers a working justfile — so in a repo
    whose gate is named something else the block asserted something false,
    inside a region the repo is not allowed to hand-correct. Appending the
    alias is what makes the block true by construction; the alternative,
    writing the detected name into the block, was rejected because it makes the
    block's text per-repo (korg:1255).

    Returns the recipe that was aliased, or None when nothing was written.
    """
    path = target / "justfile"
    if not path.exists():
        return None

    text, crlf = _read(path)
    names = _recipe_names(text)
    if "check" in names:
        return None

    gate = next((g for g in GATE_RECIPES if g in names), None)
    if gate is None:
        print(
            "WARN     : justfile defines no `check` recipe and no recognisable gate "
            f"({'/'.join(GATE_RECIPES)}) — the managed block's `just check` is not "
            "true here; add a `check` recipe by hand",
            file=sys.stderr,
        )
        return None

    _write(path, text.rstrip("\n") + "\n\n" + CHECK_ALIAS.format(gate=gate), crlf)
    return gate


def warn_old_harness(target: Path) -> None:
    found = [p for p in OLD_HARNESS_PATHS if (target / p).exists()]
    for p in found:
        print(f"WARN     : possible old harness remnant: {p}", file=sys.stderr)
    if found:
        print(
            "WARN     : run /kproject-init in this repo to migrate/clean up interactively",
            file=sys.stderr,
        )


# --- driver ------------------------------------------------------------------


def apply(target: Path, agent: str, stack: str) -> None:
    for d in LAYOUT_DIRS:
        (target / d).mkdir(parents=True, exist_ok=True)
    print(f"layout   : {' '.join(LAYOUT_DIRS)}")

    roadmap = target / "sprints" / "planning" / "roadmap.md"
    _seed(roadmap, "roadmap.md", "sprints/planning/roadmap.md")
    _seed(target / "justfile", f"justfile.{stack}", f"justfile ({stack})")
    # After the seed, never before: a freshly seeded justfile already has
    # `check`, so this only ever fires on a justfile the repo brought itself.
    if gate := ensure_check_recipe(target):
        print(f"justfile : added `check: {gate}` alias")

    for entry in ensure_gitignore(target, stack):
        print(f"gitignore: added {entry}")

    block = render_block(stack)
    for rel in AGENT_FILES[agent]:
        action = inject_block(target / rel, block)
        print(f"agents   : {action} managed block in {rel}")

    warn_old_harness(target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kproject-install",
        description="Apply the kproject minimal harness to a target repo.",
    )
    parser.add_argument("target", help="path to the target repo")
    parser.add_argument(
        "--agent", choices=AGENTS, default="both", help="which agent files to write"
    )
    parser.add_argument(
        "--stack",
        choices=STACKS,
        default=None,
        help="tooling stanza and justfile to apply (default: detect from the repo)",
    )
    args = parser.parse_args(argv)

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        print(f"not a directory: {args.target}", file=sys.stderr)
        return 1
    if not (target / ".git").exists():
        print(f"WARN     : {target} is not a git repo root", file=sys.stderr)

    stack = args.stack or detect_stack(target)
    origin = "given" if args.stack else "detected"
    print(f"stack    : {stack} ({origin})")

    apply(target, args.agent, stack)
    print(f"done     : kproject harness applied to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
