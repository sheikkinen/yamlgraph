# Feature Request: Map-to-map chaining must deliver true per-branch _map_index

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS (R-1–R-4 folded 2026-08-31); see [FR-944-map-to-map-index-attribution.judgement.md](FR-944-map-to-map-index-attribution.judgement.md)
**Effort:** 0.5 days
**Requested:** 2026-08-31
**First consumer / first event:** the FR-943 corpus_census containment layer, at the next `yamlgraph graph run examples/demos/corpus_census/graph.yaml` over tmp/sparks-full batches 01–04 — currently batch-fatal in all four because a poison row's error finding claims index 0 instead of its true index.
**Research:** [FR-944.research.md](FR-944.research.md)
**Prior art:** [FR-718-edge-compiler-decomposition.md](FR-718-edge-compiler-decomposition.md) — named MAP_TO_MAP as an EdgeShape and preserved its semantics verbatim; this FR corrects those semantics, not the classification. [FR-467-conditional-edge-to-map-node.md](FR-467-conditional-edge-to-map-node.md) — routed conditional edges *to* maps; explicitly left `_handle_map_to_map_edge` unchanged. [FR-936-map-node-hardening.md](FR-936-map-node-hardening.md) — hardened single-map fan-out; did not touch chaining. [FR-943-census-row-failure-containment.md](FR-943-census-row-failure-containment.md) — the consumer that exposed this defect; its frozen contract is a regression gate here, not a change target. Research-retrieved hits (FR-260, FR-488, FR-611, FR-612, FR-614): FR-260 is cited as gate discipline precedent by two personas; the roundtrip-skeleton FRs (488/611/612/614) share only brief vocabulary, no map-semantics overlap — dismissed.

## Summary

When two `type: map` nodes are chained, the edge compiler attaches the second map's fan-out function to the **first map's sub-node**, so it fires once per upstream branch on task-local state where the collected list has exactly one element. `enumerate` yields `i=0` in every branch: every second-map Send carries `_map_index: 0`. Fan-in ordering (`sorted_add`) becomes race-timing arbitrary and error-row attribution collapses to index 0.

## Value Statement

Graph authors chaining maps get true row identity end-to-end: deterministic fan-in order and correct error attribution, unblocking the FR-943 census containment live run.

## Problem

`_compile_map_to_map` ([edge_compiler.py](../yamlgraph/compile/edge_compiler.py) L221–224):

```python
def _compile_map_to_map(ctx: _EdgeContext) -> None:
    _, from_sub = ctx.map_nodes[ctx.from_node]
    to_map_edge_fn, to_sub = ctx.map_nodes[ctx.to_node]
    ctx.graph.add_conditional_edges(from_sub, to_map_edge_fn, [to_sub])
```

Conditional edges attached to a Send sub-node execute **per task**, with that task's local state view. The second map's `over: "{state.collected}"` therefore resolves to a one-item list inside each branch, and `Send(sub, {**state, item_var: item, "_map_index": i})` ([map_compiler.py](../yamlgraph/compile/map_compiler.py) L364) always sends `i=0`.

**Empirical proof** (LLM-free, two chained python-tool maps over 3 items — durable form committed as tests/unit/test_fr944_map_to_map_index.py; the transient session repro under tmp/ is context only):

```
firsts:  [{_map_index: 0}, {_map_index: 1}, {_map_index: 2}]   ← first map correct
seconds: [{_map_index: 0}, {_map_index: 0}, {_map_index: 0}]   ← all zero
```

**Live incident (2026-08-31, transient context — not acceptance evidence):** all 4 corpus_census batch reruns failed with `duplicate finding for item index 0`. tmp/census-debug-findings.json: `Counter(_map_index) == {0: 200}` while the model-echoed `source_index` was unique and correct — the census only ever worked because the prompt smuggled the true index through the LLM. The poison row at index 178 emitted an `_error` finding attributed to index 0, colliding with the genuine index-0 finding — batch-fatal under the frozen FR-943 duplicate contract (logs/fr943-census-rerun.log).

**Blast radius beyond FR-943:**
1. `sorted_add` ([state_builder.py](../yamlgraph/models/state_builder.py) L38–57) sorts fan-in by `_map_index`; all-zeros makes chained-map output order silently nondeterministic.
2. Per-branch fan-out is also semantically wrong when the second map's `over` is NOT the first map's collect output: each of N branches fans out over the full other list → N×M duplicate Sends.
3. No runtime test covers chained-map execution; only shape classification is tested (tests/unit/test_fr718_edge_shapes.py).

## Ideal Result

`map1 → map2` behaves exactly like `map1 → node → map2`: the second fan-out fires once, on the merged state after the first map's fan-in barrier, so every branch receives its true index, `sorted_add` restores deterministic order, error findings attribute to the correct row, and the FR-943 census containment passes live against the poisoned batches without modification.

## Proposed Solution

