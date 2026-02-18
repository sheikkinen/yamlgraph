# Feature Request: Full Migration to yamlgraph.contrib.utils

**Priority:** LOW
**Type:** Refactoring
**Status:** IMPLEMENTED
**Effort:** 2-3 hours
**Requested:** 2026-02-18
**Depends on:** FR-044 (complete)

## Implementation (2026-02-18)

**Migrated 10 files:**
1. `examples/ocr_cleanup/tools/merger.py` — `get_map_result` + `to_serializable`
2. `examples/beautify/nodes.py` — 3 `to_serializable` calls
3. `examples/npc/demo.py` — 3 `to_serializable` calls
4. `examples/npc/api/session.py` — 3 `to_serializable` calls
5. `examples/npc/nodes/image_node.py` — 1 `to_serializable` call
6. `examples/daily_digest/nodes/formatting.py` — 1 `to_serializable` call
7. `examples/storyboard/nodes/character_node.py` — 1 `to_serializable` call
8. `examples/storyboard/nodes/animated_character_node.py` — 2 `to_serializable` calls
9. `examples/storyboard/nodes/animated_image_node.py` — 2 `to_serializable` calls
10. `examples/yamlgraph_gen/tools/file_ops.py` — 2 `to_serializable` calls

**Skipped:**
- `examples/questionnaire/tools/handlers.py` — Has local `_to_dict` that returns `{}` for non-dicts (different semantics than `to_serializable`). Left as-is.

**Test results:** 1537 passed, 1 skipped, 2 xfailed

## Summary

Migrate all remaining duplicated code to use `yamlgraph.contrib.utils` functions (`get_map_result`, `to_serializable`). This is cleanup work following FR-044 Phase 1.

## Migration Inventory

### get_map_result Duplicates (1 file)

| File | Status | Action |
|------|--------|--------|
| `examples/ocr_cleanup/tools/merger.py` | Local definition | Replace with import |

### to_serializable Candidates (11 files, ~21 occurrences)

Files using `hasattr(obj, "model_dump")` pattern that can use `to_serializable()`:

| File | Occurrences | Pattern |
|------|-------------|---------|
| `examples/beautify/nodes.py` | 3 | Conditional model_dump for analysis, mermaid |
| `examples/npc/api/session.py` | 3 | Conditional model_dump for identity, personality, behavior |
| `examples/npc/demo.py` | 4 | Conditional model_dump in multiple places |
| `examples/npc/nodes/image_node.py` | 1 | scene_prompt conversion |
| `examples/yamlgraph_gen/tools/file_ops.py` | 2 | prompts and tools conversion |
| `examples/ocr_cleanup/tools/merger.py` | 1 | page_data conversion |
| `examples/daily_digest/nodes/formatting.py` | 1 | ranked_stories list conversion |
| `examples/questionnaire/tools/handlers.py` | 1 | Generic obj conversion |
| `examples/storyboard/nodes/character_node.py` | 1 | story conversion |
| `examples/storyboard/nodes/animated_character_node.py` | 2 | story and panel conversion |
| `examples/storyboard/nodes/animated_image_node.py` | 2 | panel and story conversion |

## Migration Approach

### Phase 1: get_map_result (5 min)
Replace local definition in `merger.py` with import from contrib.

```python
# Before
def get_map_result(item: dict | None) -> dict | None:
    """..."""
    if not isinstance(item, dict):
        return None
    for key, value in item.items():
        if key.startswith("_map_") and key.endswith("_sub"):
            return value
    return None

# After
from yamlgraph.contrib import get_map_result
```

### Phase 2: to_serializable (2 hours)
For each file, replace conditional model_dump patterns:

```python
# Before
if hasattr(obj, "model_dump"):
    obj = obj.model_dump()
elif hasattr(obj, "dict"):
    obj = obj.dict()

# After
from yamlgraph.contrib import to_serializable
obj = to_serializable(obj)
```

**Note:** Some usages may be context-specific (e.g., list comprehensions, conditional checks). Each needs inspection.

## Acceptance Criteria

- [ ] `examples/ocr_cleanup/tools/merger.py` uses imported `get_map_result`
- [ ] All 11 files migrated to use `to_serializable` where applicable
- [ ] Existing tests pass (no regression)
- [ ] Any skipped migrations documented with reason

## Risks & Considerations

1. **Behavioral differences:** `to_serializable()` is recursive; some existing code may only do shallow conversion. Test each migration.

2. **Context-specific patterns:** Some usages might be intentionally different (e.g., only converting if needed for a specific condition). Review each case.

3. **Import overhead:** Adding imports to examples doesn't affect performance meaningfully, but keeps examples simple.

## Decision

**Recommendation:** APPROVE as low-priority background work.

This is purely cleanup — no new functionality. Can be done incrementally file-by-file. Value is reducing drift and demonstrating contrib usage patterns.

## Related

- FR-044: Initial contrib.utils implementation
- FR-044a: Skip visibility (framework feature, separate)
