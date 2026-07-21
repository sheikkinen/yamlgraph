# Feature Request: FR-757 Relocate FSM Bridge from yamlgraph/utils/fsm to yamlgraph/contrib/fsm

**Priority:** MEDIUM
**Type:** Refactor
**Status:** Proposed
**Effort:** 2-3 days
**Requested:** 2026-07-21
**Prior art:** FR-755 (parent ruling C — this FR is its mandated follow-up, executing the relocation the ruling deferred); FR-756 (defines the process-marker classification this move must preserve — complementary, no overlap); FR-493 (dm-adapter FSM split — different module in examples, mechanics precedent only); FR-078 (test relocation precedent — shim-free move mechanics reused here); FR-090 (projects-vs-examples boundary taxonomy — background precedent, no scope overlap).
**First consumer / first event:** maintainers enforcing FR-755 ruling C; first event is the first FSM bridge change where package ownership must match documented contrib-tier identity.

## Summary

Relocate the FSM bridge package from `yamlgraph/utils/fsm` to `yamlgraph/contrib/fsm` to align package layout with FR-755 ownership ruling C (supported repeating pattern, not core API identity).

## Problem

FR-755 documents and enforces ownership boundaries, but the current package path still signals core utility status (`yamlgraph.utils.*`). This mismatch keeps contributor confusion alive and prolongs dual-identity risk.

## Ideal Result

`yamlgraph/contrib/fsm` is the sole FSM bridge package path. All known consumers import the new path. No compatibility shim remains.

## Proposed Solution

1. Move package directory `yamlgraph/utils/fsm` to `yamlgraph/contrib/fsm`.
2. Update all in-repo consumers:
   - `.chaplain/actions/yamlgraph_async_action.py`
   - `examples/demos/hook_classifier/actions/classify_action.py`
   - `examples/fsm-router/actions/yamlgraph_async_action.py`
   - tests importing `yamlgraph.utils.fsm.*`
3. Update capability docs and references for CAP-141/CAP-146 module paths.
4. Remove old path with no re-export shim (Commandment 8).
5. Add/refresh tests proving all imports resolve through contrib path only.

## Migration Inventory Baseline (from FR-755, 2026-07-21)

- `yamlgraph`: 0 imports (outside package itself)
- `.chaplain`: 3 imports
- `examples`: 17 imports
- `tests`: 40 imports
- `scripts`: 0 imports
- sibling scan: `../statemachine-engine`: 0, `../ninchat_voice`: missing in current workspace

## Acceptance Criteria

- [ ] No import of `yamlgraph.utils.fsm` remains in tracked files.
- [ ] All known consumers import `yamlgraph.contrib.fsm`.
- [ ] CAP-141 and CAP-146 module lists updated.
- [ ] `lint-imports` passes with updated ownership contract.
- [ ] Unit tests for shared bridge pass with new import path.
- [ ] Changelog fragment and diary entry added.

## Purge List

- No compatibility shim or re-export alias from `yamlgraph.utils.fsm`.
- No unrelated FSM behavior change in same FR.

## Related

- FR-755 ownership ruling C (contrib tier)
- CAP-141 Shared FSM Bridge Module
- CAP-146 FSM Snapshot Hooks Phase 2 Subclassing
