#!/usr/bin/env bash
# validate-fsm-single.sh — Run FSM dispatcher for a single topic, then verify.
# Usage: bash .chaplain/scripts/validate-fsm-single.sh [topic_file]
#
# If no topic_file given, creates a trivial test topic in .chaplain/inbox-fsm/.
# Runs the dispatcher in single-cycle mode (one topic, then stop).
# Asserts: topic processed, worktree cleaned, no errors.

set -euo pipefail

INBOX_DIR=".chaplain/inbox-fsm"
LOG_DIR="logs/fsm-validation"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${LOG_DIR}/validate-${TIMESTAMP}.log"

mkdir -p "$INBOX_DIR" "$LOG_DIR"

# --- Create test topic if none provided ---
TOPIC_FILE="${1:-}"
if [ -z "$TOPIC_FILE" ]; then
    TOPIC_FILE="${INBOX_DIR}/test-fsm-validation.md"
    cat > "$TOPIC_FILE" << 'EOF'
# Test: FSM Validation Run

Fix a trivial typo in USER.md to validate the FSM pipeline end-to-end.

## Details

Change "YAMLGraph" to "YAMLGraph" in USER.md (no-op if already correct).
This is a minimal change to exercise the full plan→judge→enforce→merge cycle.
EOF
    echo "📝 Created test topic: $TOPIC_FILE"
fi

# --- Pre-flight checks ---
echo "🔍 Pre-flight checks..."
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "❌ Must be on main branch (currently on: $BRANCH)"
    exit 1
fi

if ! command -v statemachine &>/dev/null; then
    echo "❌ statemachine CLI not found. Install: pip install statemachine-engine"
    exit 1
fi

# Count worktrees before
WT_BEFORE=$(git worktree list | wc -l | tr -d ' ')

# Count topics in inbox
TOPIC_COUNT=$(ls -1 "$INBOX_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
echo "📥 Topics in ${INBOX_DIR}: ${TOPIC_COUNT}"

if [ "$TOPIC_COUNT" -eq 0 ]; then
    echo "❌ No topics in $INBOX_DIR"
    exit 1
fi

# --- Run dispatcher (single cycle) ---
echo "🚀 Starting FSM dispatcher (single cycle)..."
echo "   Inbox: $INBOX_DIR"
echo "   Log: $LOG_FILE"

# Run dispatcher with test inbox, capture output
# The dispatcher will: sync inbox → find topic → run pipeline → return to idle
# We send a 'stop' event after the first cycle completes
statemachine .chaplain/config/watcher-dispatcher.yaml \
    --actions-dir .chaplain/actions \
    --initial-context "{\"inbox_dir\":\"${INBOX_DIR}\"}" \
    --debug \
    2>&1 | tee "$LOG_FILE" &

DISPATCHER_PID=$!
echo "   PID: $DISPATCHER_PID"

# Wait for dispatcher to finish (it loops — we need to detect completion)
# Monitor for "topic_done" or "error" event, then send stop
TIMEOUT=1800  # 30 minutes max
ELAPSED=0
INTERVAL=10

while kill -0 "$DISPATCHER_PID" 2>/dev/null; do
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "⏰ Timeout after ${TIMEOUT}s — killing dispatcher"
        kill "$DISPATCHER_PID" 2>/dev/null || true
        exit 1
    fi

    # Check if topic was processed (inbox should be empty, processing should have the file)
    REMAINING=$(ls -1 "$INBOX_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
    if [ "$REMAINING" -eq 0 ] && grep -q "topic_done\|→ idle" "$LOG_FILE" 2>/dev/null; then
        echo "✅ Topic processed — sending stop signal"
        sleep 2
        kill "$DISPATCHER_PID" 2>/dev/null || true
        break
    fi

    sleep "$INTERVAL"
    ELAPSED=$((ELAPSED + INTERVAL))
done

wait "$DISPATCHER_PID" 2>/dev/null || true

# --- Post-run assertions ---
echo ""
echo "🔍 Post-run assertions..."
PASS=0
FAIL=0

# 1. Topic moved out of inbox
REMAINING=$(ls -1 "$INBOX_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$REMAINING" -eq 0 ]; then
    echo "  ✅ Inbox empty (topic consumed)"
    PASS=$((PASS + 1))
else
    echo "  ❌ Inbox still has $REMAINING topics"
    FAIL=$((FAIL + 1))
fi

# 2. No stale worktrees
WT_AFTER=$(git worktree list | wc -l | tr -d ' ')
if [ "$WT_AFTER" -le "$WT_BEFORE" ]; then
    echo "  ✅ No stale worktrees (before: $WT_BEFORE, after: $WT_AFTER)"
    PASS=$((PASS + 1))
else
    echo "  ❌ Stale worktrees detected (before: $WT_BEFORE, after: $WT_AFTER)"
    git worktree list
    FAIL=$((FAIL + 1))
fi

# 3. Check log for errors
ERROR_COUNT=$(grep -ci "error\|traceback\|exception" "$LOG_FILE" 2>/dev/null || echo 0)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "  ✅ No errors in log"
    PASS=$((PASS + 1))
else
    echo "  ⚠️  $ERROR_COUNT error-like lines in log (review: $LOG_FILE)"
    FAIL=$((FAIL + 1))
fi

# 4. Check for completed state in log
if grep -q "completed\|cleaning_up" "$LOG_FILE" 2>/dev/null; then
    echo "  ✅ Pipeline reached completion states"
    PASS=$((PASS + 1))
else
    echo "  ❌ Pipeline did not reach completion"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Results: $PASS passed, $FAIL failed"
echo "  Log: $LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "🎉 FSM single-worker validation passed!"
