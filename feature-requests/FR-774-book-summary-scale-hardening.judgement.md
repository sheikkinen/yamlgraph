# Judgement: FR-774 Book-Summary Scale Hardening

**Prior art:** FR-773 + its judgement (parent contract this FR extends — reconciled in R-1), FR-772 (inline kwargs authorizing the new args without core change), FR-769/FR-770 (vision tool — kept a non-goal per C-6), FR-767 (sole authoring route enforced by C-4). No rejected FR occupies this territory.

**Verdict:** APPROVED WITH REVISIONS - the example-scoped hardening is real and minimal, but authority activates only after the FR reconciles the default splitter contract, proves the 418-page cap fix, updates page-level language to chunk/excerpt semantics, and prevents success-shaped empty output after filtering.

**Reviewed against:** `feature-requests/FR-774-book-summary-scale-hardening.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; repo doctrine supplied in session instructions; `feature-requests/FR-773-shared-document-splitter-manifest.md`; `feature-requests/FR-773-shared-document-splitter-manifest.judgement.md`; `feature-requests/FR-772-tool-call-inline-dict-args.md`; `feature-requests/FR-769-shared-vision-tool.md`; `feature-requests/FR-770-vision-demo-consumes-manifest.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `capabilities/CAP-218-shared-document-splitter.yaml`; `examples/shared/split_document.py`; `examples/shared/split_document.tool.yaml`; `examples/demos/book-summary/graph.yaml`; `examples/demos/book-summary/prompts/summarize_page.yaml`; `examples/demos/book-summary/prompts/combine_summaries.yaml`; `examples/demos/book-summary/README.md`.

## What is sound

The problem is real and evidenced by the first non-fixture run: the FR names the exact `summarize_pages` truncation warning, blank-page commentary, and empty-text scanned-PDF failure class (`feature-requests/FR-774-book-summary-scale-hardening.md:10-18`, `feature-requests/FR-774-book-summary-scale-hardening.md:30-49`). The value statement correctly classifies the current output as a `plausible_wrong_answer`: a partial 100-page summary can look valid while omitting most of a 418-page book (`feature-requests/FR-774-book-summary-scale-hardening.md:22-26`).

The proposed implementation is correctly example-scoped. It extends the existing shared splitter signature and manifest rather than changing `yamlgraph/` runtime surfaces (`feature-requests/FR-774-book-summary-scale-hardening.md:72-107`), and the current implementation is indeed a small kwargs-based poppler wrapper suited to that extension (`examples/shared/split_document.py:15-20`, `examples/shared/split_document.py:60-73`). FR-772 already authorized inline dict args for `tool_call`, so the demo can pass `pages_per_chunk` and `min_chars` without a core dispatch change (`feature-requests/FR-772-tool-call-inline-dict-args.md:13-26`, `feature-requests/FR-772-tool-call-inline-dict-args.md:51-62`).

The scope correctly rejects the tempting adjacent feature. A vision fallback for scanned PDFs would require rendering pages, routing image inputs, and accepting a new cost profile, so making OCR-less text extraction fail loudly is the right hardening move for this FR (`feature-requests/FR-774-book-summary-scale-hardening.md:122-130`). Strategic classification: **Contrib/example hardening**, not a framework primitive; one committed demo and one shared example tool are being hardened, with no new YAMLGraph abstraction justified.

## Required revisions

### R-1: Reconcile the default splitter contract with OCR-less detection

Revise the claim that `pages_per_chunk=1, min_chars=0` preserves the FR-773 contract "byte-for-byte" or "exactly" (`feature-requests/FR-774-book-summary-scale-hardening.md:88-97`, `feature-requests/FR-774-book-summary-scale-hardening.md:134-135`). The proposed OCR-less check intentionally changes default behavior for a valid PDF whose selected pages all extract to empty text: it now raises before filtering (`feature-requests/FR-774-book-summary-scale-hardening.md:100-104`), whereas the existing splitter returns chunks for every selected page (`examples/shared/split_document.py:60-73`) and CAP-218 currently describes one chunk per selected page with explicit subprocess failure modes only (`capabilities/CAP-218-shared-document-splitter.yaml:15-21`).

