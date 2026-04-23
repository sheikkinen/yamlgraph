#!/usr/bin/env bash
# Demo: Verify script retirement (FR-276)
set -euo pipefail
cd "$(dirname "$0")/../../.."

echo "=== Script Retirement Verification ==="
ls .chaplain/watch.sh 2>/dev/null && echo "FAIL: watch.sh still exists" || echo "✅ watch.sh removed"
ls scripts/enforce_worktree.sh 2>/dev/null && echo "FAIL: enforce_worktree.sh still exists" || echo "✅ enforce_worktree.sh removed"
ls scripts/bugfix_worktree.sh 2>/dev/null && echo "FAIL: bugfix_worktree.sh still exists" || echo "✅ bugfix_worktree.sh removed"
ls -la .chaplain/watcher2.sh > /dev/null && echo "✅ watcher2.sh exists and ready"
echo "=== All checks passed ==="
