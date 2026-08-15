# Feature Request: Repair Subgraph Interrupt Propagation Under LangGraph 1.x

**Priority:** HIGH
**Type:** Bug
**Status:** Judged 2026-08-15 — APPROVED WITH REVISIONS (R-1..R-5 folded below)
**Effort:** 1–2 days
**Requested:** 2026-08-15
**First consumer / first event:** any graph using `type: subgraph` with an interrupt node in the child (`examples/demos/interrupt/interrupt-parent.yaml`, `interrupt-parent-redis.yaml`) — the first event is the next human-in-loop pipeline that expects the parent to pause on a child interrupt and instead silently runs to completion. Named forward demand: `projects/ninchat_voice/backlog.txt:48-58` plans a navigator router → active-subgraph architecture ("booking → type: subgraph, interrupt-based"; "questionnaire → type: subgraph, multi-turn") — the exact mechanism this FR repairs; ninchat_voice never adopted it precisely because FR-210 was rejected and the mechanism stayed broken. Cross-checked 2026-08-15: ninchat_voice today uses only top-level `type: interrupt` + `Command(resume)` (`actions/real/yamlgraph_async_action.py:95`) — untouched by this FR (C-3), so the consumer is unaffected by the fix and unblocked by it.

**Prior art:** FR-006 (original interrupt_output_mapping mechanism and the `except GraphInterrupt` design this FR replaces), FR-060 (two-phase interrupt nodes — payload-commit contract unaffected, reused as-is), FR-210 (REJECTED — dispositioned below per R-1), FR-624 (`ecf5beb4`, 2026-06-30 — the langgraph `>=1.2.0` floor bump that changed the interrupt contract; shipped with no integration-test evidence because CI runs `tests/unit` only), FR-717 (moved these tests during the compile-seam refactor; machinery untouched — ruled out by `git log`), `feature-requests/fix-subgraph-interrupt-output-mapping.md` (pending-writes-discarded evidence — addressed by C-2 witness).

### FR-210 disposition (R-1)

FR-210 attacked the same bug and was REJECTED because it bundled a two-node compiler split with router redirects, outgoing-edge rewrites, `compile_nodes` return-type changes, and dynamic pause-flag state (J-11..J-14 compiler surgery). FR-797 is not a resurrection of that plan: the relay design stays **inside the single subgraph node** — no synthetic nodes, no edge rewrites, no compiler signature changes — because LangGraph 1.x `interrupt()` provides in-node pause/resume that did not exist when FR-210 was drafted. Per-finding mapping:

