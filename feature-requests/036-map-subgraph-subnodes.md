# Feature Request: Agent Support in Map Sub-Nodes

**Priority:** HIGH
**Type:** Feature
**Status:** Implemented (Phase 1)
**Effort:** <1 day
**Requested:** 2026-02-15
**Accepted:** 2026-02-15
**Implemented:** 2026-02-15

## Decision Record

Original petition requested `type: subgraph` in map sub-nodes. Implementors proposed `type: agent` instead — it solves the immediate need (parallel web search) with far less complexity. Subgraph support deferred to Phase 2 pending evidence of real use cases that agent can't solve.

## Summary

Enable `type: agent` sub-nodes within `type: map` nodes, allowing dynamic parallel execution of agent loops (with tool access, e.g., web search) over runtime-generated lists.

## Problem

Map sub-nodes currently support `llm`, `python`, `tool_call`, and `router` — but NOT `subgraph` or `agent`. This means any map item that requires a multi-step pipeline (e.g., web search → analyze → compile) must be flattened to a single LLM call, losing:

1. **Web search capability** — `websearch` tool requires `agent` nodes (multi-turn tool-calling loop). Agent nodes can't be map sub-nodes. So dynamic parallel web search is impossible.
2. **Multi-step processing** — A research pipeline (search → filter → synthesize) must be crammed into a single prompt, reducing quality and losing tool access.
3. **Composition** — Subgraphs are the unit of reuse in YAMLGraph. Excluding them from map breaks the "compose graphs from graphs" principle.

---

## Critical Analysis

### Is This Scope-Appropriate?

This FR conflates two distinct capabilities:
- **Web search in parallel** (immediate need for opinto-ohjaus)
- **General subgraph composition in maps** (architectural elegance)

Per copilot-instructions: *"Documenting patterns is cheaper than new code."* The question: **does opinto-ohjaus need full subgraph support, or just parallel web search?**

### Simpler Alternative: `type: agent` as Map Sub-node

The FR dismisses this in Alternative #3 as "doesn't generalize," but:
- Agent IS the unit needed for web search (handles tool-calling loop)
- Agent is simpler than subgraph (no state schema mapping)
- Agent already has well-tested node factory infrastructure
- YAGNI: implement what's needed now, generalize when proven

**Effort comparison:**

| Approach | Effort | Complexity | Solves web search? |
|----------|:------:|:----------:|:------------------:|
| Map + agent sub-node | <1 day | Low | ✅ |
| Map + subgraph sub-node | 2-3 days | Medium-High | ✅ |

### State Mapping Complexity (Subgraph Approach)

The original FR underestimates this. Subgraphs have independent state schemas. Composing:
- Map's item injection (`{item_var: item, _map_index: i}`)
- Subgraph's `input_mapping` / `output_mapping`
- Error handling per item with `on_error: skip`
- Checkpointer propagation through nested boundaries

...creates a 4-layer abstraction maze. Debug/trace story becomes painful.

### Testing Burden

Map × Subgraph × Agent × Websearch = explosion of test combinations. Each integration test requires real LLM calls.

---

## Recommended Approach: Phased Implementation

### Phase 1: `type: agent` as Map Sub-node — ACCEPTED

**Solves the immediate opinto-ohjaus need:**
```yaml
research_topics:
  type: map
  over: "{state.topics}"
  as: topic
  node:
    type: agent           # ← NEW: agent sub-node support
    tools: [websearch]
    prompt: research-topic
    state_key: research
    max_iterations: 3
  collect: research_results
```

**Implementation**: Add `NodeType.AGENT` case in `compile_map_node()`, pattern identical to `tool_call` and `python` sub-nodes. Agent node factory (`create_agent_node`) exists and is battle-tested.

```python
# In compile_map_node(), add case after PYTHON:
elif sub_node_type == NodeType.AGENT:
    sub_node = create_agent_node(
        sub_node_name,
        sub_node_config,
        tools=tools_registry or {},
        python_tools=python_tools or {},
        defaults=defaults,
        graph_path=graph_path,
    )
```

**Implementation changes:**
1. **`map_compiler.py`** (~10 lines): Add agent case, pass tools/python_tools registries
2. **`node_compiler.py`**: Pass `tools` registry to `compile_map_node()` (currently only passes `callable_registry`)
3. **Linter** (`linter/patterns/map.py`): Allow `type: agent` in map sub-node validation
4. **Tests**: Unit test for map+agent compilation, integration test with mock websearch
5. **Docs**: Update `reference/map-nodes.md` sub-node types table

**Acceptance Criteria (Phase 1):**
- [x] `type: agent` works in map sub-node configuration
- [x] `tools` list resolved from parent graph's tool registry
- [x] `max_iterations` respected per map item (via existing agent infrastructure)
- [x] `_map_index` preserved in output for ordering (via existing wrap_for_reducer)
- [x] `on_error: skip` works — failed agent items don't crash the pipeline (via existing error handling)
- [x] `max_items` cap works as before (unchanged)
- [ ] `websearch` tool works inside map agent sub-node (needs integration test)
- [x] Tests added for happy path and error cases
- [ ] Reference docs updated (`reference/map-nodes.md`)

