#!/usr/bin/env bash
# .chaplain/watch.sh — Thin polling wrapper for Plan → Judge workflow
# FR-084: Delegates to yamlgraph graph run (copilot nodes via FR-081)
# FR-093: Added date and diary_prefix vars for diary append
# FR-098: Consolidated to examples/copilot/graph.yaml
set -euo pipefail
cd "$(dirname "$0")/.."

INBOX=".chaplain/inbox"
DRAFTS=".chaplain/drafts"
POLL=5

echo "👀 Watching $INBOX/"

while true; do
    topic_file=$(find "$INBOX" -name "*.md" -type f 2>/dev/null | head -1)
    [[ -z "$topic_file" ]] && { sleep "$POLL"; continue; }

    echo "📋 Processing: $topic_file"

    # FR-116: Snapshot feature-requests/ before graph execution
    before=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)

    yamlgraph graph run examples/copilot/graph.yaml \
        --var topic_file="$topic_file" \
        --var drafts_dir="$DRAFTS" \
        --var date="$(date +%Y-%m-%d)" \
        --var diary_prefix="Chaplain" \
        --full

    # FR-116: Detect new FR and spawn enforce pipeline
    after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
    new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)

    # FR-175: Sequential enforcement — wait for each pipeline before next
    if [[ -n "$new_fr" ]]; then
        if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
            echo "⏭️  Skipping rejected FR: $new_fr"
        # FR-173: Route Bug-type FRs to condemning test pipeline
        elif grep -q 'Type.*Bug' "$new_fr" 2>/dev/null; then
            echo "🐛 Enforcing bugfix pipeline for: $new_fr (sequential)"
            mkdir -p tmp
            LOG="tmp/bugfix-$(basename "$new_fr" .md).log"
            EXIT_CODE=0
            scripts/bugfix_worktree.sh "$new_fr" > "$LOG" 2>&1 || EXIT_CODE=$?
            echo "   Completed: exit $EXIT_CODE  Log: $LOG"
            if [[ $EXIT_CODE -ne 0 ]]; then
                echo "⚠️  Enforcement failed (exit $EXIT_CODE) for: $new_fr — see $LOG"
            fi
        else
            mkdir -p tmp
            LOG="tmp/enforce-$(basename "$new_fr" .md).log"
            echo "🚀 Enforcing: $new_fr (sequential, log: $LOG)"
            EXIT_CODE=0
            scripts/enforce_worktree.sh "$new_fr" > "$LOG" 2>&1 || EXIT_CODE=$?
            echo "   Completed: exit $EXIT_CODE  Log: $LOG"
            if [[ $EXIT_CODE -ne 0 ]]; then
                echo "⚠️  Enforcement failed (exit $EXIT_CODE) for: $new_fr — see $LOG"
            fi
        fi
    fi

    echo ""
done
