# Feature Request: FR-658 — Graph-as-Tool: In-Process Pipeline Invocation

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced ✅
**Effort:** 2 days
**Requested:** 2026-07-03
**Judged:** 2026-07-03
**Enforced:** 2026-07-03 (commit `9ecaf65b`)

## Summary

Add a `type: graph` tool that invokes a YAMLGraph pipeline in-process as a
callable tool. An `agent` node can use it without knowing the tool is a
full pipeline — it sees a typed tool with input schema and text output. No
MCP server, no A2A network, no subprocess.

## Problem

YAMLGraph has three ways to compose pipelines:

| Mechanism | Abstraction | Overhead | Caller knows? |
|-----------|-------------|----------|---------------|
| `type: subgraph` node | Node in parent graph | None | Yes — visible in graph topology |
| MCP server tool | Network tool | HTTP/stdio process | No — sees a tool |
| A2A client call | Network agent | HTTP + JSON-RPC | No — sees a message |

**Missing:** an in-process tool that wraps a graph. The caller (an `agent` node
or `tool_call` node) sees a typed tool with `inputSchema` and returns text. The
implementation calls `invoke_graph()` directly.

### Use Case: Fact-Checking in novel_fandom

worldgen's `deepen` node produces entities that reference non-existent IDs,
contradict canon timelines, or violate schema constraints. A fact-check pipeline
could validate proposed entities against the current canon:

```yaml
tools:
  fact_check:
    type: graph
    path: fact_check.yaml
    input_mapping:
      entity: drafted_entity
      canon: canon_pages
    output_key: violations

nodes:
  deepen:
    type: agent
    tools:
      - fact_check    # agent calls this like any other tool
      - web_search
```

The agent doesn't know `fact_check` is a pipeline — it sees a tool that takes
an entity and returns violations.

## Acceptance Criteria

