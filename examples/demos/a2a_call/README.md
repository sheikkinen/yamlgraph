# A2A Call Node Demo

Demonstrates the `type: a2a_call` node (FR-240), which sends a message to an
external A2A agent via HTTP JSON-RPC and stores the response in graph state.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/a2a_call/graph.yaml

# Run the full demo (starts server, runs graph, stops server)
bash examples/demos/a2a_call/demo.sh
```

## What It Does

1. Starts the hello-world graph as a local A2A server on port 9240
2. Runs the `a2a-call-demo` graph which:
   - Sends `name=World style=casual` to the A2A server via `ask_agent` node
   - Passes the response to a local `summarise` LLM node
3. Stops the server

## Pipeline

```
START → ask_agent (a2a_call) → summarise (llm) → END
```

## Key Concepts

- **`type: a2a_call`** — Calls an external A2A agent over HTTP JSON-RPC
- **`agent_url`** — URL of the target A2A server
- **`message`** — Jinja2 template rendered with state variables
- **`timeout`** — Request timeout in seconds

## Files

```
a2a_call/
├── graph.yaml          # Graph with a2a_call + llm nodes
├── prompts/
│   └── summarise.yaml  # Prompt for the local LLM summariser
├── demo.sh             # Orchestrates server + graph run
└── README.md
```

## Requirements

- An LLM API key (e.g. `ANTHROPIC_API_KEY`) for both the A2A server and the summarise node
