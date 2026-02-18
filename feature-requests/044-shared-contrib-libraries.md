# Feature Request: Shared Contributor Libraries (`yamlgraph.contrib`)

**Priority:** HIGH
**Type:** Enhancement
**Status:** IMPLEMENTED (Phase 1)
**Effort:** 1 day (Phase 1), 2 days (Phase 2)
**Requested:** 2026-02-17

## Implementation (2026-02-18)

**Phase 1 COMPLETE:**
- Created `yamlgraph/contrib/__init__.py` and `yamlgraph/contrib/utils.py`
- Implemented `get_map_result()` and `to_serializable()`
- Added 12 tests in `tests/unit/test_contrib_utils.py`
- Added REQ-YG-070 to ARCHITECTURE.md and req_coverage.py (CAP-20)
- Refactored `examples/book_translator/nodes/tools.py` to use contrib

**Files created:**
- `yamlgraph/contrib/__init__.py`
- `yamlgraph/contrib/utils.py`
- `tests/unit/test_contrib_utils.py`

**Files modified:**
- `ARCHITECTURE.md` — added CAP-20 and REQ-YG-070
- `scripts/req_coverage.py` — added CAP-20 and extended ALL_REQS
- `examples/book_translator/nodes/tools.py` — now imports from contrib

**Next:** Phase 2 (contrib.io) is DEFERRED pending evidence of need.

## Judgment (2026-02-18) — REVISED

**Verdict:** APPROVE Phase 1 (revised scope). SPLIT OFF SkipReport.

### Contradictions Found in Original Judgment

**Contradiction 1: Phase 1 was invention, not extraction**
Original claimed "SkipReport — simple extraction." But research shows: "Category 7: Progress / Reporting — **No dedicated modules found.** 0 of 56 tool files report skip counts." SkipReport doesn't exist anywhere — it would be inventing a new pattern, not extracting.

