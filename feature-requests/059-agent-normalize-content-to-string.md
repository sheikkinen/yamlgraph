# Feature Request: Normalize agent response.content to string

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-20

## Summary

Agent node stores `response.content` directly into `state_key` without normalizing. Anthropic Claude returns content as a list of blocks (`[{"type": "text", "text": "..."}]`), causing downstream consumers to receive a list instead of a string.

## Problem

In `tools/agent.py` L280 and L350:
```python
state_key: response.content,  # may be list, not str
```

When using Anthropic Claude models, `AIMessage.content` is often a **list of content blocks**:
```python
[{"type": "text", "text": "Terveystalo tarjoaa hammaslääkäripalveluita..."}]
```

This list propagates to `state.response`, causing:
1. SSE streaming emits a JSON chunk with `content: [...]` instead of `content: "..."`
2. FR-058 streaming filter (`isinstance(chunk.content, str)`) rejects these chunks entirely
3. `_format_sse_chunk` receives a list, breaking `json.dumps` or client-side `.join()`

**Observed:** Terveystalo agent Turn 4 crashes with `TypeError: sequence item 0: expected str instance, list found`.

## Proposed Solution

Normalize `response.content` to string in agent.py before storing:

```python
def _normalize_content(content) -> str:
    """Normalize LLM content to string. Handles Anthropic list format."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content) if content else ""
```

Apply at L280 and L350:
```python
state_key: _normalize_content(response.content),
```

This also fixes the streaming issue because `AIMessageChunk.content` will be a string, passing the FR-058 `isinstance(chunk.content, str)` filter.

## Acceptance Criteria

- [x] `response.content` normalized to `str` before storing in state
- [x] Anthropic list content blocks extracted correctly
- [x] OpenAI string content passed through unchanged
- [x] FR-058 streaming filter works with normalized content
- [x] Max-iterations path (L350) also normalizes
- [x] Tests with both string and list content formats

## Related

- `yamlgraph/tools/agent.py` L280, L350
- FR-058 — agent streaming filter (depends on string content)
- Anthropic Claude content block format
