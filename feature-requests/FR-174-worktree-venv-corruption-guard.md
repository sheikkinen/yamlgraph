# Feature Request: Worktree .venv Corruption Guard

**ID:** FR-174
**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-03-09

## Summary

Add validation guards to `enforce_worktree.sh` and `worktree_helpers.py` that prevent .venv corruption when worktrees share the main repo's virtual environment via symlink.

## Value Statement

All developers using the enforce pipeline get immediate, loud failures when .venv is missing or broken, and automatic cleanup of stale editable-install references after worktree removal.

## Problem

`enforce_worktree.sh` symlinks the main repo's `.venv` into worktrees (line 103-112). Two corruption scenarios are unguarded:

### 1. Silent skip when .venv is missing or broken

When `.venv` doesn't exist or lacks a working `bin/python`, the script silently skips the symlink:

```bash
if [[ -d "$MAIN_VENV" ]]; then
    ln -sf "$MAIN_VENV" "$WORKTREE_DIR/.venv"
fi
```

The worktree then fails later with confusing errors from pre-commit hooks that reference `.venv/bin/python`. **Violates Commandment 6:** "Expose every fault. No silent fallbacks."

### 2. Editable install .pth corruption

If the enforce pipeline runs `pip install -e .` inside the worktree (using the shared `.venv`), it creates `.pth` files in `.venv/lib/pythonX.Y/site-packages/` pointing to the worktree directory. When the worktree is cleaned up, these paths become dangling references that corrupt the main repo's import resolution.

**Example:** After worktree cleanup, `.venv/lib/python3.11/site-packages/yamlgraph.egg-link` contains `/path/to/tmp/worktrees/feat/fr-xxx/` which no longer exists.

## Proposed Solution

### Python guards in `yamlgraph/utils/worktree_helpers.py`

**Guard 1: `validate_venv_health(venv_path: Path) -> None`**

Validate that a .venv directory exists and has a working Python binary:
- Asserts `venv_path` is a directory
- Asserts `venv_path / "bin" / "python"` exists and is executable
- Raises `FileNotFoundError` with actionable message if missing

**Guard 2: `validate_venv_symlink(symlink_path: Path, target_path: Path) -> None`**

Validate that a .venv symlink in a worktree resolves correctly:
- Asserts `symlink_path` is a symlink
- Asserts symlink target resolves to `target_path`
- Asserts resolved `bin/python` exists
- Raises `OSError` with diagnostic message if broken

**Guard 3: `clean_stale_pth_entries(venv_path: Path, worktree_dir: str) -> list[Path]`**

Find and remove `.pth` and `.egg-link` files that reference a worktree directory:
- Scans `venv_path/lib/python*/site-packages/` for `.pth` and `.egg-link` files
- Returns list of cleaned files (empty if none found)
- Logs a warning for each removed file

### Shell integration in `enforce_worktree.sh`

1. **Before symlink**: Call `validate_venv_health` — fail loudly if .venv is missing/broken
2. **After symlink**: Call `validate_venv_symlink` — fail loudly if symlink is broken
3. **In cleanup()**: Call `clean_stale_pth_entries` — remove dangling worktree references

## Acceptance Criteria

- [ ] `validate_venv_health()` raises `FileNotFoundError` when `.venv` directory is missing
- [ ] `validate_venv_health()` raises `FileNotFoundError` when `.venv/bin/python` is missing
- [ ] `validate_venv_health()` returns `None` (no error) for a healthy .venv
- [ ] `validate_venv_symlink()` raises `OSError` when path is not a symlink
- [ ] `validate_venv_symlink()` raises `OSError` when symlink target doesn't resolve
- [ ] `validate_venv_symlink()` returns `None` for valid symlink to healthy .venv
- [ ] `clean_stale_pth_entries()` removes `.pth` files containing worktree path references
- [ ] `clean_stale_pth_entries()` removes `.egg-link` files containing worktree path references
- [ ] `clean_stale_pth_entries()` returns empty list when no stale entries exist
- [ ] `enforce_worktree.sh` fails with clear error when `.venv` is missing (no silent skip)
- [ ] `enforce_worktree.sh` cleanup removes stale `.pth` entries for the worktree being removed
- [ ] All tests tagged with `@pytest.mark.req("REQ-YG-156")`
- [ ] Existing worktree tests (`test_worktree_helpers.py`, `test_enforce_worktree_bare_guard.py`) still pass

## Alternatives Considered

1. **Copy .venv instead of symlinking** — Eliminates symlink risks but costs 1-2 minutes per worktree creation and wastes disk space. Rejected.
2. **Run `pip install -e .` guard only** — Insufficient. Missing .venv is the more common failure. Both guards needed.
3. **Install fresh .venv per worktree** — Most thorough but slowest. Defer to a separate FR if symlink approach proves fundamentally unreliable.

## Related

- `scripts/enforce_worktree.sh` — Primary shell file to modify
- `yamlgraph/utils/worktree_helpers.py` — Primary Python file to extend
- `feature-requests/FR-139-enforce-worktree-bare-corruption-guard.md` — Sibling guard (bare=true)
- `tests/unit/test_enforce_worktree_bare_guard.py` — Pattern to follow
- `tests/unit/test_worktree_helpers.py` — Existing helper tests

## Judgement

**Verdict:** APPROVE — Scope frozen, authority granted.

**Evaluation:**

1. **Scope: Clear and minimal.** Three Python functions in one module (`worktree_helpers.py`), three integration points in one shell script (`enforce_worktree.sh`). Each guard addresses a distinct failure mode with a specific, testable remedy.

2. **No contradictions.** The guards complement FR-139's bare=true protection. FR-139 guards git config; FR-174 guards Python environment. No overlap.

3. **Acceptance criteria: Measurable.** All 13 items are binary pass/fail. Each maps to a specific test case.

4. **Commandment 6 compliance.** The primary fix — replacing silent `if [[ -d ]]` skip with loud `validate_venv_health()` failure — directly addresses the "no silent fallbacks" commandment.

5. **Architecture alignment.** Changes stay in the utility layer (`utils/worktree_helpers.py`) and presentation layer (`scripts/`). No framework core changes.

**Notes for implementation:**
- Tag all tests with `@pytest.mark.req("REQ-YG-156")` for ADR-001 traceability.
- Register REQ-YG-156 as CAP-58 in `scripts/req_coverage.py` and `ARCHITECTURE.md`.