Insert a synchronizing pass-through join node between chained maps (the **barrier join** solution class — recorded with its runtime probe in FR-944.research.md per judgement R-1; note the persona rows prescribe index threading, a direction the research amendment dispositions against). Airflow's chained dynamic-task-mapping guarantee (librarian entry) states the requirement the barrier satisfies:

```python
def _compile_map_to_map(ctx: _EdgeContext) -> None:
    _, from_sub = ctx.map_nodes[ctx.from_node]
    to_map_edge_fn, to_sub = ctx.map_nodes[ctx.to_node]
    join_name = f"_map_join_{ctx.from_node}_{ctx.to_node}"
    ctx.graph.add_node(join_name, lambda state: {})
    ctx.graph.add_edge(from_sub, join_name)
    ctx.graph.add_conditional_edges(join_name, to_map_edge_fn, [to_sub])
```

LangGraph's superstep barrier makes the join run once after all first-map tasks complete; the second `map_edge` then sees the fully collected list and enumerates true indexes. This is precisely how `_compile_to_map` already behaves for `node → map` — chaining stops being a special case with divergent semantics.

Non-goals: no change to `map_compiler.py` Send construction, no change to `sorted_add`, no change to single-map behavior, no change to the FR-943 census contract.

## Acceptance Criteria

Revised per judgement (R-2/R-3 folded; the judgement's AC list is binding):

- [ ] AC-01: Committed research record contains the barrier-join solution class, bounded direct runtime probe and output, contrary-alternative dispositions, and one explicit `is_this_a_graph` answer; no ignored `tmp/` or `logs/` path treated as authoritative evidence.
- [ ] AC-02: A committed RED test in tests/unit/test_fr944_map_to_map_index.py fails on current behavior because the downstream map path/index contract is violated, before any production change is committed.
- [ ] AC-03: For an N=3 chain where map 2 consumes map 1's collected output, map 2 fans out once and returns exactly three ordered results with indexes `[0, 1, 2]` paired to the correct values.
- [ ] AC-04: For an N=3 upstream map and an independent M=2 downstream `over` list, map 2 returns exactly two results with indexes `[0, 1]`, proving no per-upstream-branch N×M fan-out.
- [ ] AC-05: A map-2 exception at downstream index 2 produces the existing `wrap_for_reducer` error envelope with `_map_index == 2`, exact error text/type, and unchanged successful peers.
- [ ] AC-06: The compiled path is upstream sub-node → generated pass-through join → downstream conditional `Send` router; no downstream-map conditional router remains directly attached to the upstream sub-node, and the join returns `{}` without state mutation.
- [ ] AC-07: A generated join-name collision fails compilation explicitly naming both the map-to-map edge and conflicting synthetic node name.
- [ ] AC-08: `EdgeShape.MAP_TO_MAP`, `map_edge`, `wrap_for_reducer`, `sorted_add`, and all single-map behavior remain unchanged; this exact regression command passes:

```bash
pytest \
  tests/unit/test_fr944_map_to_map_index.py \
  tests/unit/test_fr718_edge_shapes.py \
  tests/unit/test_compile_graph_map.py \
  tests/unit/test_map_node.py \
  tests/unit/test_map_flatten_output.py \
  tests/unit/test_map_node_timeout.py \
  tests/unit/test_state_builder.py \
  tests/unit/test_fr943_census_row_failure_containment.py \
  -q --no-cov
```

- [ ] AC-09: CAP-210 and regenerated ARCHITECTURE.md assign the frozen map-to-map behavior and new test module to REQ-YG-568; every new test carries `@pytest.mark.req("REQ-YG-568")`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: reference/map-nodes.md, the REQ-YG-568 `fix` changelog fragment, FR implementation record, committed research evidence, and diary reflection are delivered.

No paid corpus-census rerun is required for acceptance (the operator's census rerun proceeds after merge as validation, not as gate).

## Alternatives Considered

Dispositioned in [FR-944.research.md](FR-944.research.md):
- **Inherit index in fused mode** (wrap the chained `map_edge` to propagate the branch's `_map_index` when fan-out is single-item): keeps pipelining but leaves hazard #2 (N×M duplication when `over` differs from the upstream collect) unfixed, and gives no clean index for 1→N expansion. Rejected — patches the symptom inside a semantically wrong shape.
- **Delete map-to-map chaining** (subtractionist): removes the defect class but breaks corpus_census and a natural pipeline shape; migration cost exceeds the one-node fix. Rejected.
- **Rely on prompt-echoed indexes** (status quo, census `source_index`): routes row identity through an LLM — `model_as_trusted_peer` trap; already witnessed masking this defect. Rejected.

## Related

- Committed executable witnesses: tests/unit/test_fr944_map_to_map_index.py (the durable LLM-free reproduction; transient repro/incident paths under tmp/ and logs/ are context, not evidence)
- CAP-11 (subgraph & map), CAP-210 (edge shape classification, REQ-YG-568)
