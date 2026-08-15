# Feature Request: Repair Subgraph Interrupt Propagation Under LangGraph 1.x

**Priority:** HIGH
**Type:** Bug
**Status:** Judged 2026-08-15 (rejudged after C-2 return) — APPROVED WITH REVISIONS; R-1..R-7 of the rejudgement folded below, enforcement authority active
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

## C-2 Gate Evidence (2026-08-15 — gate FIRED)

First enforcement step executed per judgement C-2, langgraph 1.2.9. Probes (session transcript) mechanized as permanent witnesses in `tests/unit/test_fr797_subgraph_interrupt_seam.py`:

1. `__pregel_send([("committed", ...)])` before `interrupt()` in a checkpointed single-node graph: the write **surfaces in the paused `invoke()` result** and in the post-resume result (deterministic replay re-executes the node and re-sends it).
2. But it is **never committed**: `get_state().values` at the pause is `{}` — identically under `durability="sync"|"async"|"exit"`.
3. A `put_writes` spy on `MemorySaver` shows only `__interrupt__` reaches the checkpointer; the sent tuple never arrives.
4. This matches the pre-1.x evidence the judge cited (`fix-subgraph-interrupt-output-mapping.md`: "state.values stays None" for the `interrupt()` approach; FR-210:80-87): 1.x added result-surfacing of pending task writes but not persistence.

Verdict per the binding gate: the load-bearing assumption is false. AC-04 ("committed to parent state at the pause boundary, not only present in a transient result dict") cannot be satisfied by any single-node relay — the motivating consumer (an FSM reading `get_state()` while paused, `fix-subgraph-interrupt-output-mapping.md`) reads exactly the surface that stays empty. STOP honored; no workaround improvised. Witness suite shape: 2 boundary-contract tests GREEN (pin the refutation; alarm if a langgraph upgrade changes the seam), 3 condemning tests RED until the fix lands. FR-060's own interrupt node (`control_nodes.py:create_interrupt_node`) already embodies the conclusion: commit-before-pause requires a node boundary between the commit and the `interrupt()`.

## Proposed Solution (revised after C-2 gate)

**Chosen mechanism (replaces the refuted single-node relay): compile-time two-node split**, the FR-060 pattern applied to subgraph nodes, importing FR-210 J-11..J-15 mitigations.

**Relay scope contract (rejudgement R-1, one contract):** invoke-mode subgraph nodes whose child graph **can interrupt** (child declares a `type: interrupt` node OR `interrupt_output_mapping` is configured on the node) are deliberately changed to pause/resume through the parent — whether or not `interrupt_output_mapping` is configured (a no-mapping child-interrupt witness covers the broadened path). Invoke-mode children that cannot interrupt, and all `mode: direct` subgraphs, retain existing behavior exactly.

Per relay-capable node `{name}`, `node_compiler` emits two parent nodes:

