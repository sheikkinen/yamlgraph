# Feature Request: `on_error: skip` Visibility

**Priority:** MEDIUM
**Type:** Framework Enhancement
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-02-18
**Split from:** FR-044

## Summary

Make `on_error: skip` behavior visible. Currently, 19 occurrences across 10 pipelines silently swallow failures. Items vanish without any indication of what was skipped or why.

## Problem

When a map node has `on_error: skip`, failed items are silently dropped:
- No error in logs
- No count of skipped items
- No indication which items failed
- No reason recorded

A pipeline that processes 20 items and skips 3 appears to succeed with 17 results. The user has no way to know items were lost.

**Evidence from FR-044 research:**
- 19 `on_error: skip` occurrences across 10 YAML files
- 0 skip reports implemented
- "Category 7: Progress / Reporting — No dedicated modules found"

## Proposed Solution

### Framework Changes (`map_compiler.py`)

Track skip information during map execution:

```python
# In map node wrapper
skip_info = []
for item in items:
    try:
        result = sub_node(item)
        results.append(result)
    except Exception as e:
        if on_error == "skip":
            skip_info.append({
                "item_index": idx,
                "item_key": get_item_key(item),  # Try to identify the item
                "error_type": type(e).__name__,
                "error_message": str(e)[:200],
            })
            continue
        raise

# Write to state
return {
    state_key: results,
    f"{state_key}_skipped": skip_info,  # New: skip information
}
```

### Console Output

When skips occur, log them:
```
⚠ Map node 'generate_lessons': 3 of 20 items skipped
  - topic_05: TimeoutError: API call timed out after 30s
  - topic_12: ValidationError: Missing required field 'title'
  - topic_18: RateLimitError: Rate limit exceeded
```

### State Access

Users can access skip information in subsequent nodes:
```yaml
nodes:
  report_failures:
    type: python
    module: my_nodes
    function: report_skips
    # Access: state["lessons_skipped"]
```

## Acceptance Criteria

- [ ] `on_error: skip` accumulates skip information (item index, error type, message)
- [ ] Skip info written to state as `{state_key}_skipped`
- [ ] Console logs skip summary when items are skipped
- [ ] Skip info includes identifiable item key when possible
- [ ] Works with both sync and async map execution
- [ ] Tests with `@pytest.mark.req` tags
- [ ] Documentation updated

## Alternatives Considered

- **Contrib library (SkipReport):** Originally proposed in FR-044. But this requires framework changes first — a library can't access skip info that isn't recorded.
- **Error state accumulation:** Already exists but is separate from skip tracking. Skip is intentional (user chose it), errors are failures.
- **Logging only:** Log skips but don't write to state. Insufficient — users can't programmatically react to skips.

## Related

- FR-044: Shared Contrib Libraries (split from)
- FR-040: Default Quality Gates (would use skip visibility)
- Diary: "Silent fallbacks that produce plausible output are worse than loud failures"
