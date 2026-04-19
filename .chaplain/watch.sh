#!/usr/bin/env bash
# .chaplain/watch.sh — Thin polling wrapper for Plan → Judge workflow
# FR-084: Delegates to yamlgraph graph run (copilot nodes via FR-081)
# FR-093: Added date and diary_prefix vars for diary append
# FR-098/FR-196: Consolidated to .chaplain/graphs/copilot/graph.yaml
set -euo pipefail
cd "$(dirname "$0")/.."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INBOX=".chaplain/inbox"
DRAFTS=".chaplain/drafts"
POLL=5

# FR-251: Author allowlist and body size cap
ALLOWED_AUTHORS="$SCRIPT_DIR/allowed-authors.txt"
BODY_SIZE_CAP=10000

echo "👀 Watching $INBOX/"

while true; do
    # FR-243: Sync GitHub Issues labeled 'chaplain' into local inbox
    # FR-251: Author allowlist, body size cap, audit header
    if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
        gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \
        | while read -r num; do
            [[ -f "$INBOX/gh-$num.md" ]] && continue

            # FR-251: Author allowlist check
            author=$(gh issue view "$num" --json author --jq '.author.login' 2>/dev/null) || continue
            if [[ -f "$ALLOWED_AUTHORS" ]] && ! grep -qxF "$author" "$ALLOWED_AUTHORS"; then
                echo "⚠️ Skipped issue #$num from untrusted author @$author"
                continue
            fi

            title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
            body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue

            # FR-251: Body size cap — truncate oversized bodies
            if [[ ${#body} -gt $BODY_SIZE_CAP ]]; then
                echo "⚠️ Issue #$num body truncated from ${#body} to $BODY_SIZE_CAP chars"
                body="${body:0:$BODY_SIZE_CAP}"
            fi

            # FR-251: Author audit header
            printf "<!-- author: @%s -->\n# %s\n\n%s\n" "$author" "$title" "$body" > "$INBOX/gh-$num.md"
            gh issue edit "$num" --remove-label chaplain 2>/dev/null || true
            echo "📥 Imported GitHub Issue #$num: $title"
        done
    fi

    topic_file=$(find "$INBOX" -name "*.md" -type f 2>/dev/null | head -1)
    [[ -z "$topic_file" ]] && { sleep "$POLL"; continue; }

    echo "📋 Processing: $topic_file"

    # FR-116: Snapshot feature-requests/ before graph execution
    before=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)

    yamlgraph graph run .chaplain/graphs/copilot/graph.yaml \
        --var topic_file="$topic_file" \
        --var drafts_dir="$DRAFTS" \
        --var date="$(date +%Y-%m-%d)" \
        --var diary_prefix="Chaplain" \
        --full

    # FR-116: Detect new FR and spawn enforce pipeline
    after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
    new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)

    # FR-175: Sequential enforcement — wait for each pipeline before next
    # FR-243: Initialize EXIT_CODE as failure sentinel (rejected FRs never override)
    EXIT_CODE=1
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

        # FR-243: Close originating GitHub Issue on successful enforcement
        if [[ $EXIT_CODE -eq 0 ]]; then
            inbox_basename=$(basename "$topic_file")
            if [[ "$inbox_basename" == gh-*.md ]]; then
                gh_num="${inbox_basename#gh-}"
                gh_num="${gh_num%.md}"
                gh issue close "$gh_num" \
                    --comment "✅ Implemented via $(git log -1 --format='%h %s')" 2>/dev/null || true
                echo "🔒 Closed GitHub Issue #$gh_num"
            fi
        fi
    fi

    echo ""
done
