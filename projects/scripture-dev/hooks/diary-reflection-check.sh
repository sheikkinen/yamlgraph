#!/usr/bin/env bash
# hooks/diary-reflection-check.sh — Block commits with unfilled diary reflection stubs
set -euo pipefail

STAGED=$(git diff --cached --name-only 2>/dev/null || true)
DIARY_FILES=$(echo "$STAGED" | grep '^docs/diary/' || true)

if [ -z "$DIARY_FILES" ]; then
    exit 0
fi

fail=0
for f in $DIARY_FILES; do
    if [ ! -f "$f" ]; then
        continue
    fi
    # Check for unfilled template markers
    if grep -qE '^\[INSERT |^\[DESCRIBE |^\[YOUR ' "$f"; then
        echo "FAIL: Unfilled diary template markers in $f"
        fail=1
    fi
done

exit $fail
