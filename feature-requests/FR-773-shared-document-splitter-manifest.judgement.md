# Judgement: FR-773 Shared Document Splitter Manifest with Book-Summary Map/Reduce Demo

**Prior art:** FR-044 (shared contrib libraries) — its rejection of forcing
divergent implementations under one abstraction transfers and is honored:
declarations only, existing splitters byte-unchanged (C-7). FR-719 (SMT
condition verification) — noun collision on "splitter" only; unrelated
mechanism and consumer. FR-770 judgement — filename-noun match only; it is
the terminal-tool precedent this FR builds on, dispositioned in the body.

**Verdict:** APPROVED WITH REVISIONS - the feeder-tool example is real, valuable, and correctly example-scoped, but authority activates only after the FR fixes the `tool_call` callable signature mismatch, freezes traceability, and makes the PDF fixture/smoke proof deterministic.

**Reviewed against:** `feature-requests/FR-773-shared-document-splitter-manifest.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/044-shared-contrib-libraries.md`; `feature-requests/FR-719-smt-condition-verification.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-767-graph-authoring-sole-route.judgement.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `feature-requests/FR-770-vision-demo-consumes-manifest.md`; `feature-requests/FR-770-vision-demo-consumes-manifest.judgement.md`; `feature-requests/FR-771-vision-demo-executes-manifest-tool.md`; `feature-requests/FR-771-vision-demo-executes-manifest-tool.judgement.md`; `feature-requests/FR-772-tool-call-inline-dict-args.md`; `feature-requests/FR-772-tool-call-inline-dict-args.judgement.md`; `docs/diary/diary-2026-08-04-the-feeder-tool-is-the-real-manifest-customer.md`; `examples/ocr_cleanup/graph.yaml`; `examples/ocr_cleanup/tools/pdf_extract.py`; `examples/book_translator/graph.yaml`; `examples/book_translator/nodes/tools.py`; `examples/demos/philosopher_book/graph.yaml`; `examples/demos/philosopher_book/editorial_graph.yaml`; `examples/demos/philosopher_book/tools.py`; `examples/shared/README.md`; `examples/shared/describe_image.tool.yaml`; `examples/demos/shared-vision-tool/graph.yaml`; `yamlgraph/tools/manifest.py`; `yamlgraph/node_factory/tool_nodes.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/tools/python_tool.py`; `reference/graph-yaml.md`; `capabilities/CAP-05-tool-agent-integration.yaml`; `capabilities/CAP-216-tool-manifests.yaml`; `capabilities/CAP-217-shared-vision-tool.yaml`; `tests/unit/test_shared_vision_tool.py`; `tests/unit/test_fr770_demo_manifest.py`; `tests/unit/test_fr771_demo_invocation.py`; repository searches for cited legacy FRs, `load_chapters`, manifest consumers, PDF/poppler assets, and current CAP/REQ maxima.

## What is sound

The problem is real and not merely a documentation wish. FR-773 names a concrete first consumer and first event: a new `examples/demos/book-summary/` graph needing a page list from a PDF via a shared `manifest:` declaration, with `examples/ocr_cleanup` named as the next migration candidate but not in this FR's scope (`feature-requests/FR-773-shared-document-splitter-manifest.md:8-12`). The summary and value statement target a specific feeder pattern: split a document into chunks for a map node, then reduce the page summaries (`feature-requests/FR-773-shared-document-splitter-manifest.md:16-27`).

The cited splitter family exists. `ocr_cleanup` declares `extract_pdf_pages` inline (`examples/ocr_cleanup/graph.yaml:31-36`), uses it before a map node over `state.pages` (`examples/ocr_cleanup/graph.yaml:50-75`), and the donor implementation shells to `pdfinfo` and `pdftotext` before returning page dictionaries (`examples/ocr_cleanup/tools/pdf_extract.py:28-76`). `book_translator` declares `split_by_markers` inline (`examples/book_translator/graph.yaml:31-37`), stores `chunks` from `split_book` (`examples/book_translator/graph.yaml:67-72`), and fans those chunks into two map nodes (`examples/book_translator/graph.yaml:73-113`); its tool returns `{"chunks": chunks}` (`examples/book_translator/nodes/tools.py:15-29`, `examples/book_translator/nodes/tools.py:79-92`, `examples/book_translator/nodes/tools.py:141-152`). The philosopher-book editorial graph declares `load_chapters` inline (`examples/demos/philosopher_book/editorial_graph.yaml:31-36`), maps over `state.chapters` (`examples/demos/philosopher_book/editorial_graph.yaml:61-78`), and its loader returns `chapters` plus brief inputs (`examples/demos/philosopher_book/tools.py:423-476`).

The proposal is strategically classified as **Contrib/example**, not a framework primitive. FR-768 already implemented the manifest primitive as declaration translation over existing runtimes, with typed load-boundary validation and no new execution engine (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:16-20`, `feature-requests/FR-768-tool-manifest-declaration-reuse.md:84-107`; `yamlgraph/tools/manifest.py:1-10`, `yamlgraph/tools/manifest.py:63-70`, `yamlgraph/tools/manifest.py:114-180`). FR-770 and FR-771 moved the shared-vision demo from manifest declaration to registry execution (`feature-requests/FR-770-vision-demo-consumes-manifest.md:13-17`; `feature-requests/FR-771-vision-demo-executes-manifest-tool.md:13-18`), and FR-772 supplied the inline-dict `tool_call.args` shape this FR intends to use (`feature-requests/FR-772-tool-call-inline-dict-args.md:11-26`; `reference/graph-yaml.md:696-735`). FR-773 is therefore the next committed example consumer that stresses the tool-to-map seam, exactly the gap the diary names for feeder tools (`docs/diary/diary-2026-08-04-the-feeder-tool-is-the-real-manifest-customer.md:24-50`).

