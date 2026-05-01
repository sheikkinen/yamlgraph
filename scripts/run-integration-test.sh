#!/usr/bin/env bash
# FR-301: One-command integration test wrapper (A4)
# Runs the full watcher pipeline end-to-end with bash stubs instead of LLM calls.
# Usage: scripts/run-integration-test.sh
set -euo pipefail

INBOX=".chaplain/inbox-integration"
LOG_FILE="docs/watcher-integration.md"
TOPIC_SLUG="smoke-$(date +%Y%m%d-%H%M%S)"
BRANCH_NAME="feat/watcher2-${TOPIC_SLUG}"

echo "=== FR-301 Integration Test ==="
echo "Topic: $TOPIC_SLUG | Branch: $BRANCH_NAME"
echo ""

# Clean up stale state from previous runs (any smoke-* artifacts)
for wt in $(git worktree list --porcelain | grep -oE 'tmp/worktrees/feat/watcher2-smoke-[^ ]+'); do
  git worktree remove "$wt" --force 2>/dev/null || true
done
git branch --list "feat/watcher2-smoke-*" | xargs -r git branch -D 2>/dev/null || true
rm -f .chaplain/failed/smoke-*.md .chaplain/processing/smoke-*.md

# Clean stale pipeline logs so polling loop doesn't find old results
rm -f logs/fsm-integration-smoke-*.log

# Seed the inbox
mkdir -p "$INBOX"
echo "# Integration smoke test — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$INBOX/${TOPIC_SLUG}.md"
echo "✓ Seeded $INBOX/${TOPIC_SLUG}.md"

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
  --debug > logs/integration-dispatcher-${TOPIC_SLUG}.log 2>&1 &
DISPATCHER_PID=$!

# Wait for pipeline to complete (monitor log for terminal state)
FINAL_LOG=""
for i in $(seq 1 120); do
  sleep 5
  FINAL_LOG=$(ls -1t logs/fsm-integration-${TOPIC_SLUG}-*.log 2>/dev/null | head -1)
  if [ -n "$FINAL_LOG" ] && grep -qE "terminal state: (completed|stopped)|Integration pipeline failed" "$FINAL_LOG" 2>/dev/null; then
    echo "✓ Pipeline terminal state detected (iteration $i)"
    break
  fi
  # Progress indicator every 12 iterations (60s)
  if (( i % 12 == 0 )); then echo "⏳ Waiting... ($((i*5))s)"; fi
done

# Kill dispatcher
kill "$DISPATCHER_PID" 2>/dev/null || true
sleep 2
kill -9 "$DISPATCHER_PID" 2>/dev/null || true
wait "$DISPATCHER_PID" 2>/dev/null || true

echo ""
echo "=== Integration Test Result ==="

# Assert pipeline outcome
if [ -z "$FINAL_LOG" ]; then
  echo "❌ FAIL: No pipeline log found"
  exit 1
fi
if grep -q "terminal state: completed" "$FINAL_LOG"; then
  echo "✅ PASS: Pipeline reached completed"
  exit 0
else
  echo "❌ FAIL: Pipeline did not reach completed"
  echo ""
  echo "Last 20 lines of log:"
  tail -20 "$FINAL_LOG"
  exit 1
fi
