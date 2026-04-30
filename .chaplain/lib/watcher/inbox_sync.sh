#!/usr/bin/env bash
# inbox_sync.sh — Import GitHub Issues labeled 'chaplain' into local inbox
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

    gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \
    | while read -r num; do
        # Skip if already in any pipeline stage (inbox, processing, or failed)
        [[ -f "$INBOX/gh-$num.md" ]] && continue
        [[ -f "$PROCESSING/gh-$num.md" ]] && continue
        [[ -f ".chaplain/failed/gh-$num.md" ]] && continue

        # FR-251: Author allowlist check
        author=$(gh issue view "$num" --json author --jq '.author.login' 2>/dev/null) || continue
        if [[ -f "$ALLOWED_AUTHORS" ]] && ! grep -qxF "$author" "$ALLOWED_AUTHORS"; then
            log_warn "Skipped issue #$num from untrusted author @$author"
            continue
        fi

        title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
        body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue

        # FR-251: Body size cap
        if [[ ${#body} -gt $BODY_SIZE_CAP ]]; then
            log_warn "Issue #$num body truncated from ${#body} to $BODY_SIZE_CAP chars"
            body="${body:0:$BODY_SIZE_CAP}"
        fi

        # FR-251: Author audit header
        printf "<!-- author: @%s -->\n# %s\n\n%s\n" "$author" "$title" "$body" > "$INBOX/gh-$num.md"
        gh issue edit "$num" --remove-label chaplain 2>/dev/null || log_warn "Failed to remove label from issue #$num"
        log_info "📥 Imported GitHub Issue #$num: $title"
    done
}

inbox_sync
