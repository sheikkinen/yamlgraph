# Feature Request: FR-456 Structured Output JSON Fallback

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-05-24

## Summary

When `with_structured_output()` fails (provider rejects `response_format`), fall back to parsing JSON from the raw completion text. This recovers structured verdicts from models that can produce JSON but don't support the formal structured output API.

## Value Statement

DeepSeek completed all 12 judge iterations successfully during FR-453 eval, then crashed at the structured output extraction step — the verdict was *inside the agent's last message* but couldn't be extracted because `with_structured_output()` uses `response_format` which DeepSeek rejects. A JSON fallback would have recovered the verdict.

## Problem

The agent node's final structured output extraction uses `with_structured_output()`, which calls the provider's `response_format` API. Not all providers support this:

```
Error code: 400 - {'error': {
  'message': 'This response_format type is unavailable now',
  'type': 'invalid_request_error'
}}
```

The agent completed 12 iterations (25 tool calls) and produced a verdict in natural language. The structured extraction is a *post-processing step* that failed — all the expensive LLM work was wasted.

Flow:
```
Agent loop (12 iterations, 25 tool calls) → ✓ completed
  → with_structured_output() → ✗ 400 Bad Request
  → No verdict returned
```

## Proposed Solution

In the agent's structured output extraction step, catch the `response_format` failure and fall back to JSON parsing from the last message:

```python
try:
    result = llm.with_structured_output(schema).invoke(messages)
except Exception as e:
    logger.warning(f"Structured output failed, attempting JSON fallback: {e}")
    # Extract JSON from last assistant message
    last_msg = messages[-1].content
    result = _extract_json_fallback(last_msg, schema)
```

### `_extract_json_fallback(text, schema)`

1. Try `json.loads(text)` directly (if model returned pure JSON)
2. Try extracting JSON from markdown code block: ````json\n{...}\n````
3. Try finding first `{` to last `}` and parsing that substring
4. Validate against Pydantic schema
5. If all fail, raise the original error

### Scope Boundary

This FR covers the fallback in `agent.py`'s structured output step only. It does NOT change `executor.py`'s `execute_prompt()` — that's a separate path with different trade-offs. If the pattern proves useful, a follow-up FR can generalize it.

## Acceptance Criteria

- [ ] Agent node recovers structured output when `with_structured_output()` raises on `response_format`
- [ ] Fallback attempts JSON extraction from last assistant message
- [ ] Extracted JSON is validated against the Pydantic schema
- [ ] Warning logged when fallback is used (not silent)
- [ ] Unit test: mock LLM that rejects `response_format` but produces JSON in message content
- [ ] DeepSeek produces a verdict in FR-453 eval re-run

## Alternatives Considered

- **Pre-check provider capabilities** — Would require maintaining a capability matrix per provider. Fragile and always out of date. Try/catch is simpler and self-healing.
- **Always use JSON parsing, never `with_structured_output()`** — Loses the type safety and retry logic that `with_structured_output()` provides for capable providers. Fallback-only is the right trade-off.
- **Prompt the model to output JSON** — Already happens via the schema in the prompt. The issue is the extraction mechanism, not the model's ability to produce JSON.

## Related

- FR-453 — Judge model evaluation (discovered this limitation)
- FR-455 — Reasoning model temperature guard (sibling provider compatibility FR)
- `yamlgraph/tools/agent.py` — Agent node structured output extraction
- `yamlgraph/executor.py` — Separate structured output path (out of scope)
