# Router Candidates Race Demo

Demonstrates FR-272: `type: router` with `candidates` to race providers and route
using the first valid result.

## Usage

```bash
# Validate
yamlgraph graph lint examples/demos/router-race-candidates/graph.yaml

# Run
yamlgraph graph run examples/demos/router-race-candidates/graph.yaml \
  --var user_query="My invoice was charged twice this month." --full
```

## What It Demonstrates

1. A router node can use `candidates` instead of a single `provider`.
2. The winning candidate determines the route via `route_field`.
3. `_race_winner` is recorded in state for telemetry.
4. Route handlers are deterministic `type: tool` nodes for easy local execution.

## Files

```text
router-race-candidates/
├── graph.yaml
├── prompts/
│   └── classify_intent.yaml
├── README.md
└── demo-output.log
```
