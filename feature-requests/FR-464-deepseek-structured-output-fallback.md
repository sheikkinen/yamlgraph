# Feature Request: FR-464 Structured Output Fallback for executor.py and race_node.py

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-05-30

## Summary

Extend the FR-456 `extract_json()` + `model_validate()` fallback pattern — proven in `agent.py` — to the two remaining `with_structured_output()` call sites: `executor.py::_invoke_with_retry()` and `race_node.py::_invoke_candidate_async()`. DeepSeek V4 models reject `response_format: json_schema` in thinking mode, causing 400 errors on any prompt with a `schema:` block.

## Value Statement

Graph authors can use schema-based prompts with DeepSeek (and future providers with similar limitations) across all node types — LLM, agent, and race — without per-node workarounds.

## Problem

Two call sites use `llm.with_structured_output(output_model)` without fallback:

1. **`executor.py:162`** — `_invoke_with_retry()`, used by all LLM nodes with `schema:`
2. **`race_node.py:~60`** — `_invoke_candidate_async()`, used by race nodes with `schema:`

FR-456 already fixed the same vulnerability in `agent.py::_try_structured_output()` using `extract_json()` + `model_validate()` + lenient `model_construct()`. That FR's scope boundary explicitly deferred `executor.py` to a follow-up: *"executor.py's execute_prompt() has the same vulnerability — deferred to a follow-up FR if this pattern proves useful."*

Observed behavior:
- `parse_json: true` (free-text JSON extraction) works fine with DeepSeek V4
- `schema:` (structured output via API) fails with `400 Bad Request: This response_format type is unavailable now`
- Both `deepseek-v4-flash` and `deepseek-v4-pro` are affected
- The old aliases `deepseek-chat` and `deepseek-reasoner` will be deprecated

## Proposed Solution

Replicate the proven FR-456 pattern at both call sites. No new functions needed — `extract_json()` from `yamlgraph/utils/json_extract.py` is already available.

### Call site 1: `executor.py::_invoke_with_retry()`

```python
if output_model:
    try:
        structured_llm = llm.with_structured_output(output_model)
        return structured_llm.invoke(messages)
    except Exception as e:
        if "response_format" in str(e):
            logger.info("Structured output rejected, falling back to JSON extraction")
            response = llm.invoke(messages)
            text = response.content if isinstance(response.content, str) else str(response.content)
            parsed = extract_json(text)
            if isinstance(parsed, dict):
                return output_model.model_validate(parsed)
        raise
```

### Call site 2: `race_node.py::_invoke_candidate_async()`

```python
if output_model:
    try:
        structured_llm = llm.with_structured_output(output_model)
        result = await structured_llm.ainvoke(messages)
        return candidate, result
    except Exception as e:
        if "response_format" in str(e):
            logger.info("Structured output rejected in race candidate, falling back to JSON extraction")
            response = await llm.ainvoke(messages)
            content = normalize_content(response.content)
            parsed = extract_json(content)
            if isinstance(parsed, dict):
                return candidate, output_model.model_validate(parsed)
        raise
```

## Acceptance Criteria

- [x] `executor.py`: prompts with `schema:` work with DeepSeek V4 models (thinking mode)
- [x] `race_node.py`: race nodes with `schema:` work with DeepSeek V4 models
- [x] Fallback produces valid Pydantic model instances via `model_validate()`
- [x] No regression for providers that support `with_structured_output()`
- [x] Five-whys demo runs successfully with `PROVIDER=deepseek`
- [x] Tests added for fallback path in both `executor.py` and `race_node.py`
- [x] INFO-level log message when falling back

## Alternatives Considered

1. **Require `parse_json: true` for DeepSeek** — pushes the burden to graph authors, violates provider-agnostic design
2. **Disable thinking mode** — loses DeepSeek's main differentiator

## Related

- **FR-456** (predecessor): Structured output JSON fallback in `agent.py` — **Enforced**
- `yamlgraph/executor.py:162` — `with_structured_output()` call site
- `yamlgraph/node_factory/race_node.py:~60` — `with_structured_output()` call site
- `yamlgraph/utils/json_extract.py` — existing `extract_json()` utility
- `yamlgraph/tools/agent.py::_try_structured_output()` — proven pattern (FR-456)
- Knowledge graph trap: `downstream_fix` — guard at boundary, not symptom
- Knowledge graph cure: `tolerant_matching` — provider differences need normalization
