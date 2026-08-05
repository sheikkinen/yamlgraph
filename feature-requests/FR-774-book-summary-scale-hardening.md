# FR-774: Book-Summary Scale Hardening — Page Batching, Blank Chunks, OCR-less Detection

**Status:** Judged 2026-08-05 — APPROVED WITH REVISIONS; R-1..R-4 folded below; authority active per judgement
**Date:** 2026-08-05
**Author:** agent session (operator-reported defects from first real-world run)
**Parent:** FR-773 (shared document splitter + book-summary demo)

## Summary

The first real run of the book-summary demo (418-page `tmp/book1.pdf`)
surfaced three defects the 2-page fixture could not: the map node
silently truncated 418 pages to 100 (`max_items` cap), blank/near-blank
pages made the summarizer LLM complain and emit preamble text instead of
summaries, and a scanned (OCR-less) PDF would produce garbage silently.
Batch pages into multi-page chunks at the splitter boundary, drop
sub-threshold chunks explicitly, harden the prompts to summary-only
output, and make zero-extractable-text an explicit error instead of a
silent bad summary.

## Value Statement

For anyone summarizing a real book (not a fixture), the demo currently
produces a summary of the first 100 pages, polluted by blank-page
complaints — a `plausible_wrong_answer`. After this FR, a 400+ page text
PDF summarizes completely and cleanly, and an image-only PDF fails loudly
naming the reason, instead of failing quietly with an empty-text summary.

## Problem

Observed run: `Map node 'summarize_pages': truncating 418 items to 100`.

1. **Truncation.** The in-route author added `max_items: 100` to satisfy
   the dynamic-fan-out lint. Real books exceed it; the truncation is a
   WARNING, not an error — the summary silently covers 24% of the book.
2. **Blank pages.** One-chunk-per-page fan-out sends blank and
   near-blank pages (part titles, printing pages) to the LLM, which
   responds with "this page appears to be blank..." commentary; the
   combine step then weaves that noise into the book summary. The
   summarize prompt also lacks an output constraint, so the model adds
   preamble beyond the summary itself.
3. **OCR-less PDFs.** A scanned book yields `pdftotext` success with
   empty text on every page. Nothing detects this; the pipeline would
   emit a confident summary of nothing — the exact silent-fallback class
   the FR-773 judgement (C-3) forbade inside the splitter.

Cost is coupled to (1): 418 per-page LLM calls is the wrong shape;
batching pages into multi-page chunks reduces calls ~10× and dilutes
blank pages into their surrounding context, attacking (1) and (2) with
one mechanism at the boundary where chunks are born (`the_one_law`).

