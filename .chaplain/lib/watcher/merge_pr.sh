#!/usr/bin/env bash
# merge_pr.sh — Squash merge a PR via gh CLI
#
# Expects: PR_NUMBER set by orchestrator

merge_pr() {
    log_info "Merging PR #$PR_NUMBER (squash)..."

    gh pr merge "$PR_NUMBER" --squash --delete-branch 2>&1 || {
        log_error "Failed to merge PR #$PR_NUMBER"
        return 1
    }

    log_info "PR #$PR_NUMBER merged"
}