The scope is mostly minimal and correctly rejects adjacent complexity. The FR keeps `mode: chapter|paragraph`, manifest input/output schema machinery, pypdf, and existing splitter migrations out of scope (`feature-requests/FR-773-shared-document-splitter-manifest.md:161-181`). That honors FR-044's lesson that divergent implementations should not be forced under one generic Python abstraction when the unified API is more complex than the local code (`feature-requests/044-shared-contrib-libraries.md:23-30`, `feature-requests/044-shared-contrib-libraries.md:51-87`). It also preserves FR-768's translation-only design rather than changing manifest runtime semantics (`reference/graph-yaml.md:1418-1468`).

The graph-authoring discipline is correctly recognized. The demo graph and prompt files are governed artifacts, and repo doctrine requires `scripts/author.sh <task-brief.md>` plus a `tmp/draft-authoring-report.md` validation record for material graph/prompt authoring (`.github/copilot-instructions.md:15`). FR-773 already includes that as AC-06 (`feature-requests/FR-773-shared-document-splitter-manifest.md:150-151`).

## Required revisions

### R-1: Make `split_document` compatible with the authorized `tool_call` invocation path

Revise the proposed shared implementation signature and every affected path reference before enforcement. FR-773 currently proposes `def split_document(state: dict) -> dict` (`feature-requests/FR-773-shared-document-splitter-manifest.md:71-80`) but the demo sketch invokes it through a `type: tool_call` node with inline dict args (`feature-requests/FR-773-shared-document-splitter-manifest.md:113-124`). The runtime calls tool registry callables as keyword arguments, `tool_func(**args)` (`yamlgraph/node_factory/tool_nodes.py:80-83`), while state-dict functions are the `type: python` node contract (`yamlgraph/tools/python_tool.py:230-233`, `yamlgraph/tools/python_tool.py:305-306`).

Fold one exact contract into the FR: `split_document(path: str, mode: str = "page", start: int | None = None, end: int | None = None) -> dict` returns `{"chunks": [{"index": int, "text": str}], "total": int}` and is invoked by `tool_call` inline kwargs. The demo's map path must consistently consume `state.split_result.result.chunks`; remove or correct the earlier `state.chunks.chunks` wording (`feature-requests/FR-773-shared-document-splitter-manifest.md:59-62`) so the ideal, solution sketch, tests, and smoke proof describe the same state shape.

### R-2: Complete the splitter error contract instead of inheriting donor blind spots

Add an explicit failure contract for the lifted PDF path. The donor implementation is useful precedent but it does not check subprocess return codes and assumes `pdfinfo` output contains a `Pages:` line (`examples/ocr_cleanup/tools/pdf_extract.py:28-34`, `examples/ocr_cleanup/tools/pdf_extract.py:44-57`). FR-773 promises unknown mode and missing poppler errors with no silent fallback (`feature-requests/FR-773-shared-document-splitter-manifest.md:83-91`, `feature-requests/FR-773-shared-document-splitter-manifest.md:136-138`) and AC-05 also expects missing-file rejection (`feature-requests/FR-773-shared-document-splitter-manifest.md:147-149`). Repo doctrine requires errors to surface rather than degrade into plausible success (`.github/copilot-instructions.md:216-220`).

