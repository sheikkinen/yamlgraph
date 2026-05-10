# FR-361: Fix Double-Brace JSON Output from executor.py

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-05-10

## Summary

`execute_prompt()` occasionally returns JSON output wrapped in `{{ ... }}` double braces (e.g., `{{"intent": "crisis"}}`). This is a downstream symptom of Jinja2 template escaping propagating through to LLM output. A workaround `_normalize_json()` function was patched into `projects/ninchat_voice/evaluations/navigator/provider.py` — a downstream fix at symptom site rather than root cause.

## Value Statement

Consumers of `execute_prompt()` get clean JSON output without workarounds, and the `_normalize_json` patch in the navigator eval provider can be deleted.

## Problem

When a prompt template uses Jinja2 syntax and the LLM responds with a JSON object, the response content can arrive with doubled curly braces:

```python
# Expected
'{"intent": "crisis"}'

# Actual (observed in navigator eval)
'{{"intent": "crisis"}}'
```

The navigator evaluation provider in `projects/ninchat_voice/evaluations/navigator/provider.py` contains this workaround:

```python
def _normalize_json(text: str) -> str:
    """Strip double braces produced by Jinja2-escaped prompt template."""
    return re.sub(r"^\{\{", "{", re.sub(r"\}\}$", "}", text.strip()))
```

This is a `downstream_fix` trap: the guard was added where the symptom manifests (consumer of `execute_prompt()`), not at the boundary where external data enters (executor output). Any other consumer of `execute_prompt()` that returns JSON faces the same silent corruption without realising it. JSON with doubled outer braces fails `JSON.parse()` in Promptfoo JavaScript assertions, causing false test failures.

### Root Cause Hypothesis

`executor.py` returns `response.content` raw from the LLM. If the prompt template was rendered with Jinja2 and the LLM mirrors the structure of the template in its response (common with instruction-following models), `{{` in the prompt template can cause `response.content` to contain `{{` in the output. Alternatively, the Jinja2 render step may double-escape braces in the rendered system/user message, causing the model to reproduce the escaped form.

The exact trigger needs to be confirmed with a failing test before fixing.

## Proposed Solution

### Step 1: Condemn with a failing test

Write a unit test that exercises `execute_prompt()` with a prompt that uses Jinja2 syntax and a schema that returns a JSON object. Assert that the returned string is valid JSON (no double braces).

```python
# tests/unit/test_executor_json_output.py
def test_execute_prompt_returns_valid_json_not_double_brace(mock_llm):
    """Executor must not return double-brace-wrapped JSON."""
    # Arrange: mock LLM returns {"intent": "crisis"} as content
    mock_llm.invoke.return_value.content = '{"intent": "crisis"}'
    result = execute_prompt("classify", variables={"user_message": "test"}, ...)
    # Act + Assert: result is parseable JSON, no double braces
    import json
    parsed = json.loads(result)  # must not raise
    assert parsed["intent"] == "crisis"
    assert not result.startswith("{{")
```

### Step 2: Fix at the boundary

In `executor.py`, `PromptExecutor._invoke_with_retry()` is where `response.content` is returned. Add output normalization here — the correct boundary where external data (LLM response) enters our system:

```python
# In _invoke_with_retry, before returning raw content:
response = llm.invoke(messages)
content = response.content
# Normalize double-brace wrapping that can appear when Jinja2 prompt
# templates cause instruction-following models to mirror brace syntax.
if isinstance(content, str):
    content = _strip_outer_double_braces(content)
return content
```

```python
def _strip_outer_double_braces(text: str) -> str:
    """Remove outer {{ }} wrapping from LLM JSON responses.

    Jinja2-rendered prompts can cause instruction-following models to
    mirror {{ }} syntax in their JSON output. This normalizes at the
    output boundary so consumers receive clean JSON.
    """
    stripped = text.strip()
    if stripped.startswith("{{") and stripped.endswith("}}"):
        return stripped[1:-1]
    return text
```

### Step 3: Delete the downstream workaround

After the test passes, delete `_normalize_json` from `projects/ninchat_voice/evaluations/navigator/provider.py` and its call site. The function becomes dead code.

## Acceptance Criteria

- [ ] Failing test written first (RED): `test_execute_prompt_returns_valid_json_not_double_brace`
- [ ] `_strip_outer_double_braces` added to `executor.py`, applied in `_invoke_with_retry` for non-structured output
- [ ] Test passes (GREEN)
- [ ] `_normalize_json` function and its call site deleted from `navigator/provider.py`
- [ ] Existing executor tests still pass
- [ ] The fix only strips double braces when the full string is wrapped — not mid-string occurrences (e.g., a JSON object whose string values happen to contain `{{`)

## Alternatives Considered

**Keep the workaround per-consumer**: Each promptfoo provider that returns JSON adds its own `_normalize_json`. This violates the `partial_remediation` trap — fixing only the cited occurrence rather than the root cause. Every future consumer silently inherits the bug.

**Fix in the Jinja2 render step**: Ensure the rendered prompt template never contains `{{` that the model could mirror. Fragile — depends on prompt content and model behavior. Normalizing at the output boundary is more robust.

**Only fix if structured output (`output_model`) is not used**: When `output_model` is provided, `with_structured_output()` handles JSON parsing via Pydantic. The raw string path (`response.content`) is the only affected path — correct to scope fix there.

## Related

- `yamlgraph/executor.py` — `_invoke_with_retry()`, line ~165
- `projects/ninchat_voice/evaluations/navigator/provider.py` — `_normalize_json` workaround to delete
- `reference/promptfoo-eval.md` — documents the eval pattern where this bug was first observed
- FR-299 (promptfoo-router demo — pattern that established `execute_prompt()` as eval surface)
- Diary trap: `downstream_fix` — "Guard added where symptom manifests → normalize at entry boundary instead"
