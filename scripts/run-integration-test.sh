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

# Clean stale pipeline logs so polling loop doesn't find old results
rm -f logs/fsm-integration-smoke-test-*.log

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

# Run the dispatcher in background so we can kill it after pipeline terminates
statemachine .chaplain/config/integration-dispatcher.yaml \
  --actions-dir .chaplain/actions \
  --initial-context "{\"inbox_dir\":\"$INBOX\"}" \
  --debug &
DISPATCHER_PID=$!

# Wait for pipeline to complete (monitor log for terminal state)
FINAL_LOG=""
for i in $(seq 1 120); do
  sleep 5
  FINAL_LOG=$(ls -1t logs/fsm-integration-smoke-test-*.log 2>/dev/null | head -1)
  if [ -n "$FINAL_LOG" ] && grep -q "terminal state: stopped" "$FINAL_LOG" 2>/dev/null; then
    break
  fi
done

# Kill dispatcher
kill "$DISPATCHER_PID" 2>/dev/null || true
wait "$DISPATCHER_PID" 2>/dev/null || true

echo ""
echo "=== Integration Test Result ==="

# Assert pipeline outcome
if [ -z "$FINAL_LOG" ]; then
  echo "❌ FAIL: No pipeline log found"
  exit 1
fi
if grep -q "completed --job_done--> stopped" "$FINAL_LOG"; then
  echo "✅ PASS: Pipeline reached completed"
  exit 0
else
  echo "❌ FAIL: Pipeline did not reach completed"
  echo ""
  echo "Last 20 lines of log:"
  tail -20 "$FINAL_LOG"
  exit 1
fi
