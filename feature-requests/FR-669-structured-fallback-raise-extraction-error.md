# Feature Request: Raise extraction failure instead of provider error in FR-464 fallback

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-07-03

## Summary

When the FR-464 structured-output fallback fails to extract JSON from the
LLM response, `_invoke_with_retry` re-raises the original opaque provider
`response_format` error instead of reporting that JSON extraction failed.
The diagnostic points at the wrong cause.

## Value Statement

Users hitting the structured-output fallback on providers without
`response_format` support get an actionable "could not extract JSON" error
with a response snippet, instead of a misleading provider exception.

## Problem

`yamlgraph/executor.py` (`PromptExecutor._invoke_with_retry`):

```python
response = llm.invoke(retry_msgs)
text = normalize_content(response.content)
parsed = extract_json(text)
if isinstance(parsed, dict):
    return output_model.model_validate(parsed)
raise  # ← re-raises struct_err, not an extraction error
```

`extract_json()` (`yamlgraph/utils/json_extract.py`) returns the *original
string* when no JSON is detected. The `isinstance` check fails and control
falls through to `raise`, surfacing the provider's `response_format`
rejection — the error the fallback already worked around — instead of the
actual failure: the model returned prose, not JSON. Boundary normalization
gap at the schema boundary (`the_one_law`).

**Note (Judgement):** `executor_async.py` does NOT have `_invoke_with_retry`
— it delegates to `llm_factory_async.py`. Verify whether the async path
hits this code at all before fixing it.

## Proposed Solution

```python
parsed = extract_json(text)
if isinstance(parsed, (dict, list)):
    return output_model.model_validate(parsed)
raise ValueError(
    f"Structured output fallback failed: could not extract JSON "
    f"from LLM response: {text[:200]}"
) from struct_err
```

## Acceptance Criteria

- [ ] Failing test first (RED): mock LLM whose structured output raises
      `response_format` and whose plain invoke returns prose; assert raised
      error mentions JSON extraction and includes a response snippet
- [ ] Original provider error preserved as `__cause__` (`from struct_err`)
- [ ] Verify whether async path hits this code; if not, drop async criterion
- [ ] All unit tests green
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

- **Make `extract_json` raise on no-JSON** — rejected: it is a shared
  utility with callers that rely on pass-through behavior; fix at the
  callsite (`callsite_fix`), not the utility.

## Related

- docs/2026-07-03-review-fable.md (Issue 2)
- FR-464 (original fallback)
- yamlgraph/executor.py
- yamlgraph/utils/json_extract.py

## Judgement

**APPROVED.** Bare `raise` at executor.py:200 confirmed — re-raises the
original provider error after JSON extraction fails, hiding the real cause.
`extract_json` returns the original string on no-match (json_extract.py:127).
The `isinstance(parsed, dict)` check silently passes through.

**Amendments:**
1. FR says "same fix applied to the async path" but verification shows
   `executor_async.py` does NOT have `_invoke_with_retry` — it delegates
   to `llm_factory_async.py`. Check whether the async path even hits this
   code. If not, drop the async criterion.
2. FR-672 is rejected (see below), so the sequencing note about folding
   into FR-672 is moot. This FR stands alone.
3. Add `list` to the isinstance check: `isinstance(parsed, (dict, list))`
   as proposed.
