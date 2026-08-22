# Task: Redesign examples/demos/book-summary as a cursor-loop showcase (FR-775)

Governing FR: feature-requests/FR-775-book-summary-loop-redesign.md (judged
APPROVED WITH REVISIONS; judgement in the sibling .judgement.md). This brief
implements the frozen design. The RED suite that must go green is
tests/unit/test_fr775_loop_redesign.py — its 6 artifact tests pin the exact
graph/prompt shape below. Do NOT deviate from node names, args, or wiring.

## Already in place (do not re-create; commit tools.py with your changes)

- examples/shared/split_document.py supports `mode: info` ({"total": int}),
  `allow_empty_selection: true`, and absolute page metadata per chunk
  (`page` for single-page chunks). Manifest: examples/shared/split_document.tool.yaml.
- examples/demos/book-summary/tools.py exists in the working tree (UNSTAGED —
  it must be part of your demo change set) with functions:
  `gate_probe`, `prepare_batch`, `gate_fetch`, `accumulate`, `advance`.
  gate_fetch exposes chunks via state key `chunks`; accumulate returns an
  `all_summaries` fragment for an `add` reducer; advance moves cursor by 10.

## Rewrite examples/demos/book-summary/graph.yaml

Pedagogical goal: showcase tool manifests, python tool nodes, map fan-out,
state reducers, and a bounded loop — with per-page LLM calls small models
can handle.

Shape (exact node names, required by tests):

```
START → probe → gate_probe → prepare_batch → fetch_batch → gate_fetch
      → summarize_pages (map) → accumulate → advance
      → [cursor <= total → prepare_batch | else → combine] → END
```

- `recursion_limit: 5000` (top-level; 100 iterations × ~6 nodes + map sends).
- `loop_limits: {advance: 100}` and `loop_exits: {advance: combine}` —
  advance is both the budget carrier and the router source; when the limit
  hits, routing exits to combine with whatever was accumulated.
- state:
  - `pdf: str`
  - `probe_result: dict`, `fetch_result: dict`
  - `total: int`, `cursor: int`, `batch_start: int`, `batch_end: int`
  - `chunks: list` (overwritten every iteration — must NOT accumulate)
  - `page_summaries: list` (map collect key)
  - `all_summaries: {type: list, reducer: add}` (accumulated fragments)
  - `book_summary: str`
- tools: keep `split_document: {manifest: ../../shared/split_document.tool.yaml}`;
  add the demo-local python tools loaded file-based (hyphenated dir — module
  import will not work): `path: tools.py` with the function names above.
- nodes (exact args, pinned by tests/unit/test_fr775_loop_redesign.py):
  - `probe`: tool_call split_document, args `path: "{state.pdf}"`,
    `mode: info`, state_key probe_result.
  - `gate_probe`: python node → tools.py gate_probe (raises on failed
    envelope; seeds total + cursor=1).
  - `prepare_batch`: python node → prepare_batch (batch_start=cursor,
    batch_end=min(cursor+9, total) — NO arithmetic in YAML args).
  - `fetch_batch`: tool_call split_document, args exactly:
    `path: "{state.pdf}"`, `mode: page`, `start: "{state.batch_start}"`,
    `end: "{state.batch_end}"`, `pages_per_chunk: 1`, `min_chars: 0`,
    `allow_empty_selection: true`, state_key fetch_result.
  - `gate_fetch`: python node → gate_fetch.
  - `summarize_pages`: map, `over: "{state.chunks}"`, `as: chunk`,
    `max_items: 10`, subnode prompt summarize_page, state_key page_summary,
    `skip_if_exists: false`, collect page_summaries.
  - `accumulate`: python node → accumulate.
  - `advance`: python node → advance.
  - `combine`: llm node, prompt combine_summaries, state_key book_summary,
    variables `all_summaries: "{state.all_summaries}"`.
- edges: linear as in the shape above, plus conditional from advance:
  `condition: "cursor <= total"` → prepare_batch, fallback → combine,
  and combine → END.

## Prompts (examples/demos/book-summary/prompts/)

- `summarize_page.yaml`: summarize ONE page. Inputs: `{{chunk.text}}` and
  `{{chunk.page}}`. Structured output schema (inline):
  `schema: {name: PageSummary, fields: {page: {type: int, description: echo
  the provided page number exactly}, summary: {type: str, description: 2-3
  sentence summary; empty string if the page has no meaningful text}}}`.
  The user template MUST reference `chunk.page` literally (test-pinned) and
  instruct the model to echo the given page number and return an empty
  summary for blank pages. Excerpt semantics: summarize only what is on the
  page, never invent context.
- `combine_summaries.yaml`: combine the ordered `{page, summary}` list in
  `all_summaries` into one coherent book summary. Must instruct: ignore
  entries with empty summaries; never invent pages; preserve narrative order.

## README.md rewrite

Component tour: name each showcased framework feature (tool manifest,
tool_call, python nodes, map fan-out with collect, `add` reducer,
loop_limits/loop_exits, conditional edges, inline prompt schemas).
Explain the page-identity accumulation (why _map_index restarts per batch
and why absolute pages are the cure). State the finite budget: loop_limits
100 × 10-page windows = 1000 pages covered. Do NOT use the words
"unbounded" or "any book" anywhere. Include run instructions with
`--var pdf=...`.

## Validation (required)

- `yamlgraph graph lint examples/demos/book-summary/graph.yaml`
- Smoke: `yamlgraph graph run examples/demos/book-summary/graph.yaml
  --var pdf=examples/demos/book-summary/fixture.pdf --full 2>&1 | tee
  examples/demos/book-summary/demo-output.log` (2-page fixture → 1 loop
  iteration; expect non-empty all_summaries and book_summary).
- `pytest tests/unit/test_fr775_loop_redesign.py -q --no-cov` — ALL tests
  must pass, including test_forced_loop_limit_routes_to_combine (compiles
  this graph with mocked poppler + mocked execute_prompt).
- `pytest tests/unit/test_fr773_document_splitter.py
  tests/unit/test_fr774_scale_hardening.py -q --no-cov` must stay green.

Constraints: examples/** only — no yamlgraph/ core changes (judgement C-2).
Do not touch tmp/book1.pdf. Do not add OCR/vision or parallel-batch claims.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
