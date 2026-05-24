# Feature Request: FR-449 — Agent Structured Output Fails with Anthropic Provider

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-05-24
**Discovered by:** FR-447 judge demo — three consecutive runs return prose instead of dict

## Summary

FR-448 implemented agent structured output but it silently fails with Anthropic. Two provider-boundary bugs cause `_try_structured_output()` to crash inside a bare `except Exception`, returning prose text instead of a structured dict.

## Value Statement

Graph authors using agent nodes with `schema:` blocks on Anthropic (the default provider) get the structured dict output that FR-448 promised but never delivered.

## Problem

FR-448 was marked "Implemented" but the judge demo (FR-447) returns prose on every run with `PROVIDER=anthropic`. The `_try_structured_output()` function has two provider-boundary bugs:

### Bug 1: Content type mismatch (extract_json path)

Anthropic returns `response.content` as `list[dict]` (content blocks), not `str`. The original FR-448 implementation passes this directly to `extract_json()`, which calls `.strip()` on its input. Result: `AttributeError: 'list' object has no attribute 'strip'` — caught by the bare `except Exception`, falling through to the fallback path.

```python
# FR-448 original — crashes on Anthropic
parsed = extract_json(content)  # content is list, not str
```

### Bug 2: Assistant prefill rejection (fallback path)

The fallback path invokes `structured_llm.invoke(msgs)` where `msgs` ends with an `AIMessage` (the agent's final response). Anthropic rejects conversations ending with an assistant message: "This model does not support assistant message prefill." The fallback also crashes.

```python
# FR-448 original — Anthropic rejects this
structured_llm = llm_base.with_structured_output(output_model)
result = structured_llm.invoke(msgs)  # msgs[-1] is AIMessage → error
```

**Both paths fail → the bare `except Exception` returns nothing useful → state gets prose text.**

### Root cause

The Scripture names this exactly: *"Normalize at the boundary where external data enters, not downstream where it manifests."* FR-448 assumed `response.content` is always `str` (OpenAI contract) and that any message list is valid for `with_structured_output` invoke. Both are provider-boundary violations.

## Proposed Solution

Two surgical fixes in `_try_structured_output()`:

### Fix 1: Normalize content before extract_json

Use `normalize_content()` (already exists in `yamlgraph/utils/content.py`, already imported as `_normalize_content` in `agent.py`) to convert `list[dict]` → `str` before calling `extract_json()`.

```python
text = _normalize_content(content)
parsed = extract_json(text)
```

### Fix 2: Append HumanMessage before structured output fallback

Ensure the message list ends with a `HumanMessage` before invoking `structured_llm`. This satisfies Anthropic's constraint that conversations must end with a user message.

```python
from langchain_core.messages import HumanMessage

fallback_msgs = list(msgs) + [
    HumanMessage(content="Now produce your response as structured JSON output.")
]
structured_llm = llm_base.with_structured_output(output_model)
result = structured_llm.invoke(fallback_msgs)
```

### Fix 3: Replace bare except with specific catch + logging

The silent `except Exception` masked both bugs for the entire time FR-448 was "Implemented". Add `logger.debug` on the exception so failures are visible.

```python
except Exception:
    logger.debug("JSON parse failed for structured output, falling back to LLM")
```

## Acceptance Criteria

- [ ] Agent node with `schema:` block returns `dict` (not `str`) with Anthropic provider
- [ ] Agent node with `schema:` block returns `dict` (not `str`) with OpenAI provider (no regression)
- [ ] `_try_structured_output` with `list` content (Anthropic format) produces valid dict
- [ ] `_try_structured_output` fallback works when messages end with `AIMessage`
- [ ] Agent nodes without `schema:` continue to return text (no regression)
- [ ] Condemning test: mock agent returning `list` content blocks, assert structured output is `dict` with correct fields
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-422")`

## Files Changed

1. **`yamlgraph/tools/agent.py`** — `_try_structured_output()`: normalize content, append HumanMessage, add debug logging
2. **Tests** — Unit tests with mock LLM producing `list` content (Anthropic format) and `str` content (OpenAI format)

## Alternatives Considered

- **Fix inside `extract_json`**: Wrong — `extract_json` correctly expects `str`. The boundary violation is at the caller.
- **Catch the specific errors and retry**: Symptom patching. The content should be normalized before it reaches `extract_json`.
- **Remove the `except Exception`**: Would expose the crash but not fix it. Both paths need fixing.

## Related

- FR-448 — Original implementation (marked "Implemented" but broken for Anthropic)
- FR-447 — Judge demo that exercises this path
- FR-059 — Provider content normalization (established `normalize_content`)
- Scripture: `the_one_law` — "Normalize at the boundary where external data enters"
- Scripture: `traps.downstream_fix` — "Guard added where symptom manifests → normalize at entry boundary instead"
