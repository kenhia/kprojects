#!/usr/bin/env bash
# install.sh — apply the kproject minimal harness to a target repo.
#
# Usage:
#   install.sh [--agent claude|ghcp|both] TARGET_DIR
#
# The /kproject-init skill is NOT installed from here. It lives in the
# agent-skills repo and reaches machines via k-homelab's claude-skills recipe
# (managed hosts) or bin/deploy-skill (unmanaged ones). One source, one path.
#
# Idempotent: layout pieces are only created if missing, and the agent
# instruction files get a managed block between kproject:begin/end markers
# that is replaced in place on re-run. Content outside the block is yours.
set -euo pipefail

KPROJECTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS="$KPROJECTS_DIR/harness"
BEGIN_MARK='<!-- kproject:begin — managed by kprojects/install.sh; do not edit inside this block -->'
END_MARK='<!-- kproject:end -->'

usage() {
    sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit "${1:-1}"
}

AGENT=both
TARGET=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent) AGENT="${2:?--agent needs claude|ghcp|both}"; shift 2 ;;
        -h|--help) usage 0 ;;
        -*) echo "unknown option: $1" >&2; usage ;;
        *) TARGET="$1"; shift ;;
    esac
done

case "$AGENT" in claude|ghcp|both) ;; *) echo "invalid --agent: $AGENT" >&2; usage ;; esac

# Replace (or append/create) the managed block in an agent instruction file.
inject_block() {
    local file="$1"
    mkdir -p "$(dirname "$file")"
    local tmp
    tmp="$(mktemp)"
    {
        echo "$BEGIN_MARK"
        cat "$HARNESS/instructions.md"
        echo "$END_MARK"
    } >"$tmp"

    if [[ -f "$file" ]] && grep -q 'kproject:begin' "$file"; then
        local out
        out="$(mktemp)"
        awk -v blockfile="$tmp" '
            /<!-- kproject:begin/ {
                skip = 1
                while ((getline line < blockfile) > 0) print line
                close(blockfile)
                next
            }
            /<!-- kproject:end/ { skip = 0; next }
            !skip { print }
        ' "$file" >"$out"
        mv "$out" "$file"
        echo "agents   : updated managed block in $file"
    elif [[ -f "$file" ]]; then
        printf '\n' >>"$file"
        cat "$tmp" >>"$file"
        echo "agents   : appended managed block to existing $file"
    else
        {
            cat "$tmp"
            printf '\n## Project\n\n'
            printf '<!-- project-specific instructions go here (outside the managed block).\n'
            printf '     Run /kproject-init to survey the repo and fill this in. -->\n'
        } >"$file"
        echo "agents   : created $file"
    fi
    rm -f "$tmp"
}

ensure_gitignore() {
    local entry
    touch .gitignore
    for entry in ".scratch/" ".env"; do
        grep -qxF "$entry" .gitignore || { echo "$entry" >>.gitignore; echo "gitignore: added $entry"; }
    done
}

warn_old_harness() {
    local found=0 p
    for p in .specify specs memory/constitution.md .github/prompts .atv docs/brainstorms; do
        [[ -e "$p" ]] && { echo "WARN     : possible old harness remnant: $p" >&2; found=1; }
    done
    if [[ $found -eq 1 ]]; then
        echo "WARN     : run /kproject-init in this repo to migrate/clean up interactively" >&2
    fi
}

if [[ -z "$TARGET" ]]; then
    usage
fi

[[ -d "$TARGET" ]] || { echo "not a directory: $TARGET" >&2; exit 1; }
cd "$TARGET"
[[ -d .git ]] || echo "WARN     : $TARGET is not a git repo root" >&2

mkdir -p sprints/planning sprints/review docs .scratch
echo "layout   : sprints/{planning,review} docs .scratch"

[[ -f sprints/planning/roadmap.md ]] || { cp "$HARNESS/roadmap.md" sprints/planning/roadmap.md; echo "layout   : seeded sprints/planning/roadmap.md"; }
[[ -f justfile ]] || { cp "$HARNESS/justfile" justfile; echo "layout   : seeded justfile"; }

ensure_gitignore

case "$AGENT" in
    claude) inject_block CLAUDE.md ;;
    ghcp)   inject_block .github/copilot-instructions.md ;;
    both)   inject_block CLAUDE.md
            inject_block .github/copilot-instructions.md ;;
esac

warn_old_harness
echo "done     : kproject harness applied to $(pwd)"
