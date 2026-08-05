# Judgement: FR-775 Book-Summary Loop Redesign

**Verdict:** APPROVED WITH REVISIONS - the demo redesign is a sound contrib/example composition, but authority activates only after the FR fixes the page-count probe, blank-window splitter semantics, map-collect interleaving, and measurable witness criteria.

**Reviewed against:** `feature-requests/FR-775-book-summary-loop-redesign.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `feature-requests/FR-773-shared-document-splitter-manifest.md`; `feature-requests/FR-773-shared-document-splitter-manifest.judgement.md`; `feature-requests/FR-774-book-summary-scale-hardening.md`; `feature-requests/FR-774-book-summary-scale-hardening.judgement.md`; `feature-requests/FR-238-pipeline-accumulated-state-docs.md`; `feature-requests/FR-172-loop-exit-target.md`; `feature-requests/FR-772-tool-call-inline-dict-args.md`; `capabilities/CAP-218-shared-document-splitter.yaml`; `reference/graph-yaml.md`; `reference/tool-call-nodes.md`; `reference/map-nodes.md`; `examples/shared/split_document.py`; `examples/shared/split_document.tool.yaml`; `examples/demos/book-summary/graph.yaml`; `examples/demos/book-summary/README.md`; `examples/demos/book-summary/prompts/summarize_page.yaml`; `examples/demos/book-summary/prompts/combine_summaries.yaml`; `examples/demos/book-summary/demo-output.log`; `yamlgraph/models/state_builder.py`; `yamlgraph/compile/map_compiler.py`; current loop-demo prior art in `examples/demos/five-whys/graph.yaml`, `examples/demos/wiki-memory/graph.yaml`, `examples/demos/reflexion/graph.yaml`, `examples/demos/safety-guards/graph.yaml`, `examples/demos/novel_generator/graph.yaml`, and `examples/demos/compaction/graph.yaml`; repository searches for book-summary/loop prior art, including `git --no-pager log --oneline --all -- examples/demos/ | grep -i loop`.

## What is sound

The problem is real and example-scoped. The current book-summary demo is a linear `tool_call -> map -> llm` graph with `pages_per_chunk: 10`, `min_chars: 200`, and a `max_items: 100` map cap (`examples/demos/book-summary/graph.yaml:19-54`), and its README explicitly frames the demo as bounded excerpt summarization, not a loop or cursor tour (`examples/demos/book-summary/README.md:3-21`). FR-775 names the concrete weakness: the demo now makes one LLM call per 10-page excerpt and undersells loop, router, python-node, reducer, and cursor capabilities (`feature-requests/FR-775-book-summary-loop-redesign.md:17-27`, `feature-requests/FR-775-book-summary-loop-redesign.md:42-51`).

The proposed strategic class is **Contrib/example**, not a framework primitive. The required primitives already exist: `tool_call` inline dict args are documented for deterministic manifest invocation (`reference/graph-yaml.md:696-728`; `feature-requests/FR-772-tool-call-inline-dict-args.md:42-80`), feeder-tool output can drive map fan-out (`reference/graph-yaml.md:1473-1489`), python nodes are an existing node type (`reference/graph-yaml.md:441-463`), list reducers are user-configurable (`feature-requests/FR-238-pipeline-accumulated-state-docs.md:29-93`; `reference/graph-yaml.md:931-989`), and `loop_exits` exists for post-limit routing (`feature-requests/FR-172-loop-exit-target.md:31-111`; `reference/graph-yaml.md:1530-1557`). FR-775's non-goal of no `yamlgraph/` core changes is therefore architecturally correct (`feature-requests/FR-775-book-summary-loop-redesign.md:112-120`).

The FR identifies the hardest design risk instead of hiding it: map `collect` ordering is keyed on `_map_index`, and `_map_index` restarts each iteration (`feature-requests/FR-775-book-summary-loop-redesign.md:97-110`). That risk is real in the implementation: map collect fields are forced to `Annotated[list, sorted_add]` (`yamlgraph/models/state_builder.py:247-250`), `sorted_add` sorts by `_map_index` (`yamlgraph/models/state_builder.py:31-50`), and map sends enumerate each batch from zero (`yamlgraph/compile/map_compiler.py:350-365`).

The graph-authoring and TDD constraints are properly recognized. Graph/prompt edits must go through the authoring route with `tmp/draft-authoring-report.md` evidence (`.github/copilot-instructions.md:15`; `.github/skills/graph-authoring/doctrine.md:86-102`), tests require concrete requirement markers (`.github/copilot-instructions.md:173-176`), and repo doctrine requires failing tests before fixes (`.github/copilot-instructions.md:210-220`). FR-775 includes those process gates (`feature-requests/FR-775-book-summary-loop-redesign.md:141-151`).

## Required revisions

### R-1: Replace the first-page text probe and inline arithmetic with an explicit batch-planning contract

Revise `probe` and `fetch_batch` so the graph never depends on extracting text from page 1 just to learn `total`, and never places arithmetic inside `tool_call.args`. FR-775 currently proposes `split_document(path, start=1, end=1)` as the probe and `end={cursor+9}` in the fetch args (`feature-requests/FR-775-book-summary-loop-redesign.md:76-82`). That is not safe: `split_document` raises when the selected text extraction is all empty (`examples/shared/split_document.py:96-100`), so a blank first page can make a text PDF fail before the loop starts. It is also underspecified against the actual `tool_call` contract: inline args resolve per value as templates/literals, while arithmetic is documented for passthrough `output`, not for `tool_call.args` (`reference/graph-yaml.md:680-692`, `reference/graph-yaml.md:709-728`).

Fold this exact design into the FR: extend the shared splitter under CAP-218 with `mode: info`, returning `{"total": int}` from `pdfinfo` without calling `pdftotext`; use that as `probe`. Add a `prepare_batch` python or passthrough node that writes `batch_start: cursor` and `batch_end: min(cursor + 9, total)`. `fetch_batch.args` must use only resolved state values, e.g. `start: "{state.batch_start}"` and `end: "{state.batch_end}"`; no `{cursor+9}` or equivalent inline arithmetic is authorized in `tool_call.args`.

### R-2: Make blank-only windows non-fatal without weakening the default splitter failure contract

Replace `fetch_batch`'s proposed `min_chars=200` window call (`feature-requests/FR-775-book-summary-loop-redesign.md:79-82`) with an explicit loop-safe blank-window contract. FR-774 intentionally made `split_document` raise when threshold filtering removes every chunk (`feature-requests/FR-774-book-summary-scale-hardening.md:162-168`; `examples/shared/split_document.py:101-106`) and when a selected extraction is all empty (`examples/shared/split_document.py:96-100`). That is correct for whole-demo scale hardening, but a 10-page loop window can be blank or sparse inside an otherwise valid 418-page text PDF. Treating that window as "scanned/image-only PDF" or `min_chars` fatal would stop the loop and violate FR-775's real-book target (`feature-requests/FR-775-book-summary-loop-redesign.md:146-148`).

Fold this exact design into the FR: add `allow_empty_selection: bool = False` to `split_document`, documented and tested under CAP-218. The default remains FR-774's loud failure. `fetch_batch` must call `split_document(mode=page, start=batch_start, end=batch_end, pages_per_chunk=1, min_chars=0, allow_empty_selection=true)`. The per-page summarizer schema must allow `summary: ""` for blank or sparse pages, and the reducer must ignore empty summaries. Do not use `min_chars=200` in the loop fetch path.

### R-3: Resolve the collect-key interleave by page identity, not by `_map_index`

Make the preferred cure mandatory and complete. FR-775 correctly rejects reconstructing per-iteration slices from `_map_index` as fragile (`feature-requests/FR-775-book-summary-loop-redesign.md:97-110`), but it still describes the accumulate node as appending "the batch's ordered summaries" without specifying how it obtains only the current batch after the collect key has already accumulated prior loop results (`feature-requests/FR-775-book-summary-loop-redesign.md:86-88`). The implementation proves why this matters: `collect` fields always use `sorted_add` (`yamlgraph/models/state_builder.py:247-250`), the reducer sorts by `_map_index` (`yamlgraph/models/state_builder.py:31-50`), and map branches reissue `_map_index` as `0..n-1` every loop iteration (`yamlgraph/compile/map_compiler.py:363-365`).

Fold this exact design into the FR: `split_document` chunks returned for `pages_per_chunk=1` must include absolute `page: int` metadata, and batched chunks must include `page_start`/`page_end`. The page-summary prompt must use a structured Pydantic schema `{page: int, summary: str}` and echo the provided absolute page number. The accumulate python node must filter the accumulated map collect key to entries where `batch_start <= page <= batch_end`, verify each non-empty summary page belongs to the current `fetch_batch.result.chunks`, sort by `page`, and return only that new ordered fragment as `{"all_summaries": [...]}` for the `add` reducer. It must not read existing `all_summaries` and return the combined list, because the reducer itself performs the append (`reference/graph-yaml.md:931-989`).

### R-4: Add explicit tool-result gates before map and reduce stages

Revise the graph plan so a failed `tool_call` envelope cannot flow into a map or final reducer as if it were usable state. Tool-call nodes return structured envelopes with `success`, `result`, and `error` fields, and capture tool exceptions instead of raising them (`reference/tool-call-nodes.md:52-79`, `reference/tool-call-nodes.md:137-145`). FR-774's smoke criteria correctly required `split_result.success` before crediting map/reduce success (`feature-requests/FR-774-book-summary-scale-hardening.md:184-187`), but FR-775's proposed loop does not name gates for failed `probe` or `fetch_batch` envelopes (`feature-requests/FR-775-book-summary-loop-redesign.md:76-95`).

Fold this exact design into the FR: add python gate nodes after `probe` and `fetch_batch` that raise with the envelope `error` when `success` is false, and expose mechanically testable failures for missing poppler, bad page range, and a forced batch fetch failure. The graph must not route to `summarize_pages`, `accumulate`, or `combine` after a failed probe/fetch envelope.

### R-5: Correct prior-art disposition and make the real-book witness mechanical

Revise the prior-art section and acceptance criteria so they do not overclaim novelty or rely on subjective coherence. Existing committed demos already demonstrate loops (`examples/demos/five-whys/graph.yaml:35-54`, `examples/demos/wiki-memory/graph.yaml:65-84`, `examples/demos/reflexion/graph.yaml:45-62`, `examples/demos/compaction/graph.yaml:78-90`), and `safety-guards` already combines a loop-guarded cycle with a map fan-out (`examples/demos/safety-guards/graph.yaml:11-14`, `examples/demos/safety-guards/graph.yaml:59-70`, `examples/demos/safety-guards/graph.yaml:80-100`). The accurate gap is narrower: no cited demo combines shared splitter manifest, batched cursor loop, per-page map fan-out, cross-iteration reducer accumulation, and final LLM reduction in one artifact.

Fold that prior-art statement into the FR. Also replace AC-08's "coherent summary" requirement (`feature-requests/FR-775-book-summary-loop-redesign.md:146-148`) with command-backed state evidence: the recorded real-book run must show `total == 418`, exactly 42 planned fetch windows, at least one first/middle/last non-empty page summary with absolute page numbers in increasing order, non-empty `book_summary`, zero tool-result failures, zero map truncation warnings, and `loop_exits` routing to combine when the configured limit is forced in a targeted test. Human judgement may note coherence in Implementation Status, but it cannot be the acceptance gate.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-775-book-summary-loop-redesign.md` revised to fold R-1 through R-5 before enforcement authority activates |
| D-2 | `examples/shared/split_document.py` and `examples/shared/split_document.tool.yaml` extended only for `mode: info`, `allow_empty_selection`, and absolute page metadata |
| D-3 | `capabilities/CAP-218-shared-document-splitter.yaml` updated for the D-2 contract, with req-marked tests |
| D-4 | `examples/demos/book-summary/graph.yaml` and `examples/demos/book-summary/prompts/*.yaml` re-authored only through `scripts/author.sh` |
| D-5 | Demo-local python/passthrough batch planning, envelope gates, and accumulation helper code required by the graph |
| D-6 | Unit/artifact tests covering splitter extension, batch planning, map interleave regression, loop termination, and tool-result failure gates |
| D-7 | `examples/demos/book-summary/README.md`, `demo-output.log`, FR Implementation Status, changelog fragment, and diary reflection |

