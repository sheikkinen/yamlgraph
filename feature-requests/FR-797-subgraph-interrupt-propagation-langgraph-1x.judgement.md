# Judgement: FR-797 Repair Subgraph Interrupt Propagation Under LangGraph 1.x

**Superseded:** the C-2 gate fired during enforcement (single-node relay refuted by witness); the operative verdict is the **Rejudgement** section below.

**Prior art:** FR-006, FR-060 (`feature-requests/060-interrupt-set-response-before-pause.md`), FR-210 (`feature-requests/FR-210-subgraph-interrupt-state-commit.md`, REJECTED — dispositioned in R-1), FR-624, FR-717, `feature-requests/fix-subgraph-interrupt-output-mapping.md`.

**Verdict:** APPROVED WITH REVISIONS - the regression is real and the repair belongs in the subgraph primitive, but authority activates only after the FR replaces its ambiguous "writer or two-phase" design with a mechanically testable commit-before-pause contract and dispositions the omitted FR-210 precedent.

**Reviewed against:** `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md`; `feature-requests/FR-624-langgraph-floor-bump.md`; `feature-requests/FR-717-root-package-seams.md`; `feature-requests/060-interrupt-set-response-before-pause.md`; `feature-requests/FR-210-subgraph-interrupt-state-commit.md`; `feature-requests/fix-subgraph-interrupt-output-mapping.md`; `tests/integration/test_subgraph_interrupt.py`; `yamlgraph/node_factory/subgraph_nodes.py`; `yamlgraph/node_factory/control_nodes.py`; `capabilities/CAP-11-subgraph-map.yaml`; `ARCHITECTURE.md`; `pyproject.toml`; `examples/demos/interrupt/interrupt-parent.yaml`; `examples/demos/interrupt/subgraphs/interrupt-child.yaml`; `examples/demos/interrupt/interrupt-parent-redis.yaml`; `examples/demos/interrupt/interrupt-parent-with-checkpointer-child.yaml`; commit summary for `ecf5beb4`.

## What is sound

The problem is substantiated. `subgraph_nodes.py` still invokes the child, treats `"__interrupt__"` as a normal returned key, and returns that reserved key in the parent update (`yamlgraph/node_factory/subgraph_nodes.py:174-215`); the FR correctly identifies that this cannot make the parent pause under LangGraph 1.x (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:14`, `:24-28`). The cited dependency bump is real: `pyproject.toml` declares `langgraph>=1.2.0` and `ecf5beb4` bumped that floor under FR-624 (`feature-requests/FR-624-langgraph-floor-bump.md:31-50`).

The target surface is correct and minimal in principle. `REQ-YG-042` is the subgraph node requirement (`capabilities/CAP-11-subgraph-map.yaml:17-20`; `ARCHITECTURE.md:686-688`), and the fix site is the invoke-mode subgraph node rather than `mode: direct` or top-level interrupt handling (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:57-63`, `:74-79`). The FR also preserves the FR-060 two-phase interrupt-node contract instead of rewriting ordinary interrupt nodes (`feature-requests/060-interrupt-set-response-before-pause.md:39-47`; `yamlgraph/node_factory/control_nodes.py:17-95`).

The strategic classification is **Framework primitive**. Subgraph execution and interrupt flow are existing framework capabilities, not a single application workaround: the tests are tagged to routing/flow and subgraph requirements (`tests/integration/test_subgraph_interrupt.py:44-96`), and the cited demo graphs are framework examples (`examples/demos/interrupt/interrupt-parent.yaml:14-37`).

## Required revisions

### R-1: Disposition FR-210 explicitly before claiming a one-day relay fix

Add a prior-art section entry for `feature-requests/FR-210-subgraph-interrupt-state-commit.md` and state why FR-797 is not repeating the rejected monolithic plan. FR-210 rejected single-pass enforcement while keeping the underlying bug open (`feature-requests/FR-210-subgraph-interrupt-state-commit.md:18-33`) because the prior design bundled router redirects, resume semantics, child checkpointers, compiler return types, dynamic state, and outgoing-edge rewrites (`feature-requests/FR-210-subgraph-interrupt-state-commit.md:35-51`, `:53-71`). The revision must map FR-797's narrower design against at least FR-210 J-1, J-2, J-7, J-9, and J-10, or adopt those constraints directly.

