# Feature Request: FR-162 Vulture Dead Code Cleanup

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Create a Vulture whitelist for shell-invoked `worktree_helpers` functions (false positive), delete the genuinely dead `sanitize.py` module and its orphaned tests, then lower Vulture's confidence threshold from 80 to 60 for stricter dead-code detection.

## Value Statement

Maintainers get a clean Vulture baseline with no false positives, enabling stricter dead-code detection that catches real entropy before it accumulates.

## Problem

Vulture flags two modules at 60% confidence:

1. **`yamlgraph/utils/worktree_helpers.py`** — all three functions (`derive_branch_name`, `construct_worktree_path`, `validate_clean_working_tree`) are invoked via `python3 -c` in `scripts/enforce_worktree.sh`, not via Python imports. Vulture cannot see dynamic invocation — this is a **false positive**.

2. **`yamlgraph/utils/sanitize.py`** — the entire module is **genuinely dead code**:
   - `sanitize_topic()` has zero production callers (only imported in `tests/unit/test_sanitize.py`).
   - `sanitize_variables()` has zero production callers — the identically-named function in `tools/shell.py` is a completely separate implementation using `shlex.quote()`.
   - 14 tests exist in `test_sanitize.py` (all tagged `REQ-YG-046`) but exercise code that no production path reaches.
   - A stale reference exists in `build/lib/yamlgraph/cli/validators.py` (build artifact, not source — no source `yamlgraph/cli/validators.py` exists).

The current `--min-confidence 80` threshold hides both findings. Without a whitelist, lowering the threshold surfaces false positives alongside real dead code, making the check noisy and unactionable.

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

Update `.pre-commit-config.yaml` to pass the whitelist to Vulture:

```yaml
entry: bash -c '.venv/bin/python -m vulture yamlgraph vulture_whitelist.py --min-confidence 80'
```

### Phase 2: Remove dead `sanitize.py` module

1. Delete `yamlgraph/utils/sanitize.py`.
2. Delete `tests/unit/test_sanitize.py`.
3. Update `REQ-YG-046` in `ARCHITECTURE.md`: remove `utils/sanitize` from the Key Modules column (the requirement still covers `utils/logging` and `utils/parsing`, which remain exercised by `test_logging.py` and `test_parsing.py`).
4. Clean stale build artifact: `rm -rf build/`.

### Phase 3: Lower confidence threshold

With the whitelist in place and dead code removed, lower Vulture's confidence threshold:

```yaml
entry: bash -c '.venv/bin/python -m vulture yamlgraph vulture_whitelist.py --min-confidence 60'
```

Run Vulture at the new threshold and resolve any additional findings before merging.

## Acceptance Criteria

- [ ] `vulture_whitelist.py` exists at project root with `worktree_helpers` entries
- [ ] `.pre-commit-config.yaml` Vulture hook references the whitelist file
- [ ] `yamlgraph/utils/sanitize.py` is deleted
- [ ] `tests/unit/test_sanitize.py` is deleted
- [ ] `REQ-YG-046` in `ARCHITECTURE.md` updated: `utils/sanitize` removed from Key Modules (`utils/logging`, `utils/parsing` remain); Description column updated from "Logging, parsing, and sanitization utilities" to "Logging and parsing utilities"
- [ ] `build/` stale artifacts cleaned (`build/` already in `.gitignore`)
- [ ] Vulture `--min-confidence` lowered to 60 with clean pass
- [ ] `pre-commit run vulture-dead-code` passes with zero findings
- [ ] `python scripts/req_coverage.py` passes (REQ-YG-046 still covered by `test_logging.py` and `test_parsing.py`)
- [ ] All existing tests pass (`pytest tests/ -q`)
- [ ] Tests added: none required (this is a removal, not addition)
- [ ] CHANGELOG entry for dead code removal
- [ ] `# noqa: F401` in `vulture_whitelist.py` documented in `docs/confessions.md` with CONF-XXX entry (per project noqa confession rule)

## Judgement

**Verdict: APPROVE**

**Findings:**
1. All factual claims verified against the codebase — `sanitize.py` has zero production callers, `worktree_helpers` functions are invoked via `python3 -c` in `enforce_worktree.sh`, and `tools/shell.py` has its own independent `sanitize_variables()`.
2. Scope is clear, minimal, and single-responsibility: three sequential phases toward one goal (clean Vulture baseline).
3. Phases are correctly ordered — whitelist must precede threshold lowering; dead code removal must precede threshold lowering.
4. Two acceptance criteria gaps were added during review:
   - REQ-YG-046 Description column must also be updated (not just Key Modules).
   - `# noqa: F401` in whitelist file requires a `docs/confessions.md` entry per project doctrine.
5. Effort estimate (0.5 days) is realistic for the scope.
6. Aligns with Commandment 8: "feed the dead to vulture."

**Authority granted.** Scope frozen. Implement per the Sermon: failing test first (RED for sanitize import absence), then delete, then verify.

## Alternatives Considered

1. **Keep `sanitize.py` and integrate it** — `sanitize_topic()` was likely intended for CLI input validation, but no CLI command currently needs it. The `tools/shell.py` `sanitize_variables()` already handles runtime variable sanitization with `shlex.quote()`. Adding a caller just to justify the code's existence violates Commandment 8 (kill entropy).

2. **Suppress with inline comments** — Vulture does not support `# noqa`-style inline suppressions. Its whitelist file is the canonical mechanism for false positive management.

3. **Do nothing (keep `--min-confidence 80`)** — Masks real dead code alongside false positives. The high threshold was likely set to avoid noise, but a whitelist solves that problem properly.

## Related

- `scripts/enforce_worktree.sh` — shell script that invokes `worktree_helpers` functions via `python3 -c`
- `tests/unit/test_worktree_helpers.py` — tests for worktree_helpers (remain valid)
- `tests/unit/test_sanitize.py` — tests for sanitize (to be removed)
- `tests/unit/test_logging.py`, `tests/unit/test_parsing.py` — remaining REQ-YG-046 test coverage
- `.pre-commit-config.yaml` lines 119–125 — Vulture hook configuration
- Commandment 8: "Kill all entropy and false idols — feed the dead to vulture"
