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

## Editorial pass

FR-405 adds a separate editorial graph for revising generated chapter drafts
without overwriting them. It snapshots the input folder into the output folder,
builds a global editorial brief, edits each chapter via `type: map`, and writes
an `editorial-report.md`.

```bash
yamlgraph graph run examples/demos/philosopher_book/editorial_graph.yaml \
  --var input_dir="outputs/philosopher-book/chapters" \
  --var output_dir="outputs/philosopher-book/edited-chapters"
```

The editorial graph should be run only when you are ready to edit a stable set
of drafts. It writes to a separate output directory and preserves original
filenames.

## Architecture notes

- `tools.py` hardcodes the 21 traps (stable Knowledge Graph enumeration)
- `read_file` validates path prefixes (`docs/`, `.github/`, `feature-requests/`) at the boundary
- The editorial graph snapshots chapter inputs before editing so active
  generation cannot change the files mid-run
- The editorial graph uses Python tools for filesystem effects and LLM nodes
  only for prose judgement