### R-2: Replace the ambiguous commit-before-pause mechanism with one chosen mechanism

Remove "writer = config... or return via two-phase node split" and "decide in enforcement" from the proposed solution (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:46-60`). The FR must choose exactly one mechanism for committing `interrupt_output_mapping` before the parent pause:

1. If same-node `__pregel_send` is chosen, add a required RED witness proving that writes survive a subsequent `interrupt(payload)` under LangGraph 1.x. Prior evidence says pending writes are discarded when interrupt control flow propagates (`feature-requests/FR-210-subgraph-interrupt-state-commit.md:80-87`; `feature-requests/fix-subgraph-interrupt-output-mapping.md:20-29`, `:49-54`), so the FR cannot assume this path.
2. If a two-node split is chosen, scope it as the implementation and import the relevant FR-210 constraints instead of leaving it as an enforcement-time option.

### R-3: Specify the child checkpoint and replay contract

Define how the child graph is checkpointed and how `compiled_child.get_state(child_config)` is safe. Current code compiles the child with `parent_checkpointer`, which defaults to `None` at node creation (`yamlgraph/node_factory/subgraph_nodes.py:100-149`), and FR-210 already identified that missing child checkpointers make `get_state()`/resume impossible (`feature-requests/FR-210-subgraph-interrupt-state-commit.md:57-58`, `:312-314`). The revised FR must say whether child YAML `checkpointer` is honored, whether the parent runtime checkpointer is propagated, and what happens when no checkpointer exists. Add the `ValueError` guard and mock-safety concern from FR-210 as explicit test requirements if `get_state()` remains in the design (`feature-requests/FR-210-subgraph-interrupt-state-commit.md:316-334`).

### R-4: Repair the output-mapping acceptance ambiguity

AC-02 currently requires "extracted_data from `output_mapping`" in the parent result (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:67`), but the cited parent graph maps child `extracted_data` into parent `final_result`, and then the `done` node overwrites `final_result` with `"all done"` (`examples/demos/interrupt/interrupt-parent.yaml:20-29`). Revise AC-02 to assert the actual parent keys that prove completion, or add a dedicated fixture where `output_mapping` is not overwritten. Do not leave an assertion that the cited graph cannot satisfy.

### R-5: Gate the broken demo evidence instead of assuming it smokes

