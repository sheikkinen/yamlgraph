# Feature Request: Guard editable install on worktree teardown

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-18

## Summary

After a git worktree under `tmp/worktrees/` is removed, the `.venv` editable install can remain pointing to the deleted worktree path, causing `ModuleNotFoundError: No module named 'yamlgraph'` on any subsequent CLI invocation. Add a post-cleanup `import yamlgraph` validation with self-heal to both worktree scripts, and a pre-commit hook to catch stale installs from external teardown.

## Value Statement

Developers avoid wasted time diagnosing `ModuleNotFoundError` after worktree cleanup — the install self-heals automatically in-script and fails loudly with remediation in manual teardown scenarios.

## Problem

FR-174 added `.pth`/`.egg-link` cleaning to `enforce_worktree.sh`'s cleanup trap (`clean_stale_pth_entries()`), but the problem has recurred at least twice since (FR-232, FR-235). Two gaps remain:

1. **No import validation after cleanup.** The `.pth` cleaning is necessary but not sufficient — modern pip (21.3+) can use `__editable__` finder modules and `.dist-info` metadata that also reference worktree paths. Only an actual `python3 -c "import yamlgraph"` check proves the install is healthy.

2. **No guard for external teardown.** When worktrees are removed outside the scripts (manual `rm -rf`, direct `git worktree remove`, IDE cleanup), no guard fires. The developer discovers the broken install only when the next `yamlgraph` command fails.

3. **`bugfix_worktree.sh` lacks FR-174 guards entirely.** It has the FR-139 `bare=true` guard but no `.pth` cleaning, no venv health validation, and no symlink validation before symlinking.

## Proposed Solution

### A. Complete in-script self-heal (both scripts)

Add to the `cleanup()` trap in both `enforce_worktree.sh` and `bugfix_worktree.sh`, after the existing `.pth` cleaning:

```bash
# FR-236: Validate editable install survives worktree removal
if ! python3 -c "import yamlgraph" 2>/dev/null; then
    log_warn "Editable install broken after worktree cleanup — restoring..."
    pip install -e ".[dev]" --quiet 2>/dev/null
    if python3 -c "import yamlgraph" 2>/dev/null; then
        log_info "Editable install restored successfully"
    else
        log_error "Failed to restore editable install — run: pip install -e '.[dev]'"
    fi
fi
```

Also backport the missing FR-174 guards to `bugfix_worktree.sh`:
- `validate_venv_health()` before symlinking
- `validate_venv_symlink()` after symlinking
- `clean_stale_pth_entries()` in cleanup trap

### B. Pre-commit hook for external teardown

Add a local hook to `.pre-commit-config.yaml` that validates the editable install is healthy. This catches stale installs from manual worktree removal before the developer wastes time on a full commit cycle:

```yaml
- repo: local
  hooks:
    - id: editable-install-check
      name: Validate editable install
      entry: python3 -c "import yamlgraph; print('✓ yamlgraph importable')"
      language: system
      pass_filenames: false
      always_run: true
      stages: [pre-commit]
```

The hook fails loudly with remediation (`pip install -e ".[dev]"`), not silently — Commandment 6.

### C. Python helper for reuse

Add `validate_editable_install()` to `yamlgraph/utils/worktree_helpers.py`:

```python
def validate_editable_install(package: str = "yamlgraph") -> bool:
    """Validate that a package is importable (editable install is healthy).

    Returns True if import succeeds, False otherwise. Does NOT self-heal;
    callers decide whether to reinstall or raise.
    """
    result = subprocess.run(
        [sys.executable, "-c", f"import {package}"],
        capture_output=True,
    )
    return result.returncode == 0
```

This consolidates the import check for use by both shell scripts (via `python3 -c`) and future Python-level guards.

## Acceptance Criteria

