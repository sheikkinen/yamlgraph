# Feature Request: Guard editable install from worktree venv symlink corruption

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-09

## Summary

The `yamlgraph` CLI becomes unavailable (`ModuleNotFoundError: No module named 'yamlgraph'`) after git worktree operations that symlink the main `.venv`. Add post-cleanup validation and a self-healing mechanism to `enforce_worktree.sh` to detect and recover from editable-install corruption.

## Value Statement

Developers running the enforce pipeline avoid silent venv corruption that breaks the CLI and wastes time on manual `pip install -e .` recovery.

## Problem

`scripts/enforce_worktree.sh` (line 107) creates a symlink from the worktree's `.venv` to the main repo's `.venv`:

```bash
ln -sf "$MAIN_VENV" "$WORKTREE_DIR/.venv"
```

After `git worktree remove`, the `yamlgraph` editable install breaks:

```
ModuleNotFoundError: No module named 'yamlgraph'
```

This has occurred twice (FR-169 enforce run, and one prior incident). The root cause is one or both of:

1. **`.pth` file removal** — Editable installs rely on a `.pth` file in `site-packages/` that points to the source directory. Worktree cleanup or concurrent pip operations may remove or corrupt this file.
2. **Concurrent venv access** — The enforce pipeline runs `yamlgraph graph run` inside the worktree using the shared venv. If pip or setuptools runs concurrently in both trees (e.g., pre-commit hooks triggering installs), the installation metadata can be corrupted.

This is the venv analogue of FR-139 (`bare=true` corruption guard) — an infrastructure-level failure caused by worktree lifecycle operations.

## Proposed Solution

### Post-cleanup validation and self-heal

In the `cleanup()` trap (after `git worktree remove`), verify the editable install is still healthy. This follows the same pattern as the FR-139 `bare=true` guard already present in the cleanup trap:

```bash
cleanup() {
    local exit_code=$?
    cd "$MAIN_DIR" 2>/dev/null || true

    # Existing worktree removal
    log_info "Cleaning up worktree: $WORKTREE_DIR"
    git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true

    # FR-139: bare=true guard (existing)
    ...

    # FR-174: Editable install health check
    if ! python3 -c "import yamlgraph" 2>/dev/null; then
        log_warn "Editable install corrupted after worktree cleanup — restoring..."
        pip install -e ".[dev]" --quiet
        if python3 -c "import yamlgraph" 2>/dev/null; then
            log_info "Editable install restored successfully"
        else
            log_error "Failed to restore editable install — run 'pip install -e .[dev]' manually"
        fi
    fi

    exit $exit_code
}
```

The guard is placed inline in the `cleanup()` trap, consistent with the FR-139 pattern. Tests validate the guard via subprocess invocation of extracted bash snippets, matching the established pattern in `test_enforce_worktree_bare_guard.py`.

## Acceptance Criteria

- [ ] `enforce_worktree.sh` `cleanup()` trap validates `import yamlgraph` succeeds after worktree removal
- [ ] If import fails, `pip install -e ".[dev]" --quiet` runs automatically and logs a warning
- [ ] If auto-restore also fails, a clear error message instructs the user to run manual reinstall
- [ ] Unit test: subprocess invocation of the guard snippet detects a missing editable install and triggers reinstall (following `test_enforce_worktree_bare_guard.py` pattern)
- [ ] Integration test: full worktree create → run → cleanup cycle leaves editable install healthy
- [ ] The `bare=true` guard pattern (FR-139) is preserved alongside the new guard
- [ ] Documentation updated (comment in `enforce_worktree.sh` explaining the guard)

## Alternatives Considered

### A. Separate venv per worktree
Each worktree gets its own venv via `python -m venv .venv && pip install -e ".[dev]"`. **Rejected:** adds ~30-60 seconds of install time per enforce run and duplicates disk usage. The shared venv is the correct optimization; we just need to guard against its failure mode.

### B. `PYTHONPATH` instead of symlink
Set `PYTHONPATH` to the worktree source root and reuse the main venv's `bin/` via `PATH`. Eliminates the corruption vector entirely. **Deferred to Phase 2:** requires validation that all tools resolve correctly under `PYTHONPATH` instead of an editable install. The self-heal guard (Phase 1) is cheaper and addresses the immediate pain. If warranted, file a separate FR.

### C. Use `uv` instead of `pip`
`uv` uses a different installation mechanism (hard links instead of `.pth` files). **Not pursued:** introduces a new dependency and changes the install workflow for all contributors. May be revisited as a broader migration.

### D. Lock file during venv access
Use `flock` to serialize pip operations across main repo and worktree. **Over-engineered:** the corruption likely occurs during cleanup, not concurrent access. The self-heal approach is simpler and sufficient.

## Related

- `scripts/enforce_worktree.sh` — lines 103-112 (symlink creation), lines 78-95 (cleanup trap)
- FR-139: `bare=true` corruption guard (same pattern — infrastructure self-heal in cleanup trap)
- `yamlgraph/utils/worktree_helpers.py` — branch naming and path helpers
- `tests/unit/test_enforce_worktree_bare_guard.py` — existing test pattern for worktree guards
