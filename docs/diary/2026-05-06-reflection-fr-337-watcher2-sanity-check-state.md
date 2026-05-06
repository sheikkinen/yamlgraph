# FR-337 Watcher2 Sanity Check Reflection

**Date:** 2026-05-06
**FR:** FR-337 Context planner pre-node with relevance classifier
**Reviewer:** watcher2 (post-validate sanity check)

## What Happened

FR-337 added a three-node pre-node architecture (`plan_context → assemble_context → enforce`) to the watcher-enforce session graph. The enforce session previously had a single `copilot` node; this change inserts an LLM-driven relevance classifier (lightweight `gemini-2.0-flash`) and a deterministic Python assembler (`ast.parse()`-based) before the enforce copilot invocation. The assembled context is injected into the enforce prompt via `codebase_context`.

All 8 acceptance tests pass (0.19s). The pipeline log confirms: enforce ran cleanly (exit 0), validate_fix reported 3719 tests passed, and the FSM transitioned `enforce_session → validate_fix → sanity_check` without incident.

## Trap

**working_system_inertia**: The existing single-node contract in `test_enforce_simplify.py` encoded the `START → enforce → END` topology as a hard constraint. The trap was treating the existing shape as immutable doctrine rather than a contract that needed updating as the FR expanded scope. The AC-07 acceptance test and the contract test update correctly handled this — but the risk was that an implementor might have left the old contract test red (believing it was "pre-existing") rather than updating it to match the new intended topology.

## Root Cause

The module-map (FR-331/FR-335) existed as a global artifact but was never plumbed into the enforce prompt in a task-adaptive way. Every enforce run re-discovered scope with ad-hoc file reads. The root cause was an architectural gap: no pre-selection step between the static index and the enforce invocation.

## What Worked

- **Normalize at the boundary**: The assembler normalizes the LLM plan output at the entry boundary (`_coerce_context_plan`) before any file I/O, preventing downstream failures from type variation (dict vs Pydantic model vs JSON string).
- **Deterministic + bounded**: The `ast.parse()` signature extraction and `_enforce_budget()` truncation keep the assembled context predictable and auditable.
- **Contract test migration**: `test_enforce_simplify.py` was updated to reflect the new three-node shape — not left as a silent red test.
- **Pipeline evidence**: The `validate_fix` state confirmed a clean green (3719 passed) before handing off to `sanity_check`, giving high confidence in correctness.

## Minor Observation

`test_ac07_enforce_contract_tests_reflect_pre_node_architecture` validates the same node-set invariant as `test_ac03`. The intent of AC-07 was to confirm that `test_enforce_simplify.py` *itself* was updated — the new test accomplishes this indirectly (it would fail if the graph still had a single node), but it does not directly assert that the contract file was touched. This is a soft redundancy, not a gap.

## Seed

If the context assembler is invoked on every enforce run regardless of FR size, does the cost of a `gemini-2.0-flash` LLM call (latency + token cost) justify the orientation benefit for small FRs? Should the pre-node be conditional on FR scope tier, or should the lightweight planner always run?
