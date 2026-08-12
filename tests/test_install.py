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
    assert "cargo" not in cli.render_block("other")


def test_other_stack_leaves_no_blank_bullet_hole():
    """An empty stanza should drop its line, not leave a stray blank."""
    block = cli.render_block("other")
    assert "\n\n\n" not in block
    assert "### Tooling preferences\n\n- License" in block


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


def test_cargo_wins_when_a_repo_carries_both(repo: Path):
    (repo / "Cargo.toml").write_text("[package]\n")
    (repo / "pyproject.toml").write_text("[project]\n")
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


def test_never_overwrites_an_existing_justfile_or_roadmap(repo: Path):
    (repo / "justfile").write_text("# mine\n")
    (repo / "sprints" / "planning").mkdir(parents=True)
    (repo / "sprints" / "planning" / "roadmap.md").write_text("# my roadmap\n")
    cli.main(["--agent", "claude", str(repo)])
    assert (repo / "justfile").read_text() == "# mine\n"
    assert (repo / "sprints" / "planning" / "roadmap.md").read_text() == "# my roadmap\n"


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


def test_warns_about_old_harness_remnants(repo: Path, capsys):
    (repo / "specs").mkdir()
    cli.main(["--agent", "claude", str(repo)])
    assert "specs" in capsys.readouterr().err
