# FR-775: Book-Summary Loop Redesign — Per-Page Summaries via Batched Tool Loop

**Status:** Judged 2026-08-05 — APPROVED WITH REVISIONS; R-1..R-5 folded below; authority active per judgement

**Prior art:** FR-773 (book-summary demo + shared splitter), FR-774 (scale
hardening: `pages_per_chunk`/`min_chars`, 1000-page budget), FR-238 (YAML
state reducers), FR-172 (`loop_exits`), `reference/graph-yaml.md` §Sequential
Pipeline with Shared Context (add-reducer accumulation, W021
`skip_if_exists: false`), §Loop Limits, §Self-Correction Loop. Loops as such
are well-precedented in committed demos — five-whys, wiki-memory, reflexion,
compaction all loop, and safety-guards already combines a loop-guarded cycle
with a map fan-out (judgement R-5 disposition). The accurate gap is narrower:
no cited demo combines shared splitter manifest + batched cursor loop +
per-page map fan-out + cross-iteration reducer accumulation + final LLM
reduction in one artifact. FR-774 is superseded in demo *shape* but its
splitter mechanics (batching, filtering, failure modes, tests) are reused as
the loop's fetch primitive, extended only as R-1/R-2/R-3 specify.

## Summary

Redesign `examples/demos/book-summary` from "one LLM call per 10-page
excerpt" to "loop over 10-page batches; one LLM call **per page**". The
FR-774 shape requires a long-context-capable model to comprehend a 10-page
excerpt in one call and demonstrates only a linear tool→map→reduce pipeline.
The operator's verdict after running it: *"it requires a bigger model and
falls short to demonstrate yamlgraph."* The redesigned demo summarizes one
page per call (small-model friendly) and showcases the framework's actual
breadth: tool manifests, tool_call with computed args, a python cursor node,
an expression router forming a loop with `loop_limits`/`loop_exits`, map
fan-out, YAML state reducers for cross-iteration accumulation, and an LLM
reducer.

## Value Statement

For whom: a developer evaluating yamlgraph, asking "what can a YAML graph
actually do?" What pain: the current demo works only with large-context
models and reads as a trivial three-node pipeline — it undersells the
framework and fails on the default small model. Versus what alternative:
raising the model requirement (hides the problem, showcases nothing) or a
separate loop demo (leaves book-summary broken as a demo and splits the
narrative). The first consumer is the demo reader; the firing moment is
`./examples/demos/demo.sh` / README walkthrough on a default provider.

## Problem

1. **Model-size coupling.** `pages_per_chunk: 10` concatenates ~10 pages
   (~20-30k chars) into one prompt. Small/default models truncate, drift, or
   summarize only the head. One page per call keeps context ~2-3k chars —
   any model handles it.
2. **Showcase failure.** The demo exercises tool_call → map → llm linearly.
   No loop, no router, no python node, no state reducer, no cursor state —
   the components that distinguish yamlgraph from a shell script are absent.
3. **Flat fan-out ceiling.** A flat map over all pages needs
   `max_items >= page_count`. The loop bounds fan-out at 10 per iteration;
   the budget moves to `loop_limits` where it is explicit and documented.

## Ideal Result

A reader opens `examples/demos/book-summary`, sees a graph that loops over a
book in 10-page batches — fetch batch (tool manifest), summarize each page
in parallel (map), accumulate summaries across iterations (state reducer),
advance a cursor (python node), decide continue-or-finish (expression router
with loop_limits/loop_exits), combine everything (LLM reducer) — runs it on
a real 400-page book with the default provider's small model, and gets a
coherent whole-book summary. The README names each yamlgraph component the
graph demonstrates. The demo is the framework tour.

## Proposed Solution (revised per judgement — R-1..R-4 folded)

Graph shape (authored solely via `scripts/author.sh`, FR-767):

```
START → probe (mode: info) → gate_probe → prepare_batch → fetch_batch
                                   ↑                          ↓
                                   │                     gate_fetch
                                   │                          ↓
                              advance ← accumulate ← summarize_pages (map)
                                   ↓ router: cursor > total?
                                combine (LLM reducer) → END
```

- **probe** (R-1): `split_document(path, mode=info)` — new CAP-218 mode
  returning `{"total": int}` from `pdfinfo` alone, no `pdftotext` call. No
  text extraction just to learn the page count; a blank first page cannot
  kill the run before the loop starts.
- **gate_probe / gate_fetch** (R-4): python gate nodes that raise with the
  envelope `error` when `tool_call` `success` is false. A failed envelope
  never reaches `summarize_pages`, `accumulate`, or `combine`. Mechanically
  testable failures: missing poppler, bad page range, forced fetch failure.
- **prepare_batch** (R-1): python (or passthrough) node computing
  `batch_start: cursor` and `batch_end: min(cursor + 9, total)`. No
  arithmetic in `tool_call.args` — args reference only resolved state
  values.
- **fetch_batch** (R-1/R-2): `split_document(path, mode=page,
  start={state.batch_start}, end={state.batch_end}, pages_per_chunk=1,
  min_chars=0, allow_empty_selection=true)` → ≤10 per-page chunks. New
  `allow_empty_selection: bool = False` splitter kwarg: default preserves
  FR-774's loud all-empty/all-filtered failures; the loop fetch path opts in
  because a blank 10-page window inside a valid 418-page book is normal, not
  fatal. No `min_chars=200` in the loop path.
