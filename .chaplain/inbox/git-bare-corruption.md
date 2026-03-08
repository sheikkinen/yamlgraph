# Git bare=true Corruption from Worktree Operations

## Problem

The `.git/config` file keeps getting `bare = true` set during enforce worktree operations, causing all git commands to fail with "this operation must be run in a work tree".

## Observed Behavior

- After running `enforce_worktree.sh`, the main repo's `.git/config` has `bare = true`
- This persists even after worktree cleanup
- Manual fix required: `sed -i '' 's/bare = true/bare = false/' .git/config`

## Root Cause Hypothesis

Git worktree operations or the cleanup process may be modifying the main repo config. Possibly:
1. `git worktree add` with bare repo detection issue
2. Cleanup trap setting bare=true when removing worktree
3. Environment variable pollution (GIT_DIR/GIT_WORK_TREE)

## Acceptance Criteria

1. After `enforce_worktree.sh` completes (success or failure), main repo `.git/config` has `bare = false`
2. No manual intervention needed to restore git operations
3. Add assertion/check in cleanup trap to verify config integrity
