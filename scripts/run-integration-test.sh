#!/usr/bin/env bash
# FR-301: One-command integration test wrapper (A4)
# Runs the full watcher pipeline end-to-end with bash stubs instead of LLM calls.
# Usage: scripts/run-integration-test.sh
set -euo pipefail

INBOX=".chaplain/inbox-integration"
LOG_FILE="docs/watcher-integration.md"

echo "=== FR-301 Integration Test ==="
echo ""

# Clean up stale state from previous runs
if git worktree list | grep -q "feat/watcher2-smoke-test"; then
  git worktree remove tmp/worktrees/feat/watcher2-smoke-test --force 2>/dev/null || true
fi
if git branch --list "feat/watcher2-smoke-test" | grep -q .; then
  git branch -D feat/watcher2-smoke-test 2>/dev/null || true
fi
rm -f .chaplain/failed/smoke-test.md .chaplain/processing/smoke-test.md

# Seed the inbox
mkdir -p "$INBOX"
echo "# Integration smoke test — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$INBOX/smoke-test.md"
echo "✓ Seeded $INBOX/smoke-test.md"

# Ensure log file exists on main
if [ ! -f "$LOG_FILE" ]; then
  echo "# Watcher Integration Log" > "$LOG_FILE"
  git add "$LOG_FILE"
  git commit -m "docs: init integration log"
  echo "✓ Created $LOG_FILE on main"
fi

echo "✓ Starting integration dispatcher..."
echo ""

# Run the dispatcher
statemachine .chaplain/config/integration-dispatcher.yaml \
  --actions-dir .chaplain/actions \
  --initial-context "{\"inbox_dir\":\"$INBOX\"}" \
  --debug

echo ""
echo "=== Integration Test Complete ==="
echo "Check $LOG_FILE for timestamped entries."
echo "Check GitHub for merged PR."
