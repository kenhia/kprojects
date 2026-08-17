"""Tests for the kproject harness installer.

The block-injection tests are the load-bearing ones: nine repos already carry
a managed block written by the old bash installer, and re-running is the
documented way to pick up a conventions edit. Getting replacement wrong
silently corrupts every one of them.
"""

from pathlib import Path

import pytest

from kprojects import cli

OLD_BEGIN = (
    "<!-- kproject:begin — managed by kprojects/install.sh; do not edit inside this block -->"
)
OLD_END = "<!-- kproject:end -->"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    return tmp_path


# --- harness resources -------------------------------------------------------


def test_harness_ships_with_the_package():
    """The whole point of #699: templates resolve without a clone on disk."""
    root = cli.harness_root()
    assert (root / "instructions.md").is_file()
    for stack in cli.STACKS:
        assert (root / "tooling" / f"{stack}.md").is_file()
        assert (root / f"justfile.{stack}").is_file()


@pytest.mark.parametrize("stack", cli.STACKS)
def test_rendered_block_has_no_placeholder_and_no_absolute_path(stack: str):
    block = cli.render_block(stack)
    assert "{{TOOLING}}" not in block
    assert "~/src/ai-agents/kprojects" not in block
    assert block.startswith(cli.BEGIN_MARK)
    assert block.rstrip().endswith(cli.END_MARK)


def test_rendered_block_carries_the_stack_specific_stanza():
    assert "ruff" in cli.render_block("python")
    assert "ruff" not in cli.render_block("rust")
    assert "cargo clippy --all-targets" in cli.render_block("rust")
    assert "gofmt" in cli.render_block("go")
    assert "ruff" not in cli.render_block("go")
    assert "ctest" in cli.render_block("cmake")
    assert "cargo" not in cli.render_block("other")


@pytest.mark.parametrize("stack", cli.STACKS)
def test_no_stanza_leaves_a_blank_bullet_hole(stack: str):
    assert "\n\n\n" not in cli.render_block(stack)


def test_an_empty_stanza_drops_its_line(monkeypatch):
    """No shipped stack is empty since #1258 filled `other`, but the drop is
    still the correct response to one — a stray blank reads as a lost bullet."""
    monkeypatch.setattr(
        cli,
        "_read_harness",
        lambda *parts: (
            "" if parts[0] == "tooling" else cli.harness_root().joinpath(*parts).read_text()
        ),
    )
    block = cli.render_block("other")
    assert "\n\n\n" not in block
    assert "### Tooling preferences\n\n- License" in block


# --- `other`: guidance instead of a blank slot (#1258) ------------------------


def test_other_stanza_carries_the_gate_reasoning():
    """`other` means the harness cannot name the stack, so the one thing it can
    still supply is how to decide what `just check` should assert. The four
    points homelab-ai-plan derived unaided (PR #1) are what this pins."""
    stanza = cli.render_block("other").lower()
    assert "get wrong" in stanza, "ask what the repo can actually get wrong"
    assert "no dependency" in stanza or "dependency" in stanza
    assert "negative-test" in stanza, "a gate never seen to fail is not a gate"


def test_other_justfile_placeholder_gate_fails():
    """The seeded `other` gate is a TODO. Exiting 0 would make it the exact
    'passes by not looking' gate this project keeps refusing to ship — and the
    managed block would then promise a `just check` that succeeds while
    asserting nothing. An unwritten gate must not report success."""
    body = cli._read_harness("justfile.other")
    check = body.split("check:")[1]
    assert "exit 1" in check


# --- block injection ---------------------------------------------------------


def test_creates_agent_file_when_missing(repo: Path):
    action = cli.inject_block(repo / "CLAUDE.md", cli.render_block("python"))
    assert action == "created"
    text = (repo / "CLAUDE.md").read_text()
    assert cli.BEGIN_MARK in text
    assert cli.END_MARK in text
    assert "## Project" in text


