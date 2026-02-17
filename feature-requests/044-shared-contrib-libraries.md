# Feature Request: Shared Contributor Libraries (`yamlgraph.contrib`)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 5 days
**Requested:** 2026-02-17

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

## Related

- Lesson generator `save_lessons.py` and kertomus `result_writer.py` (60% identical)
- `on_error: skip` usage across all pipelines (15 occurrences, 0 reports)
- Diary entry: "The Constraint Shift" — Observation 5
- FR-040 (quality gates) and FR-043 (evaluation) — contrib.quality supports both
