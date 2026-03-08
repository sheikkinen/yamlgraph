# Feature Request: FR-162 Vulture Dead Code Cleanup

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Investigate and resolve dead code flagged by Vulture: `worktree_helpers.py` (false positive) and `sanitize.py` (genuinely unused module). Add a Vulture whitelist to distinguish legitimate false positives from real dead code, then lower the confidence threshold to catch more issues.

## Value Statement

Maintainers get a clean Vulture baseline with no false positives, enabling stricter dead-code detection that catches real entropy before it accumulates.

## Problem

Vulture flags two modules at 60% confidence:

1. **`yamlgraph/utils/worktree_helpers.py`** — all three functions (`derive_branch_name`, `construct_worktree_path`, `validate_clean_working_tree`) appear unused to Vulture because they are invoked via `python3 -c` in `scripts/enforce_worktree.sh`, not via Python imports. This is a **false positive**.

2. **`yamlgraph/utils/sanitize.py`** — the entire module is **genuinely dead code** in production:
   - `sanitize_topic()` has no production caller (only imported in `tests/unit/test_sanitize.py`).
   - `sanitize_variables()` has no production caller — the identically-named function in `tools/shell.py` is a completely separate implementation.
   - Tests exist (tagged `REQ-YG-046`) but exercise code that no production path reaches.
   - A stale reference exists in `build/lib/yamlgraph/cli/validators.py` (build artifact, not source).

The current Vulture pre-commit hook uses `--min-confidence 80`, which hides both findings. Without a whitelist, lowering the threshold would surface false positives alongside real dead code, making the check noisy and unactionable.

## Proposed Solution

### Phase 1: Whitelist for false positives

Create `vulture_whitelist.py` at the project root — Vulture's standard mechanism for suppressing known false positives:

```python
# vulture_whitelist.py
# Functions invoked via python3 -c in scripts/enforce_worktree.sh
from yamlgraph.utils.worktree_helpers import (  # noqa: F401
    construct_worktree_path,
    derive_branch_name,
    validate_clean_working_tree,
)
```

Update `.pre-commit-config.yaml` to include the whitelist:

```yaml
entry: bash -c '.venv/bin/python -m vulture yamlgraph vulture_whitelist.py --min-confidence 80'
```

### Phase 2: Remove dead `sanitize.py` module

1. Delete `yamlgraph/utils/sanitize.py`.
2. Delete `tests/unit/test_sanitize.py`.
3. Update `REQ-YG-046` in `ARCHITECTURE.md` to remove the `utils/sanitize` reference (REQ-YG-046 also covers `utils/logging` and `utils/parsing`, which remain).
4. Clean up stale build artifact: `rm -rf build/`.

### Phase 3: Lower confidence threshold

With the whitelist in place and dead code removed, lower Vulture's confidence threshold to catch more issues:

```yaml
entry: bash -c '.venv/bin/python -m vulture yamlgraph vulture_whitelist.py --min-confidence 60'
```

Run Vulture at the new threshold and resolve any additional findings before merging.

## Acceptance Criteria

- [ ] `vulture_whitelist.py` exists at project root with `worktree_helpers` entries
- [ ] `.pre-commit-config.yaml` Vulture hook references the whitelist file
- [ ] `yamlgraph/utils/sanitize.py` is deleted
- [ ] `tests/unit/test_sanitize.py` is deleted
- [ ] `REQ-YG-046` traceability updated: remove `utils/sanitize` from the requirement description (logging and parsing coverage remains)
- [ ] `build/` stale artifacts cleaned (add `build/` to `.gitignore` if not present)
- [ ] Vulture `--min-confidence` lowered to 60 with clean pass
- [ ] `pre-commit run vulture-dead-code` passes with zero findings
- [ ] All existing tests pass (`pytest tests/ -q`)
- [ ] Tests added: none required (this is a removal, not addition)
- [ ] Documentation updated: CHANGELOG entry for dead code removal

## Alternatives Considered

1. **Keep `sanitize.py` and integrate it** — `sanitize_topic()` was likely intended for CLI input validation. However, no CLI command currently needs it, and the `tools/shell.py` `sanitize_variables()` already handles the runtime variable sanitization use case. Adding a caller just to justify the code's existence violates Commandment 8 (kill entropy).

2. **Suppress with `# noqa` or inline comments** — Vulture's whitelist file is the canonical mechanism; inline suppressions are not supported by Vulture and would require per-function `type: ignore` comments that drift.

3. **Do nothing (keep `--min-confidence 80`)** — Masks real dead code alongside false positives. The current threshold was likely set high to avoid noise, but a whitelist solves that problem properly.

## Related

- `scripts/enforce_worktree.sh` — shell script that invokes `worktree_helpers` functions
- `tests/unit/test_worktree_helpers.py` — tests for worktree_helpers (remain valid)
- `tests/unit/test_sanitize.py` — tests for sanitize (to be removed)
- `.pre-commit-config.yaml` lines 117-125 — Vulture hook configuration
- Commandment 8: "Kill all entropy and false idols — feed the dead to vulture"
