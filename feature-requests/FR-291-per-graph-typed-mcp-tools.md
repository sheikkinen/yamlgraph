# Feature Request: Per-Graph Typed MCP Tools & Mastra Integration Example

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 4 days
**Requested:** 2026-04-27
**Judged:** 2026-04-27

## Summary

Derive per-graph typed MCP tool definitions from graph YAML metadata (`name`, `description`, `state:`) so that each graph appears as its own named tool with a typed JSON Schema — not a generic `yamlgraph_run_graph` dispatcher. Prove the pattern with a cross-runtime Mastra (TypeScript) integration example.

## Value Statement

External callers (Copilot, Mastra agents, Claude Desktop) discover and invoke YAMLGraph graphs as first-class typed tools without knowing they are YAML pipelines, making the graph YAML the single source of truth for both pipeline logic and API contract.

## Problem

Today the MCP server exposes exactly two tools:
- `yamlgraph_list_graphs` — list all graphs
- `yamlgraph_run_graph(graph, vars)` — invoke any graph with untyped `vars: object`

This means:
1. **LLM callers cannot discover parameter schemas.** An agent calling `yamlgraph_run_graph` must already know what variables `intent-classifier` expects. There is no JSON Schema for `{message: string}` — only a bag of `Any`.
2. **Tool names are opaque.** Every graph is called through the same generic dispatcher. The LLM sees one tool that does everything, rather than N tools with clear names and purposes.
3. **A2A Agent Cards have the same gap.** Skills list graph names but lack typed input schemas derived from `state:`.

The graph YAML already declares everything needed for a typed contract:
```yaml
name: intent-classifier          # → tool name
description: Classify intent     # → tool description
state:
  message: str                   # → { message: { type: "string" } }
  context: str                   # → { context: { type: "string" } }
```

This metadata is parsed at discovery time but discarded at the protocol boundary.

**Input vs output ambiguity:** The `state:` block declares *all* fields — both inputs and node outputs. A node's `state_key` target (e.g., `greeting`) is an output, not something the caller supplies. The schema derivation must exclude `state_key` targets to avoid exposing outputs as required parameters.

## Proposed Solution

### Piece 1: Per-graph typed MCP tools

Modify `mcp_server.py` to register each discovered graph as its own MCP tool:

```python
# Before (one generic tool):
# yamlgraph_run_graph(graph: str, vars: object)

# After (per-graph typed tools):
# intent_classifier(message: str, context: str)
# order_support(order_id: str, customer_message: str)
# quality_gate(draft_response: str)
```

**Type mapping** from YAML `state:` to JSON Schema:

| YAML type | JSON Schema type |
|-----------|-----------------|
| `str`     | `string`        |
| `int`     | `integer`       |
| `float`   | `number`        |
| `bool`    | `boolean`       |
| `list`    | `array`         |
| `dict`    | `object`        |

**Tool name derivation:** `name` field with hyphens → underscores (e.g., `intent-classifier` → `intent_classifier`). Collisions fail loudly at startup.

**Input/output separation:** Input vars = `state:` keys that are NOT used as any node's `state_key`. This is derivable from the YAML without compiling the graph:

```python
state_keys_used_as_output = {
    node.get("state_key") for node in config.get("nodes", {}).values()
    if "state_key" in node
}
input_vars = [k for k in state.keys() if k not in state_keys_used_as_output]
```

The derivation logic lives in `discovery.py` as shared infrastructure (reusable by A2A in a follow-up FR).

**Type constraints:** Parameterized types (e.g., `list[str]`) map to the base type (`array`). Graphs without a `state:` block register as tools with empty input schema. Unknown type strings fall back to `string`.

**Retain the generic tools** (`yamlgraph_list_graphs`, `yamlgraph_run_graph`) for discovery and programmatic access. The per-graph tools are additive.

### Piece 2: Mastra integration example

Create `examples/demos/mastra-integration/` containing:

```
examples/demos/mastra-integration/
├── graph.yaml              # YAMLGraph graph (e.g., intent classifier)
├── prompts/
│   └── classify.yaml       # Prompt with inline schema
├── mastra-app/
│   ├── package.json        # Mastra + @mastra/mcp dependencies
│   ├── tsconfig.json
│   └── src/
│       └── index.ts        # Mastra agent consuming YAMLGraph via MCP
├── demo.sh                 # Starts MCP server + runs Mastra agent
├── demo-output.log         # Proof of execution
└── README.md               # Setup instructions
```