def test_injection_is_idempotent(repo: Path):
    block = cli.render_block("python")
    cli.inject_block(repo / "CLAUDE.md", block)
    first = (repo / "CLAUDE.md").read_text()
    action = cli.inject_block(repo / "CLAUDE.md", block)
    assert action == "updated"
    assert (repo / "CLAUDE.md").read_text() == first


def test_replacement_preserves_content_outside_the_block(repo: Path):
    f = repo / "CLAUDE.md"
    f.write_text(
        f"# Above the block\n\n{cli.BEGIN_MARK}\nstale conventions\n{cli.END_MARK}\n"
        "\n## Project\n\nhand-written project notes\n"
    )
    cli.inject_block(f, cli.render_block("rust"))
    text = f.read_text()
    assert "# Above the block" in text
    assert "hand-written project notes" in text
    assert "stale conventions" not in text
    assert "cargo clippy --all-targets" in text


def test_replaces_a_block_written_by_the_old_bash_installer(repo: Path):
    """Marker *text* changed this sprint; the prefix did not. Nine live repos."""
    f = repo / "CLAUDE.md"
    f.write_text(f"{OLD_BEGIN}\nold conventions\n{OLD_END}\n\n## Project\n\nkeep me\n")
    action = cli.inject_block(f, cli.render_block("python"))
    assert action == "updated"
    text = f.read_text()
    assert "old conventions" not in text
    assert "keep me" in text
    assert text.count("kproject:begin") == 1
    assert text.count("kproject:end") == 1


def test_appends_to_an_agent_file_that_has_no_block(repo: Path):
    f = repo / "CLAUDE.md"
    f.write_text("# Existing notes\n\nsomething I wrote\n")
    action = cli.inject_block(f, cli.render_block("python"))
    assert action == "appended"
    text = f.read_text()
    assert "something I wrote" in text
    assert cli.BEGIN_MARK in text


def test_crlf_file_keeps_crlf_and_is_not_mangled(repo: Path):
    """cleo hazard from #699: core.autocrlf must not corrupt the markers."""
    f = repo / "CLAUDE.md"
    f.write_bytes(
        f"# Notes\r\n\r\n{cli.BEGIN_MARK}\r\nstale\r\n{cli.END_MARK}\r\n\r\nkeep me\r\n".encode()
    )
    cli.inject_block(f, cli.render_block("python"))
    raw = f.read_bytes()
    assert b"\r\n" in raw
    assert raw.replace(b"\r\n", b"\n").count(b"\n\n\n") == 0
    text = raw.decode()
    assert "keep me" in text
    assert "stale" not in text
    assert text.count("kproject:begin") == 1


def test_creates_parent_directory_for_ghcp(repo: Path):
    cli.inject_block(repo / ".github" / "copilot-instructions.md", cli.render_block("other"))
    assert (repo / ".github" / "copilot-instructions.md").is_file()


# --- stack detection ---------------------------------------------------------


def test_detects_rust_from_cargo_toml(repo: Path):
    (repo / "Cargo.toml").write_text("[package]\n")
    assert cli.detect_stack(repo) == "rust"


def test_detects_python_from_pyproject(repo: Path):
    (repo / "pyproject.toml").write_text("[project]\n")
    assert cli.detect_stack(repo) == "python"


def test_detects_other_when_nothing_matches(repo: Path):
    assert cli.detect_stack(repo) == "other"


def test_detects_go_from_go_mod(repo: Path):
    (repo / "go.mod").write_text("module example.com/x\n")
    assert cli.detect_stack(repo) == "go"


def test_cargo_wins_when_a_repo_carries_both(repo: Path):
    (repo / "Cargo.toml").write_text("[package]\n")
    (repo / "pyproject.toml").write_text("[project]\n")
    assert cli.detect_stack(repo) == "rust"


def test_go_mod_wins_over_pyproject(repo: Path):
    """`pyproject.toml` is the weakest marker — it doubles as tool config."""
    (repo / "go.mod").write_text("module example.com/x\n")
    (repo / "pyproject.toml").write_text("[project]\n")
    assert cli.detect_stack(repo) == "go"


