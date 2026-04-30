#!/usr/bin/env bash
# merge_pr.sh — Squash merge a PR via gh CLI
#
# Usage: bash merge_pr.sh --pr <pr_number>
#
# Note: --delete-branch is intentionally omitted because gh tries to
# switch to the default branch after deleting, which fails when 'main'
# is already checked out in the main worktree. Branch cleanup is handled
# by worktree_teardown instead.

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr) PR_NUMBER="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$PR_NUMBER" ]]; then
    log_error "Usage: merge_pr.sh --pr <pr_number>"
    exit 1
fi

merge_pr() {
    log_info "Merging PR #$PR_NUMBER (squash)..."

    gh pr merge "$PR_NUMBER" --squash 2>&1 || {
        # gh pr merge can fail even after a successful merge (e.g. branch
        # switch error). Verify actual merge state before returning failure.
        local pr_state
        pr_state=$(gh pr view "$PR_NUMBER" --json state --jq '.state' 2>/dev/null)
        if [[ "$pr_state" == "MERGED" ]]; then
            log_warn "gh pr merge exited non-zero but PR is MERGED — continuing"
        else
            log_error "Failed to merge PR #$PR_NUMBER (state: ${pr_state:-unknown})"
            return 1
        fi
    }

    log_info "PR #$PR_NUMBER merged"
}

merge_pr
