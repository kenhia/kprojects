# List available recipes
default:
    @just --list

# Apply the harness to a target repo (agent: claude|ghcp|both)
apply target agent="both":
    ./install.sh --agent {{agent}} {{target}}

# Install the /kproject-init skill into ~/.claude/skills
install-skill:
    ./install.sh --skill

# Run CI gates
check:
    bash -n install.sh
    @command -v shellcheck >/dev/null && shellcheck install.sh || echo "shellcheck not available; skipped"
