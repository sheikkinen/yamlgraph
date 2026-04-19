# A2A Call Demo (Contrib Client)

Demonstrates calling an external A2A agent via `type: python` +
`yamlgraph.contrib.a2a_client` (FR-253). Replaces the former `type: a2a_call`
dedicated node with a contrib function invoked through the standard python node.

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
   - Sends `name=World style=casual` to the A2A server via `ask_agent` python node
   - Passes the response to a local `summarise` LLM node
3. Stops the server

## Pipeline

```
START → ask_agent (python: a2a_client) → summarise (llm) → END
```

## Key Concepts

- **`type: python`** — Invokes `yamlgraph.contrib.a2a_client.send_a2a_message`
- **`variables:`** — Injects `agent_url`, `message`, `timeout` into state (FR-252)
- **`yamlgraph.contrib.a2a_client`** — Contrib function for A2A consumer calls
- **Agent Card** — Auto-fetched from `/.well-known/agent.json` when `skill:` specified

## Files

```
a2a_call/
├── graph.yaml          # Graph with python (a2a_client) + llm nodes
├── prompts/
│   └── summarise.yaml  # Prompt for the local LLM summariser
├── demo.sh             # Orchestrates server + graph run
└── README.md
```

## Requirements

- An LLM API key (e.g. `ANTHROPIC_API_KEY`) for both the A2A server and the summarise node
