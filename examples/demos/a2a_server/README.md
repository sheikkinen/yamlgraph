# A2A Server Demo

Demonstrates exposing YAMLGraph graphs as [A2A protocol](https://google.github.io/A2A/) agents.

## What it shows

- **Agent Card generation** — `yamlgraph a2a card` produces a standards-compliant Agent Card from graph metadata
- **Server startup** — `yamlgraph a2a serve` starts an HTTP server exposing graphs as A2A agents
- **Task lifecycle** — clients send tasks via JSON-RPC, receive structured responses

## Quick start

```bash
# View the Agent Card (no API key needed)
yamlgraph a2a card examples/demos/hello/

# Start the A2A server (requires LLM API key for task execution)
yamlgraph a2a serve examples/demos/hello/ --port 9090

# In another terminal, fetch the Agent Card
curl http://localhost:9090/.well-known/agent.json

# Send a task
curl -X POST http://localhost:9090/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tasks/send",
    "params": {
      "id": "demo-task-1",
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "name=World style=casual"}]
      }
    }
  }'
```

## How it works

The A2A server reuses the same graph discovery as the MCP server (CAP-19).
Each discovered graph becomes an A2A skill. The server maps A2A task lifecycle
(`tasks/send`, `tasks/get`, `tasks/cancel`) to LangGraph graph execution.
