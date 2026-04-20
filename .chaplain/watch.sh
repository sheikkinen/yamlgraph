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

# FR-256: Pipeline timing metrics
METRIC_DIR="tmp/pipeline-metrics"
mkdir -p "$METRIC_DIR"

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
    t_cycle_start=$(date +%s)
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

    # FR-256: Write cycle metrics JSON (best-effort, inline — not trap-based)
    t_cycle_end=$(date +%s)
    if [[ -n "$new_fr" ]]; then
        local_cycle_seconds=$((t_cycle_end - t_cycle_start))
        cycle_fr=$(basename "$new_fr" .md | grep -oE 'FR-[0-9]+' || echo "unknown")
        cycle_verdict="unknown"
        if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
            cycle_verdict="rejected"
        elif grep -q 'Status.*Approved' "$new_fr" 2>/dev/null; then
            cycle_verdict="approved"
        fi
        cycle_outcome="failure"
        if [[ $EXIT_CODE -eq 0 ]]; then cycle_outcome="success"; fi
        inbox_base=$(basename "$topic_file")
        cycle_gh_num=""
        if [[ "$inbox_base" == gh-*.md ]]; then
            cycle_gh_num="${inbox_base#gh-}"
            cycle_gh_num="${cycle_gh_num%.md}"
        fi
        ts_safe=$(date -u +%Y%m%dT%H%M%S)
        printf '{\n  "pipeline": "chaplain-cycle",\n  "inbox_item": "%s",\n  "fr_generated": "%s",\n  "verdict": "%s",\n  "enforce_outcome": "%s",\n  "total_seconds": %d\n}\n' \
            "$inbox_base" "$cycle_fr" "$cycle_verdict" "$cycle_outcome" \
            "$local_cycle_seconds" \
            > "$METRIC_DIR/chaplain-cycle-${ts_safe}.json" 2>/dev/null || true
    fi

    # ── FR-258: Post-merge finalization ──────────────────────────────────────
    if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
        git checkout main --quiet 2>/dev/null || true
        git pull --quiet 2>/dev/null || true

        STATE_DIR=".chaplain/state"
        mkdir -p "$STATE_DIR"
        LAST_CHECK_FILE="$STATE_DIR/last-finalized-at"
        if [[ -f "$LAST_CHECK_FILE" ]]; then
            SINCE=$(cat "$LAST_CHECK_FILE")
        else
            SINCE=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
                || date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
        fi

        source .chaplain/lib/finalize_lib.sh

        gh pr list --state merged --search "merged:>=$SINCE" \
            --json number,headRefName,mergedAt \
            --jq '.[].headRefName' 2>/dev/null \
        | while read -r branch; do
            fr_num=$(echo "$branch" | grep -oiE 'fr-[0-9]+' | head -1) || continue
            [[ -z "$fr_num" ]] && continue

            fr_file=$(find feature-requests/ -maxdepth 1 -iname "${fr_num}-*.md" \
                -type f 2>/dev/null | head -1)
            [[ -z "$fr_file" ]] && continue
            grep -q 'Status.*Implemented' "$fr_file" 2>/dev/null && continue

            fin_branch="chore/finalize-$(echo "$fr_num" | tr '[:upper:]' '[:lower:]')"
            if gh pr list --state open --head "$fin_branch" --json number \
                --jq 'length' 2>/dev/null | grep -q '[1-9]'; then
                continue
            fi

            echo "🔄 Creating finalization PR for: $fr_file"
            git checkout -b "$fin_branch" main --quiet 2>/dev/null || {
                echo "⚠️  Branch $fin_branch already exists, skipping"
                git checkout main --quiet 2>/dev/null || true
                continue
            }

            extract_fr_metadata "$fr_file"
            create_changelog_fragment "$FR_NUM" "$FR_TITLE" "$FR_SUMMARY" "$REQ_ID"
            update_fr_status "$fr_file"
            create_diary_stub "$FR_NUM" "$FR_TITLE"

            git add changelog/unreleased/ "$fr_file"
            mkdir -p ./tmp
            cat > ./tmp/msg.txt << CMSG
chore: ${FR_NUM} post-merge finalization

- Changelog fragment created in changelog/unreleased/
- FR status updated to Implemented
- Diary reflection stub created (untracked)
CMSG
            git commit -F ./tmp/msg.txt 2>/dev/null || {
                echo "⚠️  Nothing to commit for $fr_file"
                git checkout main --quiet 2>/dev/null || true
                git branch -D "$fin_branch" 2>/dev/null || true
                continue
            }

            git push origin "$fin_branch" --quiet 2>/dev/null && \
            gh pr create --base main --head "$fin_branch" \
                --title "chore: ${FR_NUM} post-merge finalization" \
                --body "Auto-generated by watch.sh (FR-258)." \
                2>/dev/null && \
            gh pr merge "$fin_branch" --auto --squash 2>/dev/null || {
                echo "⚠️  Finalization PR creation failed for $fr_file"
            }

            git checkout main --quiet 2>/dev/null || true
        done

        date -u +%Y-%m-%dT%H:%M:%SZ > "$LAST_CHECK_FILE" 2>/dev/null || true
    fi

    echo ""
done