- **summarize_pages** (R-3): map over batch chunks, `max_items: 10`,
  `skip_if_exists: false` (W021). Per-page chunks carry absolute
  `page: int` metadata (batched chunks: `page_start`/`page_end`) — CAP-218
  extension. Prompt uses structured Pydantic schema `{page: int,
  summary: str}`, echoing the *provided* absolute page number (echoing is
  not inventing). Blank/sparse pages yield `summary: ""`.
- **accumulate** (R-3): python node filters the map collect key to entries
  with `batch_start <= page <= batch_end`, verifies each non-empty summary
  page belongs to the current `fetch_batch.result.chunks`, sorts by `page`,
  and returns ONLY that new ordered fragment as `{"all_summaries": [...]}`
  — the `add` reducer performs the append; the node never reads existing
  `all_summaries` and returns a combined list. This kills the `sorted_add`
  `_map_index`-restart interleave by page identity, not by index
  reconstruction.
- **advance**: `cursor: cursor + 10`.
- **router**: expression router — `cursor <= total` → prepare_batch, else →
  combine. `loop_limits: {fetch_batch: 100}` (10 pages × 100 iterations =
  1000-page budget, README states it) with `loop_exits: {fetch_batch:
  combine}` so a limit-hit still combines what was gathered.
- **combine**: LLM reducer over `all_summaries`, ignoring empty summaries,
  never inventing page numbers.

## Non-Goals

- No vision/OCR fallback (FR-774 C-6 stands; error signposting retained).
- No changes to `yamlgraph/` core — loop, reducers, routers all exist; if
  the design cannot be expressed without core changes, that is a finding
  to escalate, not silently implement (FR-774 C-2 precedent).
- No unbounded book support; budget stays finite and documented.
- No parallel batch processing — the loop is deliberately sequential; that
  is the point of demonstrating a loop.

## Acceptance Criteria (revised per judgement — binding set)

- [ ] AC-01: The FR prior-art section names existing loop demos and narrows
      the novelty claim to the combined shared-splitter + batched loop +
      per-page map + cross-iteration accumulation + final reducer shape.
- [ ] AC-02: `split_document` supports `mode: info` without `pdftotext`,
      `allow_empty_selection: false` by default, and absolute page metadata
      (`page` for per-page chunks, `page_start`/`page_end` for batched
      chunks); defaults preserve FR-774 failure behavior when
      `allow_empty_selection` is omitted.
- [ ] AC-03: The graph obtains total pages from `mode: info`, computes
      `batch_start` and `batch_end` in a python or passthrough node, and
      `fetch_batch.args` reference only state values, not inline arithmetic.
- [ ] AC-04: `fetch_batch` uses `pages_per_chunk=1`, `min_chars=0`, and
      `allow_empty_selection=true`; each summarization LLM call receives at
      most one page of text and a structured `{page, summary}` output
      schema, with blank/sparse pages represented as empty summaries.
- [ ] AC-05: A mocked witness with at least 3 loop batches and repeated
      `_map_index` values proves `all_summaries` contains each non-empty
      page summary exactly once, sorted by absolute page, with no
      interleaving or duplicate append.
- [ ] AC-06: Loop termination tests cover exact-multiple and partial final
      batches, plus a forced `loop_limits` hit that routes to `combine`
      through `loop_exits`; the README states the 1000-page budget and
      makes no unbounded claim.
- [ ] AC-07: Probe and fetch failure envelopes are gated before map/reduce;
      tests prove failed `tool_call` results do not reach
      `summarize_pages`, `accumulate`, or `combine`.
- [ ] AC-08: Governed graph/prompt edits are authored via
      `scripts/author.sh`; `tmp/draft-authoring-report.md` records graph
      lint and a smoke attempt for `examples/demos/book-summary/graph.yaml`.
- [ ] AC-09: Committed `demo-output.log` proves fixture success with at
      least one loop iteration, `split/fetch success` true for every
      executed fetch, non-empty `all_summaries`, non-empty `book_summary`,
      and no truncation warning.
- [ ] AC-10: Real-book witness on `tmp/book1.pdf` is recorded in FR
      Implementation Status with `total == 418`, 42 planned fetch windows,
      first/middle/last absolute page summaries in increasing order,
      non-empty `book_summary`, zero tool failures, and zero truncation
      warnings.
- [ ] AC-11: New/changed tests carry `@pytest.mark.req` markers;
      CAP-218/REQ-YG-577 is updated for splitter behavior; no `yamlgraph/`
      files change.
- [ ] AC-12: Changelog fragment and diary reflection are included.

## Alternatives Considered

- **Raise model size / keep 10-page excerpts:** hides the framework, keeps
  the demo model-coupled — rejected by operator verdict.
- **Flat map over all pages (`max_items: 500`):** no loop showcased; fan-out
  budget becomes a magic number; 418 parallel branches hammer rate limits.
- **Subgraph-per-batch map:** showcases subgraphs but nests fan-out and
  obscures the loop; heavier than the pain requires.
- **Separate loop demo, book-summary untouched:** splits the narrative and
  leaves book-summary as a bad demo.

## Related

- FR-773 (demo + splitter), FR-774 (scale hardening — mechanics reused,
  demo shape superseded), FR-238 (state reducers), FR-172 (loop_exits)
- CAP-218 / REQ-YG-577 (extended if splitter gains absolute page spans)