**Contradiction 2: SkipReport requires framework changes, not a contrib library**
To report skipped items, the framework must accumulate skip information during map execution (currently doesn't), surface it to state (currently swallowed), and provide a hook to report it. This is a framework feature in `map_compiler.py`, not a utility function.

**Contradiction 3: Actual extractable code was ignored**
Research shows real duplication:
- `get_map_result()` — duplicated verbatim in 3 files
- `to_serializable()` / `_unwrap_map_value()` — duplicated ~15 times
- Save pattern — 60% identical between `save_lessons.py` and `result_writer.py`

These are extractable today with zero framework changes.

### Revised Phasing

**Phase 1 (1 day) — APPROVED:**
- `yamlgraph/contrib/__init__.py`
- `yamlgraph/contrib/utils.py`:
  - `get_map_result(item)` — unwrap single-key dict from map output
  - `to_serializable(obj)` — Pydantic → dict recursively
- Refactor one existing file (e.g., `save_lessons.py`) to use it
- Tests with `@pytest.mark.req`

**Phase 1a — SPLIT OFF to FR-044a:**
- SkipReport is a **framework feature**, not a contrib library
- New FR-044a: "on_error: skip visibility"
- Changes to `map_compiler.py` to accumulate and expose skip information

**Phase 2 (2 days) — DEFERRED:**
- `contrib.io` with `ItemWriter`, `save_items()`
- Extract from `save_lessons.py` + `result_writer.py`
- Defer `contrib.quality` until FR-040/043 need it

**Reasoning:** Start with what's actually duplicated and extractable. The SkipReport feature is real but belongs in a different FR because it requires framework changes, not library code.

## Summary

Extract recurring patterns from the 10 existing YAMLGraph pipelines into shared contributor libraries: `yamlgraph.contrib.io` (load/save/report), `yamlgraph.contrib.quality` (review/grade/iterate), `yamlgraph.contrib.bootstrap` (template/render/init). Kill copy-paste entropy across projects.

## Problem

The 10 YAMLGraph pipelines were built sequentially. Each partially reinvents the same utilities:

- **Save patterns:** `save_lessons.py` (lesson generator) and `result_writer.py` (kertomus) are 60% identical code — both write structured output to files with metadata, both handle directories, both format filenames.
- **Load patterns:** Every pipeline has a Python node that reads files, parses JSON/YAML, and populates state. These are structurally identical.
- **Error reporting:** `on_error: skip` appears 15 times across all pipelines, but no pipeline reports what was skipped. Failed items vanish silently. No pipeline says "3 of 20 lessons failed, here are the errors."
- **Progress reporting:** Some pipelines log item counts, some don't. No standard progress pattern.
- **Map error handling:** Each map node reinvents how to handle partial failures.

This is entropy accumulation. Each new pipeline copies from a previous one, makes small changes, and the divergence grows. Bug fixes in one pipeline don't propagate to others.

## Proposed Solution

### Module Structure

```
yamlgraph/
  contrib/
    __init__.py
    io.py          # File I/O primitives for Python nodes
    quality.py     # Quality review and grading utilities
    bootstrap.py   # Template rendering and project init
    progress.py    # Standardized progress reporting
```

### `yamlgraph.contrib.io`

```python
from yamlgraph.contrib.io import save_items, load_items, ItemWriter

# In a Python node:
def save_lessons(state: dict) -> dict:
    """Save generated lessons to files."""
    writer = ItemWriter(
        output_dir=state["output_dir"],
        filename_template="{module}_{index:02d}_{title}.md",
        metadata={"subject": state["subject"]},
    )
    report = writer.write_all(state["lessons"])
    # report: {written: 18, skipped: 0, errors: [], paths: [...]}
    return {"save_report": report}
```

### `yamlgraph.contrib.quality`

```python
from yamlgraph.contrib.quality import ReviewResult, collect_failures

# Standard review result aggregation
def aggregate_reviews(state: dict) -> dict:
    """Collect review results and identify failures."""
    reviews = state["reviews"]
    failures = collect_failures(reviews, threshold=0.7)
    # failures: [{"index": 3, "score": 0.4, "issues": [...]}, ...]
    return {
        "quality_report": {
            "total": len(reviews),
            "passed": len(reviews) - len(failures),
            "failed": len(failures),
            "mean_score": sum(r.score for r in reviews) / len(reviews),
        },
        "items_to_retry": failures,
    }
```

### `yamlgraph.contrib.progress`

```python
from yamlgraph.contrib.progress import SkipReport

# Standard skip reporting for on_error: skip
def report_skips(state: dict) -> dict:
    """Report what was skipped and why."""
    report = SkipReport.from_errors(state.get("errors", []))
    # Logs: "⚠ 3 of 20 items skipped: [item_5: timeout, item_12: validation, item_18: rate_limit]"
    report.log()
    return {"skip_report": report.to_dict()}
```

### Graph YAML Integration

Contrib modules can be referenced directly in graph nodes:

```yaml
nodes:
  save_results:
    type: python
    module: yamlgraph.contrib.io
    function: save_items
    config:
      output_dir: "{output_dir}"
      filename_template: "{module}_{index:02d}.md"
```

## Acceptance Criteria

- [ ] `yamlgraph.contrib.io` module with `ItemWriter`, `save_items`, `load_items`
- [ ] `yamlgraph.contrib.quality` module with `collect_failures`, review aggregation
- [ ] `yamlgraph.contrib.progress` module with `SkipReport` for `on_error: skip` visibility
- [ ] All contrib modules use Pydantic models (no untyped dicts)
- [ ] At least one existing pipeline refactored to use contrib (lesson generator or kertomus)
- [ ] `on_error: skip` items produce visible reports, not silent drops
- [ ] Tests added with `@pytest.mark.req` tags
- [ ] API documentation for each contrib module
- [ ] Migration guide for converting existing Python nodes to use contrib

## Alternatives Considered

- **Per-project shared utils:** Each project maintains its own `utils/` directory. Current approach — leads to drift and duplication.
- **Generic plugin system:** A full plugin architecture with discovery, registration, etc. Overkill for shared utilities; contrib is just well-organized library code.
- **Extracting to separate package:** `pip install yamlgraph-contrib`. Adds release management overhead; better to ship with core until the API stabilizes.

## Research: Tool Inventory (2026-02-17)

**56 Python tool/node files** across 5 examples, 3 projects, 1 shared module, and framework tools.
**19 `on_error: skip` occurrences** across 10 YAML files. **0 skip reports** — every skip is silent.

### `on_error: skip` Occurrences (19 total)

| File | Count |
|------|-------|
| `projects/innovators_toolkit/toolkit.yaml` | 9 |
| `examples/book_translator/graph.yaml` | 2 |
| `projects/opinto_ohjaus/prepare.yaml` | 1 |
| `projects/opinto_ohjaus/generate.yaml` | 1 |
| `projects/opinto_ohjaus/projects/psykologia/prepare.yaml` | 1 |
| `projects/opinto_ohjaus/projects/psykologia/generate.yaml` | 1 |
| `examples/ocr_cleanup/graph.yaml` | 1 |
| `examples/daily_digest/graph.yaml` | 1 |
| `examples/demos/system-status/graph.yaml` | 1 |
| `tests/fixtures/linter/retry_tool_pass.yaml` | 1 |

### Category 1: IO — Load / Save / Report

| File | Pipeline | Description |
|------|----------|-------------|
| `projects/kertomus-yamlgraph/nodes/result_writer.py` | kertomus | Multi-file save with manifest (patient history, kertomus, summaries, validation) |
| `projects/opinto_ohjaus/nodes/save_lessons.py` | opinto_ohjaus | Map-output → numbered markdown files + index.md |
| `projects/opinto_ohjaus/nodes/save_preparation.py` | opinto_ohjaus | Saves preparation phase as JSON, strips LLM metadata |
| `projects/opinto_ohjaus/nodes/load_data.py` | opinto_ohjaus | Loads JSON, builds per-topic lesson bundles for map fan-out |
| `projects/innovators_toolkit/nodes/write_report.py` | innovators_toolkit | Single-file save to `output/{run_id}/report.md` |
| `projects/innovators_toolkit/nodes/assemble_report.py` | innovators_toolkit | Section-per-file + concatenated report |
| `examples/beautify/nodes.py` (load/save) | beautify | Loads graph YAML as text; saves rendered HTML |
| `examples/questionnaire/tools/handlers.py` (save) | questionnaire | Saves feature request as markdown with slug filename |
| `examples/yamlgraph_gen/tools/file_ops.py` | yamlgraph_gen | `read_file`, `write_file`, `list_files`, `ensure_directory`, `write_generated_files` |
| `examples/ocr_cleanup/tools/pdf_extract.py` | ocr_cleanup | Extracts text from PDF page-by-page via `pdftotext` |
| `examples/ocr_cleanup/tools/merge_corrected.py` | ocr_cleanup | Merges corrected text with original JSON using fuzzy matching |
| `examples/ocr_cleanup/tools/verify_merge.py` | ocr_cleanup | Verifies merged output: low confidence, page coverage, order violations |
| `examples/daily_digest/nodes/email.py` | daily_digest | Sends email via Resend API with dry-run support |
| `examples/rag/tools/rag_retrieve.py` | rag | LanceDB vector store retrieval |

**Duplication hotspots:**
- `result_writer.py` (kertomus) and `save_lessons.py` (opinto_ohjaus) are ~60% identical
- `_to_serializable()` / `_unwrap_map_value()` / `get_map_result()` duplicated in 4 files
- Pydantic→dict conversion (`hasattr(x, 'model_dump')`) repeated ~15 times

### Category 2: Transform — Data Manipulation

| File | Pipeline | Description |
|------|----------|-------------|
| `projects/kertomus-yamlgraph/nodes/history_merger.py` | kertomus | Merges 6 patient history sections into single markdown |
| `projects/kertomus-yamlgraph/nodes/fhir_extractor.py` | kertomus | Per-encounter FHIR bundle reconstruction (556 lines) |
| `projects/kertomus-yamlgraph/nodes/link_enhancer.py` | kertomus | Date references → clickable markdown links via 6 regex patterns |
| `projects/innovators_toolkit/nodes/cartesian.py` | innovators_toolkit | Cartesian product of capability × constraint pairs |
| `projects/innovators_toolkit/nodes/format_output.py` | innovators_toolkit | Pydantic `TopIdeas` → plain markdown |
| `examples/book_translator/nodes/splitter.py` | book_translator | Text chunking by chapters/size/LLM markers (273 lines) |
| `examples/book_translator/nodes/tools.py` | book_translator | LLM chapter markers + `get_map_result()` |
| `examples/book_translator/nodes/glossary.py` | book_translator | Merge extracted terms into unified glossary |
| `examples/book_translator/nodes/assembler.py` | book_translator | Reassemble proofread chunks with priority fallback chain |
| `examples/ocr_cleanup/tools/merger.py` | ocr_cleanup | Merge spanning paragraphs, aggregate corrections. Also has `get_map_result()` |
| `examples/ocr_cleanup/tools/preprocessor.py` | ocr_cleanup | Text normalization: quotes, unexpected characters (Finnish) |
| `examples/daily_digest/nodes/content.py` | daily_digest | Fetch + extract article text via BeautifulSoup |
| `examples/daily_digest/nodes/filters.py` | daily_digest | Filter recent articles, deduplicate with SQLite |
| `examples/daily_digest/nodes/sources.py` | daily_digest | Hacker News API + RSS feed fetcher |
| `examples/questionnaire/tools/handlers.py` | questionnaire | Conversation state: append/prune/detect gaps/apply corrections |

### Category 3: Bootstrap — Template / Render / Init

| File | Pipeline | Description |
|------|----------|-------------|
| `projects/opinto_ohjaus/nodes/render_templates.py` | opinto_ohjaus | Jinja2 prompt templates using subject summaries, writes vars.yaml |
| `examples/daily_digest/nodes/formatting.py` | daily_digest | HTML email via Jinja2 with fallback to embedded default template |
| `examples/beautify/nodes.py` (render_html) | beautify | HTML infographic template with theme support via Jinja2 |
| `examples/yamlgraph_gen/tools/snippet_loader.py` | yamlgraph_gen | Loads YAML snippets by pattern (linear/router/map/etc.) |
| `examples/codegen/tools/template_tools.py` | codegen | Extracts reusable function/class/test templates via AST (357 lines) |
| `examples/codegen/tools/meta_tools.py` | codegen | Extracts patterns from existing graph/prompt YAML for meta-templates |

### Category 4: Quality — Review / Grade / Validate

| File | Pipeline | Description |
|------|----------|-------------|
| `examples/openai_proxy/nodes/tools.py` | openai_proxy | Guardrail: echo input + validate (stamps "validation missing") |
| `examples/yamlgraph_gen/tools/linter.py` | yamlgraph_gen | Wraps `yamlgraph graph lint` as a node |
| `examples/yamlgraph_gen/tools/prompt_validator.py` | yamlgraph_gen | Validates prompt YAML structure: required/optional keys, schema blocks |
| `examples/yamlgraph_gen/tools/runner.py` | yamlgraph_gen | Runs generated graph with real LLM for validation; parses runtime errors |
| `examples/codegen/tools/syntax_tools.py` | codegen | Validates Python code syntax via `ast.parse()` |

### Category 5: External — API / Shell / Image Generation

| File | Pipeline | Description |
|------|----------|-------------|
| `examples/shared/replicate_tool.py` | **shared** | Image generation via Replicate API (z-image, hidream). **Already shared.** |
| `examples/shared/websearch.py` | **shared** | Web search via DuckDuckGo. **Already shared.** |
| `examples/npc/nodes/image_node.py` | npc | NPC scene images via shared/replicate_tool |
| `examples/storyboard/nodes/image_node.py` | storyboard | Storyboard panel images via shared/replicate_tool |
| `examples/storyboard/nodes/animated_image_node.py` | storyboard | 3 frames per panel for animation |
| `examples/storyboard/nodes/character_node.py` | storyboard | Character-consistent storyboard with img2img |
| `examples/storyboard/nodes/animated_character_node.py` | storyboard | Animated character-consistent images |
| `examples/storyboard/nodes/replicate_tool.py` | storyboard | Re-exports from `examples.shared.replicate_tool` |
| `examples/booking/nodes/slots_handler.py` | booking | Booking operations: check availability, book. Mock + DB |
| `examples/booking/nodes/schema.py` | booking | Pydantic models: `Slot`, `Booking` |
| `examples/codegen/tools/git_tools.py` | codegen | `git_blame` and `git_log` for code context |
| `examples/codegen/tools/impl_executor.py` | codegen | Parses impl-agent instructions → shell scripts (615 lines) |

### Category 6: Code Analysis (codegen-specific)

| File | Pipeline | Description |
|------|----------|-------------|
| `examples/codegen/tools/ast_analysis.py` | codegen | AST module structure: classes, functions, imports with line numbers |
| `examples/codegen/tools/jedi_analysis.py` | codegen | Semantic analysis: `find_references`, `get_callers`, `get_callees` |
| `examples/codegen/tools/code_context.py` | codegen | `read_lines`, `find_related_tests`, `search_in_file`, `search_codebase` |
| `examples/codegen/tools/code_nav.py` | codegen | `list_package_modules` — discovers Python modules with summaries |
| `examples/codegen/tools/dependency_tools.py` | codegen | `get_imports` and `get_dependents` — import analysis |
| `examples/codegen/tools/ai_helpers.py` | codegen | `summarize_module`, `diff_preview`, `find_similar_code` |
| `examples/codegen/tools/example_tools.py` | codegen | Finds real usage examples and error handling patterns |

### Category 7: Progress / Reporting

**No dedicated modules found.** This confirms the diary observation: 0 of 56 tool files report skip counts or progress. The `on_error: skip` pattern (19 occurrences) is entirely silent.

### Framework-Level Tools (`yamlgraph/tools/`) — NOT extraction candidates

| File | Description |
|------|-------------|
| `yamlgraph/tools/shell.py` | Shell executor with `shlex.quote` sanitization |
| `yamlgraph/tools/python_tool.py` | Dynamic Python function loader from module path |
| `yamlgraph/tools/nodes.py` | Node factories for tool nodes: variable resolution, shell execution |
| `yamlgraph/tools/agent.py` | Agent node factory: LLM-driven tool loops |

### Top Extraction Candidates

1. **`yamlgraph.contrib.io`** — Highest duplication:
   - `save_items_as_files(items, dir, pattern)` — replaces `save_lessons.py`, `result_writer.py`, `assemble_report.py`
   - `get_map_result(item)` — duplicated verbatim in 3 files
   - `to_serializable(obj)` — Pydantic→dict conversion, duplicated ~15 times

2. **`yamlgraph.contrib.progress`** — Zero existing implementations:
   - `SkipReport` for `on_error: skip` visibility (19 silent occurrences)

3. **`yamlgraph.contrib.quality`** — Validation helpers exist but scattered:
   - Syntax checking, prompt validation, lint wrappers

4. **`yamlgraph.contrib.bootstrap`** — Template rendering in 3 pipelines:
   - Jinja2 render pattern used in opinto_ohjaus, daily_digest, beautify

## Related

- Lesson generator `save_lessons.py` and kertomus `result_writer.py` (60% identical)
- `on_error: skip` usage across all pipelines (19 occurrences, 0 reports)
- Diary entry: "The Constraint Shift" — Observation 5
- FR-040 (quality gates) and FR-043 (evaluation) — contrib.quality supports both