Fold into the FR: direct calls to `split_document` must raise `ValueError` naming the offending condition for unknown `mode`, missing input file, missing `pdfinfo` or `pdftotext` with a poppler install hint, nonzero `pdfinfo`/`pdftotext`, and unparseable page-count output. In graph execution, the `tool_call` envelope may contain `success: false` because that is the node contract, but the demo smoke must assert `split_result.success` is true before any map/reduce success is credited.

### R-3: Freeze requirement traceability for the new shared tool and artifact tests

Replace "the governing REQ" with exact registry instructions. AC-05 requires tests "tagged with the governing REQ" but does not name the requirement (`feature-requests/FR-773-shared-document-splitter-manifest.md:147-149`). Repo doctrine requires every test to carry a concrete `@pytest.mark.req("REQ-YG-XXX")`, and new capabilities require a capability YAML file (`.github/copilot-instructions.md:173-176`). The closest precedent is the shared vision tool: it has its own `capabilities/CAP-217-shared-vision-tool.yaml` and `REQ-YG-575`, separate from the manifest primitive (`capabilities/CAP-217-shared-vision-tool.yaml:1-24`), while manifest mechanics remain under `REQ-YG-574` (`capabilities/CAP-216-tool-manifests.yaml:1-25`) and inline `tool_call.args` under `REQ-YG-576` (`capabilities/CAP-05-tool-agent-integration.yaml:18-28`).

Fold into the FR: add `capabilities/CAP-218-shared-document-splitter.yaml` with `REQ-YG-577` for `examples.shared.split_document.split_document`, and tag direct splitter tests with `REQ-YG-577`. Artifact tests whose purpose is manifest expansion may use `REQ-YG-574`; artifact tests whose purpose is inline kwargs dispatch may use `REQ-YG-576`. If those numeric IDs are consumed by another merge before enforcement, revise the FR to the actual next-free exact IDs before implementation; do not leave the choice to the enforcer.

### R-4: Make the PDF fixture and smoke evidence deterministic

Replace the fixture alternative with one exact, reviewable strategy. The FR currently says a "small public-domain PDF fixture (or one generated at demo time from `sample_book.txt` via the shell)" serves as input (`feature-requests/FR-773-shared-document-splitter-manifest.md:130-132`), while AC-04 requires a real multi-page PDF smoke (`feature-requests/FR-773-shared-document-splitter-manifest.md:144-146`). That is not mechanically checkable: "public-domain" needs provenance, and "generated at demo time" needs a named generator and dependency contract. The feeder-tool diary also identifies external PDF dependencies as the exact manifest gap this example is meant to expose (`docs/diary/diary-2026-08-04-the-feeder-tool-is-the-real-manifest-customer.md:40-43`).