`interrupt-parent-with-checkpointer-child.yaml` points to `subgraphs/interrupt-child-with-checkpointer.yaml` (`examples/demos/interrupt/interrupt-parent-with-checkpointer-child.yaml:14-24`), but no such cited child file exists in the committed demo tree. Revise AC-06 to either remove this graph from the authorized smoke set or require a separate, properly routed graph-artifact repair before using it as evidence. FR-797 may validate existing demos; it must not silently expand into demo graph authoring.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/node_factory/subgraph_nodes.py` invoke-mode subgraph interrupt handling |
| D-2 | A CI-visible unit witness for the LangGraph 1.x return-value interrupt seam |
| D-3 | `tests/integration/test_subgraph_interrupt.py` passing with test intent preserved |
| D-4 | Existing valid `examples/demos/interrupt/` smoke evidence and output log, if no graph artifact repair is required |
| D-5 | `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md` updated with implementation status, design decisions, and deviations |
| D-6 | Changelog fragment and diary entry required by repo doctrine |

Not authorized: LangGraph version changes; CI lane redesign; streaming-mode subgraph changes; `mode: direct` behavior changes; top-level interrupt/CLI/A2A resume-loop changes; broad edge compiler/router rewrites from FR-210 unless the FR is revised and rejudged to include them; graph artifact creation or repair except through the repository's graph-authoring route or a separate FR.

## Revised acceptance criteria

- [ ] AC-01: FR-797 is amended with an explicit FR-210 disposition and a single chosen commit-before-pause design before enforcement begins.
- [ ] AC-02: `tests/integration/test_subgraph_interrupt.py` passes unmodified in behavior: parent first invocation pauses with `"__interrupt__"` present, mapped `child_phase == "processing"` and `child_data == "partial result from child"` are visible, parent resume reaches the child, and the parent completes.
- [ ] AC-03: A unit test named for the seam, e.g. `test_subgraph_interrupt_relay_langgraph_1x`, proves a child `invoke()` returning `"__interrupt__"` causes a real parent `interrupt(payload)`, not a returned reserved state key.
- [ ] AC-04: A state-persistence witness proves mapped interrupt output is committed to parent state at the pause boundary, not only present in a transient result dict.
- [ ] AC-05: A resume witness proves `invoke(Command(resume=...))` on the parent relays exactly once into the paused child and does not restart the child from scratch.
- [ ] AC-06: A replay-safety witness asserts the child pre-interrupt work executes once across pause/resume.
- [ ] AC-07: Child-checkpointer behavior is mechanically covered: configured child checkpointers are honored or parent checkpointer propagation is proven; no-checkpointer behavior is explicit and tested.
- [ ] AC-08: The dead `except GraphInterrupt` path and any reserved-key-as-state-update path are deleted, or every retained line is justified in the amended FR.
- [ ] AC-09: `mode: direct` subgraphs and subgraphs without `interrupt_output_mapping` retain existing behavior.
- [ ] AC-10: Existing valid interrupt demos are smoke-validated with an output log; the missing checkpointer-child demo is not counted as evidence until its child graph exists through an authorized route.
- [ ] AC-11: Changelog fragment uses `type: fix` with `REQ-YG-042`; diary entry records the boundary-contract lesson.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the FR before implementation authority activates. | GATE |
| C-2 | If the implementation depends on `__pregel_send` before `interrupt()`, the first enforcement step must be a failing test proving the current behavior does not commit mapped state; if the test cannot be made meaningful, return for rejudgement with a split design. | GATE |
| C-3 | Do not change dependency pins, CI topology, streaming semantics, `mode: direct`, or top-level interrupt behavior in this FR. | GATE |
| C-4 | Do not modify graph artifacts to make the demo smoke pass unless the graph-authoring route or a separate judged FR authorizes that artifact work. | GATE |
| C-5 | Any retained `GraphInterrupt` catch path or `__interrupt__` parent update must have a cited necessity in the amended FR and a direct regression test. | GATE |

Authority granted: after the revisions are folded into FR-797, enforcement may repair invoke-mode subgraph interrupt propagation under LangGraph 1.x within `subgraph_nodes.py` and add the narrow tests/logs needed to prove pause, mapped-state commit, resume relay, and replay safety.

---

# Rejudgement (2026-08-15, after C-2 return): FR-797 Repair Subgraph Interrupt Propagation Under LangGraph 1.x

**Verdict:** APPROVED WITH REVISIONS — the two-node split is the right repair after C-2 refuted the single-node relay, but authority activates only after the FR resolves the relay scope contradiction, names the compiler/state surfaces precisely, and makes the demo/checkpointer evidence mechanically testable.

**Reviewed against:** `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md`; `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.judgement.md`; `feature-requests/FR-210-subgraph-interrupt-state-commit.md`; `feature-requests/fix-subgraph-interrupt-output-mapping.md`; `feature-requests/060-interrupt-set-response-before-pause.md`; `feature-requests/FR-624-langgraph-floor-bump.md`; `feature-requests/FR-717-root-package-seams.md`; `tests/integration/test_subgraph_interrupt.py`; `tests/unit/test_fr797_subgraph_interrupt_seam.py`; `yamlgraph/node_factory/subgraph_nodes.py`; `yamlgraph/node_factory/control_nodes.py`; `yamlgraph/compile/node_compiler.py`; `yamlgraph/compile/edge_compiler.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/models/state_builder.py`; `yamlgraph/storage/checkpointer_factory.py`; `yamlgraph/linter/patterns/interrupt.py`; `capabilities/CAP-11-subgraph-map.yaml`; `pyproject.toml`; `examples/demos/interrupt/interrupt-parent.yaml`; `examples/demos/interrupt/interrupt-parent-redis.yaml`; `examples/demos/interrupt/interrupt-parent-with-checkpointer-child.yaml`; `examples/demos/interrupt/subgraphs/interrupt-child.yaml`.

## What is sound

The C-2 return is substantive, not procedural churn. The FR records that pre-interrupt `__pregel_send` writes surface transiently but do not commit to checkpointed state (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:48-57`), and that evidence is now captured in unit witnesses (`tests/unit/test_fr797_subgraph_interrupt_seam.py:57-101`). That directly answers the previous judgement's gate and justifies abandoning the single-node relay.

