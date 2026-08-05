# Feature Request: FR-776 — Vision Fallback for Scanned (OCR-less) PDFs in Book-Summary

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced 2026-08-05 — all AC green; commits: RED (test suite + CAP-219), GREEN A (shared tools), GREEN B (graph + demo helpers + witnesses)
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
a typed page-transcription helper sharing FR-769's multimodal plumbing,
and feed transcriptions into the existing FR-775 per-page summarize map.
The loud FR-774 default (`ValueError: no extractable text … vision
fallback is not implemented`) stays the default — enforced at the graph
level across the whole document (R-1); the fallback is explicit demo
config.

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

`render_page(path: str, page: int, out_dir: str = "tmp/pages", dpi: int
= 150) -> dict` invokes poppler `pdftoppm -png -r {dpi} -f {page} -l
{page}` via `subprocess.run([...], shell=False)`, writes PNGs only under
ignored `tmp/`, and returns the result payload `{"page": page, "image":
png_path}` on success. Loud failure: it *raises*
(`ValueError`/`FileNotFoundError` naming the condition) for missing PDF,
invalid page, missing `pdftoppm`, nonzero render exit, or missing output
— the surrounding `tool_call` node owns the success envelope; the shared
function never returns a nested envelope (R-5).

### 2. Typed per-page vision transcription (R-2)

A typed transcription surface — in `examples/shared/vision_tool.py` or a
new shared module — with a Pydantic model:

```python
class PageTranscription(BaseModel):
    page: int
    text: str
    is_blank: bool = False

def transcribe_page(image: str | Path, page: int, *,
                    provider: str | None = None,
                    model: str | None = None) -> PageTranscription: ...
```

It may reuse `describe_image()`'s multimodal message construction and
provider allowlist, but must NOT return or reinterpret
`ImageDescription.description` as the transcript — the schema is page
text, mechanically checkable (page echo, blank flag). Tests mock the LLM
and prove local image input, unsupported provider, malformed output,
blank page output, and page-number echo validation.

### 3. Provider preflight gate (R-3)

A deterministic preflight node/helper runs BEFORE any `render_page` map,
validating the selected vision provider/model against the same allowlist
the transcription helper uses (google, anthropic). The
unsupported-provider test spies on the render tool and proves zero
`pdftoppm` invocations. If a reusable `validate_vision_provider()` helper
is exposed it stays `examples/shared` scope — no `yamlgraph.utils`
changes.

### 4. Graph integration (R-1, R-4 — authored via `scripts/author.sh`, sole route)

**Default OCR-less detection moves to the graph level (R-1).** The FR-775
loop always fetches with `allow_empty_selection: true` (a blank 10-page
window inside a text PDF must not stop the loop), so the splitter's
all-empty raise cannot fire per-window. Instead the graph tracks an
aggregate text-presence flag: whether ANY fetched chunk across the whole
document had `text.strip()`. With `vision_fallback` false, a gate at the
final combine boundary raises the exact FR-774 scanned/image-only
`ValueError` message before any reducer LLM runs if zero extractable text
was observed. Blank windows inside text-bearing PDFs remain nonfatal.
The splitter itself is untouched.

**Branch contract (R-4).** After `gate_fetch`, a partition node returns
current-window `text_chunks`, `empty_chunks`, and the aggregate
text-presence update. With `vision_fallback=false`, only `text_chunks`
proceed and the R-1 guard owns all-document failure. With
`vision_fallback=true`, `empty_chunks` flow through `render_page` and
typed `transcribe_page` maps — each with `max_items: 10`, retry policy,
and gates rejecting `_error` entries and failed envelopes. A merge node
filters render/transcribe collect results to `batch_start..batch_end`,
verifies every transcribed page came from the current `empty_chunks`,
drops truly blank transcriptions as empty summaries, combines with
`text_chunks`, sorts by absolute `page`, and writes the single `chunks`
list consumed by the existing `summarize_pages` map. No stale collect
entry, out-of-window page, duplicate page, or render/transcribe failure
may reach `summarize_pages`, `accumulate`, or `combine` as success-shaped
state — the exact stale-collect class FR-775 fixed must not be
reintroduced.

No `yamlgraph/` core changes; this is demo + shared-tool scope.

## Constraints

