# Feature Request: Watcher2 should reuse existing PRs

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-04-23

## Summary

Currently, watcher2 fails when a PR already exists for the worktree branch. It should check for an existing PR and reuse/update it instead of blindly calling `gh pr create`.

## Value Statement

Pipeline operators get robust automation that handles existing PRs gracefully, eliminating manual intervention and workflow failures.

## Problem

Watcher2's `create_pr.sh` function calls `gh pr create` without checking if a PR already exists for the current branch. This causes failures in the automated pipeline when:

1. A previous cycle created a PR but failed later (CI timeout, merge conflicts, etc.)
2. Manual intervention created a PR for the branch
3. Network glitches caused partial failures leaving orphaned PRs

The current implementation in `.chaplain/lib/watcher/create_pr.sh` blindly executes:

```bash
pr_output=$(gh pr create \
    --title "$PR_TITLE" \
    --body "Automated by watcher2 pipeline (FR-273)." \
    --base main \
    --head "$WT_BRANCH" 2>&1) || {
    log_error "Failed to create PR: $pr_output"
    return 1
}
```

This pattern was identified as problematic in issue #180 where redundant PR creation attempts caused automated workflow failures.

## Proposed Solution

Update `create_pr.sh` to follow the same pattern already established in `watch.sh` (lines 183-186):

1. **Check for existing PR first**: Use `gh pr list --state open --head "$WT_BRANCH"` to check if a PR already exists
2. **Reuse existing PR if found**: Extract PR number and URL from existing PR
3. **Create new PR only if none exists**: Fall back to current `gh pr create` logic
4. **Update PR if needed**: Optionally update title/body if they differ (nice-to-have)

```bash
create_pr() {
    log_info "Checking for existing PR on branch: $WT_BRANCH"
    
    # Check if PR already exists for this branch
    local existing_pr
    existing_pr=$(gh pr list --state open --head "$WT_BRANCH" --json number,url,title \
        --jq '.[0] | select(.number != null)' 2>/dev/null)
    
    if [[ -n "$existing_pr" ]]; then
        PR_NUMBER=$(echo "$existing_pr" | jq -r '.number')
        PR_URL=$(echo "$existing_pr" | jq -r '.url')
        local existing_title=$(echo "$existing_pr" | jq -r '.title')
        
        log_info "Reusing existing PR: $PR_URL (#$PR_NUMBER)"
        
        # Optional: Update title if different
        if [[ "$existing_title" != "$PR_TITLE" ]]; then
            log_info "Updating PR title from '$existing_title' to '$PR_TITLE'"
            gh pr edit "$PR_NUMBER" --title "$PR_TITLE" 2>/dev/null || true
        fi
        
        return 0
    fi
    
    # No existing PR found — create new one (existing logic)
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
}
```

## Acceptance Criteria

- [ ] `create_pr.sh` checks if a PR exists for `$WT_BRANCH` before attempting to create one
- [ ] If an existing open PR is found, it reuses the PR number and URL instead of creating a new one
- [ ] If no existing PR is found, it creates a new PR as before
- [ ] The function sets `PR_NUMBER` and `PR_URL` variables correctly in both cases
- [ ] Existing PR detection uses `gh pr list --state open --head "$WT_BRANCH"` pattern (consistent with `watch.sh`)
- [ ] Function logs clearly whether it's reusing an existing PR or creating a new one
- [ ] Error handling remains robust — network failures don't crash the pipeline
- [ ] Tests added to verify both existing-PR and new-PR code paths
- [ ] Manual testing confirms watcher2 handles pre-existing PRs gracefully

## Alternatives Considered

**Close and recreate PR**: Delete existing PR and create fresh one. **Rejected** because it loses PR discussion history, review comments, and CI status.

**Fail fast with clear error**: Detect existing PR and fail with instructive message. **Rejected** because it requires manual intervention, defeating the purpose of automation.

**Branch name disambiguation**: Generate unique branch names to avoid conflicts. **Rejected** because it doesn't solve the core issue and complicates worktree management.

## Related

- Issue #180: Redundant PR creation attempts causing workflow failures
- `.chaplain/watch.sh` lines 183-186: Existing pattern for PR existence checking
- FR-273: Watcher2 pipeline architecture
- FR-258: Automated post-merge finalization (similar PR management patterns)
- `.chaplain/lib/watcher/create_pr.sh`: Current implementation to be updated