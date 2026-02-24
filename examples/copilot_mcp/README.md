# Copilot MCP Sampling Demo

**FR-082**: Demonstrates copilot nodes with `backend: sampling` — uses MCP sampling protocol to loop back to the host LLM (e.g., GitHub Copilot, Claude) at zero API cost.

## Key Difference from CLI Backend

| Feature | `backend: cli` | `backend: sampling` |
|---------|----------------|---------------------|
| Requires | `copilot` CLI binary | MCP server context |
| API Cost | Host LLM (free) | Host LLM (free) |
| File Access | Yes (`cli_flags`) | No |
| Subprocess | Yes | No |
| Use Case | Agentic tasks with tools | Pure LLM reasoning |

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Host LLM (Copilot/Claude)                              │
│    ↓ calls yamlgraph_run_graph                          │
├─────────────────────────────────────────────────────────┤
│  YAMLGraph MCP Server                                   │
│    ↓ executes graph                                     │
├─────────────────────────────────────────────────────────┤
│  Copilot Node (backend: sampling)                       │
│    ↓ session.create_message() ← loops back to host LLM  │
└─────────────────────────────────────────────────────────┘
```

## Running the Demo

### 1. Start YAMLGraph MCP Server

Ensure `.mcp.json` includes:

```json
{
  "mcpServers": {
    "yamlgraph": {
      "command": ".venv/bin/python3",
      "args": ["yamlgraph/mcp_server.py"]
    }
  }
}
```

### 2. Run via Copilot/Claude

In VS Code Copilot Chat or Claude:

```
Run the copilot-mcp-demo graph with topic="The future of programming languages" and perspective="economics"
```

The MCP server will:
1. Receive the `yamlgraph_run_graph` call
2. Execute the graph with `backend: sampling` nodes
3. Each copilot node calls `session.create_message()` — looping back to the host LLM
4. Return the final synthesis

### 3. Expected Output

```json
{
  "analysis": {
    "output": "...",
    "backend": "sampling"
  },
  "critique": {
    "output": "...",
    "backend": "sampling"
  },
  "synthesis": {
    "output": "...",
    "backend": "sampling"
  }
}
```

## Graph Structure

```
START → analyze → critique → synthesize → END
```

- **analyze**: Initial analysis of the topic
- **critique**: Reviews analysis from specified perspective
- **synthesize**: Combines both views into conclusion

## Requirements

- MCP SDK: `pip install yamlgraph[mcp]`
- MCP server running (auto-starts in VS Code with `.mcp.json`)
- Host that supports MCP sampling (Copilot, Claude)

## Note

This demo **cannot** be run via CLI (`yamlgraph graph run`) because `backend: sampling` requires MCP server context. For CLI usage, see `examples/copilot/` which uses `backend: cli`.