def test_cargo_wins_over_go_mod(repo: Path):
    (repo / "Cargo.toml").write_text("[package]\n")
    (repo / "go.mod").write_text("module example.com/x\n")
    assert cli.detect_stack(repo) == "rust"


def test_detects_cmake_from_cmakelists(repo: Path):
    (repo / "CMakeLists.txt").write_text("project(x C)\n")
    assert cli.detect_stack(repo) == "cmake"


def test_cmake_wins_over_pyproject(repo: Path):
    """The kpidash shape: a C build at the root, Python only in a client package.

    `CMakeLists.txt` defines a build the way `Cargo.toml` and `go.mod` do, so it
    ranks above the marker that doubles as tool config.
    """
    (repo / "CMakeLists.txt").write_text("project(x C)\n")
    (repo / "pyproject.toml").write_text("[project]\n")
    assert cli.detect_stack(repo) == "cmake"


def test_cargo_and_go_win_over_cmakelists(repo: Path):
    """CMake commonly appears as a *dependency's* build system inside a Rust or
    Go repo (`cc`/`cgo` vendoring), so it must not outrank either."""
    (repo / "CMakeLists.txt").write_text("project(x C)\n")
    (repo / "go.mod").write_text("module example.com/x\n")
    assert cli.detect_stack(repo) == "go"
    (repo / "Cargo.toml").write_text("[package]\n")
    assert cli.detect_stack(repo) == "rust"


def test_explicit_stack_overrides_detection(repo: Path):
    (repo / "Cargo.toml").write_text("[package]\n")
    cli.main(["--stack", "other", "--agent", "claude", str(repo)])
    assert "cargo" not in (repo / "CLAUDE.md").read_text()


def test_detection_drives_the_block_when_no_flag_given(repo: Path):
    (repo / "Cargo.toml").write_text("[package]\n")
    cli.main(["--agent", "claude", str(repo)])
    assert "cargo clippy --all-targets" in (repo / "CLAUDE.md").read_text()


# --- gitignore ---------------------------------------------------------------


def test_gitignore_gets_base_entries(repo: Path):
    cli.ensure_gitignore(repo, "other")
    lines = (repo / ".gitignore").read_text().splitlines()
    assert ".scratch/" in lines
    assert ".env" in lines


def test_gitignore_gets_stack_entries(repo: Path):
    cli.ensure_gitignore(repo, "python")
    lines = (repo / ".gitignore").read_text().splitlines()
    assert ".venv/" in lines
    assert "__pycache__/" in lines
    cli.ensure_gitignore(repo, "rust")
    assert "target/" in (repo / ".gitignore").read_text().splitlines()
    cli.ensure_gitignore(repo, "go")
    lines = (repo / ".gitignore").read_text().splitlines()
    assert "*.test" in lines
    assert "go.work" in lines
    cli.ensure_gitignore(repo, "cmake")
    lines = (repo / ".gitignore").read_text().splitlines()
    assert "build/" in lines
    assert "build-*/" in lines, "kpidash carries build-native/ and build-pi5/"
    assert "CMakeCache.txt" in lines


def test_gitignore_does_not_duplicate_on_rerun(repo: Path):
    (repo / ".gitignore").write_text(".env\n")
    cli.ensure_gitignore(repo, "python")
    cli.ensure_gitignore(repo, "python")
    lines = (repo / ".gitignore").read_text().splitlines()
    assert lines.count(".env") == 1
    assert lines.count(".venv/") == 1


def test_gitignore_preserves_existing_entries(repo: Path):
    (repo / ".gitignore").write_text("mine/\n")
    cli.ensure_gitignore(repo, "other")
    assert "mine/" in (repo / ".gitignore").read_text().splitlines()


# --- layout and seeds --------------------------------------------------------


