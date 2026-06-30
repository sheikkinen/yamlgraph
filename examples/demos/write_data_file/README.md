# Write Data File Demo — Accumulating World Bible

Demonstrates the `write_data_file` tool type (FR-625) in a read→augment→write-back
cycle. Each invocation reads an existing YAML "world bible", integrates new facts
via LLM, and writes the updated bible back — accumulating knowledge across runs.

## What it demonstrates

- `data_files` directive: loads `wiki/world.yaml` into state at compile time
- `type: write_data_file` tool: persists LLM-structured output back to YAML
- Inline schema: enforces consistent world bible structure via Pydantic
- Jinja2 templates: renders existing wiki for the LLM prompt
- **Zero custom Python** — entire demo is YAML-only

## Usage

```bash
# Run 1 — introduce a character
yamlgraph graph run examples/demos/write_data_file/graph.yaml \
  --var new_fact="Kael is a wandering blacksmith who lost his forge in the Ashfall." \
  --full

# Run 2 — add a location
yamlgraph graph run examples/demos/write_data_file/graph.yaml \
  --var new_fact="The Crimson Bazaar is a floating market above the salt flats, visited by traders from three kingdoms." \
  --full

# Run 3 — connect them with an event
yamlgraph graph run examples/demos/write_data_file/graph.yaml \
  --var new_fact="Kael arrived at the Crimson Bazaar seeking dragonsteel, but found only rumors of a sealed vault beneath the salt." \
  --full
```

After each run, inspect `wiki/world.yaml` to see accumulated knowledge.

## Pattern: Read → Augment → Write-Back

```
┌──────────────┐      ┌───────────┐      ┌──────────────┐
│  data_files  │─────▶│  LLM node │─────▶│write_data_file│
│  (compile)   │      │ (compress)│      │  (persist)   │
└──────────────┘      └───────────┘      └──────────────┘
       ▲                                         │
       │            wiki/world.yaml              │
       └─────────────────────────────────────────┘
```

This pattern enables persistent, cross-run memory without databases or
custom Python — useful for knowledge bases, character bibles, project
wikis, and incremental data accumulation.