Fold this exact contract into the FR: defaults preserve the existing normal text-PDF/page-range behavior and all existing FR-773 tests, except that all-empty extraction is a new explicit `ValueError` failure mode. Extend CAP-218/REQ-YG-577 text accordingly, and require a new regression test for the intentional all-empty default-behavior change.

### R-2: Prove the 418-page cap fix and make the supported page budget honest

The FR's ideal says "`<any-real-book.pdf>` summarizes the whole book" (`feature-requests/FR-774-book-summary-scale-hardening.md:63-68`), but the proposed demo retains `max_items: 100`, merely reinterpreted as 100 chunks / 1000 pages (`feature-requests/FR-774-book-summary-scale-hardening.md:114-116`). The current graph already has the truncating cap on the map node (`examples/demos/book-summary/graph.yaml:27-35`), and the observed defect is specifically 418 pages being truncated to 100 (`feature-requests/FR-774-book-summary-scale-hardening.md:30-34`).

Fold into the FR a bounded support statement and a mechanical witness. Either revise the ideal/value/README wording to "up to the declared supported page budget" with `pages_per_chunk * max_items` named explicitly, or choose a different cap and document the cost/spend implication as a human decision. Add an acceptance criterion proving the actual reported shape: a monkeypatched/subprocess-recorder 418-page text PDF with `pages_per_chunk=10` produces 42 chunks, and the committed graph's `summarize_pages.max_items` is high enough that this case cannot trigger the map truncation warning.

### R-3: Convert downstream language from page summaries to chunk/excerpt summaries

The proposed splitter changes the unit of work from one page to a multi-page excerpt (`feature-requests/FR-774-book-summary-scale-hardening.md:88-95`, `feature-requests/FR-774-book-summary-scale-hardening.md:117-120`), but the existing prompt and README still teach page-level semantics: "single page" in `summarize_page`, "Page {{ loop.index }}" in the reducer, and "page-by-page" in the demo docs (`examples/demos/book-summary/prompts/summarize_page.yaml:1-7`, `examples/demos/book-summary/prompts/combine_summaries.yaml:5-13`, `examples/demos/book-summary/README.md:1-18`). After batching and `min_chars` drops, reducer loop indexes are chunk ordinals, not page numbers.

Fold into the FR that human-visible prompt and README language must become chunk/excerpt-based. The file names may remain if the FR chooses not to rename governed artifacts, but the content must not describe 10-page chunks as individual pages. The reducer prompt must label inputs as excerpts/chunks and ignore empty items without inventing page numbers.

### R-4: Fail loudly when `min_chars` filters every extractable chunk

The FR correctly makes all-empty OCR-less extraction a hard error, but `min_chars` can still produce a success envelope with `chunks: []` after all chunks are dropped (`feature-requests/FR-774-book-summary-scale-hardening.md:92-104`, `feature-requests/FR-774-book-summary-scale-hardening.md:140-145`). In the demo graph, an empty chunk list would flow into an empty map and then an LLM reducer, recreating the same plausible-empty-summary class this FR is meant to kill (`examples/demos/book-summary/graph.yaml:27-42`; repo doctrine: no silent success-shaped fallback).

