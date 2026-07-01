# Wiki Memory with Reference Gate

Demonstrates inter-run state accumulation with a deterministic integrity gate.

## Features Demonstrated

| Feature | Source |
|---------|--------|
| `data_files` glob (`wiki/*.yaml`) | FR-629 |
| `write_data_file` tool | FR-625 |
| Python gate node (deterministic) | FR-628 |
| Conditional edges + fix loop | Core |
| Inter-run state chaining | FR-120 |

## How It Works

```
draft → gate → (valid) → persist → END
               (invalid) → fix → gate  (loop limit: 2)
```

1. **Draft**: LLM creates a wiki page with references (no awareness of existing pages)
2. **Gate**: Python node checks all references resolve to existing wiki pages
3. **Fix**: If gate fails, LLM removes invalid references (sees existing page list)
4. **Persist**: Writes the page to `wiki/<id>.yaml` via `write_data_file`

Each run grows the wiki. Subsequent runs can reference pages created by earlier runs.

## Running

```bash
# Run 1: Create a page (gate may catch hallucinated refs)
yamlgraph graph run graph.yaml --var input="Node.js - server-side JavaScript runtime" --full

# Run 2: Reference the page from Run 1
yamlgraph graph run graph.yaml --var input="Express.js - web framework for Node.js" --full

# Run 3: Technology with many deps (gate will reject some)
yamlgraph graph run graph.yaml \
  --var input="Webpack - module bundler using tapable, Babel, PostCSS" --full
```

## Seed Pages

The wiki starts with 3 seed pages: `javascript`, `typescript`, `react`.
New pages written by the graph persist to disk and are loaded on next run.

## Key Design Decisions

- **Draft prompt does NOT see wiki**: This intentionally produces invalid refs,
  demonstrating the gate's value as a safety net.
- **Gate normalizes Pydantic → dict**: Boundary normalization for downstream nodes.
- **Gate computes save_path**: Avoids string interpolation limitations in variables.
