#!/usr/bin/env bash
# create_pr.sh — Create a pull request via gh CLI
#
# Expects: WT_BRANCH, PR_TITLE set by orchestrator
# Sets: PR_NUMBER, PR_URL

create_pr() {
    log_info "Checking for existing PR on branch: $WT_BRANCH"
    
    # Check if PR already exists for this branch
    local pr_list_output
    pr_list_output=$(gh pr list --state open --head "$WT_BRANCH" --json number,url 2>/dev/null) || {
        log_error "Failed to check for existing PRs"
        return 1
    }
    
    local pr_count
    pr_count=$(echo "$pr_list_output" | jq 'length' 2>/dev/null) || {
        log_error "Failed to parse PR list JSON"
        return 1
    }
    
    if [ "$pr_count" -gt 0 ]; then
        # PR exists - get details and reuse
        local pr_data
        pr_data=$(echo "$pr_list_output" | jq -r '.[0]' 2>/dev/null) || {
            log_error "Failed to parse PR data"
            return 1
        }
        
        PR_NUMBER=$(echo "$pr_data" | jq -r '.number')
        PR_URL=$(echo "$pr_data" | jq -r '.url')
        log_info "Reusing existing PR: $PR_URL (#$PR_NUMBER)"
        
        # Update PR title and body to match current values
        gh pr edit "$PR_NUMBER" --title "$PR_TITLE" \
            --body "Automated by watcher2 pipeline (FR-273)." 2>/dev/null || true
    else
        # No existing PR - create new one
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
    fi
}
