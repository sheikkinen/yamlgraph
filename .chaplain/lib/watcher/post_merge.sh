#!/usr/bin/env bash
# post_merge.sh — Post-merge cleanup for watcher2
#
# Expects: TOPIC_FILE set by orchestrator
# Uses: PR_NUMBER / PR_TITLE when available

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
        log_info "No FR token available for post_merge inbox cleanup; returning success"
        return 0
    fi

    consume_matching_inbox_items "$merged_fr_token"
    return 0
}