Fold into the FR: when `min_chars > 0` drops every chunk from a selection that had extractable text before filtering, `split_document` raises `ValueError` naming the path and `min_chars` threshold. Tests must cover the distinction among normal surviving filtering, all-empty OCR-less extraction, and all-filtered-by-threshold extraction.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-774-book-summary-scale-hardening.md` revised to fold R-1 through R-4 before enforcement authority activates |
| D-2 | `examples/shared/split_document.py` adding `pages_per_chunk`, `min_chars`, all-empty OCR-less detection, all-filtered failure, and validation errors |
| D-3 | `examples/shared/split_document.tool.yaml` and `capabilities/CAP-218-shared-document-splitter.yaml` updated to the extended contract |
| D-4 | Direct splitter tests and artifact tests covering batching, filtering, cap proof, and error modes with `REQ-YG-577` markers where applicable |
| D-5 | `examples/demos/book-summary/graph.yaml` and `examples/demos/book-summary/prompts/*.yaml` edited only through the graph-authoring sole route |
| D-6 | `examples/demos/book-summary/README.md` and `demo-output.log` updated with batching/filter/cap/OCR-less evidence |
| D-7 | Changelog fragment and diary reflection required by repo gates |

Not authorized: changes under `yamlgraph/`; changing map-node truncation semantics or dynamic-fan-out lint rules; adding a vision fallback, OCR engine, PDF rendering tool, or new runtime dependency; migrating `examples/ocr_cleanup`, `examples/book_translator`, or `examples/demos/philosopher_book`; changing judge/review/authoring doctrine, hooks, CI, or release behavior; claiming unbounded "any book" support while a finite map cap remains.

## Revised acceptance criteria

- [ ] AC-01: With `pages_per_chunk=1, min_chars=0`, existing FR-773 normal text-PDF/page-range behavior and tests still pass; all-empty extraction is documented and tested as the one intentional new default failure mode.
- [ ] AC-02: `pages_per_chunk < 1` and `min_chars < 0` raise `ValueError` naming the offending argument.
- [ ] AC-03: `pages_per_chunk=10` on an N-page selected range returns `ceil(N_selected / 10)` chunks, renumbered 0..n-1, with `total` equal to the whole-document page count and exactly one `pdftotext -f first -l last` invocation per chunk.
- [ ] AC-04: `min_chars` drops sub-threshold chunks after batching, renumbers surviving chunks, preserves `total`, and raises `ValueError` naming `min_chars` when threshold filtering removes every prefilter nonempty chunk.
- [ ] AC-05: All-empty extraction before threshold filtering raises `ValueError` naming the path, "scanned" or "image-only", and the FR-774 vision-fallback non-goal.
- [ ] AC-06: A 418-page mocked/subprocess-recorded text PDF with `pages_per_chunk=10` produces 42 chunks, and an artifact assertion proves the committed demo graph's map cap cannot truncate that case.
- [ ] AC-07: The demo graph carries `pages_per_chunk: 10`, `min_chars: 200`, and the justified finite `max_items`; the README states the resulting supported page budget and does not claim unbounded book support.
- [ ] AC-08: Demo prompt/README content describes chunks/excerpts, not individual pages; the reducer prompt labels inputs as excerpts/chunks and ignores empty summaries without inventing page numbers.
- [ ] AC-09: Graph and prompt edits are authored via `scripts/author.sh`; `tmp/draft-authoring-report.md` records graph lint and smoke evidence.
- [ ] AC-10: Demo smoke on the committed fixture succeeds with state evidence: `split_result.success` true, fixture chunks survive `min_chars`, non-empty `page_summaries`, non-empty `book_summary`, and no truncation warning.
- [ ] AC-11: CAP-218/REQ-YG-577 is extended to cover batching, filtering, and new failure modes; new/changed tests carry requirement markers; no `yamlgraph/` files change.
- [ ] AC-12: Changelog fragment and diary reflection are added.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-4 are folded into `feature-requests/FR-774-book-summary-scale-hardening.md`. | GATE |
| C-2 | The implementation must remain examples/shared + demo scope; any `yamlgraph/` runtime, map-node, linter, hook, or doctrine change requires a separate judged FR. | GATE |
| C-3 | The splitter must not return a success-shaped empty chunk list for all-empty extraction or all-filtered threshold output. | GATE |
| C-4 | Governed graph and prompt artifacts must be edited through `scripts/author.sh` and retain its validation report evidence. | GATE |
| C-5 | The retained map cap must be documented as a finite supported page budget, and the 418-page reported failure shape must be mechanically witnessed. | GATE |
| C-6 | Vision/OCR fallback remains a non-goal; failure may signpost a follow-up but must not implement rendering, OCR, or image-routing in this FR. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may harden the shared example splitter and book-summary demo for batched text-PDF summarization, add the directly related tests/docs/capability/changelog/diary, and nothing else.
