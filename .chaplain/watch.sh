#!/usr/bin/env bash
# .chaplain/watch.sh — Thin polling wrapper for Plan → Judge → Enforce workflow
# FR-084: Delegates to yamlgraph graph run (copilot nodes via FR-081)
# FR-093: Added date and diary_prefix vars for diary append
# FR-098: Consolidated to examples/copilot/graph.yaml
# FR-114: Added enforce detection loop for approved FRs
set -euo pipefail
cd "$(dirname "$0")/.."

INBOX=".chaplain/inbox"
DRAFTS=".chaplain/drafts"
POLL=5
LAST_SHA_FILE=".chaplain/.last-enforce-sha"

echo "👀 Watching $INBOX/"

while true; do
    # --- Phase 1: Inbox processing (Plan → Judge) ---
    topic_file=$(find "$INBOX" -name "*.md" -type f 2>/dev/null | head -1)
    if [[ -n "$topic_file" ]]; then
        echo "📋 Processing: $topic_file"
        yamlgraph graph run examples/copilot/graph.yaml \
            --var topic_file="$topic_file" \
            --var drafts_dir="$DRAFTS" \
            --var date="$(date +%Y-%m-%d)" \
            --var diary_prefix="Chaplain" \
            --full
        echo ""
    fi

    # --- Phase 2: Enforce detection (FR-114) ---
    # Detect FRs committed since last check and trigger enforce_worktree.sh
    last_sha=$(python3 -c "from yamlgraph.utils.worktree_helpers import read_enforce_sha; s = read_enforce_sha('$LAST_SHA_FILE'); print(s if s else '')")
    current_sha=$(git rev-parse HEAD)

    if [[ -z "$last_sha" ]]; then
        last_sha="$current_sha"
    fi

    if [[ "$last_sha" != "$current_sha" ]]; then
        new_frs=$(python3 -c "
from yamlgraph.utils.worktree_helpers import detect_new_feature_requests
frs = detect_new_feature_requests('$last_sha', '$current_sha')
print('\n'.join(frs))
")
        for fr in $new_frs; do
            if [[ -f "$fr" ]]; then
                echo "🚀 Enforcing: $fr"
                scripts/enforce_worktree.sh "$fr" &
            fi
        done
        python3 -c "from yamlgraph.utils.worktree_helpers import write_enforce_sha; write_enforce_sha('$LAST_SHA_FILE', '$current_sha')"
    fi

    sleep "$POLL"
done
