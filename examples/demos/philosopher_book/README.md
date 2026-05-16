# Philosopher's Book Demo

FR-404 demo generating a 21-chapter philosophical work — one chapter per cognitive trap from the Knowledge Graph.

## What this demonstrates

1. Sequential `map` over 21 items (traps) with `copilot` sub-nodes
2. `copilot` nodes with diary search tools (`search_diary`, `read_file`)
3. Python tools providing hardcoded stable enumeration (`load_trap_list`)
4. `assemble_book` Python node producing structured markdown output

## Pipeline

1. `load_trap_list`: returns all 21 traps with part/chapter/title/definition/cure
2. `plan_book`: copilot node reads letter-to-the-philosopher, plans the arc
3. `write_chapters`: sequential map × 21, each copilot node searches diary and writes a chapter
4. `write_epilogue`: copilot node argues every trap traces to the One Law (boundary violation)
5. `assemble_book`: assembles title page, TOC, chapters, epilogue → `philosopher-book.md`

## Running

```bash
./examples/demos/philosopher_book/demo.sh
```

Or directly:

```bash
yamlgraph graph run examples/demos/philosopher_book/graph.yaml \
  --var output_dir="outputs/philosopher-book"
```

Output: `outputs/philosopher-book/philosopher-book.md`

## Architecture notes

- `tools.py` hardcodes the 21 traps (stable Knowledge Graph enumeration)
- `read_file` validates path prefixes (`docs/`, `.github/`, `feature-requests/`) at the boundary
- `sequential: true` on the map node prevents API rate limiting
- `on_error: skip` allows partial book generation if some chapters fail
