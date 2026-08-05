# FR-775: Book-Summary Loop Redesign — Per-Page Summaries via Batched Tool Loop

**Status:** Proposed 2026-08-05

**Prior art:** FR-773 (book-summary demo + shared splitter), FR-774 (scale
hardening: `pages_per_chunk`/`min_chars`, 1000-page budget), FR-238 (YAML
state reducers), FR-172 (`loop_exits`), `reference/graph-yaml.md` §Sequential
Pipeline with Shared Context (add-reducer accumulation, W021
`skip_if_exists: false`), §Loop Limits, §Self-Correction Loop. No existing
demo combines tool loop + map + reducer accumulation; `git log --oneline
--all -- examples/demos/ | grep -i loop` returns nothing demo-shaped. FR-774
is superseded in demo *shape* but its splitter mechanics (batching, filtering,
failure modes, tests) are reused unchanged as the loop's fetch primitive.

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

## Proposed Solution

Graph shape (authored solely via `scripts/author.sh`, FR-767):

```
START → probe → fetch_batch → summarize_pages (map, per page)
              ↑                    ↓
              └── advance (python) ← accumulate
                     ↓ router: cursor > total?
                  combine (LLM reducer) → END
```

- **probe**: `split_document(path, start=1, end=1)` — cheap call whose
  `total` yields the page count; python node (or the same tool result)
  seeds `cursor: 1`.
- **fetch_batch**: `split_document(path, mode=page, start={cursor},
  end={cursor+9}, pages_per_chunk=1, min_chars=200)` → ≤10 per-page chunks.
  Reuses FR-774 mechanics verbatim; `end` is clamped to `total` by the
  existing range logic.
- **summarize_pages**: map over batch chunks, `max_items: 10`,
  `skip_if_exists: false` (W021), prompt summarizes ONE page in 2-3
  sentences, summary-only output (FR-774 R-3 language retained).
- **accumulate + advance**: python node appends the batch's ordered
  summaries to `all_summaries` (state config `reducer: add`) and returns
  `cursor: cursor + 10`.
- **router**: expression router — `cursor <= total` → fetch_batch, else →
  combine. `loop_limits: {fetch_batch: 100}` (10 pages × 100 iterations =
  1000-page budget, README states it; FR-774 R-2 preserved) with
  `loop_exits: {fetch_batch: combine}` so limit-hit still combines what was
  gathered.
- **combine**: LLM reducer over `all_summaries`, excerpt/page semantics per
  FR-774 R-3, never inventing page numbers.

**Named design risk (from research, must be resolved at judge time):** the
map `collect` key is compiled with the `sorted_add` reducer keyed on
`_map_index`, which restarts 0..9 each iteration — reusing one collect key
across loop iterations interleaves batches (stable-sort artifact). Cure
candidates:
- (a) **Preferred**: chunks carry their absolute page numbers (small
  CAP-218 extension: `split_document` chunk dicts gain absolute page span
  when `start` is given); the per-page prompt uses a structured schema
  `{page: int, summary: str}` echoing the *provided* page number (echoing
  is not inventing — R-3 compatible); the accumulate python node sorts the
  current batch by `_map_index` before appending, and final order is
  batch-append order, verifiable by page fields.
- (b) Per-iteration collect-key slicing via stable-sort reconstruction —
  rejected: fragile, undemonstrable.

## Non-Goals

- No vision/OCR fallback (FR-774 C-6 stands; error signposting retained).
- No changes to `yamlgraph/` core — loop, reducers, routers all exist; if
  the design cannot be expressed without core changes, that is a finding
  to escalate, not silently implement (FR-774 C-2 precedent).
- No unbounded book support; budget stays finite and documented.
- No parallel batch processing — the loop is deliberately sequential; that
  is the point of demonstrating a loop.

## Acceptance Criteria

- [ ] AC-01: The demo graph contains, and the README names, each showcased
      component: tool manifest, tool_call with computed args, map fan-out,
      python node, expression router loop with `loop_limits` +
      `loop_exits`, YAML state reducer accumulation, LLM reducer.
- [ ] AC-02: Each summarization LLM call receives at most one page of text;
      no prompt concatenates multiple pages.
- [ ] AC-03: The loop fetches 10-page batches via `split_document` with
      `pages_per_chunk=1` within a `start`/`end` window; FR-773/774
      splitter tests remain green; any splitter extension (absolute page
      numbers) is covered by new req-marked tests under CAP-218.
- [ ] AC-04: Cross-iteration accumulation preserves page order — a
      mocked-poppler witness with ≥3 batches asserts final summary order
      matches page order (kills the sorted_add interleave risk with a test).
- [ ] AC-05: Loop terminates: cursor witness covers exact-multiple and
      partial final batch; `loop_limits` hit routes to combine via
      `loop_exits`, not END, and the budget (1000 pages) is stated in the
      README with no unbounded claim.
- [ ] AC-06: Graph/prompt edits authored solely via `scripts/author.sh`
      with `tmp/draft-authoring-report.md` evidence (lint + smoke).
- [ ] AC-07: Fixture smoke committed as `demo-output.log`: success, ≥1 loop
      iteration, non-empty accumulated summaries, non-empty book_summary,
      no truncation warnings.
- [ ] AC-08: Real-book witness: `tmp/book1.pdf` (418 pages) runs end-to-end
      on the default provider — 42 loop iterations, coherent summary,
      recorded in the FR Implementation Status (not committed as fixture).
- [ ] AC-09: RED committed before GREEN; all new tests carry
      `@pytest.mark.req` markers; CAP-218 updated; changelog fragment and
      diary reflection included; no `yamlgraph/` changes.

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
