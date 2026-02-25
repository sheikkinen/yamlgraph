#!/usr/bin/env bash
# .chaplain/watch.sh — Thin polling wrapper for Plan → Judge workflow
# FR-084: Delegates to yamlgraph graph run (copilot nodes via FR-081)
# FR-093: Added date and diary_prefix vars for diary append
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
    yamlgraph graph run .chaplain/graph.yaml \
        --var topic_file="$topic_file" \
        --var drafts_dir="$DRAFTS" \
        --var date="$(date +%Y-%m-%d)" \
        --var diary_prefix="Chaplain" \
        --full

    echo ""
done