### Phase 2: Subgraph Support — DEFERRED

Only proceed when:
1. Real use case emerges that agent sub-nodes can't solve
2. Production experience validates the pattern
3. State mapping complexity is worth the architectural elegance

---

## Questions for Requestor

1. **For opinto-ohjaus specifically**: Is the web search → analyze → compile flow truly multi-step requiring separate nodes, or can a single agent with good prompt + tool loop handle it?

2. **Quality validation**: Have you run opinto-ohjaus manually (flattened to single LLM call) to quantify the quality gap from missing web search?

3. **Blocking or nice-to-have**: Would agent sub-nodes unblock opinto-ohjaus, or is subgraph support essential?

---

## Original Proposal (for reference)

*The following sections describe the full subgraph approach as originally proposed. See [Critical Analysis](#critical-analysis) for recommended phased approach.*

### Real Use Case: Opinto-ohjaus (Student Counseling)

The `projects/opinto_ohjaus` pipeline generates lesson plans for Finnish lukio guidance counseling. The ideal architecture:

```yaml
# DESIRED but unsupported:
research_topics:
  type: map
  over: "{state.topics}"          # 15-25 topics generated at runtime
  as: topic
  node:
    type: subgraph                # ← NOT SUPPORTED
    graph: topic-research.yaml    # web_search → analyze → compile
  collect: research_results
```

The `topic-research.yaml` subgraph would:
1. Execute web search queries (Finnish educational sources: oph.fi, opintopolku.fi)
2. Analyze and filter results for relevance
3. Compile a structured research summary with citations

**Forced workaround**: Flatten to `map` + `llm` sub-node (single prompt per topic). This drops web search entirely, relying solely on LLM training data. The pipeline works, but loses access to current sources (e.g., yhteishaku 2026 dates, oppimisen tuki reform 1.8.2025).

### Why Topological Parallelism Doesn't Help

The `innovators_toolkit` project solved map+subgraph for a **static** case: 9 known tool nodes wired via compile-time edges from a common predecessor (LangGraph auto-parallelizes). But opinto-ohjaus has **dynamic** items — 15-25 topics generated at runtime. Static edges can't express "run this subgraph for each item in a list whose length is unknown at compile time." That's exactly what `map` + `Send()` is designed for.

| Pattern | Static items? | Dynamic items? | Multi-step per item? |
|---------|:---:|:---:|:---:|
| Topological parallelism | ✅ | ❌ | ✅ |
| Map + llm sub-node | ✅ | ✅ | ❌ (single call) |
| **Map + subgraph** (proposed) | ✅ | ✅ | ✅ |

## Proposed Solution

Extend `compile_map_node()` in `map_compiler.py` to handle `type: subgraph`:

```python
# In compile_map_node(), add case after PYTHON:
elif sub_node_type == NodeType.SUBGRAPH:
    if graph_path is None:
        raise ValueError(
            f"Map node '{name}' has subgraph sub-node but no graph_path "
            "for relative path resolution"
        )
    sub_node = create_subgraph_node(
        sub_node_name,
        sub_node_config,
        parent_graph_path=graph_path,
    )
```

### YAML Syntax

```yaml
nodes:
  research_topics:
    type: map
    over: "{state.topics}"
    as: topic
    max_items: 30
    on_error: skip
    node:
      type: subgraph
      graph: topic-research.yaml
      input_mapping:
        topic: topic             # parent state.topic → child state.topic
        module: module           # parent state.module → child state.module
      output_mapping:
        research_summary: result # child state.result → collected item
    collect: research_results
```

### Subgraph: `topic-research.yaml`

```yaml
name: topic-research
version: "1.0"

nodes:
  search:
    type: agent
    tools: [websearch]
    prompt: search-topic
    state_key: search_results
    max_iterations: 3

  analyze:
    type: llm
    prompt: analyze-search-results
    state_key: analysis

  compile:
    type: llm
    prompt: compile-topic-summary
    state_key: result

edges:
  - from: START
    to: search
  - from: search
    to: analyze
  - from: analyze
    to: compile
  - from: compile
    to: END
```

### Implementation Changes

1. **`map_compiler.py`** (~20 lines):
   - Import `create_subgraph_node`
   - Add `NodeType.SUBGRAPH` case in sub-node type switch
   - Handle `input_mapping` / `output_mapping` in the sub-node config
   - The `wrap_for_reducer` wrapper handles collection — subgraph node returns a dict, same as llm/python

2. **`wrap_for_reducer` adaptation**:
   - `create_subgraph_node` returns `subgraph_node(state, config)` (2 args) or `CompiledGraph` (mode=direct)
   - `wrap_for_reducer` currently calls `node_fn(state)` (1 arg) — needs to handle the config arg
   - For `mode=invoke`: wrapper passes `state` including the injected map item variable
   - For `mode=direct`: LangGraph handles state mapping natively

3. **State mapping**:
   - Map injects `{item_var: item, _map_index: i}` into state (existing behavior)
   - Subgraph's `input_mapping` receives this enriched state
   - Subgraph's `output_mapping` feeds back to `wrap_for_reducer`
   - Reducer collects results into `collect` key (existing behavior)

4. **Linter** (`linter/patterns/map.py`):
   - Allow `type: subgraph` in map sub-node validation
   - Validate `graph` field exists when sub-node type is subgraph
   - Validate `input_mapping` and `output_mapping` present

5. **Tests**:
   - Unit: map + subgraph sub-node compilation
   - Unit: wrap_for_reducer with subgraph callable
   - Unit: input/output mapping through map
   - Integration: map + subgraph with mock LLM
   - Integration: map + subgraph + agent sub-node (web search)
   - Error: missing graph path, circular reference, subgraph compile failure

### Complexity Analysis

The core change is small (~20 lines in `map_compiler.py`). The main complexity is:

| Concern | Difficulty | Notes |
|---------|:---:|-------|
| Add subgraph case to switch | Low | Same pattern as python/tool_call cases |
| `wrap_for_reducer` config arg | Medium | Subgraph node expects `(state, config)` vs `(state)` |
| Input/output mapping in map context | Medium | Must compose with map's item injection |
| Circular reference detection | Low | Already handled by `_loading_stack` in `create_subgraph_node` |
| Checkpointer propagation | Low | `create_subgraph_node` already handles this |
| Error handling per item | Low | `wrap_for_reducer` + `on_error: skip` already work |

## Acceptance Criteria

- [ ] `type: subgraph` works in map sub-node configuration
- [ ] `graph` path resolved relative to parent graph
- [ ] `input_mapping` / `output_mapping` compose with map's item variable injection
- [ ] Circular reference detection works (subgraph → map → same subgraph)
- [ ] `_map_index` preserved in output for ordering
- [ ] `on_error: skip` works — failed subgraph items don't crash the pipeline
- [ ] `max_items` cap works as before
- [ ] Agent nodes (with websearch) work inside map subgraphs
- [ ] Linter validates subgraph-specific fields in map sub-node
- [ ] Tests added for happy path, error cases, and agent+websearch
- [ ] Reference docs updated (`reference/map-nodes.md`, `reference/graph-yaml.md`)
- [ ] Example added: map + subgraph with agent/websearch

## Alternatives Considered

1. **Flatten to map+llm**: Current workaround. Works but loses web search and multi-step processing. Quality degrades for research-heavy tasks.
2. **Map + python sub-node with inline LLM calls**: Python tool calls DuckDuckGo + `execute_prompt()`. Works but bypasses graph orchestration, tracing, and error handling. Violates 3-layer pattern.
3. **Map + agent sub-node**: Supporting `agent` directly in map (without subgraph) would solve the web search case specifically, but doesn't generalize to multi-step pipelines. If both are desired, subgraph is the more general solution.
4. **Pre-map batch research**: Single agent node before map that searches all topics at once. Loses per-topic parallelism and overloads a single agent with 15-25 search tasks.
5. **Topological parallelism**: Wire static nodes from common predecessor. Only works for fixed/known items at compile time. Fails for dynamic lists.

## Dependencies

- `create_subgraph_node` — [subgraph_nodes.py](../yamlgraph/node_factory/subgraph_nodes.py) (exists, works)
- `compile_map_node` — [map_compiler.py](../yamlgraph/map_compiler.py) (modification target)
- `wrap_for_reducer` — [map_compiler.py](../yamlgraph/map_compiler.py) (may need 2-arg support)
- `websearch` tool — [tools/websearch.py](../yamlgraph/tools/websearch.py) (exists, works with agent)
- FR-021 (python map sub-nodes) — implemented, established the pattern for adding new sub-node types

## Related

- [map_compiler.py](../yamlgraph/map_compiler.py) — Current implementation (lines 148-172: sub-node type switch)
- [subgraph_nodes.py](../yamlgraph/node_factory/subgraph_nodes.py) — Subgraph node factory
- [FR-021](021-python-map-subnodes.md) — Python map sub-nodes (established the extension pattern)
- [FR-030](030-map-concurrency-control.md) — Map concurrency control (complementary)
- [innovators_toolkit/plan.md](../projects/innovators_toolkit/plan.md) — Documents the static workaround
- [opinto_ohjaus/plan-opinto-ohjaus-overall.md](../projects/opinto_ohjaus/plan-opinto-ohjaus-overall.md) — Use case that discovered this gap