| FR-210 finding | FR-797 treatment |
|---|---|
| J-1 (child resume missing — bare `invoke()` won't resume a paused child) | **Adopted.** Replay guard: `compiled_child.get_state(child_config)`; if `.next` is truthy, invoke with `Command(resume=...)`, never the original input (AC-05/AC-06). |
| J-2 (child checkpointer always `None`; child YAML `checkpointer:` loaded but never used) | **Adopted.** When the relay is active, child checkpointer is created from `subgraph_config` via `get_checkpointer_for_graph()` — see child checkpoint contract (R-3). |
| J-7 (`__interrupt__` marker path for non-checkpointed children) | **Superseded with fail-loud.** A checkpointer-less child that returns `__interrupt__` cannot be resumed; the node raises a clear `ValueError` instead of silently continuing (Commandment 6). No legacy marker path retained. |
| J-9 (`response_key` derivation undefined) | **Dissolved.** The pause payload is the child's `Interrupt.value` taken directly from `child_output["__interrupt__"][0]` — no state-key convention needed. |
| J-10 (`resume_key` derivation ambiguous) | **Dissolved.** The parent's resume value is relayed verbatim via `Command(resume=resume_value)` into the child — no state-key indirection, no `resume_key` config. |

## Summary

Child subgraph interrupts no longer pause the parent graph. Under LangGraph 1.x, a checkpointed child graph invoked imperatively **returns** `{'__interrupt__': [Interrupt(...)]}` from `invoke()` instead of **raising** `GraphInterrupt`. `yamlgraph/node_factory/subgraph_nodes.py` was built for the pre-1.x raising contract: its `except GraphInterrupt` branch is dead code, and its fallback — returning `__interrupt__` as a parent state update — is silently dropped by LangGraph (reserved key, not a state channel). The parent proceeds to the next node as if the child completed. No error is raised; `errors` stays empty. Three integration tests in `tests/integration/test_subgraph_interrupt.py` are RED, including `test_output_mapping_works_on_completion`, which passed before the bump — this is a regression, not the documented FR-006 limitation.

## Value Statement

Graph authors using human-in-loop subgraphs get back the core contract — a child interrupt pauses the parent and `Command(resume=...)` on the parent reaches the child — instead of a silent plausible-wrong-answer completion.

## Problem

Verified causal chain (repro run 2026-08-15, this session):

1. Child alone (`subgraphs/interrupt-child.yaml`, own `MemorySaver`): `invoke()` returns `__interrupt__: [Interrupt(value='What is your answer?', ...)]` in the output dict. **Nothing raises.** Child correctly pauses at `ask_user`; `finalize` never runs.
2. Parent run (`interrupt-parent.yaml`): `subgraph_node`'s normal-completion path detects `is_interrupted=True`, applies `interrupt_output_mapping` (`child_phase: processing` and `child_data` DO surface in the parent result — half the mechanism works), and returns `__interrupt__` in the node update dict.
3. LangGraph 1.x drops the reserved `__interrupt__` key from node updates without error. The parent continues to `done`; `final_result: "all done"` overwrites. Parent result has no `__interrupt__` key.
4. The paused child checkpoint is stranded under derived thread `"{parent_thread}:{node_name}"` (`_build_child_config`). `Command(resume=...)` on the parent resumes a parent that is not interrupted — the resume never reaches the child.
5. The `except GraphInterrupt` branch (FR-006's `__pregel_send` machinery) is unreachable under langgraph 1.2.x for checkpointed children — dead code.

Failure mode class: `plausible_wrong_answer` at a dependency boundary (`the_one_law`: the provider's contract changed; we never normalized at the seam). Gate blindness: CI runs `tests/unit` only, so the regression has been invisible since 2026-06-30.

## Ideal Result

A `type: subgraph` node under langgraph 1.x behaves exactly as FR-006 specified: when the child hits an interrupt, the mapped child state (`interrupt_output_mapping`) is committed to parent state **and** the parent genuinely pauses with the child's interrupt payload surfaced in the parent's `__interrupt__`; a single `Command(resume=...)` invoked on the parent flows into the paused child, the child completes, `output_mapping` applies, and the parent continues. The three RED integration tests pass unmodified, and a checkpointer-free unit witness guards the seam in CI.

## Proposed Solution

Rewrite the invoke-mode interrupt path in `yamlgraph/node_factory/subgraph_nodes.py` for the 1.x return-value contract (detect–commit–relay). **Chosen commit-before-pause mechanism (R-2): same-node `__pregel_send` writes before `interrupt()`** — no two-node split, no compiler changes.

```python
# replay guard (J-1): if child is already paused, skip the initial invoke
child_state = compiled_child.get_state(child_config) if child_has_checkpointer else None
if child_state and child_state.next:
    child_output = compiled_child.invoke(Command(resume=resume_value), child_config)
else:
    child_output = compiled_child.invoke(child_input, child_config)

if "__interrupt__" in child_output:
    if not child_has_checkpointer:
        raise ValueError(...)  # cannot resume a checkpointer-less child (J-7 fail-loud)
    payload = child_output["__interrupt__"][0].value
    # commit mapped child state to parent BEFORE pausing (FR-006 intent)
    send = config["configurable"]["__pregel_send"]
    send([(k, v) for k, v in _map_output_state(child_output, interrupt_output_mapping).items()])
    resume_value = interrupt(payload)          # pause the PARENT here
    child_output = compiled_child.invoke(Command(resume=resume_value), child_config)

return _map_output_state(child_output, output_mapping)
```

**C-2 gate (binding):** the first enforcement step is a witness test for the mechanism's load-bearing assumption — that `__pregel_send` writes made before `interrupt()` survive the pause and are visible in parent state under langgraph 1.2.x. Prior evidence from the pre-1.x era (`fix-subgraph-interrupt-output-mapping.md`, FR-210:80-87) says pending writes were discarded when interrupt control flow propagated; if the witness proves writes still do not survive under 1.x, STOP and return this FR for rejudgement with a two-node split design importing FR-210 J-11..J-14 constraints. No workaround improvisation.

**Child checkpoint contract (R-3):**

- `parent_checkpointer` at node-creation time is `None` in practice (FR-210 J-2); the child's own YAML `checkpointer:` config is currently loaded but never used. Fix: when the relay is active (child declares interrupt nodes or `interrupt_output_mapping` is configured), create the child checkpointer from `subgraph_config` via `get_checkpointer_for_graph(subgraph_config)` and pass it to `state_graph.compile(checkpointer=...)`. A configured `parent_checkpointer` (when the compile seam supplies one) takes precedence.
- No checkpointer available + child returns `__interrupt__` → raise `ValueError` with a message naming the child graph and the missing `checkpointer:` config. Explicit and tested (frozen AC-07).
- `get_state()` is called only when the child has a checkpointer; the call is guarded against mocks/fakes in unit tests per FR-210:316-334 (state check wrapped, not assumed).
- Child thread derivation (`{parent_thread}:{node_name}`, `_build_child_config`) is unchanged.

Other mechanics:

- Delete the dead `except GraphInterrupt` branch and the reserved-key-as-state-update path (Commandment 8; frozen AC-08). Any retained line requires cited necessity in this FR plus a direct regression test (C-5).
- `interrupt_output_mapping` semantics preserved exactly (parent sees `child_phase`/`child_data` while paused — this is what `test_get_state_can_access_child_state` and the FR-006 doc promise).
- `mode: direct` subgraphs (child compiled into parent, native propagation) are untouched (frozen AC-09).

## Acceptance Criteria (frozen by Judgement 2026-08-15)

- [x] AC-01: FR-797 amended with explicit FR-210 disposition and a single chosen commit-before-pause design before enforcement begins (this fold).
- [ ] AC-02: `tests/integration/test_subgraph_interrupt.py` passes unmodified in behavior: parent first invocation pauses with `"__interrupt__"` present, mapped `child_phase == "processing"` and `child_data == "partial result from child"` are visible, parent resume reaches the child, and the parent completes. (R-4 note: completion is proven by `final_result == "all done"` — the `done` node intentionally overwrites the `output_mapping` value in this fixture; no AC asserts an overwritten key.)
- [ ] AC-03: A unit test named for the seam, e.g. `test_subgraph_interrupt_relay_langgraph_1x`, proves a child `invoke()` returning `"__interrupt__"` causes a real parent `interrupt(payload)`, not a returned reserved state key.
- [ ] AC-04: A state-persistence witness proves mapped interrupt output is committed to parent state at the pause boundary, not only present in a transient result dict. (This is the C-2 gate witness — first enforcement step.)
- [ ] AC-05: A resume witness proves `invoke(Command(resume=...))` on the parent relays exactly once into the paused child and does not restart the child from scratch.
- [ ] AC-06: A replay-safety witness asserts the child pre-interrupt work executes once across pause/resume.
- [ ] AC-07: Child-checkpointer behavior is mechanically covered: configured child checkpointers are honored or parent checkpointer propagation is proven; no-checkpointer behavior is explicit and tested.
- [ ] AC-08: The dead `except GraphInterrupt` path and any reserved-key-as-state-update path are deleted, or every retained line is justified in the amended FR.
- [ ] AC-09: `mode: direct` subgraphs and subgraphs without `interrupt_output_mapping` retain existing behavior.
- [ ] AC-10: Existing valid interrupt demos are smoke-validated with an output log; the missing checkpointer-child demo (`interrupt-parent-with-checkpointer-child.yaml` references a child graph absent from the tree — R-5) is NOT counted as evidence until its child graph exists through an authorized route.
- [ ] AC-11: Changelog fragment uses `type: fix` with `REQ-YG-042`; diary entry records the boundary-contract lesson.

## Non-Goals

- Adding an integration-test lane to CI (real gap exposed here, but a separate infrastructure FR — this FR must not couple a bug fix to CI redesign).
- Changing streaming-mode subgraph behavior, `mode: direct`, or top-level interrupt flows (CLI resume loop, A2A) — all unaffected and out of scope.
- Upgrading the langgraph pin.

## Alternatives Considered

- **Native propagation (compile child with `checkpointer=True`, pass parent config unmodified):** LangGraph's sanctioned subgraph idiom; interrupts propagate to the parent automatically. Rejected as primary path because it abandons the derived-thread architecture (`{parent_thread}:{node_name}`) that `test_get_state_can_access_child_state`, the Redis demo, and independent child-state inspection depend on, and it changes checkpoint namespace layout for every existing subgraph user. Larger blast radius than the relay fix.
- **Raise `GraphInterrupt` manually from the node:** revives the old exception path, but under 1.x a hand-raised `GraphInterrupt` from inside a node is not the supported way to signal a dynamic interrupt and bypasses the resume-value plumbing that `interrupt()` provides.
- **Do nothing / document as limitation:** rejected — `test_output_mapping_works_on_completion` previously passed; this is a regression of shipped behavior, not a known limitation.

## Related

- `tests/integration/test_subgraph_interrupt.py` — the condemning RED suite
- `yamlgraph/node_factory/subgraph_nodes.py` — fix site
- `yamlgraph/node_factory/control_nodes.py` — FR-060 two-phase interrupt node (unchanged, contract reused)
- `capabilities/CAP-11-subgraph-map.yaml` — REQ-YG-042
- FR-624 / commit `ecf5beb4` — the breaking dependency bump
- `feature-requests/FR-210-subgraph-interrupt-state-commit.md` — rejected precedent, dispositioned above
- Repro evidence: session transcript 2026-08-15 (child-alone vs parent-run invoke outputs)

## Judgement (2026-08-15)

**Verdict:** APPROVED WITH REVISIONS — see `FR-797-subgraph-interrupt-propagation-langgraph-1x.judgement.md` for the full verdict, frozen scope (D-1..D-6), and revised acceptance criteria (adopted above).

Conditions for enforcement (binding gates):

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the FR before implementation authority activates. (Done — this revision.) | GATE |
| C-2 | The first enforcement step is a failing test proving current behavior does not commit mapped state; if `__pregel_send`-before-`interrupt()` writes do not survive under 1.x, return for rejudgement with a split design. | GATE |
| C-3 | Do not change dependency pins, CI topology, streaming semantics, `mode: direct`, or top-level interrupt behavior in this FR. | GATE |
| C-4 | Do not modify graph artifacts to make the demo smoke pass unless the graph-authoring route or a separate judged FR authorizes that artifact work. | GATE |
| C-5 | Any retained `GraphInterrupt` catch path or `__interrupt__` parent update must have a cited necessity in the amended FR and a direct regression test. | GATE |

Not authorized: LangGraph version changes; CI lane redesign; streaming-mode subgraph changes; `mode: direct` behavior changes; top-level interrupt/CLI/A2A resume-loop changes; FR-210's edge compiler/router rewrites unless rejudged; graph artifact creation or repair except through the graph-authoring route or a separate FR.