The selected direction aligns with an existing framework pattern. FR-060 already established the commit-before-pause two-node split for ordinary interrupt nodes (`feature-requests/060-interrupt-set-response-before-pause.md:33-47`), and the current implementation embodies that as prepare plus interrupt functions (`yamlgraph/node_factory/control_nodes.py:17-95`). Applying the same shape to invoke-mode subgraphs is architecture-aligned because the current subgraph node still invokes the child and returns a reserved `__interrupt__` key as a parent update (`yamlgraph/node_factory/subgraph_nodes.py:174-215`), which is exactly the boundary failure FR-797 describes (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:34-42`).

The prior-art handling is materially improved. FR-210 rejected a monolithic implementation while keeping the bug open (`feature-requests/FR-210-subgraph-interrupt-state-commit.md:18-33`), and the amended FR now maps the relevant FR-210 findings into the new design (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:12-23`, `:61-82`). The strategic classification remains **Framework primitive**: the affected capability is `REQ-YG-042` subgraph node creation (`capabilities/CAP-11-subgraph-map.yaml:17-20`), not a one-off application workaround.

## Required revisions

### R-1: Resolve the relay-capable scope contradiction

Rewrite the proposed scope so it has one contract. The FR currently says relay-capable nodes are `mode: invoke` plus either `interrupt_output_mapping` or a child graph declaring a `type: interrupt` node (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:61`), but AC-09 says subgraphs without `interrupt_output_mapping` retain existing behavior (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:106`). Fold this as: invoke-mode child graphs that can interrupt are deliberately changed to pause/resume through the parent; invoke-mode child graphs that cannot interrupt, plus `mode: direct`, retain existing behavior. Add a no-`interrupt_output_mapping` child-interrupt witness if that broadened behavior remains authorized.

### R-2: Name the compiler API changes accurately

Correct the implementation description around compiler rails. `build_router_route_mapping()` and `_add_conditional_edges()` already accept `subgraph_interrupt_nodes` (`yamlgraph/compile/edge_compiler.py:150-168`, `:324-373`), but `_process_edge()` and `_EdgeContext` do not (`yamlgraph/compile/edge_compiler.py:96-109`, `:259-267`), and `graph_loader` currently destructures only `(map_nodes, interrupt_nodes)` and passes only `interrupt_nodes` into edge processing (`yamlgraph/compile/graph_loader.py:324-354`; `yamlgraph/compile/node_compiler.py:393-435`). Revise the FR to state the exact API delta: `compile_nodes()` returns `(map_nodes, interrupt_nodes, subgraph_interrupt_nodes)`, `graph_loader` passes that set to `_process_edge()` and `_add_conditional_edges()`, and `_process_edge()` performs the subgraph incoming/outgoing rewrite before ordinary edge-shape dispatch.

### R-3: Make outgoing-edge restrictions a tested gate

