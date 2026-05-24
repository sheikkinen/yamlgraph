# Feature Request: FR-456 Structured Output JSON Fallback

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
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

**Key insight from judgement:** The codebase already has `yamlgraph/utils/json_extract.py` with `extract_json()` that implements steps 1-3 (raw JSON, markdown blocks, balanced brackets). It's already imported in `agent.py`. No new extraction function needed.

The existing `_try_structured_output()` in `agent.py` already calls `extract_json()` as its first attempt (cheap path). The bug is that when `extract_json()` succeeds but the result is a raw dict, it proceeds to re-invoke `with_structured_output()` which crashes on providers that reject `response_format`.

**Fix:** Wrap the `with_structured_output()` re-invoke in `_try_structured_output()` with try/catch. When the provider rejects `response_format`, validate the already-parsed `extract_json()` result against the Pydantic schema and return it.

```python
# In _try_structured_output():
parsed = extract_json(content)  # Already exists — cheap path
if parsed:
    try:
        return schema.model_validate(parsed)  # NEW: validate against schema
    except ValidationError:
        pass  # Fall through to with_structured_output re-invoke

try:
    result = llm.with_structured_output(schema).invoke(messages)  # Existing
except Exception as e:
    if parsed:  # extract_json succeeded but schema validation failed
        logger.warning(f"Structured output API rejected, returning best-effort parse: {e}")
        return schema.model_construct(**parsed)  # Lenient construction
    raise  # No parsed data available — propagate original error
```

### Scope Boundary

This FR covers the fallback in `agent.py`'s `_try_structured_output()` only. `executor.py`'s `execute_prompt()` has the same vulnerability for LLM nodes with structured output — deferred to a follow-up FR if this pattern proves useful.

## Acceptance Criteria

- [x] Agent node recovers structured output when `with_structured_output()` raises on `response_format`
- [x] Fallback attempts JSON extraction from last assistant message
- [x] Extracted JSON is validated against the Pydantic schema
- [x] Warning logged when fallback is used (not silent)
- [x] Unit test: mock LLM that rejects `response_format` but produces JSON in message content
- [ ] DeepSeek produces a verdict in FR-453 eval re-run

## Alternatives Considered

- **Pre-check provider capabilities** — Would require maintaining a capability matrix per provider. Fragile and always out of date. Try/catch is simpler and self-healing.
- **Always use JSON parsing, never `with_structured_output()`** — Loses the type safety and retry logic that `with_structured_output()` provides for capable providers. Fallback-only is the right trade-off.
- **Prompt the model to output JSON** — Already happens via the schema in the prompt. The issue is the extraction mechanism, not the model's ability to produce JSON.

## Judgement Notes

- **No new function needed** — `extract_json()` already exists in `yamlgraph/utils/json_extract.py` and is imported in `agent.py`
- **Missing gap identified:** `extract_json()` returns raw dict, not validated against Pydantic schema. Must add `schema.model_validate(parsed)` after extraction.
- **`executor.py` deferral documented** — same vulnerability exists for LLM nodes but is out of scope

## Related

- FR-453 — Judge model evaluation (discovered this limitation)
- FR-448 — Introduced `_try_structured_output()` with try-parse-first strategy
- FR-449 — Content normalization (`_normalize_content`) at boundary
- FR-455 — Reasoning model temperature guard (sibling provider compatibility FR)
- `yamlgraph/tools/agent.py` — Agent node structured output extraction
- `yamlgraph/executor.py` — Separate structured output path (out of scope)
