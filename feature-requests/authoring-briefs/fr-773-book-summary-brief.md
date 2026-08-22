# Task: book-summary demo — manifest-fed map/reduce over PDF pages (FR-773)

Create `examples/demos/book-summary/` — a demo graph that summarizes a book
PDF page-by-page and reduces the page summaries into one book summary.

## Frozen constraints (FR-773 judgement — binding)

- Graph: `examples/demos/book-summary/graph.yaml`
- The splitter tool MUST be declared via manifest only (FR-768 syntax):

  ```yaml
  tools:
    split_document:
      manifest: ../../shared/split_document.tool.yaml
  ```

  No inline runtime keys — the tools entry must contain EXACTLY the
  `manifest` key. Do NOT create any new tool implementation; the shared
  splitter `examples/shared/split_document.py` and its manifest
  `examples/shared/split_document.tool.yaml` already exist.

- Node 1 — `split` (type `tool_call`, tool `split_document`) with inline
  kwargs (FR-772 syntax), state_key `split_result`:

  ```yaml
  args:
    path: "{state.pdf}"
    mode: page
  ```

- Node 2 — `summarize_pages`: map node fanning out over
  `"{state.split_result.result.chunks}"`, item var `chunk`, collecting
  into `page_summaries`. Each branch calls an LLM prompt
  `summarize_page` that summarizes `{chunk.text}` (a single page of a
  book) in 1-2 sentences. Plain text output, no schema needed.

- Node 3 — `combine_summaries`: LLM node with prompt `combine_summaries`
  that joins the page summaries (Jinja2 loop over `page_summaries`) into
  one coherent book summary, state_key `book_summary`.

- Edges: START -> split -> summarize_pages -> combine_summaries -> END.

- Graph variables: `pdf` (path to the PDF; demo default
  `examples/demos/book-summary/fixture.pdf` — a committed 2-page fixture
  that already exists).

- Prompts live in `examples/demos/book-summary/prompts/`.
- Keep it minimal: 3 nodes, 2 prompts, no error-handling scaffolding
  beyond defaults. Provider defaults (no pinning).

## Validation

- `yamlgraph graph lint examples/demos/book-summary/graph.yaml` clean.
- Smoke: `yamlgraph graph run examples/demos/book-summary/graph.yaml
  --var pdf=examples/demos/book-summary/fixture.pdf` — judged by graph
  state evidence: `split_result.success` true, total == len(chunks) == 2,
  2 page summaries, non-empty `book_summary`.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
