# Feature Request: FR-773 — Shared Document Splitter Manifest with Book-Summary Map/Reduce Demo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-08-04
**First consumer / first event:** a new `examples/demos/book-summary/`
graph, the first time it needs a page list from a PDF — it consumes the
shared splitter via `manifest:` instead of copying a fourth splitter
implementation. Second consumer already exists: `examples/ocr_cleanup`
migrates its inline `extract_pdf_pages` declaration on its next edit.

## Summary

Extract the third-strike document-splitter family into one shared tool
(`examples/shared/split_document.tool.yaml` + implementation module),
declared once via an FR-768 tool manifest, and prove it with the
operator-named use case: split a PDF by page, map an LLM summary over each
page, reduce the page summaries into a book summary.

## Value Statement

Any graph gets "document → chunk list for a map node" with one manifest
line, ending the per-project splitter rewrites (three exist today) and
giving the manifest primitive its first *feeder*-tool consumer — the shape
that actually stresses declaration reuse.

## Problem

Measured 2026-08-04 across all tool-fed map nodes in `examples/` (14 total):
the "split a document into chunks for `over:`" job has been implemented
three times, each project-locked:

| Implementation | Project | Shape |
|---|---|---|
| `extract_pages` (`tools/pdf_extract.py`) | ocr_cleanup | PDF → `pages: [{page_num, raw_text, prev_last_line}]` via `pdfinfo`/`pdftotext` subprocess |
| `split_by_markers` (`nodes/tools.py`) | book_translator | text + LLM markers → chunk list (feeds 2 map nodes) |
| `load_chapters` (`tools.py`) | philosopher_book | dir of `.md` → chapter list |

A fourth consumer (book summarization) would today write a fourth copy.

**Prior art:** FR-044 (shared contrib libraries, COMPLETE) rejected forcing
divergent *implementations* under one abstraction — honored here: the three
existing splitters keep their code; only future *declarations* share one
tool, and migration of existing projects is explicitly out of scope (AC-09).
FR-719 (SMT condition verification, COMPLETED) matches on the noun
"splitter" only — it splits condition expressions for solver verification,
an unrelated domain; no overlap in mechanism or consumer.

This is the exact drift class FR-768 was built to end — but FR-768's only
committed consumer (shared-vision-tool, FR-770) is a *terminal* tool. The
splitter is a *feeder*: its output shape is the interface a downstream
`over:` path couples to. The manifest primitive has not yet passed that
acceptance test (diary 2026-08-04, feeder-tool reflection).

## Ideal Result

