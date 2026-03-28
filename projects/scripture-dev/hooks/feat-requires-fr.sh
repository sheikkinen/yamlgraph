#!/usr/bin/env bash
# hooks/feat-requires-fr.sh — Enforce FR-XXX in feat: commit messages
set -euo pipefail

MSG_FILE="${1:-}"
if [ -z "$MSG_FILE" ] || [ ! -f "$MSG_FILE" ]; then
    exit 0
fi

MSG=$(head -1 "$MSG_FILE")

# Only enforce on feat: commits
if echo "$MSG" | grep -qE '^feat(\(.+\))?:'; then
    if ! echo "$MSG" | grep -qE 'FR-[0-9]+'; then
        echo "FAIL: feat commits must reference FR-XXX"
        echo "  Got: $MSG"
        exit 1
    fi
fi
