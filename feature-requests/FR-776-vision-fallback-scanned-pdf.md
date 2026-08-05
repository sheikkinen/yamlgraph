# Feature Request: FR-776 — Vision Fallback for Scanned (OCR-less) PDFs in Book-Summary

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1-2 days
**Requested:** 2026-08-05

**Prior art:** FR-774 (Enforced) froze this exact scope as an explicit
non-goal and pointed its ValueError at a future vision fallback — this FR
is that follow-up, not a re-litigation; its OCR-less *detection* stays
untouched. FR-775 (Enforced) built the cursor loop/map/accumulate this FR
branches inside — mechanics reused, gates unchanged. FR-773 (Enforced)
established the shared-tool manifest pattern the new `render_page` tool
copies. None rejected this scope; all three point toward it.

## Summary

Give the book-summary demo an opt-in vision branch for scanned/image-only
PDFs: render undecodable pages to images with poppler `pdftoppm` (shared
render tool + `.tool.yaml` manifest), transcribe each rendered page with
the shared vision tool (FR-769 `describe_image`), and feed transcriptions
into the existing FR-775 per-page summarize map. The loud FR-774 default
(`ValueError: no extractable text … vision fallback is not implemented`)
stays the default; the fallback is explicit demo config.

## Value Statement

Owners of scanned books get real summaries instead of a refusal, and the
FR-769 vision tool gains its second committed consumer — proving the
shared-tool manifest pattern composes across demos.

## Ideal Result

`yamlgraph graph run examples/demos/book-summary/graph.yaml --var
pdf=tmp/scanned.pdf --var vision_fallback=true` summarizes a scanned book
end to end: every image-only page is rendered, transcribed, and
summarized with its absolute page identity intact, blank pages drop
exactly as text pages do, and the run report shows which pages took the
vision path. Without the flag, the FR-774 ValueError fires unchanged.

## Problem

FR-774 made OCR-less detection *raise*, never substitute
(`examples/shared/split_document.py:113` — "vision fallback is not
implemented (FR-774 non-goal)"), explicitly deferring the fallback and
naming it "the vision tool's second-consumer moment". The scope boundary
was correct then; this FR picks it up:

1. A scanned book today yields only an error — the demo cannot serve the
   most common real-world "book PDF" (scans).
2. FR-769's `describe_image` has exactly one consumer
   (`examples/demos/shared-vision-tool`); the shared-tool pattern's claim
   of reuse is unproven until a second demo consumes the manifest.

## Proposed Solution

### 1. Shared page-render tool (`examples/shared/render_page.py` + `.tool.yaml`)

Follow the FR-768/FR-773 shared-tool pattern exactly:

```yaml
# examples/shared/render_page.tool.yaml
name: render_page
runtime: {type: python, module: examples.shared.render_page, function: render_page}
```

`render_page(path, page, out_dir="tmp/pages", dpi=150)` shells poppler
`pdftoppm -png -r {dpi} -f {page} -l {page}` (binary verified present)
and returns the standard success envelope with the PNG path. Loud
failure: missing binary, bad page, empty output all raise into the
envelope's `success: false`.

### 2. Per-page vision transcription

New shared function (or thin wrapper) `transcribe_page(image)` calling
FR-769 `describe_image(image, instruction)` with a transcription
instruction ("Transcribe all legible text on this book page verbatim…").
Constraint inherited from FR-769: vision requires the provider allowlist
(google, anthropic) — the branch fails loudly if the configured vision
provider is unsupported, before any rendering happens.

### 3. Graph integration (authored via `scripts/author.sh` — sole route)

Inside the FR-775 cursor loop, after `fetch_batch`/`gate_fetch`: a
deterministic python node partitions the window's chunks into text-bearing
and empty; when `vision_fallback` is true, empty-text pages route through
`render_page` + `transcribe_page` (map, same `max_items: 10` budget,
`on_error: retry`) and rejoin the summarize map as ordinary
`{page, text}` chunks. Splitter change: `allow_empty_selection` /
OCR-less raise gains a demo-config bypass ONLY when the vision flag is
set — default behavior byte-identical to FR-774.

No `yamlgraph/` core changes expected; this is demo + shared-tool scope.

## Constraints

- C-1: Default behavior unchanged — without `vision_fallback=true`, the
  FR-774 ValueError fires with its current message.
- C-2: No `yamlgraph/` core changes; demo + `examples/shared/` only.
- C-3: Governed graph/prompt edits go through `scripts/author.sh` only
  (FR-767), verified via `tmp/draft-authoring-report.md`.
- C-4: Page identity end to end — transcribed pages carry absolute page
  numbers through map, accumulate, and combine exactly as text pages do
  (FR-775 accumulate gates unchanged).
- C-5: Loud defaults — render/transcribe failures surface as envelope
  `success: false` and are gated before the map; no silent skips.
- C-6: Vision provider allowlist enforced before rendering begins.
- C-7: Test PDFs and rendered PNGs live in `tmp/`, never committed;
  a tiny committed fixture (1-2 page scanned PDF) is allowed only if
  < 100 KB, else generated in-test.
- C-8: README claims bounded: state the vision path is per-page,
  provider-restricted, and budgeted like the text path; no OCR-quality
  claims.

## Acceptance Criteria

- [ ] AC-01: `render_page.tool.yaml` manifest committed; unit test proves
      manifest args resolve and the envelope contract (success PNG path;
      loud failure on bad page/missing file).
- [ ] AC-02: With `vision_fallback` unset/false, an image-only PDF raises
      the exact FR-774 ValueError (regression test on message substring).
- [ ] AC-03: With `vision_fallback=true`, a mocked witness proves
      empty-text pages route render → transcribe → summarize while
      text-bearing pages skip the vision path, page identity preserved.
- [ ] AC-04: Transcribe failures (envelope `success: false`, `_error`
      map entries) abort loudly via existing gates — test proves no
      silent page loss.
- [ ] AC-05: Provider allowlist violation fails before any `pdftoppm`
      invocation (test with unsupported provider).
- [ ] AC-06: Governed edits via `scripts/author.sh`;
      `tmp/draft-authoring-report.md` records lint + smoke.
- [ ] AC-07: Real witness on a scanned PDF (may be generated by rendering
      a few book1 pages to images and re-assembling) recorded in
      Implementation Status: pages transcribed, summarized in order,
      non-empty `book_summary`, zero unexplained failures.
- [ ] AC-08: Tests carry `@pytest.mark.req` markers; CAP registry updated
      (extend CAP-217/CAP-218 or add new CAP); no `yamlgraph/` diff.
- [ ] AC-09: Changelog fragment and diary reflection included.

## Alternatives Considered

- **OCR via tesseract:** new system dependency, worse on stylized scans,
  and doesn't exercise the vision tool — rejected; the point is the
  second-consumer moment.
- **Whole-book render + flat vision map:** loses the loop/budget design
  FR-775 just established; 400 renders with no windowing.
- **Separate scanned-book demo:** splits the narrative; the loop, gates,
  and accumulate are identical — a branch, not a sibling.
- **Do nothing (keep the ValueError):** honest but leaves the shared
  vision tool a single-consumer pattern and scans unserved.

## Related

- FR-774 non-goals §3 (frozen boundary this FR picks up);
  `examples/shared/split_document.py:113` error message
- FR-769 (shared vision tool, CAP-217), FR-770/FR-771 (first consumer),
  FR-772 (tool_call inline args)
- FR-773 (shared-tool manifest pattern), FR-775 (cursor loop, map,
  accumulate — mechanics reused)
- FR-767 (sole authoring route)
