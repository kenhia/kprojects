# Windows: `just` runs recipes through `sh`, which Windows does not ship — put
# Git for Windows' `usr\bin` on PATH (it holds `sh.exe`) or run from Git Bash.
# (Upstream's own requirement: "sh must be available in the PATH".)

# List available recipes
default:
    @just --list

# This placeholder exits 1 deliberately. The managed block tells every agent
# that `just check` runs the gates; a TODO that exits 0 would satisfy that
# promise in the letter while asserting nothing — the "passes by not looking"
# gate. Failing until it is written is the honest state. See the tooling
# stanza in CLAUDE.md for how to decide what it should assert.

# Run CI gates — TODO: write them, this repo has no stack to infer them from
check:
    @echo "No gate yet. Ask what this repo can actually get wrong, add no"
    @echo "dependency to check it, and prove the gate fails on a planted"
    @echo "error before trusting it. Then replace this recipe."
    @exit 1
