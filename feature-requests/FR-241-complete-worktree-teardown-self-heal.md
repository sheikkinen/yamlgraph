# Feature Request: Complete worktree teardown self-heal and pre-commit guard

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-04-19

## Summary

FR-236 fixed `clean_stale_pth_entries()` to remove stale `direct_url.json` from `*.dist-info/`, but the remaining acceptance criteria — import validation with self-heal in both worktree scripts, `validate_editable_install()` helper, pre-commit guard, and `bugfix_worktree.sh` FR-174 parity — were never implemented. The editable install still breaks silently after external worktree teardown, requiring manual diagnosis.

## Value Statement

Developers never encounter `ModuleNotFoundError` after worktree teardown — the install self-heals in-script and the pre-commit hook catches any remaining stale state before the next commit.

## Problem

Three confirmed gaps remain after FR-236's partial delivery:

1. **No import validation after cleanup.** `enforce_worktree.sh` cleans `.pth` and `direct_url.json` entries (FR-174 + FR-236), but never verifies the install actually works. If a stale `__editable__` finder module or other metadata survives, the import still fails.

2. **`bugfix_worktree.sh` lacks FR-174 guards entirely.** Its cleanup trap has only the FR-139 `bare=true` guard — no `.pth` cleaning, no venv health validation before symlinking, no symlink validation after symlinking. Any worktree created via `bugfix_worktree.sh` leaves full stale metadata on teardown.

3. **No pre-commit guard for external teardown.** When worktrees are removed via `git worktree remove`, `rm -rf`, or IDE cleanup (i.e., outside the scripts), no guard fires. The broken install is only discovered when `yamlgraph` commands fail.

## Proposed Solution

### A. `validate_editable_install()` in `worktree_helpers.py`

```python
def validate_editable_install(package: str = "yamlgraph") -> bool:
    """Validate that a package is importable (editable install is healthy).

    Spawns a subprocess to avoid bootstrapping paradox (this function
    lives inside the package it validates).

    Returns True if import succeeds, False otherwise. Does NOT self-heal;
    callers decide whether to reinstall or raise.
    """
    result = subprocess.run(
        [sys.executable, "-c", f"import {package}"],
        capture_output=True,
    )
    return result.returncode == 0
```

### B. Self-heal in both worktree script cleanup traps

Add after the existing FR-174 `.pth` cleaning in `enforce_worktree.sh`, and add new to `bugfix_worktree.sh`:

```bash
# FR-241: Validate editable install survives worktree removal
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

### C. FR-174 parity for `bugfix_worktree.sh`

Backport from `enforce_worktree.sh`:
- `validate_venv_health()` before symlinking
- `validate_venv_symlink()` after symlinking
- `clean_stale_pth_entries()` in cleanup trap

### D. Pre-commit hook for external teardown

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

This catches stale installs from manual worktree removal before the developer wastes time on a full commit cycle.

## Acceptance Criteria

- [ ] `validate_editable_install()` function added to `yamlgraph/utils/worktree_helpers.py`
- [ ] `enforce_worktree.sh` cleanup trap validates `import yamlgraph` after `.pth` cleaning; self-heals with `pip install -e ".[dev]"` if broken; logs error with manual remediation if self-heal also fails
- [ ] `bugfix_worktree.sh` cleanup trap has FR-174 guards: `clean_stale_pth_entries()`, and the same import validation + self-heal as `enforce_worktree.sh`
- [ ] `bugfix_worktree.sh` has FR-174 pre-symlink guards: `validate_venv_health()` before symlinking, `validate_venv_symlink()` after symlinking
- [ ] Pre-commit hook `editable-install-check` added to `.pre-commit-config.yaml` with `always_run: true`
- [ ] Unit test: `validate_editable_install()` returns `False` when package is not importable
- [ ] Unit test: `validate_editable_install()` returns `True` for an importable package (e.g., `json`)
- [ ] Existing FR-174 (`test_worktree_venv_guard.py`), FR-139 (`test_enforce_worktree_bare_guard.py`), and FR-236 (`test_worktree_editable_install_guard.py`) tests continue to pass
- [ ] Guard chain documented in both scripts: FR-139 → FR-174 → FR-236 → FR-241

## Judgement

**Verdict: APPROVE** — Scope frozen, authority granted.

**Evaluation:**

1. **Scope:** Clear and minimal. Single concern — guard editable install against worktree teardown — with four complementary mechanisms (Python helper, in-script self-heal, FR-174 backport, pre-commit hook). No component is independently useful without the others; they form one coherent guard chain.

2. **Contradictions:** None. Code inspection confirms all three claimed gaps:
   - `enforce_worktree.sh` lines 94-104: `.pth` cleaning only, no import validation.
   - `bugfix_worktree.sh` lines 78-94: FR-139 `bare=true` guard only, no FR-174 guards, no `.pth` cleaning.
   - `worktree_helpers.py`: no `validate_editable_install()` function.
   - `.pre-commit-config.yaml`: no `editable-install-check` hook.

3. **Acceptance criteria:** 9 ACs, all specific and measurable. Removed 2 vague/redundant ACs ("Tests added" — redundant with specific test ACs; "Documentation updated" — unspecified target).

4. **Feasibility:** All referenced files exist. Proposed code is straightforward and follows established patterns (FR-139 self-heal, FR-174 validation). 1-day effort is realistic.

5. **Architecture alignment:** Pre-commit as infrastructure boundary — correct per Commandment 6 and existing doctrine. Python helper in `worktree_helpers.py` — consistent with module responsibility. `subprocess.run` avoids bootstrapping paradox.

6. **Single responsibility:** Confirmed. FR-174 backport to `bugfix_worktree.sh` is prerequisite for import validation (can't validate after `.pth` cleaning if there's no `.pth` cleaning). Not orthogonal.

**Process note:** FR-236 status should be updated to note partial delivery (only `direct_url.json` cleanup in `clean_stale_pth_entries()` was implemented; remaining ACs carried forward to FR-241). This is process hygiene for the implementer, not a blocker.

**Observation for implementer:** `validate_editable_install()` uses `sys.executable` but the proposed code does not import `sys` — add the import. The function's primary consumers are tests; shell scripts use raw `python3 -c "import yamlgraph"` directly.

## Alternatives Considered

### A. Extend FR-236 scope instead of new FR

FR-236 is already in `Approved` status with changelog, diary, and tests merged. Reopening it conflates delivered and undelivered work, making git blame and traceability unclear. A new FR with explicit cross-reference is cleaner.

### B. Only add the pre-commit hook, skip script self-heal

The pre-commit hook catches external teardown, but script-initiated teardown is the most common path. Self-heal in the scripts prevents the developer from ever seeing the error in the normal workflow; the pre-commit hook is the safety net for the abnormal path. Both are needed.

### C. Merge bugfix_worktree.sh into enforce_worktree.sh

The two scripts serve different pipelines (enforce vs. bugfix) with different graph configs. Merging would conflate concerns. Backporting the guards to `bugfix_worktree.sh` achieves parity without architectural change.

## Related

- FR-236: Worktree teardown editable install guard (partial implementation — `direct_url.json` cleanup only)
- FR-174: Worktree `.venv` corruption guard (implemented `.pth` cleaning; import validation was in AC but not implemented)
- FR-139: `bare=true` corruption guard (established the cleanup trap self-heal pattern)
- FR-106: Parallel Development Pipeline via Git Worktrees
- FR-173: Bug-Fix Pipeline via Git Worktrees (`bugfix_worktree.sh`)
- `scripts/enforce_worktree.sh` — lines 78-105 (cleanup trap with FR-139 + FR-174 guards)
- `scripts/bugfix_worktree.sh` — lines 78-95 (cleanup trap, FR-139 only, missing FR-174 + FR-236 guards)
- `yamlgraph/utils/worktree_helpers.py` — `clean_stale_pth_entries()`, `validate_venv_health()`, `validate_venv_symlink()`
- `tests/unit/test_worktree_editable_install_guard.py` — FR-236 tests (pass with current code)
- `tests/unit/test_enforce_worktree_bare_guard.py` — test pattern for shell guard snippets