Move the Phase-1 outgoing-edge constraint from prose into acceptance criteria. The FR says outgoing edges from relay-capable subgraph nodes must be simple and that graph lint errors on `condition` or `type: conditional` (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:74-77`), but no AC requires a linter/compiler test. Add a specific AC requiring an error for conditional outgoing edges from relay-capable subgraph nodes and a positive witness for the simple `run_child -> done` demo edge (`examples/demos/interrupt/interrupt-parent.yaml:31-37`).

### R-4: Specify state plumbing and codegen witnesses

The FR requires `state_builder` to synthesize `__{name}_paused__`, `__{name}_payload__`, and `__{name}_resume__` (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:79`), but current state extraction only adds declared state, data files, node `state_key`, and a few node-type fields (`yamlgraph/models/state_builder.py:168-255`), while codegen has its own field extraction path (`yamlgraph/models/state_builder.py:341-438`). Add an AC that proves both runtime `build_state_class()` and generated TypedDict code include the relay fields for relay-capable subgraph nodes and exclude them for non-relay subgraphs.

### R-5: Add a multi-interrupt resume-cycle witness

The loop-back edge is load-bearing, and the FR itself notes `{name}__run` must execute once per pause cycle without tripping loop protection (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:79`). AC-05/AC-06 currently prove only one resume cycle (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:102-103`; `tests/unit/test_fr797_subgraph_interrupt_seam.py:146-160`). Add a witness with a child that interrupts twice, commits mapped state at both pause boundaries, relays two parent `Command(resume=...)` values, and does not restart pre-interrupt work.

### R-6: Repair the demo-evidence inventory without authoring graph artifacts

Update AC-10 to enumerate which demos are valid evidence and which are excluded. `interrupt-parent-with-checkpointer-child.yaml` references a missing `subgraphs/interrupt-child-with-checkpointer.yaml` (`examples/demos/interrupt/interrupt-parent-with-checkpointer-child.yaml:14-24`), and `interrupt-parent-redis.yaml` references a missing `subgraphs/interrupt-child-with-checkpointer-redis.yaml` (`examples/demos/interrupt/interrupt-parent-redis.yaml:17-27`). The only committed child graph under the interrupt demo tree is `subgraphs/interrupt-child.yaml`; do not count either broken parent as smoke evidence unless graph-authoring or a separate judged FR repairs the artifacts.

### R-7: Make checkpointer defaults explicit by persistence class

