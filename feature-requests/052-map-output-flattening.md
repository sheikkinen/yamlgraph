# Feature Request: Map Output Flattening

**FR-052**
**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 2-3 days
**Requested:** 2026-02-19
**Implemented:** 2026-02-22

## Summary

Improve map node output format to reduce boilerplate in downstream nodes. Currently, map outputs require manual extraction of `_map_xxx_sub` keys.

## Problem

Map nodes produce outputs with internal structure that leaks to consumers:

```python
# Current map output format
[
    {"_map_index": 0, "_map_analyze_sub": RelevanceScore(score=0.8, ...)},
    {"_map_index": 1, "_map_analyze_sub": RelevanceScore(score=0.3, ...)},
]

# What downstream nodes expect
[
    {"score": 0.8, "title": "...", "url": "..."},
    {"score": 0.3, "title": "...", "url": "..."},
]
```

This mismatch caused 2 of 4 layers in the "Onion of Silent Failures" (diary-digest post-mortem):

1. **Layer 3:** `filter_relevant` couldn't find `relevance_score` at top level
2. **Layer 4:** Synthesize prompt expected `article.title` but got `_map_analyze_sub.title`

Current workaround: `get_map_result()` helper in `yamlgraph.contrib.utils`. But this requires Python code in every downstream node.

## Proposed Solutions

### Option A: `flatten_output: true` (Recommended)

Add node-level option to merge map output with original input:

```yaml
nodes:
  analyze_all:
    type: map
    source: articles
    prompt: analyze_relevance
    state_key: analyzed_articles
    flatten_output: true  # NEW: merge _map_xxx_sub into item
```

Result:
```python
[
    {"_map_index": 0, "score": 0.8, "title": "...", "url": "..."},  # Flattened
    {"_map_index": 1, "score": 0.3, "title": "...", "url": "..."},
]
```

Implementation: In `map_compiler.py`, after collecting results, iterate and merge:

```python
if node.flatten_output:
    for item in results:
        sub_key = next((k for k in item if k.startswith("_map_") and k.endswith("_sub")), None)
        if sub_key:
            sub_value = item.pop(sub_key)
            if hasattr(sub_value, "model_dump"):
                sub_value = sub_value.model_dump()
            item.update(sub_value)
```

### Option B: `output_key` Override

Let user specify the output key name:

```yaml
nodes:
  analyze_all:
    type: map
    source: articles
    prompt: analyze_relevance
    state_key: analyzed_articles
    output_key: analysis  # Instead of _map_analyze_all_sub
```

Result:
```python
[
    {"_map_index": 0, "analysis": RelevanceScore(...)},
]
```

Still requires access by key, but key is user-controlled and predictable.

### Option C: Auto-Flatten (Breaking Change)

Change default behavior to always flatten. Keep `_map_index` but remove `_map_xxx_sub` wrapper.

**Risk:** Breaks existing graphs that rely on current structure. Would need major version bump.

## Recommendation

**Option A (`flatten_output: true`)** — Opt-in, non-breaking, addresses the exact pain point.

## Acceptance Criteria

- [x] `flatten_map_results()` function added to `map_compiler.py`
- [x] When called, `_map_xxx_sub` contents merged into item
- [x] Pydantic models converted via `model_dump()`
- [x] `_map_index` preserved for ordering
- [x] Output fields overwrite input fields (output wins)
- [x] `flatten_output: bool = False` added to NodeConfig (Phase 2)
- [x] Wired into `wrap_for_reducer` in `compile_map_node` (Phase 2)
- [x] Unit tests for flatten behavior (12 tests, REQ-YG-075)
- [x] Documentation in reference/map-nodes.md

## Edge Cases

### 1. Field Name Conflicts

What if input has `score` and output also has `score`?

**Proposed:** Output wins (overwrites input). Log warning. Users should use distinct names.

### 2. Nested Pydantic Models

What if `_map_xxx_sub` contains nested Pydantic models?

**Proposed:** Recursive `model_dump(mode="python")` — preserves Python types, not JSON.

### 3. Non-Dict Outputs

What if map sub-node returns a scalar (string, int)?

**Proposed:** `flatten_output` is no-op for scalars. Keep `_map_xxx_sub` wrapper. Log info.

## Migration Path

1. Add `flatten_output` option (default `false`)
2. Document in reference/map-nodes.md
3. Update examples to use `flatten_output: true` where appropriate
4. Consider making `true` the default in v2.0

## Related

- FR-044b — Contrib migration (added `get_map_result()` helper)
- FR-050 — Skip-If-Exists Truthiness (related silent failure)
- FR-051 — Output Shape Contracts (complementary validation)
- Diary entry: "The Onion of Silent Failures" (2026-02-19)
- [reference/contrib.md](../reference/contrib.md) — Current `get_map_result()` workaround

## Implementation Notes

1. Add `flatten_output: bool = False` to `MapNodeConfig` in models
2. Modify `_collect_map_results()` in `map_compiler.py`
3. Add `_flatten_map_item()` helper function
4. Handle Pydantic model serialization
5. Preserve `_map_index` but remove `_map_xxx_sub` after flatten