Fold into the FR either a committed repo-contained multi-page PDF fixture with provenance and license/source text documented beside it, or a deterministic generation step that names the command, input text, and dependency. The smoke criterion must require `demo-output.log` to prove: the splitter ran against that real PDF, `split_result.success` is true, `total == N`, `len(chunks) == N` for `N >= 2`, exactly `N` page summaries were collected by the map node, and the reduced book summary is non-empty.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-773-shared-document-splitter-manifest.md` revised to fold R-1 through R-4 before enforcement authority activates |
| D-2 | `examples/shared/split_document.py` implementing the kwargs-compatible page splitter and explicit failure contract |
| D-3 | `examples/shared/split_document.tool.yaml` declaring `split_document` as a `runtime.type: python` module manifest |
| D-4 | Unit tests for direct splitter behavior and artifact tests for committed manifest/tool_call/demo wiring, with exact requirement markers |
| D-5 | `capabilities/CAP-218-shared-document-splitter.yaml` with `REQ-YG-577`, unless the FR is revised to the actual next-free exact IDs before enforcement |
| D-6 | `examples/demos/book-summary/` graph, prompts, fixture or deterministic fixture-generation artifact, and `demo-output.log`, all authored through the graph-authoring route |
| D-7 | `examples/shared/README.md` and `reference/graph-yaml.md` directly related docs, including the feeder tool -> `over:` wiring example |
| D-8 | Changelog fragment and diary reflection required by repo gates |

Not authorized: changes under `yamlgraph/`; manifest schema changes such as `inputs:` or `output:`; new runtime dependency declarations; `mode: chapter`, `mode: paragraph`, OCR cleanup migration, book translator migration, philosopher-book migration, or any change to their existing splitter behavior; pypdf or other new Python PDF dependencies; changes to global `tool_call`, expression, map, graph-loader, linter, CI, hook, judge, review, or release doctrine; committing copyrighted or provenance-unclear PDF content; substituting mocked/stale demo output for the required real PDF smoke.

## Revised acceptance criteria

- [ ] AC-01: `examples/shared/split_document.py` exposes `split_document(path: str, mode: str = "page", start: int | None = None, end: int | None = None) -> dict`, supports only `mode: "page"`, and returns `{"chunks": [{"index": int, "text": str}], "total": int}` with 0-based chunk indexes and one chunk per selected PDF page.
- [ ] AC-02: Direct splitter tests cover page-range slicing, chunk shape, unknown-mode rejection, missing-file rejection, missing `pdfinfo`/`pdftotext` rejection with a poppler install hint, nonzero subprocess rejection, and unparseable page-count rejection; these tests are marked `@pytest.mark.req("REQ-YG-577")`.
- [ ] AC-03: `examples/shared/split_document.tool.yaml` validates as a `ToolManifest`, uses `runtime.type: python` with `module: examples.shared.split_document` and `function: split_document`, and its description states the full args and output contract.
- [ ] AC-04: A committed artifact test loads the book-summary graph and proves `tools.split_document` contains only `manifest: ../../shared/split_document.tool.yaml`; the expanded config matches the manifest module/function/description contract.
- [ ] AC-05: A committed artifact test feeds the book-summary `split` node config to `create_tool_call_node` with a recorder and proves inline args resolve to real kwargs for `path`, `mode`, `start`, and `end` as configured, with no unresolved `{state.` placeholder and no state-dict callable assumption.
- [ ] AC-06: `examples/demos/book-summary/graph.yaml` consumes the manifest-declared splitter through a `type: tool_call` node, maps over `"{state.split_result.result.chunks}"`, collects one page summary per chunk, and reduces those page summaries into one `book_summary`.
- [ ] AC-07: The demo graph and prompt files are authored via `scripts/author.sh`; the run's `tmp/draft-authoring-report.md` records graph lint and smoke evidence for `examples/demos/book-summary/graph.yaml`.
- [ ] AC-08: The demo uses one exact real multi-page PDF fixture strategy recorded in the FR. `demo-output.log` proves `split_result.success is true`, `total == len(chunks) == N` for `N >= 2`, `len(page_summaries) == N`, and a non-empty reduced book summary.
- [ ] AC-09: `examples/shared/README.md` documents `split_document` beside `describe_image`, including poppler dependency and failure modes; `reference/graph-yaml.md` adds a <= 10-line feeder manifest example showing tool output wired into `over:`.
- [ ] AC-10: `capabilities/CAP-218-shared-document-splitter.yaml` with `REQ-YG-577` is added unless the FR is revised before enforcement to another exact next-free capability/requirement pair; every new or changed test has a requirement marker.
- [ ] AC-11: No files under `yamlgraph/` change, and existing splitters in `examples/ocr_cleanup`, `examples/book_translator`, and `examples/demos/philosopher_book` are byte-unchanged.
- [ ] AC-12: A changelog fragment and diary reflection are added.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-4 are folded into `feature-requests/FR-773-shared-document-splitter-manifest.md`. | GATE |
| C-2 | The shared splitter must match the `tool_call` kwargs contract. If enforcement wants a `state: dict` callable, a passthrough workaround, or a core dispatch change, stop and re-enter judgement. | GATE |
| C-3 | Invalid splitter inputs and poppler/subprocess failures must fail explicitly; no empty chunk list, partial success, or fallback-to-all-pages behavior may stand in for an error. | GATE |
| C-4 | The PDF fixture must be repo-contained with documented provenance or generated by a documented deterministic command; no copyrighted or provenance-unclear PDF content may be added. | GATE |
| C-5 | The book-summary graph and prompt artifacts must be authored through the graph-authoring route and must retain its validation report evidence. | GATE |
| C-6 | Smoke success is judged by graph state evidence (`split_result.success`, chunk count, page-summary count, non-empty book summary), not by process exit or a stale `demo-output.log` alone. | GATE |
| C-7 | Existing splitter projects remain untouched; migration of any existing consumer requires separate authority. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may add the shared page splitter manifest and kwargs-compatible implementation, create the book-summary feeder demo through the graph-authoring route, add the directly related tests/docs/capability/changelog/diary, and nothing else.
