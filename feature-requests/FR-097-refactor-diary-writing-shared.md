# Feature Request: Refactor diary writing utilities to examples/shared

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-25
**Implemented:** 2026-02-25

## Summary

Move the shared diary writing functions (`format_diary_entry`, `append_to_diary`, `write_diary`) from `examples/diary_digest/nodes/writing.py` to `examples/shared/diary.py`, establishing neutral ownership for code consumed by multiple workflows.

## Value Statement

Graph authors and maintainers get clean module boundaries, eliminating implicit coupling between unrelated examples (`diary_digest` and `.chaplain`).

## Problem

The `diary_writing` tool lives in `examples/diary_digest/nodes/writing.py` but is consumed by two independent workflows:

1. **`examples/diary_digest/graph.yaml`** — the original Daily Digest pipeline
2. **`.chaplain/graph.yaml`** — the Plan→Judge→Diary workflow (FR-093)

This creates:
- **Implicit coupling**: `.chaplain/` depends on `diary_digest`'s internal module structure
- **Confusing import paths**: `examples.diary_digest.nodes.writing` suggests diary_digest ownership
- **Fragile refactoring**: Changes to `diary_digest` internals can break `.chaplain/`

`examples/shared/` already exists with `replicate_tool.py` and `websearch.py`, establishing precedent for cross-example shared utilities.

## Proposed Solution

### 1. Create `examples/shared/diary.py`

Move **only** the diary-related pure functions and `write_diary` graph tool:

```python
# examples/shared/diary.py
"""Shared diary writing utilities.

Used by diary_digest and .chaplain workflows.
"""
from pathlib import Path

DIARY_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "diary.md"

def format_diary_entry(date_str, theme, body, seed, prefix="World Digest"): ...
def append_to_diary(path, entry): ...
def should_write_entry(articles, threshold=0.3): ...
def write_diary(state): ...
```

### 2. Update `examples/diary_digest/nodes/writing.py`

Keep `filter_relevant`, `_extract_score`, and `_flatten_article` in place (diary_digest-specific). Re-export shared functions for backward compatibility:

```python
# examples/diary_digest/nodes/writing.py
from examples.shared.diary import (
    format_diary_entry,
    append_to_diary,
    should_write_entry,
    write_diary,
)
```

### 3. Update YAML graph references

```yaml
# .chaplain/graph.yaml — change tool module
tools:
  write_diary_tool:
    type: python
    module: examples.shared.diary
    function: write_diary

# examples/diary_digest/graph.yaml — change tool modules
tools:
  filter_tool:
    module: examples.diary_digest.nodes.writing  # stays (filter_relevant is local)
  write_tool:
    module: examples.shared.diary                 # moved
```

### 4. Update tests

Update `tests/unit/test_diary_digest.py` import paths for `format_diary_entry`, `append_to_diary`, `should_write_entry`, and `write_diary` to import from `examples.shared.diary`. Keep `filter_relevant` tests importing from `examples.diary_digest.nodes.writing`.

## Acceptance Criteria

- [x] `examples/shared/diary.py` contains `format_diary_entry()`, `append_to_diary()`, `should_write_entry()`, and `write_diary()`
- [x] `DIARY_PATH` in `examples/shared/diary.py` resolves correctly to `docs/diary.md`
- [x] `.chaplain/graph.yaml` tool references `module: examples.shared.diary`
- [x] `examples/diary_digest/graph.yaml` write_tool references `module: examples.shared.diary`
- [x] `examples/diary_digest/nodes/writing.py` re-exports shared functions (backward compatibility)
- [x] `filter_relevant` and its helpers remain in `examples/diary_digest/nodes/writing.py`
- [x] No duplicate function bodies (re-exports only)
- [x] All existing tests pass with updated imports
- [x] `ruff check` passes on modified files

## Alternatives Considered

1. **Move everything to `yamlgraph/tools/diary.py`**: Rejected — diary writing is example-specific, not a core framework tool. Putting it in the framework package would conflate application logic with library code.

2. **Symlink or `__init__.py` re-export in shared**: Rejected — symlinks are fragile across platforms; `__init__.py` re-exports obscure the actual module location.

3. **Keep as-is with a comment**: Rejected — the coupling will worsen as more workflows adopt diary writing. The inbox note correctly identifies this as a modularity defect.

## Constraints

- **Backward compatible**: Re-exports in `diary_digest/nodes/writing.py` preserve existing import paths
- **Minimal scope**: Only diary-related utilities move; `filter_relevant` and its helpers stay in `diary_digest`
- **No new dependencies**: Pure relocation of existing code

## Related

- FR-093: Chaplain diary append (introduced the cross-example dependency)
- `examples/shared/README.md`: Documents shared utilities pattern
- `.chaplain/graph.yaml`: Primary consumer driving the refactor
