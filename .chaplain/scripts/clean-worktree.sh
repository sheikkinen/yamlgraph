#!/usr/bin/env bash
# clean-worktree.sh — Remove worktree, local branch, and remote branch for a given issue
#
# Usage:
#   .chaplain/scripts/clean-worktree.sh 339
#   .chaplain/scripts/clean-worktree.sh 339 340 341

set -uo pipefail

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <issue_number> [issue_number ...]"
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

for issue in "$@"; do
    branch="feat/watcher2-gh-${issue}"
    worktree="tmp/worktrees/feat/watcher2-gh-${issue}"

    echo "=== gh-${issue} ==="

    if [[ -d "$worktree" ]]; then
        rm -rf "$worktree"
        echo "  ✓ Removed worktree: $worktree"
    else
        echo "  - No worktree found"
    fi

    if git branch --list "$branch" | grep -q .; then
        git branch -D "$branch" 2>/dev/null
        echo "  ✓ Deleted local branch: $branch"
    else
        echo "  - No local branch"
    fi

    if git ls-remote --heads origin "$branch" 2>/dev/null | grep -q .; then
        git push origin --delete "$branch" 2>/dev/null
        echo "  ✓ Deleted remote branch: $branch"
    else
        echo "  - No remote branch"
    fi
done
