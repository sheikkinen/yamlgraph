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

## Research Brief

### Competitive Landscape

- **GitHub Actions + peter-evans/create-pull-request**: Popular action (marketplace leader) automatically checks for existing PRs on the same branch and updates them instead of creating duplicates. Uses GitHub REST API `/repos/{owner}/{repo}/pulls` with head branch filtering.
- **GitHub CLI (`gh pr create`)**: Standard tool fails with error when PR already exists for branch. Documentation shows no built-in reuse/update functionality - users must manually implement existence checks.
- **GitHub REST API**: Provides `/repos/{owner}/{repo}/pulls?head={branch}` endpoint for checking existing PRs by branch, which is the foundation pattern most tools use.
- **github-script action**: Advanced users write custom JavaScript to query PR API and implement conditional create-or-update logic, essentially reinventing what this FR proposes.

Most CI/CD automation tools solve this by pre-checking before creation rather than handling the error after failure. The pattern of `gh pr list --head {branch}` followed by conditional creation is standard practice.

### Existing Abstractions

- **`.chaplain/watch.sh:183-186`**: Already implements the exact PR existence check pattern using `gh pr list --state open --head "$fin_branch" --json number --jq 'length'` for post-merge finalization PRs
- **`.chaplain/lib/watcher/create_pr.sh`**: Current target file that needs enhancement (24 lines, simple create-only logic)
- **Nine watcher library scripts** in `.chaplain/lib/watcher/`: Modular PR lifecycle management (create, wait, merge, teardown) already established
- **FR-258 post-merge finalization**: Uses identical `gh pr list --head` pattern, proving the approach works reliably at scale
- **Overall pattern**: 28+ `gh pr` invocations across codebase, with 4 different PR management contexts (watcher2, watch.sh, bugfix, examples)

### Diary Precedents

- **`downstream_fix` trap** (2026-03-08): Adding enforcement checks inside already-guarded paths while leaving unguarded paths open. This FR avoids the trap by fixing at the actual boundary (create_pr function) where the failure occurs.
- **`audit_as_ritual` pattern**: Multiple diary entries note missing CI gates that detect but don't block. This FR addresses a blocking failure that already exists, avoiding detection-without-enforcement.
- **Pipeline failure recovery** (2026-04-21, 2025-04-23): Several entries describe watcher2/enforce pipeline failures requiring manual intervention. PR existence errors are a known recovery scenario.
- **Branch protection bypass concerns**: Multiple audits flag direct pushes that bypass PR workflow. This FR strengthens the PR path by making it more resilient to restart scenarios.

### Usage Evidence

- **Existing graphs using related abstractions**: 1 (watcher2 orchestration)
- **Real-world use cases beyond the proposal**:
  - Post-merge finalization (watch.sh) - identical pattern already proven
  - Manual recovery scenarios when pipeline fails mid-process  
  - Development workflow where manual PR creation happens before re-running automation
  - Branch protection failure recovery scenarios

### Classification Signal

- **Abstraction level**: integration
- **Recommended approach**: build  
- **Key risk**: PR update logic might interfere with existing PR reviewers/comments if title/body updates are too aggressive