def test_creates_the_layout(repo: Path):
    cli.main(["--agent", "claude", str(repo)])
    for d in ("sprints/planning", "sprints/review", "docs", ".scratch"):
        assert (repo / d).is_dir()
    assert (repo / "sprints" / "planning" / "roadmap.md").is_file()


def test_seeds_the_justfile_for_the_stack(repo: Path):
    (repo / "pyproject.toml").write_text("[project]\n")
    cli.main(["--agent", "claude", str(repo)])
    assert "uv run ruff format --check ." in (repo / "justfile").read_text()


def test_seeds_the_go_justfile_when_go_mod_is_present(repo: Path):
    (repo / "go.mod").write_text("module example.com/x\n")
    cli.main(["--agent", "claude", str(repo)])
    text = (repo / "justfile").read_text()
    assert "go vet ./..." in text
    assert "go test ./..." in text


def test_go_gate_does_not_trust_gofmt_exit_status():
    """`gofmt -l` prints offenders and exits 0 — a bare call is a gate that lies.

    Same class of trap as `clippy` without `--all-targets`. The gate must
    assert on gofmt's *output*, so it has to capture it.
    """
    check = cli._read_harness("justfile.go").split("check:")[1].split("\n\n")[0]
    assert "gofmt -l" in check
    assert "$(gofmt -l" in check, "gate must capture gofmt output, not just run it"


def test_seeds_the_cmake_justfile_when_cmakelists_is_present(repo: Path):
    (repo / "CMakeLists.txt").write_text("project(x C)\n")
    cli.main(["--agent", "claude", str(repo)])
    text = (repo / "justfile").read_text()
    assert "cmake --build" in text
    assert "ctest" in text


def test_cmake_gate_treats_an_empty_test_suite_as_failure():
    """`ctest` prints "No tests were found!!!" and exits 0 when nothing is
    registered — so a bare call is a gate that passes loudest when there is
    least to check. Same class of trap as `gofmt -l` (003) and `clippy` without
    `--all-targets`: the gate must opt into the strict behaviour explicitly.
    """
    check = cli._read_harness("justfile.cmake").split("check:")[1]
    assert "ctest" in check
    assert "--no-tests=error" in check, "bare ctest exits 0 with no tests registered"


def test_cmake_gate_builds_out_of_source_in_its_own_tree():
    """A cross-compiled repo already has a build tree per target; the gate must
    not fight one of them for CMakeCache.txt."""
    body = cli._read_harness("justfile.cmake")
    assert "build-check" in body


def test_never_overwrites_an_existing_justfile_or_roadmap(repo: Path):
    (repo / "justfile").write_text("# mine\n")
    (repo / "sprints" / "planning").mkdir(parents=True)
    (repo / "sprints" / "planning" / "roadmap.md").write_text("# my roadmap\n")
    cli.main(["--agent", "claude", str(repo)])
    assert (repo / "justfile").read_text() == "# mine\n"
    assert (repo / "sprints" / "planning" / "roadmap.md").read_text() == "# my roadmap\n"


# --- the `check` alias --------------------------------------------------------
#
# #1254: the managed block says `just check` runs the gates, but an existing
# justfile is never overwritten — so in a repo whose gate is named something
# else the block asserted something false, inside a region the repo is not
# allowed to correct. klams hit this for real (sprint 044) and fixed it by hand
# with exactly the alias these tests pin.


def test_recipe_names_ignores_assignments_and_bodies():
    """The two things that read as recipes if you only look for a colon."""
    names = cli._recipe_names(
        'gate := "not a recipe"\n'
        'export TOKEN := "x"\n'
        'set shell := ["bash", "-uc"]\n'
        "# check: not a recipe either\n"
        "default:\n"
        "    @just --list\n"
        "    # check: still not a recipe\n"
        "lint: default\n"
        "    ruff check .\n"
    )
    assert names == {"default", "lint"}


def test_recipe_names_sees_parameterised_recipes_and_aliases():
    names = cli._recipe_names('build target="dev":\n    echo {{target}}\nalias c := build\n')
    assert names == {"build", "c"}


