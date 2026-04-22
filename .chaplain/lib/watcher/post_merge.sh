#!/usr/bin/env bash
# post_merge.sh — Close originating GH issue after successful merge
#
# Expects: TOPIC_FILE set by orchestrator

post_merge() {
    local inbox_basename
    inbox_basename=$(basename "$TOPIC_FILE")

    # Close originating GitHub Issue if this came from one
    if [[ "$inbox_basename" == gh-*.md ]]; then
        local gh_num
        gh_num="${inbox_basename#gh-}"
        gh_num="${gh_num%.md}"
        gh issue close "$gh_num" \
            --comment "✅ Implemented via $(git log -1 --format='%h %s')" 2>/dev/null || log_warn "Failed to close issue #$gh_num"
        log_info "🔒 Closed GitHub Issue #$gh_num"
    fi
}