1. **AC-1**: New tool type `type: graph` recognized in `_parse_all_tools()`.
2. **AC-2**: Tool config fields: `path` (graph YAML path, resolved relative to
   parent graph), `input_mapping` (dict mapping tool input fields → graph
   variables), `output_key` (state key to extract from graph result as tool
   output), `description` (tool description for agent LLM; defaults to child
   graph's `description` metadata if omitted).
3. **AC-3**: Tool is registered in `callable_registry` as a `StructuredTool`
   with `inputSchema` generated from `input_mapping` keys. Each key becomes
   a `str`-typed field in a dynamic Pydantic `ArgsModel` via `create_model()`.
4. **AC-4**: Circular reference detection — reuse the `ContextVar` loading
   stack from `subgraph_nodes.py`, checked at **invocation time** (inside
   `make_tool_fn`), not at parse time.
5. **AC-5**: `agent` node can bind and call the tool in a multi-turn loop.
6. **AC-6**: `tool_call` node can invoke the tool directly.
7. **AC-7**: Demo graph showing agent with graph-tool in `examples/demos/`.
8. **AC-8**: Child graph is compiled once during `_parse_all_tools()`. Each
   tool invocation calls `compiled.invoke()`, not `invoke_graph()`.
9. **AC-9**: Pipeline errors inside graph-tool invocation are caught and
   returned as error text to the calling agent. The parent agent loop must
   not crash.

## Implementation Approach

### 1. New parser: `parse_graph_tools()`

In `yamlgraph/tools/graph_tool.py`:

```python
def parse_graph_tools(
    tools_config: dict,
    parent_graph_path: Path,
) -> tuple[dict[str, Any], dict[str, Callable]]:
    """Parse type: graph tools into callable registry entries.

    Returns:
        Tuple of (graph_tool_configs, callable_registry)
    """
    configs = {}
    callables = {}
    for name, config in tools_config.items():
        if config.get("type") != "graph":
            continue
        graph_path = resolve_relative_path(config["path"], parent_graph_path)
        input_mapping = config.get("input_mapping", {})
        output_key = config.get("output_key", "result")

        # Compile once at parse time (AC-8)
        child_config = load_graph_config(graph_path)
        compiled = compile_graph(child_config).compile()
        description = config.get("description") or child_config.description

        def make_tool_fn(cp, im, ok, gp):
            def tool_fn(**kwargs):
                # Circular reference guard at invocation time (AC-4)
                stack = _loading_stack.get([])
                if gp in stack:
                    cycle = " -> ".join(str(p) for p in [*stack, gp])
                    return f"Error: Circular graph-tool reference: {cycle}"
                token = _loading_stack.set([*stack, gp])
                try:
                    variables = {im.get(k, k): v for k, v in kwargs.items()}
                    result = cp.invoke(variables)
                    return str(result.get(ok, result))
                except Exception as e:
                    return f"Error: {e}"  # AC-9: surface, don't crash
                finally:
                    _loading_stack.reset(token)
            return tool_fn

        fn = make_tool_fn(compiled, input_mapping, output_key, graph_path)
        configs[name] = {"description": description, "input_mapping": input_mapping}
        callables[name] = fn
    return configs, callables
```

### 2. Register in `_parse_all_tools()`

Add `parse_graph_tools()` call alongside existing parsers in
`graph_loader.py:_parse_all_tools()`.

### 3. StructuredTool wrapping

Reuse the `create_model()` + `StructuredTool.from_function()` pattern from
`yamlgraph/tools/agent.py`. Build `ArgsModel` from `input_mapping` keys (each
becomes a `str` field). Use `description` from tool config or child graph
metadata.

### 4. Circular reference guard

Import the `_loading_stack` ContextVar from `subgraph_nodes.py`. Check and
push/pop at **invocation time** inside `make_tool_fn`, not at parse time.
Return error text on cycle detection (AC-9 pattern).

## Constraints

- No new node type — this is a **tool type**, not a node type.
- No network — in-process `compiled.invoke()` only.
- The child graph is compiled once at tool parse time, not per call.
- `input_mapping` keys define the tool's input schema (not child graph introspection).
- `description` field required; defaults to child graph's `description` metadata.
- No checkpointer propagation (tools are stateless calls).
- Pipeline errors are caught and returned as text — never crash the parent agent.

## Risks

- **Performance:** Compiling a graph per tool call would be expensive.
  Mitigated: compile once at parse time (AC-8).
- **Error handling:** Pipeline errors inside a tool call could crash the parent
  agent loop. Mitigated: catch and return error text (AC-9).

## Non-Goals

- This FR does not replace `type: subgraph` nodes (which are for structural
  composition within a graph's topology).
- This FR does not replace MCP/A2A (which are for cross-process/network
  composition).
- No streaming support for tool calls (tools return text, not streams).

## Demo: Style Advisor (`examples/demos/graph-tool/`)

An agent writes marketing copy and self-corrects using a graph-tool for tone
analysis. Two tools: one regular Python tool, one graph-tool wrapping the
existing `tone_router_demo.yaml` pipeline.

```yaml
# examples/demos/graph-tool/graph.yaml
tools:
  thesaurus:
    type: python
    path: nodes/thesaurus.py
    function: lookup_synonyms

  tone_check:
    type: graph
    path: ../../demos/tone-router-demo/graph.yaml
    description: "Analyze the tone of the given text"
    input_mapping:
      text: text
    output_key: tone

nodes:
  write:
    type: agent
    prompt: style_advisor
    tools:
      - thesaurus
      - tone_check
    state_key: final_copy
    max_iterations: 5
```

**Flow:** Agent drafts copy → calls `tone_check` (graph-tool) → if tone doesn't
match brand target, rewrites → calls `tone_check` again → converges. The agent
doesn't know `tone_check` is a full pipeline with its own LLM nodes.

**Why this demo:** Reuses existing graph, shows self-correcting agent loop,
runs in ~15 seconds, demonstrates the core value — an agent treating a pipeline
as an opaque tool.

## Related

- [Research: Agent Comms for Fact-Checking](../docs/research-agent-comms-fact-checking.md) — analysis leading to this FR
- [FR-655](FR-655-genesis-graph.md) — genesis pipeline (produces the entities to fact-check)
- [FR-656](FR-656-tighten-genesis-prompt.md) — prompt tightening (reduces but doesn't eliminate schema violations)
- [CAP-05](../capabilities/CAP-05-tool-agent-integration.yaml) — tool/agent integration capability
- [CAP-11](../capabilities/CAP-11-subgraph-map.yaml) — subgraph composition

---

## Judgement

**Verdict: APPROVED — scope frozen with amendments below.**

### Assessment

The FR fills a genuine gap in the composition matrix. Subgraphs are structural
(visible in topology), MCP/A2A are networked (cross-process). A `type: graph`
tool is the missing in-process opaque invocation — the caller sees a tool, not a
pipeline. The abstraction is clean and the implementation is well-scoped.

The codebase is ready:
- `invoke_graph()` already exists as a shared entry point (FR-255).
- `_LOADING_STACK` ContextVar in `subgraph_nodes.py` provides circular reference
  detection — reusable.
- `build_python_tool()` in `tools/agent.py` demonstrates the StructuredTool
  wrapping pattern with dynamic Pydantic schema via `create_model()`.
- `_parse_all_tools()` in `graph_loader.py` is a clean insertion point — add
  one parser call alongside the existing four.

### Issues Found & Required Amendments

1. **Schema inference is wrong.** AC-3 says "auto-generated `inputSchema` from
   the child graph's `variables:` or `state:` declaration." But `variables:` is
   a **node-level** field (`NodeConfig.variables`), not a graph-level field.
   There is no graph-level `variables:` declaration in `GraphConfigSchema`.
   The CLI's `inputs:` section exists in raw YAML parsing (`graph info`) but
   is not part of the Pydantic schema.

   **Amendment:** The tool's input schema MUST come from `input_mapping` keys,
   not from child graph introspection. The `input_mapping` dict is the contract.
   Each key becomes a `str`-typed field in the generated `ArgsModel`. This is
   simpler, explicit, and doesn't require the child graph to declare anything
   new. Drop AC-3's "auto-generated from `variables:`" claim — replace with
   "generated from `input_mapping` keys."

2. **Compile-once, invoke-many.** The FR correctly identifies this under Risks
   but doesn't make it an AC. The child graph MUST be compiled once at tool
   parse time and the compiled graph reused per call. `invoke_graph()` compiles
   on every call — don't use it directly.

   **Amendment:** Add AC-8: "Child graph is compiled once during
   `_parse_all_tools()`. Each tool invocation calls `compiled.invoke()`, not
   `invoke_graph()`."

3. **`_LOADING_STACK` import boundary.** AC-4 says "reuse the `ContextVar`
   loading stack from `subgraph_nodes.py`." This creates a Layer 2 → Layer 2
   import (tool module importing from node_factory). Acceptable since both are
   Layer 2, but the ContextVar should be checked at `invoke` time (when the
   tool is called), not at parse time (when the tool is registered).

   **Amendment:** Guard at invocation time inside `make_tool_fn`, not at
   parse time.

4. **Error surfacing.** The FR mentions catching errors and returning text
   under Risks. This MUST be an AC.

   **Amendment:** Add AC-9: "Pipeline errors inside graph-tool invocation are
   caught and returned as error text to the calling agent. The parent agent
   loop must not crash."

5. **`description` field.** The tool config needs a `description` field for
   the StructuredTool. The agent's LLM uses it to decide when to call the tool.
   Without it, the agent has no context.

   **Amendment:** Add `description` as required field in the tool config.
   Default to child graph's `description` field from its YAML metadata if
   not provided.

6. **Demo graph reference.** The demo references `../../demos/tone-router/graph.yaml`
   but the existing demo directory is `tone-router-demo/`. Verify the actual
   path at implementation time.

### Effort

2 days is realistic. The patterns are all established — this is a composition
task, not invention.

### Scope Freeze

- One new tool type (`type: graph`) — no new node types.
- One new file: `yamlgraph/tools/graph_tool.py`.
- One insertion in `_parse_all_tools()`.
- One demo in `examples/demos/graph-tool/`.
- One capability update: add REQ to CAP-05.
- Tests: tool parsing, circular detection, agent binding, error surfacing.

---

## Implementation Status

**Enforced 2026-07-03** in commit `9ecaf65b`. All ACs implemented and tested
(`tests/unit/test_graph_tool.py`, tagged `REQ-YG-510`). Demo executed with
`demo-output.log` committed (2-iteration agent run calling `tone_check`).

### Deviations from plan

1. **Layer split.** The plan placed `parse_graph_tools()` (including child
   graph compilation) in `yamlgraph/tools/graph_tool.py`. Compilation requires
   `load_graph_config` and `compile_graph`, which would create a Layer 3 →
   Layer 2 import violating the import-linter contract. Actual: compilation
   lives in Layer 2 as `graph_loader._parse_graph_tools()`; Layer 3
   `graph_tool.py` keeps only `make_graph_tool_fn()` (invocation wrapper with
   cycle guard + error surfacing) and `build_graph_tool()` (StructuredTool
   wrapping), receiving pre-compiled graphs from the caller.
2. **Demo child graph.** The plan reused `tone_router_demo.yaml`; the demo
   instead ships a self-contained child pipeline in
   `examples/demos/graph-tool/child/` (Judgement issue #6 flagged the path
   uncertainty).

### Traceability

- REQ-YG-510 in `capabilities/CAP-05-tool-agent-integration.yaml` and `ARCHITECTURE.md`
- Reference docs: `reference/graph-yaml.md` (Graph Tool section)
- Follow-up: FR-660 (enforced) removed the `callable()` dispatch heuristic in
  `agent.py` that this FR introduced; FR-683/FR-684 build on graph-tools.