**Prior art:** FR-773 (parent — froze the splitter kwargs/failure
contract this FR extends; its C-3 "no fallback" applies and is honored:
the new `min_chars` drop is explicit opt-in demo config, and OCR-less
detection *raises*, never substitutes). FR-769/FR-770 (shared vision
tool + manifest — the natural implementation of a future vision fallback
for scanned PDFs; deferred here as a non-goal, see below, which makes
that follow-up the vision tool's second-consumer moment). The map
`max_items` lint that motivated the cap remains satisfied — the cap is
raised and justified, not removed.

## Ideal Result

`yamlgraph graph run examples/demos/book-summary/graph.yaml --var
pdf=<real-book.pdf>` summarizes any text PDF **up to the declared
supported page budget** (`pages_per_chunk × max_items` = 10 × 100 =
1000 pages, stated in the README) — blank pages included — in ~N/10 LLM
calls with no truncation warning, no blank-page commentary, and no
preamble; an image-only PDF exits with a ValueError naming the condition
and pointing at the vision-fallback follow-up. (R-2: bounded claim, not
"any book" — the finite cap is a documented budget, and the observed
418-page shape is mechanically witnessed by test.)

## Proposed Solution

### 1. Splitter: `pages_per_chunk` + `min_chars` (examples-land only)

Extend `examples/shared/split_document.py` kwargs (no `yamlgraph/`
changes; tool_call inline kwargs already carry ints per FR-772):

```python
def split_document(
    path: str,
    mode: str = "page",
    start: int | None = None,
    end: int | None = None,
    pages_per_chunk: int = 1,
    min_chars: int = 0,
) -> dict
```

- `pages_per_chunk: N` — consecutive selected pages are joined
  (`"\n".join`) into one chunk; one `pdftotext -f first -l last` call
  per chunk (N× fewer subprocesses too). Default 1 preserves the FR-773
  normal text-PDF/page-range behavior and all existing FR-773 tests
  (R-1: not "byte-for-byte" — all-empty extraction below is the one
  intentional new default failure mode, documented in CAP-218 and
  covered by a dedicated regression test).
- `min_chars: M` — chunks whose stripped text is shorter than M are
  dropped *after* batching; `total` remains the whole-document page
  count (unchanged semantics); chunk `index` stays 0-based over the
  returned list. Default 0 = keep everything. Dropping is driven by
  explicit caller config — this is not a silent fallback; C-3 intact.
  (R-4) If `min_chars > 0` drops **every** chunk from a selection that
  had extractable text before filtering, raise
  `ValueError` naming the path and the `min_chars` threshold — never a
  success-shaped empty chunk list.
- `pages_per_chunk < 1` or `min_chars < 0` raise ValueError naming the
  argument.
- **OCR-less detection:** if, after batching and *before* `min_chars`
  filtering, every chunk's stripped text is empty, raise
  `ValueError("no extractable text in <path> — scanned/image-only PDF? "
  "vision fallback is not implemented (see FR-774 non-goals)")`.
  Loud failure, never a confident empty summary.

Manifest description in `split_document.tool.yaml` updated to the
extended contract; CAP-218/REQ-YG-577 description extended to cover
batching, filtering, and the new failure modes (R-1).

### 2. Demo: batch + filter + realistic cap (via sole authoring route)

`examples/demos/book-summary/graph.yaml` (FR-767 governed — edited via
`scripts/author.sh`):

- `split` args: add `pages_per_chunk: 10`, `min_chars: 200`.
- `summarize_pages`: `max_items: 100` retained — a **finite supported
  page budget** of 10 × 100 = 1000 pages, stated as such in the README
  (R-2); no unbounded "any book" claim. An artifact test mechanically
  witnesses the reported 418-page shape: 42 chunks at
  `pages_per_chunk=10`, below the committed cap, so the observed
  truncation warning cannot recur for that case.
- Prompt hardening (first strike, `two_strike_split` noted), with
  chunk/excerpt semantics throughout (R-3): `summarize_page` — "summarize
  this excerpt (~10 pages of a book) in 3-5 sentences; output ONLY the
  summary, no preamble, no commentary on blank or sparse regions";
  `combine_summaries` — inputs are labeled excerpts/chunks (ordinals,
  never invented page numbers) and empty items are ignored. README
  language becomes chunk/excerpt-based ("page-by-page" → batched
  excerpts); governed file names stay.

### 3. Non-goal (explicit): vision fallback for scanned PDFs

Rendering pages via `pdftoppm` and describing them with the shared
vision tool (FR-769) is real scope: a new render tool, per-page image
routing, cost profile, and a graph-level branch — a feature, not a
hardening. Deferred to a follow-up FR; the OCR-less ValueError names it
so the failure message is the signpost. This keeps the present FR
minimal and makes the follow-up the vision tool's second committed
consumer (`the-second-consumer-decides` diary, 2026-08-04).

## Acceptance Criteria (revised per judgement — binding set)

- [ ] AC-01: With `pages_per_chunk=1, min_chars=0`, existing FR-773
      normal text-PDF/page-range behavior and tests still pass;
      all-empty extraction is documented and tested as the one
      intentional new default failure mode.
- [ ] AC-02: `pages_per_chunk < 1` and `min_chars < 0` raise
      `ValueError` naming the offending argument.
- [ ] AC-03: `pages_per_chunk=10` on an N-page selected range returns
      `ceil(N_selected / 10)` chunks, renumbered 0..n-1, with `total`
      equal to the whole-document page count and exactly one
      `pdftotext -f first -l last` invocation per chunk.
- [ ] AC-04: `min_chars` drops sub-threshold chunks after batching,
      renumbers surviving chunks, preserves `total`, and raises
      `ValueError` naming `min_chars` when threshold filtering removes
      every prefilter nonempty chunk.
- [ ] AC-05: All-empty extraction before threshold filtering raises
      `ValueError` naming the path, "scanned" or "image-only", and the
      FR-774 vision-fallback non-goal.
- [ ] AC-06: A 418-page mocked/subprocess-recorded text PDF with
      `pages_per_chunk=10` produces 42 chunks, and an artifact assertion
      proves the committed demo graph's map cap cannot truncate that
      case.
- [ ] AC-07: The demo graph carries `pages_per_chunk: 10`,
      `min_chars: 200`, and the justified finite `max_items`; the README
      states the resulting supported page budget and does not claim
      unbounded book support.
- [ ] AC-08: Demo prompt/README content describes chunks/excerpts, not
      individual pages; the reducer prompt labels inputs as
      excerpts/chunks and ignores empty summaries without inventing page
      numbers.
- [ ] AC-09: Graph and prompt edits are authored via `scripts/author.sh`;
      `tmp/draft-authoring-report.md` records graph lint and smoke
      evidence.
- [ ] AC-10: Demo smoke on the committed fixture succeeds with state
      evidence: `split_result.success` true, fixture chunks survive
      `min_chars`, non-empty `page_summaries`, non-empty `book_summary`,
      and no truncation warning.
- [ ] AC-11: CAP-218/REQ-YG-577 is extended to cover batching,
      filtering, and new failure modes; new/changed tests carry
      requirement markers; no `yamlgraph/` files change.
- [ ] AC-12: Changelog fragment and diary reflection are added.

## Alternatives Considered

- **Raise `max_items` alone:** fixes truncation, keeps 418 calls and
  blank-page noise — treats one symptom of three.
- **Filter blanks in the graph (python node):** adds a node and a
  Python file to the demo; the splitter already owns chunk-shaping and
  the filter belongs at the boundary where chunks are made.
- **Prompt-only fix for blanks:** rejected as primary mechanism
  (`two_strike_split` — mechanize at the boundary, prompt as
  belt-and-braces only).
- **Vision fallback now:** rejected as scope creep; see non-goals.

## Related

- FR-773 (parent contract), FR-772 (inline kwargs), FR-769/770 (vision
  tool — follow-up consumer), FR-767 (sole authoring route for AC-05)
- CAP-218 / REQ-YG-577 (extended, not re-numbered)
