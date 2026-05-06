#!/usr/bin/env bash
# post_merge.sh — Post-merge cleanup for watcher2
#
# Called as terminal action (bash type, no capture_keys)
# Uses context vars: TOPIC_FILE, PR_NUMBER, PR_TITLE (if available)

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

resolve_post_merge_fr_token() {
    local fr_token_regex='FR-[0-9]+'
    local title_source=""
    local resolved_token=""

    if [[ -n "${PR_NUMBER:-}" ]] && command -v gh >/dev/null 2>&1; then
        title_source=$(gh pr view "$PR_NUMBER" --json title --jq '.title' 2>/dev/null || true)
    fi

    if [[ -z "$title_source" && -n "${PR_TITLE:-}" ]]; then
        title_source="$PR_TITLE"
    fi

    if [[ -n "$title_source" ]]; then
        resolved_token=$(printf '%s' "$title_source" | grep -oE "$fr_token_regex" | head -1 || true)
    fi

    if [[ -z "$resolved_token" && -n "${TOPIC_FILE:-}" && -f "$TOPIC_FILE" ]]; then
        resolved_token=$(grep -oE "$fr_token_regex" "$TOPIC_FILE" 2>/dev/null | head -1 || true)
    fi

    if [[ -z "$resolved_token" ]]; then
        log_info "No FR token resolved in post_merge context"
    else
        log_info "post_merge resolved FR token: $resolved_token"
    fi

    POST_MERGE_FR_TOKEN="$resolved_token"
    return 0
}