The TypeScript client proves typed tool discovery without requiring an LLM call (no API keys needed in CI):

```typescript
import { MCPClient } from "@mastra/mcp";

const yamlgraph = new MCPClient({
  servers: {
    yamlgraph: {
      command: "python3",
      args: ["../../yamlgraph/mcp_server.py"],
    },
  },
});

// Discover typed tools — each graph is its own tool with JSON Schema
const tools = await yamlgraph.getTools();
console.log("Discovered tools:", Object.keys(tools));
// → ["yamlgraph_list_graphs", "yamlgraph_run_graph", "hello_world", ...]

// Call a typed tool directly — no LLM required
const result = await tools.hello_world.execute({ name: "World", style: "casual" });
console.log("Result:", result);
```

A README documents the full Mastra Agent pattern (with LLM) for users who want to go further:

```typescript
// Full agent example (requires OPENAI_API_KEY)
import { Agent } from "@mastra/core/agent";
const agent = new Agent({
  id: "support-router",
  instructions: "Route customer messages using the classify tool.",
  model: "openai/gpt-4o-mini",
  tools: await yamlgraph.getTools(),
});
const result = await agent.generate("Customer says: where is my order #1234?");
```

## Acceptance Criteria

### Piece 1: Per-graph typed MCP tools
- [ ] `discovery.py` distinguishes input vars from output vars (exclude `state_key` targets)
- [ ] `discovery.py` returns typed input schema (JSON Schema dict) per graph
- [ ] Type mapping: str→string, int→integer, float→number, bool→boolean, list→array, dict→object
- [ ] Parameterized types (`list[str]`) map to base type; unknown types fall back to `string`
- [ ] Graphs without `state:` block register as tools with empty input schema
- [ ] `mcp_server.py` registers per-graph MCP tools with typed `inputSchema`
- [ ] Tool name: graph `name` with hyphens→underscores; collision raises at startup
- [ ] Generic `yamlgraph_list_graphs` and `yamlgraph_run_graph` retained
- [ ] Unit tests for input/output var separation
- [ ] Unit tests for JSON Schema derivation from state types
- [ ] Unit tests for tool name normalization and collision detection
- [ ] Tests tagged with `@pytest.mark.req`

### Piece 2: Mastra integration example
- [ ] `examples/demos/mastra-integration/` with graph, prompts, TypeScript client
- [ ] TypeScript client proves typed tool discovery via MCP (no LLM/API key required)
- [ ] `demo.sh` runs successfully and produces `demo-output.log`
- [ ] README documents full Mastra Agent pattern for users with API keys

### Out of scope
- A2A Agent Card typed skill schemas (follow-up FR; shared infra in `discovery.py` enables it)
- `contract:` override block in graph YAML (future FR if auto-derivation proves insufficient)

## Alternatives Considered

1. **Optional `contract:` block in graph YAML** — explicit override of auto-generated schema. Deferred: auto-derivation from `state:` covers the common case. Can add override support later if schemas diverge from state fields.
2. **yamlgraph-to-Mastra compiler** — rejected. The semantic gap is not syntactic (Jinja2 prompts, Pydantic schemas, Python tools cannot compile to TypeScript). MCP/A2A protocols solve cross-runtime integration without compilation.
3. **TypeScript node type** — rejected for now. Shell tools + MCP already provide TypeScript ecosystem access. No recurring demand pattern exists yet.

## Research Context

See `docs/research-mastra.md` for the full Mastra comparison that motivated this FR.

## Judgement Notes

1. **Input/output separation is critical.** Without it, output `state_key` fields appear as required parameters. The `state_key` exclusion heuristic is sound — it's derivable from YAML without compilation.
2. **A2A parity removed from scope.** Different code path (`AgentSkill` protobuf vs JSON Schema), different module. Schema derivation logic in `discovery.py` is shared infrastructure; A2A applies it in a follow-up FR.
3. **Mastra example redesigned for CI.** The TypeScript client calls tools directly (no LLM, no API key). The full Agent pattern is documented in README for manual use.
4. **Effort adjusted to 4 days** (3 for MCP typed tools + 1 for Mastra example with npm setup).

## Related

- CAP-19: MCP Server Interface (REQ-YG-066, REQ-YG-067, REQ-YG-068)
- FR-250: A2A Server Complete Gaps (follow-up for A2A parity)
- `yamlgraph/mcp_server.py` — current generic tool registration
- `yamlgraph/discovery.py` — graph discovery with state metadata
- `docs/research-mastra.md` — Mastra comparison research