The amended FR says relay-capable children default to in-process `MemorySaver` when parent and child checkpointers are absent (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:81`), while the factory returns `None` for absent config and concrete savers only for configured graphs (`yamlgraph/storage/checkpointer_factory.py:36-123`; `yamlgraph/compile/graph_loader.py:400-414`). Fold the intended persistence contract into the FR: configured child checkpointers are honored; absent child checkpointer gets MemorySaver only for in-process relay tests and non-durable runs; Redis/SQLite persistence is not claimed unless the child graph declares that checkpointer. Add tests for configured child checkpointer, default MemorySaver, and fail-loud behavior when an interrupt is detected but no resumable checkpointer can exist.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/node_factory/subgraph_nodes.py` invoke-mode relay run/pause functions and deletion of the dead `GraphInterrupt`/reserved-key parent-update path |
| D-2 | `yamlgraph/compile/node_compiler.py` split-node registration and `subgraph_interrupt_nodes` return value |
| D-3 | `yamlgraph/compile/edge_compiler.py` incoming redirect, outgoing simple-edge transformation, router route mapping, loop-back wiring, and conditional-outgoing rejection |
| D-4 | `yamlgraph/compile/graph_loader.py` threading of `subgraph_interrupt_nodes` through edge processing |
| D-5 | `yamlgraph/models/state_builder.py` runtime and codegen relay-state fields |
| D-6 | Unit/integration witnesses for LangGraph 1.x pause boundary, parent pause, mapped-state commit, resume relay, replay safety, multi-interrupt cycles, and unaffected non-relay/direct subgraphs |
| D-7 | Valid existing interrupt demo smoke logs only; broken demo artifact repair is excluded |
| D-8 | `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md` amended with implementation status, final design decisions, and deviations |
| D-9 | Changelog fragment and diary entry required by repo doctrine |

Not authorized: LangGraph version changes; CI topology changes; streaming-mode subgraph changes; top-level interrupt/CLI/A2A resume-loop changes; conditional outgoing-edge support for relay-capable subgraphs beyond a compile/lint rejection; graph artifact creation or repair except through the graph-authoring route or a separate judged FR; generalized subgraph inlining or FR-049-style expansion.

## Revised acceptance criteria

- [ ] AC-01: FR-797 folds R-1 through R-7 before enforcement authority activates.
- [ ] AC-02: `tests/integration/test_subgraph_interrupt.py` passes with intent preserved: first parent invocation pauses with `__interrupt__`, mapped `child_phase == "processing"` and `child_data == "partial result from child"` are visible and committed at the parent pause boundary, parent resume reaches the child, and completion reaches `final_result == "all done"`.
- [ ] AC-03: A seam unit test proves a child `invoke()` returning `__interrupt__` causes a real parent `interrupt(payload)`, not a returned reserved state key.
- [ ] AC-04: A state-persistence witness proves mapped interrupt output is committed to parent `get_state().values` at the pause boundary, not only present in a transient result dict.
- [ ] AC-05: A resume witness proves parent `Command(resume=...)` relays exactly once into the paused child and does not restart pre-interrupt work.
- [ ] AC-06: A multi-interrupt child witness proves two parent pause/resume cycles commit mapped state at both boundaries and preserve replay safety.
- [ ] AC-07: Child-checkpointer behavior is mechanically covered for configured child checkpointer, default in-process MemorySaver, and fail-loud non-resumable interrupt cases.
- [ ] AC-08: Runtime state construction and generated TypedDict code include relay internal fields for relay-capable subgraph nodes and exclude them for non-relay subgraphs.
- [ ] AC-09: `mode: direct` subgraphs and invoke-mode child graphs that cannot interrupt retain existing behavior; invoke-mode child graphs that can interrupt are covered by explicit pause/resume tests whether or not `interrupt_output_mapping` is configured.
- [ ] AC-10: Conditional outgoing edges from relay-capable subgraph nodes fail at lint or compile time; a simple outgoing edge from the relay node routes paused -> pause node and complete -> original target.
- [ ] AC-11: The dead `except GraphInterrupt` path and any reserved-key-as-parent-update path are deleted, or every retained line is justified in the amended FR and covered by a direct regression test.
- [ ] AC-12: Only valid existing interrupt demos are smoke-validated with output logs; `interrupt-parent-with-checkpointer-child.yaml` and `interrupt-parent-redis.yaml` are excluded until their missing child graphs are repaired through an authorized route.
- [ ] AC-13: Changelog fragment uses `type: fix` with `REQ-YG-042`; diary entry records the boundary-contract lesson.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-7 into the FR before implementation authority activates. | GATE |
| C-2 | Do not implement a single-node relay or any mechanism that depends on pre-interrupt pending writes committing; the C-2 witnesses are binding unless a failing witness proves LangGraph changed the seam. | GATE |
| C-3 | Do not change dependency pins, CI topology, streaming semantics, `mode: direct`, or top-level interrupt behavior in this FR. | GATE |
| C-4 | Do not modify graph artifacts or create missing demo children unless the graph-authoring route or a separate judged FR authorizes that artifact work. | GATE |
| C-5 | Reject, rather than partially support, conditional outgoing edges from relay-capable subgraph nodes in this phase. | GATE |
| C-6 | Any retained `GraphInterrupt` catch path or `__interrupt__` parent update must have a cited necessity in the amended FR and a direct regression test. | GATE |

Authority granted: after the required revisions are folded, enforcement may build the invoke-mode subgraph two-node relay across the named node factory, compiler, edge, state-builder, and test surfaces, solely to restore LangGraph 1.x child-interrupt pause/resume propagation and mapped-state commit.
