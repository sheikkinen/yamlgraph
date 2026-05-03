### Fixed
- Pipeline `done` state now uses `merge_pr.sh` instead of raw `gh pr merge --delete-branch`, preventing fatal error in worktree context
- Pipeline `failed` state now transitions to `stopped` via `cleanup_done` event, preventing infinite action loop that blocked the dispatcher from processing subsequent tasks
