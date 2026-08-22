# Task: harden examples/demos/book-summary for scale (FR-774)

Modify the EXISTING demo `examples/demos/book-summary/` — do not restructure
it. Three nodes (split → summarize_pages → combine_summaries) stay; only the
changes below are in scope.

## Frozen constraints (FR-774 judgement — binding)

1. `graph.yaml` — the `split` node's `args` gain two keys (the shared
   splitter `examples/shared/split_document.py` already supports them):

   ```yaml
   args:
     path: "{state.pdf}"
     mode: page
     pages_per_chunk: 10
     min_chars: 200
   ```

   `summarize_pages` keeps `max_items: 100` (documented budget:
   10 pages/chunk × 100 chunks = 1000 pages). The tools entry stays
   manifest-only (`manifest: ../../shared/split_document.tool.yaml`).
   Everything else in the graph is unchanged.

2. `prompts/summarize_page.yaml` — chunk/excerpt semantics (R-3), strict
   output contract (R-2 of FR-774): the input is a multi-page excerpt of
   a book (`{{ chunk.text }}`), NOT a single page. Instruct: summarize
   the excerpt in 3-5 sentences; output ONLY the summary text — no
   preamble, no headings, no commentary about blank, sparse, or
   repeated regions. The word "excerpt" must appear in the prompt.
   Do not use the phrase "single page".

3. `prompts/combine_summaries.yaml` — the inputs are excerpt summaries
   in book order, not page summaries. Label loop items as excerpts
   (e.g. "Excerpt {{ loop.index }}") — the literal text "Page {{" must
   not appear. Instruct: ignore empty items; never invent page numbers;
   output only the combined book summary.

## Validation

- `yamlgraph graph lint examples/demos/book-summary/graph.yaml` clean.
- Smoke: `yamlgraph graph run examples/demos/book-summary/graph.yaml
  --var pdf=examples/demos/book-summary/fixture.pdf` — the 2-page
  fixture batches into 1 chunk (pages_per_chunk=10) that survives
  min_chars=200; expect `split_result.success` true, 1 chunk, 1 excerpt
  summary, non-empty `book_summary`, and NO truncation warning.
- These committed-artifact tests must pass afterwards:
  `pytest tests/unit/test_fr774_scale_hardening.py -q --no-cov`
  (test_demo_graph_batches_and_filters, test_demo_cap_covers_reported_418_page_case,
  test_prompts_speak_excerpt_not_single_page).

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