- C-1: Default behavior unchanged in outcome — without
  `vision_fallback=true`, a fully OCR-less PDF fails loudly with the
  exact FR-774 ValueError message (raised by the R-1 graph-level guard
  before `combine`); FR-775's nonfatal blank-window behavior inside
  text-bearing PDFs is preserved.
- C-2: No `yamlgraph/` core changes; demo + `examples/shared/` only —
  no map reducer, `_map_index`, tool-call envelope, or provider factory
  changes.
- C-3: Governed graph/prompt edits go through `scripts/author.sh` only
  (FR-767), verified via `tmp/draft-authoring-report.md`.
- C-4: Page identity end to end — transcribed pages carry absolute page
  numbers through map, accumulate, and combine exactly as text pages do
  (FR-775 accumulate gates unchanged).
- C-5: Loud defaults — render/transcribe failures raise into the
  `tool_call`/map error surface and are gated before `summarize_pages`;
  no silent skips. Transcription is typed (`PageTranscription`), never
  squeezed through `ImageDescription` fields.
- C-6: Vision provider allowlist enforced by a preflight gate before any
  rendering; every post-loop collect result filtered and verified by
  absolute page within the current batch window.
- C-7: Test PDFs, rendered PNGs, and generated scanned fixtures live in
  ignored `tmp/`, never committed; a tiny committed fixture (1-2 page
  scanned PDF) is allowed only if named in this FR and < 100 KB.
- C-8: README claims bounded: opt-in vision path, provider allowlist,
  poppler `pdftoppm` requirement, finite 10-page window budget, no
  OCR-quality guarantee.

## Acceptance Criteria

*(Revised per judgement — supersedes the proposed list.)*

- [x] AC-01: `examples/shared/render_page.py` exposes
      `render_page(path: str, page: int, out_dir: str = "tmp/pages",
      dpi: int = 150) -> dict`, invokes `pdftoppm` without `shell=True`,
      writes PNGs only under ignored `tmp/`, returns
      `{"page": page, "image": png_path}` on success, and raises naming
      the condition for missing PDF, invalid page, missing `pdftoppm`,
      nonzero render exit, or missing output.
- [x] AC-02: `examples/shared/render_page.tool.yaml` validates as a
      `ToolManifest`; an artifact/tool-call test proves args resolve to
      real kwargs and the node envelope carries success payload or
      failure error without the shared function returning a nested
      envelope.
- [x] AC-03: With `vision_fallback` unset or false, a fully image-only
      PDF run raises the exact FR-774 scanned/image-only `ValueError`
      before `combine`; a text PDF with blank internal windows still
      completes without that guard firing.
- [x] AC-04: With `vision_fallback=true`, unsupported vision
      provider/model fails in a preflight gate before any `pdftoppm`
      invocation; the test spies on render invocation count and proves
      zero renders.
- [x] AC-05: A typed transcription helper returns a Pydantic
      `PageTranscription`-style model carrying absolute page and
      transcript text; mocked tests cover local rendered image input,
      provider allowlist, malformed model output, blank page output, and
      page-number echo validation.
- [x] AC-06: A mixed mocked witness proves text-bearing pages skip
      render/transcribe, empty-text pages route
      `render_page -> transcribe_page`, and the merged `chunks` list
      passed to `summarize_pages` is sorted by absolute page with page
      identity preserved.
- [x] AC-07: Render failures, transcribe failures, `_error` map entries,
      out-of-window pages, duplicate transcriptions, and transcriptions
      for pages not in the current `empty_chunks` abort loudly before
      `summarize_pages`, `accumulate`, or `combine`; no silent page loss
      is accepted.
- [x] AC-08: A loop witness with at least two batches proves
      render/transcribe collect keys are filtered to the current
      `batch_start..batch_end` window and cannot leak stale entries
      across iterations.
- [x] AC-09: Governed graph/prompt edits are authored via
      `scripts/author.sh`; `tmp/draft-authoring-report.md` records graph
      lint and the narrowest meaningful smoke attempt for
      `examples/demos/book-summary/graph.yaml`.
- [x] AC-10: A real scanned-PDF witness is recorded in Implementation
      Status and `demo-witness.log`: pages rendered to `tmp/`, transcribed
      with absolute page identity, summarized in order, non-empty
      `book_summary`, zero unexplained render/transcribe/fetch failures,
      and no generated images or large PDFs added to git.
