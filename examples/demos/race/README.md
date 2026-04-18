# Race Node Demo

Demonstrates the `type: race` node (FR-232), which fires the same prompt to
multiple LLM providers concurrently and returns the fastest successful response.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/race/graph.yaml

# Run the graph
yamlgraph graph run examples/demos/race/graph.yaml \
  --var topic="quantum computing" --full
```

## What It Does

1. Takes a `topic` as input
2. Sends the prompt to Anthropic, OpenAI, and Google concurrently
3. Returns whichever provider responds first
4. Reports the winning provider in `_race_winner` state

## Pipeline

```
START → fastest_answer (race) → END
```

## Key Concepts

- **`type: race`** — Concurrent multi-provider execution
- **`candidates`** — List of provider/model pairs to race
- **`timeout`** — Per-candidate timeout in seconds
- **`_race_winner`** — State field reporting which provider won

## Files

```
race/
├── graph.yaml          # Graph with race node
├── prompts/
│   └── answer.yaml     # Shared prompt for all candidates
└── README.md
```

## Requirements

At least two of these API keys must be set:
- `MISTRAL_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
