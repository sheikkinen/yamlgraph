# Feature Request: watcher2 should reuse existing PRs

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-04-23

## Summary

Update watcher2 to check for existing PRs before attempting to create new ones, and reuse/update existing PRs instead of failing with a `gh pr create` error.

## Value Statement

<!-- One sentence: Who benefits and how. -->
Automated pipeline operators avoid manual intervention when PRs already exist, reducing workflow disruption from recovery scenarios and re-runs.

## Problem

Currently, watcher2 fails if a PR already exists for the worktree branch during the create PR step (line 328 in `.chaplain/watcher2.sh`). This happens when:

1. A previous watcher2 cycle created a PR but failed at a later stage (CI wait, merge)
2. A manual recovery attempt creates a PR before re-running watcher2
3. Branch protection failures cause cycles to restart without cleaning up the existing PR

The failure occurs in `.chaplain/lib/watcher/create_pr.sh` which blindly calls `gh pr create` without checking for existing PRs, causing the entire cycle to abort.

## Proposed Solution

Enhance `create_pr()` function in `.chaplain/lib/watcher/create_pr.sh` to:

1. Check if a PR already exists for the current branch
2. If found, update the existing PR (title, body) if needed
3. Set `PR_NUMBER` and `PR_URL` variables from the existing PR
4. Only call `gh pr create` if no existing PR is found

```bash
# Example implementation pattern (based on .chaplain/watch.sh:183-186)
create_pr() {
    log_info "Checking for existing PR on branch: $WT_BRANCH"
    
    # Check if PR already exists for this branch
    if gh pr list --state open --head "$WT_BRANCH" --json number,url \
        --jq 'length' 2>/dev/null | grep -q '[1-9]'; then
        
        # PR exists - get details and reuse
        pr_data=$(gh pr list --state open --head "$WT_BRANCH" --json number,url --jq '.[0]')
        PR_NUMBER=$(echo "$pr_data" | jq -r '.number')
        PR_URL=$(echo "$pr_data" | jq -r '.url')
        log_info "Reusing existing PR: $PR_URL (#$PR_NUMBER)"
        
        # Optionally update PR if title/body differ
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
```

## Acceptance Criteria

- [ ] `create_pr()` function checks if a PR exists for the current branch before creating
- [ ] If existing PR found, function reuses it and sets `PR_NUMBER`, `PR_URL` variables correctly
- [ ] If no existing PR found, function creates new PR as before
- [ ] Function does not exit with error when PR already exists
- [ ] Existing PR title/body are optionally updated to match current `PR_TITLE`
- [ ] Tests added to verify PR reuse behavior
- [ ] watcher2 pipeline continues normally after reusing existing PR

## Alternatives Considered

1. **Always delete and recreate PRs**: More disruptive to reviewers, loses PR history and comments
2. **Skip PR creation entirely if exists**: Doesn't update title/body which may have changed
3. **Force push to branch and keep existing PR**: Current approach, but needs the existence check

## Related

- Issue #180: Original context where redundant PR creation attempts caused failures
- FR-273: watcher2 pipeline implementation 
- `.chaplain/watch.sh:183-186`: Existing pattern for checking open PRs by branch
- FR-258: Post-merge finalization which uses similar PR existence checking