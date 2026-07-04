# Feature Request: Reorganize modules to restore the 250-line module-map budget

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-07-04

## Summary

FR-677 (First-Class Verification) temporarily loosened the module-map line
budget from 250 to 260 to admit a new module split without blocking the
verification work. This FR pays that debt back: reorganize the modules that
grew during the guard/verify/gate work so the generated `reference/module-map.md`
fits within the original 250-line budget again, then revert the temporary
assertion.

## Value Statement

The module-map budget is an entropy gate (Commandment 8) — restoring it to 250
keeps the structural-drift signal honest instead of letting a one-time bump
become the new normal.

## Problem

Three concrete debts were taken on during FR-677:

1. **Module-map budget bumped 250 → 260.** The temporary allowance lives in
   [tests/unit/test_fr335_module_map_compression.py](../tests/unit/test_fr335_module_map_compression.py#L127)
   with a comment pointing at "a follow-up FR." This is that FR. A loosened
   entropy gate that is never re-tightened silently ratchets — every future
   split will point at the 260 precedent.

2. **`node_compiler.py` grew toward the 450-line file cap.** Move 2 added the
   `VERIFY` node-type handler and its registration. The file is now close
   enough to the cap that the next node type cannot be added without a split.

3. **`graph_schema.py` grew toward the 450-line file cap.** Move 2 added the
   `GraphVerifyRule` import and the `verify:` field. Same pressure as above.

None of these are correctness bugs — the FR-677 tests all pass. They are
structural-drift debts that the entropy gates (`radon`, file-size cap,
module-map budget) will eventually surface as blockers. Paying them now, while
the context is fresh, is cheaper than paying them under deadline pressure when
the next node type or schema field must land.

## Proposed Solution

1. **Regenerate and inspect the current module map** to see which modules push
   the count over 250:

   ```bash
   python scripts/generate_module_map.py reference/module-map.md
   wc -l reference/module-map.md
   ```

2. **Reorganize the highest-pressure modules.** Candidate moves (to be confirmed
   against the regenerated map — do not assume):
   - Extract the node-type handler registry out of `node_compiler.py` into a
     small `node_compiler_registry.py` (or similar) so the compiler file drops
     below the cap and the map entry shrinks.
   - Split the graph-schema verification models (`GraphVerifyRule` and friends)
     into the existing `models/guard_schema.py` boundary if `graph_schema.py`
     is the offender, keeping `graph_schema.py` focused on the top-level graph
     shape.

3. **Revert the temporary budget** in
   `tests/unit/test_fr335_module_map_compression.py`:
   restore `<= 250`, remove the FR-677 comment.

4. **Regenerate the committed map** and stage it.

The exact split is deferred to enforcement — the regenerated map is the source
of truth for which module is the offender, not this plan's guesses.

## Acceptance Criteria

- [ ] `reference/module-map.md` regenerated and committed at <= 250 lines
- [ ] `test_ac01_regenerated_module_map_stays_within_line_budget` asserts `<= 250` again, FR-677 comment removed
- [ ] No module exceeds the 450-line file-size cap (import-linter + file-size gate green)
- [ ] All existing FR-677 tests still pass (node guards, verify, gate) with no behavior change
- [ ] Import-linter "Three-layer architecture" and "Linter stays LLM-free" contracts still KEPT

## Notes

- This is a pure-refactor FR: no new capability, no `REQ-YG-*` needed beyond the
  existing structural-drift requirement covered by `REQ-YG-263`.
- Keep each module move a separate commit for clean blame/revert
  (`mixed_commits_erode_auditability`).