def test_adds_check_alias_when_the_gate_has_another_name(repo: Path):
    (repo / "justfile").write_text("# mine\n\ngate:\n    cargo clippy\n")
    assert cli.ensure_check_recipe(repo) == "gate"
    text = (repo / "justfile").read_text()
    assert "check: gate" in text
    assert "# mine" in text, "must extend, not replace"
    assert "cargo clippy" in text


def test_check_alias_lands_on_a_real_install(repo: Path):
    """End to end: the block's promise is true in the repo it was written into."""
    (repo / "justfile").write_text("gate:\n    cargo clippy\n")
    (repo / "Cargo.toml").write_text("[package]\n")
    cli.main(["--agent", "claude", str(repo)])
    assert "`just check`" in (repo / "CLAUDE.md").read_text()
    assert "check: gate" in (repo / "justfile").read_text()


def test_check_alias_has_a_clean_just_list_doc_comment(repo: Path):
    """`just --list` shows the comment line directly above a recipe. Without a
    blank line the rationale's last line leaks in as a sentence fragment — in
    every migrated repo's listing, which is where people look first."""
    (repo / "justfile").write_text("gate:\n    pytest\n")
    cli.ensure_check_recipe(repo)
    lines = (repo / "justfile").read_text().splitlines()
    assert lines[lines.index("check: gate") - 1] == "# Run CI gates (alias for `gate`)"


def test_leaves_an_existing_check_recipe_alone(repo: Path):
    body = "check:\n    pytest\ngate:\n    echo no\n"
    (repo / "justfile").write_text(body)
    assert cli.ensure_check_recipe(repo) is None
    assert (repo / "justfile").read_text() == body


def test_respects_a_check_that_is_already_an_alias(repo: Path):
    """A recipe colliding with an alias is a hard error in just, not a duplicate."""
    body = "gate:\n    pytest\nalias check := gate\n"
    (repo / "justfile").write_text(body)
    assert cli.ensure_check_recipe(repo) is None
    assert (repo / "justfile").read_text() == body


def test_check_alias_is_idempotent_across_reruns(repo: Path):
    (repo / "justfile").write_text("gate:\n    pytest\n")
    cli.ensure_check_recipe(repo)
    once = (repo / "justfile").read_text()
    assert cli.ensure_check_recipe(repo) is None
    assert (repo / "justfile").read_text() == once


def test_gate_name_priority_is_honoured(repo: Path):
    (repo / "justfile").write_text("all:\n    x\nci:\n    y\ngate:\n    z\n")
    assert cli.ensure_check_recipe(repo) == "gate"


def test_test_recipe_is_not_treated_as_a_gate(repo: Path):
    """`test` is one component of a gate, not the aggregate — aliasing to it
    would keep the block's promise only in the letter."""
    (repo / "justfile").write_text("test:\n    pytest\n")
    assert cli.ensure_check_recipe(repo) is None
    assert "check" not in (repo / "justfile").read_text()


def test_warns_and_writes_nothing_when_no_gate_is_recognisable(repo: Path, capsys):
    (repo / "justfile").write_text("# mine\n")
    assert cli.ensure_check_recipe(repo) is None
    assert (repo / "justfile").read_text() == "# mine\n"
    assert "check" in capsys.readouterr().err


def test_the_no_gate_warning_names_the_consequence(repo: Path, capsys):
    """#1259. Writing nothing stays right — a guessed gate passes by not looking
    — but the block's `just check` promise is unconditional, so the warning has
    to state that the promise is false here, not merely that a recipe is absent.
    kpidash (sprint 014) is the evidence this lever works: the warning was
    noticed and the gap closed in the same sitting.
    """
    (repo / "justfile").write_text("_default:\n    @just --list\npublish:\n    kpkg add\n")
    assert cli.ensure_check_recipe(repo) is None
    err = capsys.readouterr().err.lower()
    assert "managed block" in err, "must name what is now false, not just what is missing"
    assert "not true" in err or "false" in err
    assert "nothing was written" in err, "say the installer declined, so it reads as a choice"


