# Judgement: FR-797 Repair Subgraph Interrupt Propagation Under LangGraph 1.x

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
