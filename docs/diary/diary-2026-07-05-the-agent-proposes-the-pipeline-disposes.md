# The Agent Proposes, the Pipeline Disposes

**Date:** 2026-07-05
**FRs:** FR-658 (graph-as-tool), FR-688 (variables injection), FR-689 (integrated dedup)
**Trap:** `composition_bug` — every component passes its unit test but the system fails
**Cure:** `constraint_over_code` — the constraint is irreplaceable, the code is regenerable

## The Observation

Closing FR-658 (graph-as-tool) and FR-688 (CLI variables injection) revealed a pattern worth naming: **authority without privilege.**

FR-658 created the `type: graph` tool — a YAML pipeline the agent sees as an opaque function call. Before it, novel_fandom's composition options were:

| Option | Problem |
|---|---|
| Python tool | Dedup/validation is either absent or monolithic |
| Subgraph node | Agent doesn't choose when to call; graph routes to it |
| Separate tools | Agent must remember to call `dedup_check` before `create_*` |

Each fails the same test: who enforces the constraint? With Python tools, the developer does (if they remember). With subgraphs, the topology does (but the agent loses control). With separate tools, the agent does (and it forgets).

FR-658's graph-tool creates a fourth option: the agent has *authority* (it decides what to create) but not *privilege* (it cannot bypass the dedup gate). The tool IS the pipeline. The pipeline IS the constraint. The agent calls `create_character(id="hilde")` and the 4-node sub-pipeline decides whether that request survives.

## The Composition Matrix

The novel_fandom architecture landed on three layers:

```
Agent node (genesis.yaml)     → plans entity creation order
Graph-tools (create_*.yaml)   → enforces dedup + integrity per entity
Python node (final_gate)      → cross-canon consistency at the end
```

Each layer has a different enforcement model:
- The agent *persuades* (via prompt) — probabilistic
- The graph-tool *blocks* (via dedup_pre_check) — deterministic
- The final_gate *audits* (via filesystem scan) — deterministic

The insight: the middle layer is the one that didn't exist before FR-658. Without it, the only options were probabilistic persuasion or post-hoc auditing. Mechanical prevention at the moment of creation required a tool that was secretly a pipeline.

## The Variables Bug as Proof

FR-688/FR-689's variables injection bug was the `composition_bug` trap in its purest form. Every component worked:

- `make_graph_tool_fn()` accepted `default_variables` — tested ✅
- `create_character.yaml` declared `variables: entity_type: character` — valid ✅
- `dedup_pre_check` node read `entity_type` from state — correct ✅
- `_parse_graph_tools()` compiled child graphs — working ✅

The defect: `_parse_graph_tools()` never passed `default_variables` to `make_graph_tool_fn()`. One missing keyword argument. The function signature was ready, the caller didn't use it. The test for the function passed because it supplied the argument directly. The integration never exercised the callsite.

This is why the `composition_bug` trap exists in Scripture: "the defect is in the policy connecting correct parts, not in the parts."

## Heuristic

**Authority without privilege is the only agent safety model that scales.** Advisory constraints ("always check for duplicates") fail because the agent optimizes for completion, not compliance. Post-hoc constraints ("final_gate catches violations") fail because they require rollback. Inline constraints ("the tool IS the pipeline") succeed because the agent cannot express a request that bypasses the gate. The request goes through the gate or it doesn't go at all.

This is the `normalize_at_boundary` law applied to agent architecture: the boundary is the tool interface, and the normalization is the pipeline that sits behind it.

## Seed

FR-658 proved graph-as-tool for creation pipelines with simple input→output contracts. What happens when the graph-tool needs to return structured data back to the agent — not just "Created character hilde" but the full entity with cross-references resolved? The current contract stringifies the output (`str(result.get(ok, result))`). A richer return channel would let the agent reason about what the pipeline produced, not just whether it succeeded. Is that a feature or a temptation to over-engineer?