Not authorized: changes under `yamlgraph/`; changing map `collect` reducer semantics, `_map_index` behavior, `tool_call.args` expression semantics, loop runtime behavior, linter rules, hooks, CI, judge/review/authoring doctrine, or release process; adding OCR, vision fallback, PDF rendering, new runtime dependencies, or parallel batch processing; migrating other demos/examples; claiming unbounded book support; treating `tmp/book1.pdf` as a committed fixture.

## Revised acceptance criteria

- [ ] AC-01: The FR prior-art section names existing loop demos and narrows the novelty claim to the combined shared-splitter + batched loop + per-page map + cross-iteration accumulation + final reducer shape.
- [ ] AC-02: `split_document` supports `mode: info` without `pdftotext`, `allow_empty_selection: false` by default, and absolute page metadata (`page` for per-page chunks, `page_start`/`page_end` for batched chunks); defaults preserve FR-774 failure behavior when `allow_empty_selection` is omitted.
- [ ] AC-03: The graph obtains total pages from `mode: info`, computes `batch_start` and `batch_end` in a python or passthrough node, and `fetch_batch.args` reference only state values, not inline arithmetic.
- [ ] AC-04: `fetch_batch` uses `pages_per_chunk=1`, `min_chars=0`, and `allow_empty_selection=true`; each summarization LLM call receives at most one page of text and a structured `{page, summary}` output schema, with blank/sparse pages represented as empty summaries.
- [ ] AC-05: A mocked witness with at least 3 loop batches and repeated `_map_index` values proves `all_summaries` contains each non-empty page summary exactly once, sorted by absolute page, with no interleaving or duplicate append.
- [ ] AC-06: Loop termination tests cover exact-multiple and partial final batches, plus a forced `loop_limits` hit that routes to `combine` through `loop_exits`; the README states the 1000-page budget and makes no unbounded claim.
- [ ] AC-07: Probe and fetch failure envelopes are gated before map/reduce; tests prove failed `tool_call` results do not reach `summarize_pages`, `accumulate`, or `combine`.
- [ ] AC-08: Governed graph/prompt edits are authored via `scripts/author.sh`; `tmp/draft-authoring-report.md` records graph lint and a smoke attempt for `examples/demos/book-summary/graph.yaml`.
- [ ] AC-09: Committed `demo-output.log` proves fixture success with at least one loop iteration, `split/fetch success` true for every executed fetch, non-empty `all_summaries`, non-empty `book_summary`, and no truncation warning.
- [ ] AC-10: Real-book witness on `tmp/book1.pdf` is recorded in FR Implementation Status with `total == 418`, 42 planned fetch windows, first/middle/last absolute page summaries in increasing order, non-empty `book_summary`, zero tool failures, and zero truncation warnings.
- [ ] AC-11: New/changed tests carry `@pytest.mark.req` markers; CAP-218/REQ-YG-577 is updated for splitter behavior; no `yamlgraph/` files change.
- [ ] AC-12: Changelog fragment and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-775-book-summary-loop-redesign.md`. | GATE |
| C-2 | The implementation must remain examples/shared + book-summary demo scope; any `yamlgraph/` runtime, map reducer, tool_call expression, loop, linter, hook, CI, or doctrine change requires a separate judged FR. | GATE |
| C-3 | The loop fetch path may use `allow_empty_selection=true`; the default splitter path must still fail loudly for all-empty extraction or all-filtered threshold output. | GATE |
| C-4 | The map collect key must never be treated as "current batch" without absolute-page filtering and duplicate prevention. | GATE |
| C-5 | Failed `tool_call` envelopes must be surfaced before downstream map/reduce execution; no success-shaped empty summary may stand in for a probe/fetch failure. | GATE |
| C-6 | Governed graph and prompt artifacts must be authored through `scripts/author.sh` and retain its validation report evidence. | GATE |
| C-7 | The 418-page real-book witness is an uncommitted runtime witness only; do not commit `tmp/book1.pdf` or replace the committed fixture with external/provenance-unclear content. | GATE |
| C-8 | OCR/vision fallback, parallel batch processing, other demo migrations, and unbounded book support remain non-goals. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may redesign the book-summary demo into a bounded per-page batch loop, extend the shared example splitter only as specified, add directly related tests/docs/evidence/changelog/diary, and nothing else.
