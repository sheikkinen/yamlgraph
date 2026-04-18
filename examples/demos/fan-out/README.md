# Parallel Fan-Out Demo

Demonstrates parallel fan-out edges (FR-234), where a single node fans out
to multiple concurrent branches using `to: [a, b, c]` syntax.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/fan-out/graph.yaml

# Run the graph
yamlgraph graph run examples/demos/fan-out/graph.yaml \
  --var topic="quantum computing" --full
```

## What It Does

1. **generate** — Writes a short paragraph about the topic
2. **Fan-out** — Three branches run concurrently:
   - **analyze** — Identifies key themes
   - **summarize** — Produces a one-sentence summary
   - **translate** — Translates to Finnish
3. **combine** — Merges all three outputs into a final report

## Pipeline

```
START → generate → ┬─ analyze   ─┬→ combine → END
                   ├─ summarize ─┤
                   └─ translate ─┘
```

## Key Concepts

- **`to: [a, b, c]`** — Parallel fan-out (no `type: conditional`)
- **Fan-in** — Multiple edges converging on `combine`; LangGraph waits for all
- **Contrast with conditional** — `type: conditional` picks ONE target; fan-out runs ALL

## Files

```
fan-out/
├── graph.yaml          # Graph with parallel fan-out edge
├── prompts/
│   ├── generate.yaml   # Content generation
│   ├── analyze.yaml    # Theme analysis (parallel branch)
│   ├── summarize.yaml  # Summarization (parallel branch)
│   ├── translate.yaml  # Translation (parallel branch)
│   └── combine.yaml    # Fan-in combiner
└── README.md
```
