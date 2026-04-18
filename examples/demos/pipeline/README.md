# Pipeline Template Demo

Demonstrates the `type: pipeline` meta-node (FR-235), which expands a list of
items × stages into concrete nodes at compile time — eliminating repetitive
boilerplate in multi-step sequential graphs.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/pipeline/graph.yaml

# Run the graph
yamlgraph graph run examples/demos/pipeline/graph.yaml \
  --var audience="5-year-olds" --full
```

## What It Does

1. Defines 3 topics (Sun, Moon, Stars) and 2 stages (draft → polish)
2. At compile time, expands into 6 concrete nodes chained sequentially
3. Each topic gets drafted then polished before moving to the next

## Expanded Pipeline

```
START
  → topics__sun__draft → topics__sun__polish
  → topics__moon__draft → topics__moon__polish
  → topics__stars__draft → topics__stars__polish
  → END
```

## Key Concepts

- **`type: pipeline`** — Compile-time template expansion (not a runtime node)
- **`items`** — List of data items to iterate over
- **`stages`** — Sequence of node templates applied to each item
- **`{item.field}`** — Interpolation syntax for item values in stage configs

## Files

```
pipeline/
├── graph.yaml          # Graph with pipeline template node
├── prompts/
│   ├── draft.yaml      # First stage: write a draft
│   └── polish.yaml     # Second stage: polish the draft
└── README.md
```
