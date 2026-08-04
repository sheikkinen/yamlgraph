# Feature Request: FR-773 — Shared Document Splitter Manifest with Book-Summary Map/Reduce Demo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged 2026-08-04 — APPROVED WITH REVISIONS; R-1..R-4 folded below; authority active per judgement
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
`over: "{state.split_result.result.chunks}"` into a map node — for PDF pages today,
without reading any implementation code. The three existing splitters are
unaffected (migration is their own projects' concern, on their next edit);
the book-summary demo exists, runs, and its `demo-output.log` proves a real
PDF was summarized page-by-page and reduced.

## Proposed Solution

Minimal path back from the ideal — three artifacts, no core changes:

**1. Shared implementation** `examples/shared/split_document.py`:

```python
def split_document(
    path: str,
    mode: str = "page",
    start: int | None = None,
    end: int | None = None,
) -> dict:
    """Split a document into chunks for map fan-out.

    Returns {"chunks": [{"index": int, "text": str}], "total": int}
    with 0-based chunk indexes, one chunk per selected PDF page.
    """
```

Kwargs signature, invoked via `type: tool_call` inline dict args (FR-772;
the registry calls `tool_func(**args)` — a `state: dict` callable is the
`type: python` node contract and would not dispatch here; judgement R-1/C-2).

- `mode: page` delegates to the proven `pdfinfo`/`pdftotext` subprocess
  approach from `ocr_cleanup/tools/pdf_extract.py` (lifted, not imported —
  ocr_cleanup keeps its richer `prev_last_line` contract untouched).
- **Failure contract (judgement R-2, complete — no silent fallback):**
  direct calls raise `ValueError` naming the offending condition for
  unknown `mode`, missing input file, missing `pdfinfo`/`pdftotext` (with
  the `brew install poppler` hint), nonzero `pdfinfo`/`pdftotext` exit,
  and unparseable page-count output. In graph execution the `tool_call`
  envelope may carry `success: false` (node contract); the demo smoke
  must assert `split_result.success` is true before crediting map/reduce.
- Output contract is documented in the module docstring AND the manifest
  description — the feeder seam is closed by documentation + the demo's
  executed proof, not by new schema machinery (judged deliberately minimal;
  see Alternatives).
- **Traceability (judgement R-3):** new `capabilities/CAP-218-shared-document-splitter.yaml`
  with `REQ-YG-577` governs direct splitter tests; artifact tests for
  manifest expansion use `REQ-YG-574`, inline-kwargs dispatch tests use
  `REQ-YG-576`. If those IDs are consumed before enforcement, revise the
  FR to the actual next-free IDs — the choice is not the enforcer's.

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

**Fixture (judgement R-4, one exact strategy):** a committed repo-contained
multi-page PDF, `examples/demos/book-summary/fixture.pdf`, generated once
from the repo-owned `examples/book_translator/sample_book.txt` with the
generating command recorded in the demo README beside a provenance note
(source text is repo-authored; no external or provenance-unclear content).
`demo-output.log` must prove: `split_result.success` is true,
`total == len(chunks) == N` for `N >= 2`, `N` page summaries collected by
the map node, and a non-empty reduced book summary.

## Acceptance Criteria (revised per judgement — binding set)

- [ ] AC-01: `examples/shared/split_document.py` exposes
      `split_document(path: str, mode: str = "page", start: int | None = None, end: int | None = None) -> dict`,
      supports only `mode: "page"`, and returns
      `{"chunks": [{"index": int, "text": str}], "total": int}` with
      0-based chunk indexes and one chunk per selected PDF page.
- [ ] AC-02: Direct splitter tests cover page-range slicing, chunk shape,
      unknown-mode rejection, missing-file rejection, missing
      `pdfinfo`/`pdftotext` rejection with a poppler install hint, nonzero
      subprocess rejection, and unparseable page-count rejection; marked
      `@pytest.mark.req("REQ-YG-577")`. RED committed before GREEN.
- [ ] AC-03: `examples/shared/split_document.tool.yaml` validates as a
      `ToolManifest`, uses `runtime.type: python` with
      `module: examples.shared.split_document` and
      `function: split_document`, and its description states the full args
      and output contract.
- [ ] AC-04: A committed artifact test loads the book-summary graph and
      proves `tools.split_document` contains only
      `manifest: ../../shared/split_document.tool.yaml`; the expanded
      config matches the manifest module/function/description contract.
- [ ] AC-05: A committed artifact test feeds the book-summary `split` node
      config to `create_tool_call_node` with a recorder and proves inline
      args resolve to real kwargs for `path`, `mode`, `start`, and `end`
      as configured, with no unresolved `{state.` placeholder and no
      state-dict callable assumption.
- [ ] AC-06: `examples/demos/book-summary/graph.yaml` consumes the
      manifest-declared splitter through a `type: tool_call` node, maps
      over `"{state.split_result.result.chunks}"`, collects one page
      summary per chunk, and reduces those into one `book_summary`.
- [ ] AC-07: The demo graph and prompt files are authored via
      `scripts/author.sh`; the run's `tmp/draft-authoring-report.md`
      records graph lint and smoke evidence for
      `examples/demos/book-summary/graph.yaml`.
- [ ] AC-08: The demo uses the one exact fixture strategy recorded above.
      `demo-output.log` proves `split_result.success` is true,
      `total == len(chunks) == N` for `N >= 2`, `len(page_summaries) == N`,
      and a non-empty reduced book summary.
- [ ] AC-09: `examples/shared/README.md` documents `split_document` beside
      `describe_image`, including poppler dependency and failure modes;
      `reference/graph-yaml.md` adds a ≤ 10-line feeder manifest example
      showing tool output wired into `over:`.
- [ ] AC-10: `capabilities/CAP-218-shared-document-splitter.yaml` with
      `REQ-YG-577` is added (or the FR revised to the actual next-free
      pair before enforcement); every new or changed test has a
      requirement marker.
- [ ] AC-11: No files under `yamlgraph/` change; existing splitters in
      `examples/ocr_cleanup`, `examples/book_translator`, and
      `examples/demos/philosopher_book` are byte-unchanged.
- [ ] AC-12: Changelog fragment + diary reflection (diary-gate).

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

## Judgement (2026-08-04)

**Verdict:** APPROVED WITH REVISIONS — sound feeder-tool/demo direction,
gated on the `tool_call` kwargs signature (R-1), a complete splitter error
contract (R-2), frozen traceability CAP-218/REQ-YG-577 (R-3), and a
deterministic PDF fixture strategy (R-4). All four folded above
(2026-08-04). Full verdict, scope freeze, and enforcement conditions
C-1..C-7 (all GATE): `FR-773-shared-document-splitter-manifest.judgement.md`
(sole-route judge graph, gpt-5.5, session ac9abfd6).

**Scope frozen:** D-1..D-8 per judgement. Not authorized: any `yamlgraph/`
change, manifest schema changes, new PDF dependencies, chapter/paragraph
modes, or migration of existing splitter projects.