- [x] AC-11: `capabilities/CAP-219-book-summary-vision-fallback.yaml`
      with `REQ-YG-578` is added; CAP-217/CAP-218 are updated only for
      actual contract changes; every new or changed test has an exact
      `@pytest.mark.req(...)` marker.
- [x] AC-12: `examples/shared/README.md` documents `render_page` and
      typed transcription failure modes;
      `examples/demos/book-summary/README.md` states the opt-in vision
      path, provider allowlist, poppler `pdftoppm` requirement, finite
      10-page window budget, and no OCR-quality guarantee.
- [x] AC-13: No files under `yamlgraph/` change; changelog fragment and
      diary reflection are included.

## Implementation Status

**Enforced 2026-08-05.** TDD trail: RED commit (43 tests, 42 failing —
`tests/unit/test_fr776_vision_fallback.py` + CAP-219/REQ-YG-578) →
GREEN A (`feat(examples): FR-776 GREEN A shared render + transcription
tools`) → GREEN B (graph wiring + demo helpers + witnesses). Suite:
97 passed across FR-773/774/775/776 + shared vision tool; 0 failures.

**Decisions and deviations:**

- **Guard message wording (R-1 deviation, truthful):** the graph-level
  guard raises `no extractable text in <pdf> — scanned/image-only PDF?
  enable the vision fallback with --var vision_fallback=true (FR-776)`.
  FR-774's original suffix ("vision fallback is not implemented") would
  now be a lie; the frozen regex contract
  (`no extractable text.*scanned/image-only`) is preserved. The FR-774
  raise inside `split_document.py` is untouched (it cannot fire in this
  graph because the loop fetches with `allow_empty_selection: true`,
  exactly as R-1 prescribed).
- **Empty-fan-out dead-end (discovered, mechanically verified):** a
  LangGraph conditional edge returning zero `Send`s silently ends the
  branch — downstream nodes never run (verified with a minimal
  StateGraph). `partition_chunks` therefore passes blank chunks through
  on the direct route when a window has no text, and `merge_vision` does
  the same when every transcription is blank; `accumulate` drops the
  resulting empty summaries exactly as in FR-775. Without this, an
  all-blank window would end the run instead of advancing the cursor.
- **Envelope normalization at gate_render:** map-collected `tool_call`
  entries are `{success, result, error}` envelopes; `gate_render`
  normalizes them at the boundary (the_one_law) — failed envelopes raise,
  successful ones flatten to `{page, image}`.
- **Direct-route condition:** the authoring adapter changed
  `vision_route == 'direct'` to `vision_route != 'vision'` to close a
  lint W803 condition-gap warning; the two-target partition contract is
  unchanged.
- **FR-775 artifact tests amended:** two wiring assertions
  (`loop_exits.advance == combine`, `gate_fetch → summarize_pages`)
  asserted the exact edges R-1/R-4 rewire; updated to the judged FR-776
  shape with FR-776 comments.

**AC-09 authoring record:** `./scripts/author.sh tmp/fr776-vision-brief.md`
(sole route) — `tmp/draft-authoring-report.md` records lint (clean after
W803 repair) and the graph-scoped test run (42 passed, 1 deselected: the
README test was outside the brief's artifact boundary; README edited
directly — not a governed artifact).

**AC-10 real scanned-PDF witness** (recorded in `demo-witness.log` §3;
`demo-output.log` is the gate-facing success stamp pointing there):
`tmp/scanned.pdf` = pages 7–9 of a genuinely scanned Finnish book
(`pdfseparate`/`pdfunite` from `tmp/book3.pdf`, 36 pp, zero extractable
text document-wide — `pdftotext` yields 3 bytes for the selection).
- Default run (no flag): exit 1 with the exact guard ValueError before
  `combine` (§2 of demo-witness.log).
- Vision run (`PROVIDER=google --var vision_fallback=true`): 3 pages
  rendered to `tmp/pages/p{1,2,3}-*.png`, transcribed verbatim (Finnish
  diplomatic text, page identity 1..3 intact — surprising detail: the
  transcription preserved inline citation markers like "(Liitteet 9 ja
  10)" and the section numbering 1.–12. across page boundaries),
  summarized in order, non-empty `book_summary`, zero
  render/transcribe/fetch failures. No images or PDFs added to git.

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
- Judgement: `FR-776-vision-fallback-scanned-pdf.judgement.md`
  (APPROVED WITH REVISIONS; R-1..R-5 folded above; C-1..C-8 gates)