def test_seeded_justfile_needs_no_alias(repo: Path):
    """Every shipped template already defines `check`; none should be touched."""
    for stack in cli.STACKS:
        (repo / "justfile").write_text(cli._read_harness(f"justfile.{stack}"))
        assert cli.ensure_check_recipe(repo) is None, stack


def test_no_justfile_at_all_is_not_an_error(repo: Path):
    assert cli.ensure_check_recipe(repo) is None


def test_check_alias_preserves_crlf(repo: Path):
    (repo / "justfile").write_bytes(b"gate:\r\n    pytest\r\n")
    cli.ensure_check_recipe(repo)
    raw = (repo / "justfile").read_bytes()
    assert b"\r\n" in raw
    assert b"\n" not in raw.replace(b"\r\n", b""), "must not leave mixed line endings"
    assert "check: gate" in raw.decode()


# --- agent targets and CLI ---------------------------------------------------


def test_agent_both_writes_both_files(repo: Path):
    cli.main(["--agent", "both", str(repo)])
    assert (repo / "CLAUDE.md").is_file()
    assert (repo / ".github" / "copilot-instructions.md").is_file()


def test_agent_defaults_to_both(repo: Path):
    cli.main([str(repo)])
    assert (repo / "CLAUDE.md").is_file()
    assert (repo / ".github" / "copilot-instructions.md").is_file()


def test_ghcp_only_leaves_claude_alone(repo: Path):
    cli.main(["--agent", "ghcp", str(repo)])
    assert not (repo / "CLAUDE.md").exists()
    assert (repo / ".github" / "copilot-instructions.md").is_file()


def test_missing_target_is_an_error(tmp_path: Path):
    assert cli.main([str(tmp_path / "nope")]) != 0


def test_invalid_stack_is_rejected(repo: Path):
    with pytest.raises(SystemExit):
        cli.main(["--stack", "haskell", str(repo)])


def test_instructions_ask_for_work_items_to_be_resolved_as_they_complete():
    """#1166. Agents batch every resolution into sprint-ship, so kfdc's Fire
    Missions card read 1/10 for the whole life of a sprint that was nearly done
    — a progress bar that says nothing while it would be useful, then jumps to
    10/10. The instruction belongs in the block every agent already reads.
    """
    block = cli.render_block("python").lower()
    assert "resolved" in block
    assert "sprint-ship" in block


@pytest.mark.parametrize("stack", cli.STACKS)
def test_instructions_carry_the_cross_project_plan_pointer(stack: str):
    """#1406. A plan nobody reads is a document, not a constraint — but a vague
    "consider the plan" gets token-taxed in every repo and acted on in none. So
    the pointer states the applicability test first (one grep of `index.md`),
    then the location, and nothing else: the amend procedure and the
    supersede-don't-delete rule stay in the plan repo's own README, exactly as
    the skill trio's blocks do. Every stack carries it — mapping is a property
    of the project, not of its toolchain.
    """
    block = cli.render_block(stack)
    assert "cross-project-planning" in block, "the repo the routing table lives in"
    assert "index.md" in block, "the applicability test is a grep, and it must be named"
    assert 'root: "kai:src"' in block, "three of the mapped repos are read from other hosts"
    assert "clone a second copy" in block, "the drift this pointer exists to avoid"


def test_the_plan_pointer_does_not_restate_the_plan_repos_own_rules():
    """The location is duplicated in four places (three skills + this block) and
    that is affordable; the *procedure* is not. Copies of a rule drift.
    """
    block = cli.render_block("other")
    assert "supersede" not in block.lower()
    assert "GP-" not in block


def test_warns_about_old_harness_remnants(repo: Path, capsys):
    (repo / "specs").mkdir()
    cli.main(["--agent", "claude", str(repo)])
    assert "specs" in capsys.readouterr().err
