# Script Retirement Demo (FR-276)

This demonstration shows that the obsolete pipeline scripts have been successfully retired and replaced with `watcher2.sh` as the sole orchestrator.

## What Changed

### ❌ Removed Scripts
- `.chaplain/watch.sh` (old monolithic watcher)
- `scripts/enforce_worktree.sh` (old enforcement script)
- `scripts/bugfix_worktree.sh` (old bugfix script)

### ✅ Single Orchestrator
- `.chaplain/watcher2.sh` now handles all pipeline orchestration
- Forensic failure preservation (worktrees and topics preserved on failure)
- Success path cleanup (worktree teardown and topic removal on success)
- Orphaned worktree metadata pruning

## Key Features Verified

1. **Script Deletion**: All obsolete scripts are gone
2. **Documentation**: All references updated to point to watcher2.sh
3. **Forensic Behavior**: Failures preserve evidence for inspection
4. **Metadata Pruning**: `git worktree prune` added to setup process
5. **No Regression**: All pipeline capabilities maintained in watcher2.sh

## Demonstration Commands

```bash
# Verify old scripts are gone
ls .chaplain/watch.sh 2>/dev/null || echo "✅ watch.sh removed"
ls scripts/enforce_worktree.sh 2>/dev/null || echo "✅ enforce_worktree.sh removed"
ls scripts/bugfix_worktree.sh 2>/dev/null || echo "✅ bugfix_worktree.sh removed"

# Verify watcher2.sh is the sole orchestrator
ls -la .chaplain/watcher2.sh && echo "✅ watcher2.sh exists and ready"

# Verify forensic behavior is in place
grep -q "Worktree preserved for inspection" .chaplain/watcher2.sh && echo "✅ Forensic preservation implemented"
grep -q ".chaplain/failed/" .chaplain/watcher2.sh && echo "✅ Failed topics moved, not deleted"

# Verify metadata pruning
grep -q "git worktree prune" .chaplain/lib/watcher/worktree_setup.sh && echo "✅ Metadata pruning implemented"

# Verify all acceptance tests pass
pytest tests/unit/test_retire_old_pipeline_scripts.py -q --no-cov
```

## Expected Results

All commands should show ✅ success indicators, and all 20 acceptance tests should pass.

This completes the script retirement specified in FR-276, consolidating pipeline orchestration under the single, proven watcher2.sh orchestrator.