- **`{name}__run`** — invokes or resumes the child; always returns normally, so every update is committed by construction (this is the sanctioned path the boundary-contract witness pins):
  - Replay guard (J-1): if the child checkpoint is paused (`get_state(child_config).next` truthy, call guarded for mocks per FR-210:316-334) → `invoke(Command(resume=state["__{name}_resume__"]), child_config)`; else → `invoke(child_input, child_config)`.
  - Child output contains `__interrupt__` → return mapped `interrupt_output_mapping` updates + `__{name}_paused__: True` + `__{name}_payload__: child_output["__interrupt__"][0].value` (J-9 dissolved as before: payload is the child's `Interrupt.value`).
  - Child completed → return mapped `output_mapping` updates + `__{name}_paused__: False`.
  - Checkpointer-less child returning `__interrupt__` → `ValueError` naming the child graph and the missing `checkpointer:` config (J-7 fail-loud, frozen AC-07).
- **`{name}__pause`** — mirrors FR-060's `interrupt_fn`: reads `__{name}_payload__` from committed state, `resume = interrupt(payload)`, returns `{"__{name}_resume__": resume}`.

Edges (`edge_compiler` — the FR-211 rails already exist and are currently dead: `build_router_route_mapping` and `_add_conditional_edges` already accept `subgraph_interrupt_nodes` and redirect to `*__run`; no call site populates the set yet):

- Incoming edges to `{name}` redirect to `{name}__run` — string/START/expression edges by rewrite, router edges via the existing `route_mapping` branch (J-14 mitigation is already in code; original names remain router labels).
- The outgoing edge from `{name}` becomes a conditional keyed on `__{name}_paused__` (J-12): `True` → `{name}__pause`, `False` → original target. Plus the loop-back edge `{name}__pause` → `{name}__run` that relays the resume into the child.
- Phase-1 scope constraint (J-13/J-15, adopted; rejudgement R-3 makes it a tested gate — AC-10): outgoing edges from relay-capable subgraph nodes must be simple — no `condition`, no `type: conditional`; lint/compile errors otherwise, and the check sits before all edge-type handling. The demo fixture complies (`run_child → done`).
- Exact compiler API delta (rejudgement R-2): `compile_nodes()` returns `(map_nodes, interrupt_nodes, subgraph_interrupt_nodes)`; `graph_loader` passes the new set to `_process_edge()` and `_add_conditional_edges()`; `_process_edge()` and `_EdgeContext` gain the `subgraph_interrupt_nodes` parameter and perform the subgraph incoming/outgoing rewrite **before** ordinary edge-shape dispatch (J-15 position). `build_router_route_mapping()` and `_add_conditional_edges()` already accept the set (FR-211 rails, currently dead — no call site populates it).

State plumbing (rejudgement R-4): `state_builder` synthesizes `__{name}_paused__: bool`, `__{name}_payload__: Any`, `__{name}_resume__: Any` per relay-capable subgraph node — in BOTH the runtime `build_state_class()` path and the codegen TypedDict path; witnesses prove inclusion for relay-capable nodes and exclusion for non-relay subgraphs (AC-08). FR-210's dynamic pause-flag state is accepted here as the irreducible price of commit-before-pause (C-2 evidence closes the cheaper route). Loop-protection note: `{name}__run` legitimately executes once per pause cycle; the loop-back edge must not trip `check_loop_limit` for multi-interrupt children (multi-interrupt witness — AC-06, rejudgement R-5).

**Child checkpoint contract (rejudgement R-7, persistence made explicit by class):** precedence stays `parent_checkpointer` → child YAML `checkpointer:` via `get_checkpointer_for_graph(subgraph_config)` (configured child checkpointers are honored — Redis/SQLite persistence is claimed ONLY when the child graph declares that checkpointer). When the node is relay-capable and both are absent, default to an in-process `MemorySaver` — non-durable, in-process relay only; `get_checkpointer(None)` returns `None`, and without this default the AC-02 fixture (`interrupt-child.yaml` declares no `checkpointer:`) could only pass by editing the graph artifact, which C-4 forbids. Non-relay-capable children keep today's behavior (no checkpointer). Fail-loud: a child that interrupts without a resumable checkpointer (e.g. a python node calling `interrupt()` in a child that is not relay-capable by detection) → `ValueError` naming the child graph and the missing `checkpointer:` config. All three cases tested (AC-07).

**Demo evidence inventory (rejudgement R-6):** the ONLY committed child graph under the interrupt demo tree is `subgraphs/interrupt-child.yaml`; the sole valid smoke evidence is `interrupt-parent.yaml`. Excluded until their missing child graphs are repaired through an authorized route: `interrupt-parent-with-checkpointer-child.yaml` (references missing `subgraphs/interrupt-child-with-checkpointer.yaml`) and `interrupt-parent-redis.yaml` (references missing `subgraphs/interrupt-child-with-checkpointer-redis.yaml`).

Retained R-3 mechanics (unchanged by the revision):

- `get_state()` is called only when the child has a checkpointer; the call is guarded against mocks/fakes in unit tests per FR-210:316-334 (state check wrapped, not assumed).
- Child thread derivation (`{parent_thread}:{node_name}`, `_build_child_config`) is unchanged.

Other mechanics:

- Delete the dead `except GraphInterrupt` branch and the reserved-key-as-state-update path (Commandment 8; frozen AC-08). Any retained line requires cited necessity in this FR plus a direct regression test (C-5).
- `interrupt_output_mapping` semantics preserved exactly (parent sees `child_phase`/`child_data` while paused — this is what `test_get_state_can_access_child_state` and the FR-006 doc promise).
- `mode: direct` subgraphs (child compiled into parent, native propagation) are untouched (frozen AC-09).

## Acceptance Criteria (frozen by Rejudgement 2026-08-15)

- [x] AC-01: FR-797 folds R-1 through R-7 before enforcement authority activates. (This fold.)
- [ ] AC-02: `tests/integration/test_subgraph_interrupt.py` passes with intent preserved: first parent invocation pauses with `__interrupt__`, mapped `child_phase == "processing"` and `child_data == "partial result from child"` are visible and committed at the parent pause boundary, parent resume reaches the child, and completion reaches `final_result == "all done"`.
- [ ] AC-03: A seam unit test proves a child `invoke()` returning `__interrupt__` causes a real parent `interrupt(payload)`, not a returned reserved state key.
- [ ] AC-04: A state-persistence witness proves mapped interrupt output is committed to parent `get_state().values` at the pause boundary, not only present in a transient result dict.
- [ ] AC-05: A resume witness proves parent `Command(resume=...)` relays exactly once into the paused child and does not restart pre-interrupt work.
- [ ] AC-06: A multi-interrupt child witness proves two parent pause/resume cycles commit mapped state at both boundaries and preserve replay safety.
- [ ] AC-07: Child-checkpointer behavior is mechanically covered for configured child checkpointer, default in-process MemorySaver, and fail-loud non-resumable interrupt cases.
- [ ] AC-08: Runtime state construction and generated TypedDict code include relay internal fields for relay-capable subgraph nodes and exclude them for non-relay subgraphs.
- [ ] AC-09: `mode: direct` subgraphs and invoke-mode child graphs that cannot interrupt retain existing behavior; invoke-mode child graphs that can interrupt are covered by explicit pause/resume tests whether or not `interrupt_output_mapping` is configured.
- [ ] AC-10: Conditional outgoing edges from relay-capable subgraph nodes fail at lint or compile time; a simple outgoing edge from the relay node routes paused → pause node and complete → original target.
- [ ] AC-11: The dead `except GraphInterrupt` path and any reserved-key-as-parent-update path are deleted, or every retained line is justified in the amended FR and covered by a direct regression test.
- [ ] AC-12: Only valid existing interrupt demos are smoke-validated with output logs; `interrupt-parent-with-checkpointer-child.yaml` and `interrupt-parent-redis.yaml` are excluded until their missing child graphs are repaired through an authorized route.
- [ ] AC-13: Changelog fragment uses `type: fix` with `REQ-YG-042`; diary entry records the boundary-contract lesson.

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

**C-2 return (2026-08-15):** enforcement executed the C-2 gate as its first step; the gate FIRED (see C-2 Gate Evidence). Per the gate's own protocol the FR was returned for rejudgement with the two-node split design importing FR-210 J-11..J-15.

**Rejudgement (2026-08-15, via `scripts/judge.sh`):** APPROVED WITH REVISIONS — R-1..R-7 folded above; frozen scope D-1..D-9 and conditions C-1..C-6 per the Rejudgement section of the judgement file. Enforcement authority active.

Conditions for enforcement (binding gates):

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the FR before implementation authority activates. (Done — this revision.) | GATE |
| C-2 | The first enforcement step is a failing test proving current behavior does not commit mapped state; if `__pregel_send`-before-`interrupt()` writes do not survive under 1.x, return for rejudgement with a split design. | GATE |
| C-3 | Do not change dependency pins, CI topology, streaming semantics, `mode: direct`, or top-level interrupt behavior in this FR. | GATE |
| C-4 | Do not modify graph artifacts to make the demo smoke pass unless the graph-authoring route or a separate judged FR authorizes that artifact work. | GATE |
| C-5 | Any retained `GraphInterrupt` catch path or `__interrupt__` parent update must have a cited necessity in the amended FR and a direct regression test. | GATE |

Not authorized: LangGraph version changes; CI lane redesign; streaming-mode subgraph changes; `mode: direct` behavior changes; top-level interrupt/CLI/A2A resume-loop changes; FR-210's edge compiler/router rewrites unless rejudged; graph artifact creation or repair except through the graph-authoring route or a separate FR.
