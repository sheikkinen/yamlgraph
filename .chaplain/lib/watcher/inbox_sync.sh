#!/usr/bin/env bash
# inbox_sync.sh — Import GitHub Issues labeled 'chaplain' and 'chaplain-check' into local inbox
# Extracted from watch.sh (FR-243, FR-251)
#
# Uses env vars: INBOX, PROCESSING, ALLOWED_AUTHORS, BODY_SIZE_CAP
# Defaults provided for standalone execution.
# Side effects: writes $INBOX/gh-<num>.md files, removes label from issues

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

INBOX="${INBOX:-.chaplain/inbox}"
PROCESSING="${PROCESSING:-.chaplain/processing}"
ALLOWED_AUTHORS="${ALLOWED_AUTHORS:-.chaplain/config/allowed-authors.txt}"
BODY_SIZE_CAP="${BODY_SIZE_CAP:-10000}"

inbox_sync() {
    if ! command -v gh &>/dev/null || ! gh auth status &>/dev/null 2>&1; then
        log_warn "gh CLI not available or not authenticated — skipping inbox sync"
        return 0
    fi

    import_issue() {
        local num="$1"
        local mode="$2"
        local issue_label="$3"

        # Skip if already in any pipeline stage (inbox, processing, or failed)
        [[ -f "$INBOX/gh-$num.md" ]] && return 0
        [[ -f "$PROCESSING/gh-$num.md" ]] && return 0
        [[ -f ".chaplain/failed/gh-$num.md" ]] && return 0

        # FR-251: Author allowlist check
        author=$(gh issue view "$num" --json author --jq '.author.login' 2>/dev/null) || return 0
        if [[ -f "$ALLOWED_AUTHORS" ]] && ! grep -qxF "$author" "$ALLOWED_AUTHORS"; then
            log_warn "Skipped issue #$num from untrusted author @$author"
            return 0
        fi

        title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || return 0
        body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || return 0

        # FR-251: Body size cap
        if [[ ${#body} -gt $BODY_SIZE_CAP ]]; then
            log_warn "Issue #$num body truncated from ${#body} to $BODY_SIZE_CAP chars"
            body="${body:0:$BODY_SIZE_CAP}"
        fi

        # FR-251: Author audit header
        # FR-317: mode marker for health-check topics.
        if [[ "$mode" == "health-check" ]]; then
            printf "<!-- author: @%s -->\n<!-- mode: health-check -->\n# %s\n\n%s\n" "$author" "$title" "$body" > "$INBOX/gh-$num.md"
        else
            printf "<!-- author: @%s -->\n# %s\n\n%s\n" "$author" "$title" "$body" > "$INBOX/gh-$num.md"
        fi
        if [[ "$issue_label" == "chaplain" ]]; then
            gh issue edit "$num" --remove-label chaplain 2>/dev/null || log_warn "Failed to remove label 'chaplain' from issue #$num"
        else
            gh issue edit "$num" --remove-label "$issue_label" 2>/dev/null || log_warn "Failed to remove label '$issue_label' from issue #$num"
        fi
        log_info "📥 Imported GitHub Issue #$num: $title"
    }

    gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \
    | while read -r num; do
        # author is fetched before title/body inside import_issue (REQ-YG-256)
        import_issue "$num" "" "chaplain"
    done

    gh issue list --state open --label chaplain-check --json number --jq '.[].number' 2>/dev/null \
    | while read -r num; do
        import_issue "$num" "health-check" "chaplain-check"
    done
}

inbox_sync