A graph author writes `manifest: ../../shared/split_document.tool.yaml`,
calls the tool with a document path and a granularity, and wires
`over: "{state.chunks.chunks}"` into a map node — for PDF pages today,
without reading any implementation code. The three existing splitters are
unaffected (migration is their own projects' concern, on their next edit);
the book-summary demo exists, runs, and its `demo-output.log` proves a real
PDF was summarized page-by-page and reduced.

## Proposed Solution

Minimal path back from the ideal — three artifacts, no core changes:

**1. Shared implementation** `examples/shared/split_document.py`:

```python
def split_document(state: dict) -> dict:
    """Split a document into chunks for map fan-out.

    Args: path (str), mode ('page' today; 'chapter'/'paragraph' are
    future modes, rejected explicitly), start/end (optional page range).
    Returns {"chunks": [{"index": int, "text": str}], "total": int}.
    """
```

- `mode: page` delegates to the proven `pdfinfo`/`pdftotext` subprocess
  approach from `ocr_cleanup/tools/pdf_extract.py` (lifted, not imported —
  ocr_cleanup keeps its richer `prev_last_line` contract untouched).
- Unknown mode or missing binary raises at invocation with an actionable
  message naming `poppler` (`brew install poppler`). No silent fallback.
- Output contract is documented in the module docstring AND the manifest
  description — the feeder seam is closed by documentation + the demo's
  executed proof, not by new schema machinery (judged deliberately minimal;
  see Alternatives).

**2. Manifest** `examples/shared/split_document.tool.yaml`:

```yaml
name: split_document
description: "Split a document into chunks for map fan-out. Args: path,
  mode=page, start?, end?. Returns {chunks: [{index, text}], total}."
runtime:
  type: python
  module: examples.shared.split_document
  function: split_document
```

**3. Demo** `examples/demos/book-summary/` (authored via the sole route,
`scripts/author.sh` — governed artifact, FR-767):

```yaml
tools:
  split_document:
    manifest: ../../shared/split_document.tool.yaml

nodes:
  split:
    type: tool_call
    tool: split_document
    args: {path: "{state.pdf}", mode: page}
    state_key: split_result
  summarize_pages:
    type: map
    over: "{state.split_result.result.chunks}"
    as: chunk
    node: {prompt: summarize_page, state_key: page_summary}
    collect: page_summaries
  reduce:
    prompt: combine_summaries
    state_key: book_summary
```

A small public-domain PDF fixture (or one generated at demo time from
`sample_book.txt` via the shell) serves as input; `demo-output.log` ships
per demo-gate.

## Acceptance Criteria

- [ ] AC-01: `examples/shared/split_document.py` exists with `mode: page`
      PDF splitting; unknown mode and missing poppler raise `ValueError`
      with actionable messages (no silent fallback — Commandment 6).
- [ ] AC-02: `examples/shared/split_document.tool.yaml` validates against
      `ToolManifest` and its description states the full args/output
      contract (the feeder seam is documented at the declaration).
- [ ] AC-03: `examples/demos/book-summary/graph.yaml` consumes the tool via
      `manifest:` only — zero inline `type:/module:/function:` keys for it.
- [ ] AC-04: Demo executes end-to-end on a real multi-page PDF: N page
      summaries produced by the map node, one reduced book summary;
      `demo-output.log` committed (demo-gate).
- [ ] AC-05: Unit tests for `split_document` (page-range slicing, chunk
      shape, unknown-mode rejection, missing-file rejection) tagged with
      the governing REQ; RED committed before GREEN.
- [ ] AC-06: Demo graph authored via `scripts/author.sh`; the run's
      `tmp/draft-authoring-report.md` evidences the route (FR-767).
- [ ] AC-07: `examples/shared/README.md` documents the tool beside
      `describe_image`; `reference/graph-yaml.md` manifest section gains
      the feeder example (tool → `over:` wiring) in ≤ 10 lines.
- [ ] AC-08: No changes under `yamlgraph/` (translation-only manifest layer
      stays untouched; this FR is examples-layer only).
- [ ] AC-09: Existing splitters (`ocr_cleanup`, `book_translator`,
      `philosopher_book`) are byte-unchanged by this FR.
- [ ] AC-10: Changelog fragment + diary reflection (diary-gate).

## Alternatives Considered

- **Add `inputs:`/`output:` schema to the manifest model** — rejected for
  this FR: one feeder consumer is one, not two. The feeder-tool diary
  (2026-08-04) names three candidate gaps (inputs, output shape, deps);
  this FR is the measurement instrument that shows which gap bites. Schema
  machinery gets its own FR only after a second feeder consumer drifts.
- **`mode: chapter|paragraph` now** — rejected: chapter splitting needs the
  LLM-marker two-phase from book_translator (a graph concern, not a tool
  concern) and paragraph splitting has no named consumer. The mode enum
  rejects them explicitly so the seam is visible.
- **Migrate the three existing splitters in this FR** — rejected: they are
  judged, working pipelines with richer contracts (`prev_last_line`,
  glossary context windows, editorial snapshots). Forcing them under one
  generic tool is the FR-044 code-abstraction trap; only their *inline
  declarations* are candidates, on their own projects' schedule.
- **Python library (pypdf) instead of poppler subprocess** — rejected:
  ocr_cleanup's subprocess approach is proven in-repo, adds zero Python
  dependencies, and the manifest layer cannot declare third-party deps yet
  (the deps gap from the feeder diary — do not hide it behind a new
  install requirement).

## Related

- FR-768 (manifest primitive), FR-770 (first terminal-tool consumer),
  FR-772 (tool_call inline dict args — the invocation shape this demo uses)
- FR-767 (sole authoring route — governs AC-06)
- `docs/diary/diary-2026-08-04-the-feeder-tool-is-the-real-manifest-customer.md`
  (the feeder/terminal distinction and the three-implementation measurement)
- `examples/ocr_cleanup/tools/pdf_extract.py` (donor implementation)
- `examples/book_translator/graph.yaml` (split→map→reduce precedent)

## Judgement (pending)

**Verdict:** —
