# Five Whys Demo

Iterative root cause analysis using the Five Whys technique. Given a problem statement, the pipeline asks "why?" five times, each iteration digging deeper into the underlying cause, then synthesises a summary with actionable recommendations.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/five-whys/graph.yaml

# Run the graph
yamlgraph graph run examples/demos/five-whys/graph.yaml \
  --var problem="Deployment failed on Friday" --full
```

## What It Does

1. Takes a `problem` statement as input
2. Asks "why?" five times, each iteration building on the previous answer chain
3. Synthesises a root cause summary with recommendations
4. Exports the analysis as `root_cause_analysis.md`

## Pipeline

```
START → ask_why ──┐
           ↑      │ (loop 5 times)
           └──────┘
              │
              ▼ (after 5 iterations)
          summarise → END
```

## Key Concepts

- **Fixed-count loop** — `condition: _loop_counts.ask_why < 5` controls iteration count
- **Progressive deepening** — Each iteration receives the full answer chain via Jinja2
- **`skip_if_exists: false`** — Ensures the node re-executes every iteration
- **`loop_limits` + `loop_exits`** — Safety guards against infinite loops
- **Structured accumulation** — LLM returns the full `chain` list each time (no custom reducer needed)
- **Exports** — Produces `root_cause_analysis.md` via `exports` config
- **Jinja2 iteration** — `{% for answer in previous.chain %}` renders prior answers in the prompt

## Files

```
five-whys/
├── graph.yaml          # Graph definition with loop and export
├── README.md
└── prompts/
    ├── ask_why.yaml    # Iterative why prompt with chain accumulation
    └── summarise.yaml  # Final synthesis prompt
```

## Learning Path

Try [hello](../hello/) first for basics, then [reflexion](../reflexion/) for quality-gate loops. This demo shows the complementary **fixed-count accumulation loop** pattern.
