#!/usr/bin/env bash
# copilot_session_gc.sh — Prune stale Copilot CLI sessions (FR-138)
#
# Usage:
#   scripts/copilot_session_gc.sh [--max-age DAYS] [--dry-run] [--verbose]
#
# Defaults: --max-age 7
#
# Environment:
#   COPILOT_SESSION_DIR  Override session directory (default: ~/.copilot/session-state)
#   COPILOT_SESSION_ID   Active session UUID to protect from deletion

set -euo pipefail

MAX_AGE_DAYS=7
DRY_RUN=false
VERBOSE=false
SESSION_DIR="${COPILOT_SESSION_DIR:-$HOME/.copilot/session-state}"
ACTIVE_SESSION="${COPILOT_SESSION_ID:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --max-age)
            MAX_AGE_DAYS="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

if [[ ! -d "$SESSION_DIR" ]]; then
    [[ "$VERBOSE" == true ]] && echo "Session directory does not exist: $SESSION_DIR"
    echo "🧹 Copilot session GC: 0 removed, 0 kept (directory absent)"
    exit 0
fi

removed=0
kept=0
skipped_active=0
now=$(date +%s)

for entry in "$SESSION_DIR"/*/; do
    # Skip if glob didn't match (empty directory)
    [[ -d "$entry" ]] || continue

    uuid=$(basename "$entry")

    # Protect active session
    if [[ -n "$ACTIVE_SESSION" && "$uuid" == "$ACTIVE_SESSION" ]]; then
        skipped_active=1
        echo "⏭  skip active session: $uuid"
        kept=$((kept + 1))
        continue
    fi

    # Calculate age in days using directory mtime
    if [[ "$(uname)" == "Darwin" ]]; then
        mtime=$(stat -f %m "$entry")
    else
        mtime=$(stat -c %Y "$entry")
    fi
    age_days=$(( (now - mtime) / 86400 ))

    if [[ $age_days -ge $MAX_AGE_DAYS ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            echo "🔍 would remove: $uuid (${age_days}d old)"
        else
            rm -rf "$entry"
            echo "🗑  removed: $uuid (${age_days}d old)"
        fi
        removed=$((removed + 1))
    else
        [[ "$VERBOSE" == true ]] && echo "✓  keep: $uuid (${age_days}d old)"
        kept=$((kept + 1))
    fi
done

action="removed"
[[ "$DRY_RUN" == true ]] && action="would remove"

echo "🧹 Copilot session GC: $removed $action, $kept kept (max-age: ${MAX_AGE_DAYS}d)"
