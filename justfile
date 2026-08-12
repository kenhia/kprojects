# List available recipes
default:
    @just --list

# Apply the harness to a target repo (extra flags: --agent, --stack)
apply target *flags:
    uv run kproject-install {{flags}} {{target}}

# Re-apply the harness to this repo after editing src/kprojects/harness/
apply-self:
    uv run kproject-install .

# Run CI gates (lint, typecheck, tests)
check:
    uv run ruff format --check .
    uv run ruff check .
    uv run ty check
    uv run pytest

# Apply formatting and safe autofixes
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# Build the wheel and sdist
build:
    uv build
