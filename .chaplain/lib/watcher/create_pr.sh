#!/usr/bin/env bash
# create_pr.sh — Create a pull request via gh CLI
#
# Expects: WT_BRANCH, PR_TITLE set by orchestrator
# Sets: PR_NUMBER, PR_URL

create_pr() {
    log_info "Creating PR: $PR_TITLE"

    local pr_output
    pr_output=$(gh pr create \
        --title "$PR_TITLE" \
        --body "Automated by watcher2 pipeline (FR-273)." \
        --base main \
        --head "$WT_BRANCH" 2>&1) || {
        log_error "Failed to create PR: $pr_output"
        return 1
    }

    PR_URL="$pr_output"
    PR_NUMBER=$(echo "$PR_URL" | grep -oE '[0-9]+$')
    log_info "PR created: $PR_URL (#$PR_NUMBER)"
}