consume_matching_inbox_items() {
    local fr_token="$1"
    local inbox_dir=".chaplain/inbox"
    local done_dir=".chaplain/done"
    local consumed_count=0
    local inbox_file=""
    local grep_status=0

    if [[ ! -d "$inbox_dir" ]]; then
        log_info "post_merge consumed count: 0 (inbox missing) for $fr_token"
        return 0
    fi

    if ! mkdir -p "$done_dir"; then
        log_warn "Failed to create $done_dir — skipping post_merge inbox consumption"
        return 0
    fi

    for inbox_file in "$inbox_dir"/*.md; do
        [[ -e "$inbox_file" ]] || continue

        if grep -qE "$fr_token" "$inbox_file"; then
            local source_name
            local done_path
            source_name=$(basename "$inbox_file")
            done_path="$done_dir/$source_name"

            if [[ -e "$done_path" ]]; then
                local timestamp
                local stem
                timestamp=$(date +%Y%m%d%H%M%S)
                stem="${source_name%.md}"
                done_path="$done_dir/${stem}-${timestamp}.md"
            fi

            if mv "$inbox_file" "$done_path"; then
                consumed_count=$((consumed_count + 1))
                log_info "post_merge consumed inbox item: $source_name"
            else
                log_warn "Failed to move inbox file to done queue: $source_name"
            fi
            continue
        fi

        grep_status=$?
        if [[ "$grep_status" -ne 1 ]]; then
            log_warn "Failed to scan inbox file for $fr_token: $inbox_file"
        fi
        continue
    done

    log_info "post_merge consumed count: $consumed_count for $fr_token"
    return 0
}

resolve_post_merge_pr_state() {
    local resolved_state=""

    if [[ -z "${PR_NUMBER:-}" ]]; then
        log_info "post_merge skip processing topic cleanup: PR number unavailable; merged state unknown"
        POST_MERGE_PR_STATE=""
        return 0
    fi

    if ! command -v gh >/dev/null 2>&1; then
        log_warn "post_merge skip processing topic cleanup: gh unavailable for merged-state check"
        POST_MERGE_PR_STATE=""
        return 0
    fi

    resolved_state=$(gh pr view "$PR_NUMBER" --json state --jq '.state' 2>/dev/null || true)

    if [[ -z "$resolved_state" ]]; then
        log_warn "post_merge skip processing topic cleanup: unable to read PR #$PR_NUMBER state via gh pr view --json state --jq '.state'"
    else
        log_info "post_merge PR #$PR_NUMBER state: $resolved_state"
    fi

    POST_MERGE_PR_STATE="$resolved_state"
    return 0
}

cleanup_processing_topic() {
    local processing_topic="${TOPIC_FILE:-}"
    local done_dir=".chaplain/done"
    local source_name=""
    local done_path=""

    if [[ "${POST_MERGE_PR_STATE:-}" != "MERGED" ]]; then
        log_info "post_merge skip processing topic cleanup: PR state is not merged (${POST_MERGE_PR_STATE:-unknown})"
        return 0
    fi

    if [[ -z "$processing_topic" ]]; then
        log_info "post_merge processing topic missing from context; no-op cleanup"
        return 0
    fi

    if [[ "$processing_topic" != *"/.chaplain/processing/"* && "$processing_topic" != .chaplain/processing/* ]]; then
        log_warn "post_merge skip processing topic cleanup: TOPIC_FILE is not under .chaplain/processing/: $processing_topic"
        return 0
    fi

    if [[ ! -f "$processing_topic" ]]; then
        log_info "post_merge processing topic missing; idempotent no-op: $processing_topic"
        return 0
    fi

    if ! mkdir -p "$done_dir"; then
        log_warn "Failed to create $done_dir — skipping processing topic move"
        return 0
    fi

    source_name=$(basename "$processing_topic")
    done_path="$done_dir/$source_name"

    if [[ -e "$done_path" ]]; then
        local timestamp
        local stem
        timestamp=$(date +%Y%m%d%H%M%S)
        stem="${source_name%.md}"
        done_path="$done_dir/${stem}-${timestamp}.md"
    fi

    if mv "$processing_topic" "$done_path"; then
        log_info "post_merge moved processing topic to done: $source_name"
    else
        log_warn "Failed to move processing topic to done queue: $source_name"
    fi

    return 0
}

sync_main_after_merge() {
    local stash_created=0
    local stash_message=""
    local current_branch=""
    local pull_failed=0
    local git_status_output=""

    if ! git_status_output=$(git status --porcelain); then
        log_error "post_merge failed to read git status before main sync"
        return 1
    fi

    if [[ -n "$git_status_output" ]]; then
        stash_message="watcher2-post-merge-$(date +%Y%m%d%H%M%S)"
        if git stash push --include-untracked -m "$stash_message" >/dev/null; then
            stash_created=1
            log_info "post_merge stashed local changes before main sync: $stash_message"
        else
            log_error "post_merge failed to stash local changes before main sync"
            return 1
        fi
    else
        log_info "post_merge working tree clean; no stash needed before main sync"
    fi

    current_branch=$(git branch --show-current 2>/dev/null || true)
    if [[ "$current_branch" != "main" ]]; then
        if git checkout main --quiet; then
            log_info "post_merge switched to main for reconciliation"
        else
            log_error "post_merge failed to switch to main for reconciliation"
            return 1
        fi
    fi

    if ! git pull --rebase --quiet origin main; then
        log_error "post_merge failed to pull --rebase from origin main"
        pull_failed=1
    fi

    if [[ "$stash_created" -eq 1 ]]; then
        if git stash pop >/dev/null; then
            log_info "post_merge restored stashed local changes after main sync"
        else
            log_error "post_merge failed to restore stashed local changes (git stash pop)"
            return 1
        fi
    fi

    if [[ "$pull_failed" -ne 0 ]]; then
        return 1
    fi

    log_info "post_merge main sync complete"
    return 0
}

post_merge() {
    local inbox_basename
    local merged_fr_token

    inbox_basename=$(basename "$TOPIC_FILE")

    # Close originating GitHub Issue if this came from one.
    if [[ "$inbox_basename" == gh-*.md ]]; then
        local gh_num
        gh_num="${inbox_basename#gh-}"
        gh_num="${gh_num%.md}"
        gh issue close "$gh_num" \
            --comment "✅ Implemented via $(git log -1 --format='%h %s')" 2>/dev/null || log_warn "Failed to close issue #$gh_num"
        log_info "🔒 Closed GitHub Issue #$gh_num"
    fi

    resolve_post_merge_fr_token
    merged_fr_token="${POST_MERGE_FR_TOKEN:-}"
    if [[ -z "$merged_fr_token" ]]; then
        log_info "No FR token available for post_merge inbox cleanup; continuing to main sync"
    else
        consume_matching_inbox_items "$merged_fr_token"
    fi

    resolve_post_merge_pr_state
    cleanup_processing_topic

    if ! sync_main_after_merge; then
        return 1
    fi

    return 0
}

post_merge
