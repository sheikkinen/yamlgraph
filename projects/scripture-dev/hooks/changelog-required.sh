#!/usr/bin/env bash
# hooks/changelog-required.sh — Require changelog fragment for feat/fix commits
set -euo pipefail

# Get the commit message type from staged files
MSG_TYPE=""
if git log --oneline -1 2>/dev/null | grep -qE '^[a-f0-9]+ feat'; then
    MSG_TYPE="feat"
elif git log --oneline -1 2>/dev/null | grep -qE '^[a-f0-9]+ fix'; then
    MSG_TYPE="fix"
fi

# Also check staged files for changelog fragment
STAGED=$(git diff --cached --name-only 2>/dev/null || true)

if [ "$MSG_TYPE" = "feat" ] || [ "$MSG_TYPE" = "fix" ]; then
    if ! echo "$STAGED" | grep -q '^changelog/unreleased/'; then
        echo "FAIL: feat/fix commits must include a changelog fragment in changelog/unreleased/"
        exit 1
    fi
fi