- [ ] `enforce_worktree.sh` cleanup trap validates `import yamlgraph` succeeds after worktree removal and `.pth` cleaning
- [ ] If import fails in-script, `pip install -e ".[dev]" --quiet` runs automatically with warning log
- [ ] If auto-restore also fails, a clear error message instructs the user to run manual reinstall
- [ ] `bugfix_worktree.sh` cleanup trap has the same import validation + self-heal
- [ ] `bugfix_worktree.sh` has FR-174 pre-symlink guards (`validate_venv_health`, `validate_venv_symlink`) and post-cleanup `.pth` cleaning — parity with `enforce_worktree.sh`
- [ ] `validate_editable_install()` function added to `worktree_helpers.py`
- [ ] Pre-commit hook `editable-install-check` added to `.pre-commit-config.yaml` with `always_run: true`
- [ ] Unit test: `validate_editable_install()` returns False when package is not importable
- [ ] Unit test: cleanup guard snippet detects broken import and triggers reinstall (following `test_enforce_worktree_bare_guard.py` pattern)
- [ ] Existing FR-174 and FR-139 tests continue to pass
- [ ] Documentation: comments in both scripts explaining the guard chain (FR-139 → FR-174 → FR-236)

## Alternatives Considered

### A. Git `post-checkout` hook instead of pre-commit
A `post-checkout` hook would fire on `git checkout` and `git worktree add`, but NOT on `git worktree remove` or manual `rm`. Pre-commit fires more reliably because it guards the next developer action (committing), regardless of how the worktree was removed.

### B. CLI-level guard (`yamlgraph` entrypoint self-check)
Adding a self-import check to the CLI entrypoint would catch the issue at runtime but adds latency to every invocation and conflates infrastructure concerns with application logic. **Rejected:** pre-commit is the correct boundary — infrastructure guards belong in infrastructure hooks.

### C. Wrapper script for all worktree removal
A `scripts/remove_worktree.sh` that wraps `git worktree remove` + cleanup. **Rejected:** cannot enforce usage — developers will still use `git worktree remove` or `rm` directly. The pre-commit hook catches all paths without requiring discipline.

### D. Move to non-editable install in worktrees
Run `pip install .` (non-editable) instead of symlinking `.venv`. **Rejected:** editable install is essential for development — code changes must be reflected immediately without reinstall.

## Judgement

**Verdict: APPROVE** — Scope frozen, authority granted.

**Evaluation:**

1. **Scope:** Clear and minimal. Single concern (guard editable install against worktree teardown) with three complementary mechanisms — in-script self-heal, pre-commit guard, and Python helper. The FR-174 backport to `bugfix_worktree.sh` is justified scope since it addresses a confirmed gap in the same file being modified.

2. **Contradictions:** One minor narrative imprecision — the FR states the Python helper "consolidates the import check for use by both shell scripts" but the shell scripts use `python3 -c "import yamlgraph"` directly, not the helper function. The helper's real value is testability and future Python-level guards. This does not affect implementation correctness.

3. **Acceptance criteria:** All 11 ACs are specific, measurable, and independently verifiable. Test patterns reference existing test files that are confirmed to exist.

4. **Feasibility:** All referenced files exist (`worktree_helpers.py`, both shell scripts, test files). The proposed code snippets are straightforward. 1-day effort is realistic.

5. **Architecture alignment:** Pre-commit as infrastructure boundary — correct per Commandment 6 and Alternative B's rejection rationale. Python helper in `worktree_helpers.py` — consistent with existing module's responsibility. Self-heal pattern follows FR-139 precedent.

6. **Single responsibility:** Confirmed. Three components serve one concern; none is independently useful without the others.

**Observation for implementer:** The `validate_editable_install()` function lives inside `yamlgraph` but validates that `yamlgraph` is importable — a bootstrapping paradox. This is fine because it uses `subprocess.run` (spawns a new Python process), and the shell scripts don't depend on it (they use raw `python3 -c`). The function's primary consumers are tests.

## Related

- FR-174: Worktree `.venv` corruption guard (implemented `.pth` cleaning; import validation was in AC but not implemented)
- FR-139: `bare=true` corruption guard (established the cleanup trap self-heal pattern)
- FR-106: Parallel Development Pipeline via Git Worktrees (created the worktree infrastructure)
- FR-173: Bug-Fix Pipeline via Git Worktrees (`bugfix_worktree.sh`)
- `scripts/enforce_worktree.sh` — lines 94-104 (existing `.pth` cleanup)
- `scripts/bugfix_worktree.sh` — lines 78-95 (cleanup trap, missing FR-174 guards)
- `yamlgraph/utils/worktree_helpers.py` — `clean_stale_pth_entries()`, `validate_venv_health()`, `validate_venv_symlink()`
- `tests/unit/test_enforce_worktree_bare_guard.py` — test pattern for shell guard snippets
- `tests/unit/test_worktree_venv_guard.py` — FR-174 guard tests
