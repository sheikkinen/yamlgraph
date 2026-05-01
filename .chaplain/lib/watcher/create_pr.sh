#!/usr/bin/env bash
# create_pr.sh — Create a pull request via gh CLI, or reuse existing one
#
# Usage: bash create_pr.sh --branch <branch> --dir <wt_dir> [--title <title>]
# Sets: PR_NUMBER, PR_URL

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Parse args
TITLE_OVERRIDE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch) WT_BRANCH="$2"; shift 2 ;;
        --dir)    WT_DIR="$2"; shift 2 ;;
        --title)  TITLE_OVERRIDE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$WT_BRANCH" ]]; then
    log_error "Usage: create_pr.sh --branch <branch> --dir <wt_dir> [--title <title>]"
    exit 1
fi

# Derive PR title from branch name, or use override
PR_TITLE="${TITLE_OVERRIDE:-feat(chaplain): ${WT_BRANCH#chaplain/}}"

create_pr() {
    log_info "Checking for existing PR on branch: $WT_BRANCH"

    # Check for existing open PR on this branch
    local existing_pr_json
    existing_pr_json=$(gh pr list \
        --state open \
        --head "$WT_BRANCH" \
        --json number,url,title \
        --jq ".[0] | select(.number != null)" 2>/dev/null) || {
        # If gh pr list fails (network error, etc), fall back to creating new PR
        log_info "Failed to check for existing PRs, proceeding to create new PR"
        existing_pr_json=""
    }

    if [[ -n "$existing_pr_json" && "$existing_pr_json" != "null" ]]; then
        # Reuse existing PR
        PR_NUMBER=$(echo "$existing_pr_json" | jq -r ".number")
        PR_URL=$(echo "$existing_pr_json" | jq -r ".url")
        local existing_title
        existing_title=$(echo "$existing_pr_json" | jq -r ".title")

        log_info "Reusing existing PR: $PR_URL (#$PR_NUMBER)"

        # Update title if different
        if [[ "$existing_title" != "$PR_TITLE" ]]; then
            log_info "Updating PR title from '$existing_title' to '$PR_TITLE'"
            if ! gh pr edit "$PR_NUMBER" --title "$PR_TITLE" 2>/dev/null; then
                log_info "Failed to update PR title, continuing with existing title"
            fi
        fi
    else
        # Create new PR
        log_info "Creating new PR: $PR_TITLE"

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

    # JSON stdout for bash_context_action
    echo "{\"pr_number\": \"$PR_NUMBER\", \"pr_url\": \"$PR_URL\"}"
}

create_pr
