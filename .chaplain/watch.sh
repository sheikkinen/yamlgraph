#!/usr/bin/env bash
# .chaplain/watch.sh — File watcher for Plan → Judge → Amend loop
# FR-068: Processes topic files dropped in .chaplain/inbox/
#
# Usage: .chaplain/watch.sh [--dry-run]
set -euo pipefail
cd "$(dirname "$0")/.."

# --- Config ---
INBOX_DIR=".chaplain/inbox"
DRAFTS_DIR=".chaplain/drafts"
FR_DIR="feature-requests"
MAX_AMEND_CYCLES=3
POLL_INTERVAL=5
DRY_RUN=false

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --poll) POLL_INTERVAL="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# --- Helpers ---
next_fr_number() {
    local max=0
    for f in "$FR_DIR"/*.md; do
        [[ -f "$f" ]] || continue
        local num
        num=$(basename "$f" | grep -oE '^[0-9]+' | head -1)
        [[ -n "$num" ]] && (( 10#$num > max )) && max=$((10#$num))
    done
    echo $((max + 1))
}

slugify() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//' | cut -c1-40
}

run_copilot() {
    local prompt="$1"
    if $DRY_RUN; then
        echo "[DRY-RUN] copilot prompt: ${prompt:0:80}..."
        return 0
    fi
    # Using GitHub Copilot CLI - adjust command if using different tool
    copilot -p "$prompt"
}

process_topic() {
    local topic_file="$1"
    local topic
    topic=$(cat "$topic_file")
    local slug
    slug=$(slugify "$(basename "$topic_file" .md)")
    local fr_num
    fr_num=$(next_fr_number)
    local draft_file="$DRAFTS_DIR/${fr_num}-${slug}.md"

    echo "📋 Processing: $topic"
    echo "   Draft: $draft_file"

    # Pre-create draft file with template (so Copilot only needs edit permission)
    cat > "$draft_file" << EOF
# Feature Request: FR-${fr_num} ${topic}

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Draft
**Effort:** TBD
**Requested:** $(date +%Y-%m-%d)

## Summary

${topic}

## Problem

[To be filled by Copilot]

## Proposed Solution

[To be filled by Copilot]

## Acceptance Criteria

- [ ] [To be filled by Copilot]

## Alternatives Considered

[To be filled by Copilot]

## Related

[To be filled by Copilot]
EOF

    # Plan phase
    echo "📝 Plan..."
    run_copilot "Edit the draft FR in $draft_file. Fill in all [To be filled by Copilot] sections following the patterns in feature-requests/TEMPLATE.md. Research the topic: $topic"

    # Judge loop (max 3 cycles)
    local cycles=0
    while (( cycles < MAX_AMEND_CYCLES )); do
        ((cycles++))
        echo "⚖️  Judge (cycle $cycles/$MAX_AMEND_CYCLES)..."

        local verdict
        verdict=$(run_copilot "Judge the FR in $draft_file. Updated the file itself with required amendments. Reply with exactly one word: APPROVE if ready, AMEND if needs work, REJECT if unfeasible.")

        if [[ "$verdict" == *APPROVE* ]]; then
            echo "✓ Approved!"
            local final_file="$FR_DIR/$(basename "$draft_file")"
            mv "$draft_file" "$final_file"
            rm "$topic_file"
            echo "   → Moved to $final_file"
            return 0
        elif [[ "$verdict" == *REJECT* ]]; then
            echo "✗ Rejected"
            mv "$draft_file" "${draft_file%.md}.rejected.md"
            rm "$topic_file"
            return 1
        else
            echo "📝 Amending..."
            run_copilot "Amend the FR in $draft_file based on the judgment feedback. Improve clarity, add missing sections, fix issues."
        fi
    done

    echo "⚠️  Max amend cycles reached - leaving in drafts"
    rm "$topic_file"
    return 1
}

# --- Main loop ---
echo "🔍 Chaplain Watch started"
echo "   Inbox: $INBOX_DIR"
echo "   Drafts: $DRAFTS_DIR"
echo "   Poll interval: ${POLL_INTERVAL}s"
$DRY_RUN && echo "   Mode: DRY-RUN"
echo ""

while true; do
    # Find oldest .md file in inbox (excluding .gitkeep)
    topic_file=$(find "$INBOX_DIR" -name "*.md" -type f 2>/dev/null | head -1)

    if [[ -z "$topic_file" ]]; then
        sleep "$POLL_INTERVAL"
        continue
    fi

    if ! process_topic "$topic_file"; then
        echo "⚠️  Topic processing failed, continuing..."
    fi

    echo ""
done
