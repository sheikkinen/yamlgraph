#!/usr/bin/env bash
# fix_bare.sh — Fix bare=true corruption in .git/config
#
# Usage: scripts/fix_bare.sh
#
# This is a workaround for the bug where worktree operations corrupt
# the main repo's .git/config by setting bare=true.
# See: .chaplain/inbox/git-bare-corruption.md

set -euo pipefail

CONFIG="${GIT_DIR:-.git}/config"

if grep -q 'bare = true' "$CONFIG" 2>/dev/null; then
    sed -i '' 's/bare = true/bare = false/' "$CONFIG"
    echo "✓ Fixed bare=true in $CONFIG"
else
    echo "✓ No fix needed (bare=false or not found)"
fi
