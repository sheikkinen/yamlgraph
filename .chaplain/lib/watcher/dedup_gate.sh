#!/usr/bin/env bash
# dedup_gate.sh — Skip watcher cycles for already-completed FR topics
#
# Expects: TOPIC_FILE set by orchestrator (or passed as first argument)
# Sets: DEDUP_FR_TOKEN, DEDUP_MERGED_PR_REF

dedup_gate() {
    local topic_file="${1:-$TOPIC_FILE}"
    local fr_token_regex='FR-[0-9]+'
    local fr_token
    local existing_merged_pr
    local gh_pr_list_exit=0

    fr_token=$(grep -oE "$fr_token_regex" "$topic_file" 2>/dev/null | head -1 || true)

    if [[ -z "$fr_token" ]]; then
        log_info "No FR token found in topic — continuing without dedup skip"
        return 0
    fi

    DEDUP_FR_TOKEN="$fr_token"

    if command -v gh >/dev/null 2>&1; then
        existing_merged_pr=$(gh pr list \
            --state merged \
            --search "$fr_token" \
            --json number,url,mergedAt,title \
            --jq '.[0] | select(.number != null)' 2>/dev/null) || gh_pr_list_exit=$? || true
        if [[ "$gh_pr_list_exit" -ne 0 ]]; then
            log_warn "Merged PR dedup query failed for $fr_token — continuing without dedup skip"
            return 0
        fi
        if [[ -n "$existing_merged_pr" ]]; then
            DEDUP_MERGED_PR_REF="$existing_merged_pr"
            return 2
        fi
    else
        log_warn "gh CLI unavailable — skipping merged PR dedup gate for $fr_token"
    fi

    return 0
}
