# Mastra Integration Demo

Cross-runtime integration: a Mastra (TypeScript) client discovers and consumes YAMLGraph graphs as typed MCP tools.

## What It Proves

FR-291 per-graph typed MCP tools enable any MCP client to discover YAMLGraph graphs as **first-class tools with typed JSON Schema** — not a generic `run_graph` dispatcher.

## Quick Start

```bash
# Requires Node.js >= 18
./demo.sh
```

The demo:
1. Validates the graph YAML
2. Installs TypeScript dependencies
3. Runs the Mastra MCP client to discover typed tools
4. Verifies the `hello_mastra` tool was auto-generated from `graph.yaml`

**No LLM API key required** — proves tool discovery only.

## Pipeline

```
START → greet → END
```

The `hello-mastra` graph exposes:
- **Inputs**: `name` (string), `style` (string) — from `state:` block
- **Output**: `greeting` — excluded from tool schema (it's a `state_key` target)

## Full Agent Pattern (requires API key)

For users who want to go further, here's a Mastra Agent that uses the typed tool with an LLM:

```typescript
import { Agent } from "@mastra/core/agent";
import { MCPClient } from "@mastra/mcp";

const yamlgraph = new MCPClient({
  servers: {
    yamlgraph: {
      command: "python3",
      args: ["yamlgraph/mcp_server.py"],
    },
  },
});

const agent = new Agent({
  id: "greeter",
  instructions: "Generate greetings using the hello_mastra tool.",
  model: "openai/gpt-4o-mini",   // requires OPENAI_API_KEY
  tools: await yamlgraph.getTools(),
});

const result = await agent.generate("Greet Alice in a formal style");
console.log(result.text);
// The agent discovers hello_mastra's typed schema and calls it
// with { name: "Alice", style: "formal" } automatically.
```

## Files

```
mastra-integration/
├── graph.yaml              # YAMLGraph graph (greeting generator)
├── prompts/
│   └── greet.yaml          # LLM prompt template
├── mastra-app/
│   ├── package.json        # @mastra/mcp dependency
│   ├── tsconfig.json
│   └── src/
│       └── index.ts        # MCP client proving typed tool discovery
├── demo.sh                 # Runner script
├── demo-output.log         # Proof of execution
└── README.md               # This file
```

## Key Concepts

- **Per-graph typed MCP tools** — each graph auto-generates its own tool with JSON Schema
- **Input/output separation** — `state_key` targets excluded from tool inputs
- **Cross-runtime** — Python pipeline consumed by TypeScript client via MCP protocol
- **No LLM for discovery** — tool schemas derived from YAML, not LLM introspection
