#!/usr/bin/env bash
# .chaplain/watch.sh — Simplified Plan → Judge loop
# FR-068: Only watches and calls copilot (no file ops in shell)
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

    # Plan
    echo "📝 Plan..."
    copilot --allow-all-paths -p "**Plan.** Read $topic_file. Write the feature request in $DRAFTS/. Define objectives, constraints, acceptance criteria, and implementation approach. The feature request is the plan. Follow feature-requests/TEMPLATE.md. Delete $topic_file when complete."

    # Judge
    echo "⚖️  Judge..."
    copilot --allow-all-paths -p "**Judge.** Examine the FR in $DRAFTS/. Critically examine the feature request; resolve contradictions; eliminate ambiguity; refine constraints and acceptance criteria until the path is explicit and minimal. If clear, minimal, and internally consistent: freeze scope, grant authority, move to feature-requests/. If not: write issues into the file and move back to $INBOX/."

    echo ""
done
