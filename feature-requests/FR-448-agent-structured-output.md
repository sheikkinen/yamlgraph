# Feature Request: FR-448 — Agent Node Structured Output via Prompt Schema

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-05-22
**Discovered by:** FR-447 demo run — agent returned text instead of structured dict

## Summary

When an agent node's prompt defines a `schema:` block, the agent should produce structured Pydantic output (dict) instead of raw text on its final iteration.

## Value Statement

Agent nodes gain the same structured output capability that LLM nodes already have, enabling typed state values, downstream schema validation, and dict-based event routing in FSM pipelines.

## Problem

Agent nodes ignore the prompt's `schema:` block. Both exit paths return raw text:

```python
# Exit 1: yamlgraph/tools/agent.py line 292 — agent finishes (no tool calls)
state_key: _normalize_content(response.content),  # Always text

# Exit 2: yamlgraph/tools/agent.py line 365 — max iterations reached
state_key: last_content,  # Also always text
```

LLM nodes resolve the schema via `get_output_model_for_node()` in `node_factory/base.py` and apply `llm.with_structured_output(output_model)` via `executor.py` line 161-162. Agent nodes bypass `execute_prompt()` entirely — they run their own loop with `llm.invoke(messages)`.

**Consequence:** The judge demo (FR-447) defines a `JudgeVerdict` schema with 5 typed fields, but the agent returns the verdict as markdown text. This blocks:
- Dict-based FSM event routing (`extract_event` needs a dict to iterate field values)
- Downstream node `requires` checks on typed fields
- Programmatic assertion on verdict structure in tests

## Proposed Solution

**Strategy: try-parse-first, fallback to structured output re-invoke.**

1. Resolve the output model at agent creation time using `get_output_model_for_node(node_config, prompts_dir=prompts_dir, graph_path=graph_path, prompts_relative=prompts_relative)`.
2. Save the base LLM reference before binding tools: `llm_base = create_llm(...)` then `llm = llm_base.bind_tools(lc_tools)`.
3. On both exit paths (normal completion + max-iterations), if `output_model` is set:
   a. Try `extract_json()` on the text response, then `output_model.model_validate()` on the result.
   b. If parsing fails, re-invoke with `llm_base.with_structured_output(output_model).invoke(messages)`.
   c. Return `structured_result.model_dump()` as the state value.

```python
# Helper inside node_fn
def _try_structured(content: str, msgs: list) -> Any:
    """Try to extract structured output, fallback to LLM re-invoke."""
    if not output_model:
        return _normalize_content(content)
    # Try parse first (cheap)
    try:
        parsed = extract_json(content)
        if isinstance(parsed, dict):
            return output_model.model_validate(parsed).model_dump()
    except Exception:
        pass
    # Fallback: structured output re-invoke (expensive)
    structured_llm = llm_base.with_structured_output(output_model)
    result = structured_llm.invoke(msgs)
    return result.model_dump()

# Exit 1 (line 292): no tool calls
if not response.tool_calls:
    final_value = _try_structured(response.content, messages)
    return {state_key: final_value, ...}

# Exit 2 (line 365): max iterations
last_content = messages[-1].content if hasattr(messages[-1], "content") else ""
final_value = _try_structured(last_content, messages)
return {state_key: final_value, ...}
```

**Key design choices:**
- `llm_base` saved before `bind_tools` — `with_structured_output` and `bind_tools` are mutually exclusive on most providers.
- `extract_json` + `model_validate` is tried first — avoids the cost of a full LLM re-invocation when the model already produced parseable JSON.
- Max-iterations path uses same helper — even if last message is a `ToolMessage`, the full conversation context in `messages` gives the LLM enough to produce structured output.

## Acceptance Criteria

- [ ] Agent node returns `dict` (not `str`) when prompt has `schema:` block (normal exit)
- [ ] Agent node returns `dict` (not `str`) when prompt has `schema:` block (max-iterations exit)
- [ ] Returned dict validates against the Pydantic model defined in the schema
- [ ] Agent nodes without `schema:` continue to return text (no regression)
- [ ] FR-447 judge demo produces structured `JudgeVerdict` dict when re-run
- [ ] Tests added with `@pytest.mark.req("REQ-YG-422")`

## Implementation Notes

### Files changed

1. **`yamlgraph/tools/agent.py`** — Save `llm_base` before `bind_tools`, resolve `output_model` via `get_output_model_for_node`, add `_try_structured` helper, apply on both exit paths
2. **Tests** — Unit test with mock LLM verifying dict vs text output for both exit paths

### Files NOT changed

- `node_factory/base.py` — `get_output_model_for_node` already exists
- `executor.py` — structured output invocation pattern already exists
- `utils/json_extract.py` — `extract_json` already exists
- All existing agent demos — they don't use schemas, so no regression

### Dependencies

- `get_output_model_for_node(node_config, prompts_dir, graph_path, prompts_relative)` from `node_factory/base.py`
- `extract_json(text)` from `utils/json_extract.py`
- `llm_base` — the pre-`bind_tools` LLM instance, saved in the agent closure

## Related

- FR-447 — Judge demo that exposed this gap
- `docs/plan-dogfood-chaplain.md` — Phase 2 chaplain integration needs structured dict for event routing
- `yamlgraph/tools/agent.py` line 292, 365 — both text-only return paths
- `yamlgraph/executor.py` line 161-162 — existing structured output pattern in LLM nodes

## Judge Notes

**Verdict:** AMEND → **Approved** (all 6 amendments applied)
**Classification:** framework_primitive

### Amendments Applied

1. ✅ **Max-iterations exit path** — both exit paths (line 292, 365) now in scope with shared helper
2. ✅ **Try-parse-first** — `extract_json` + `model_validate` before LLM re-invoke
3. ✅ **`get_output_model_for_node` signature** — corrected to 4-arg form
4. ✅ **`llm_base`** — explicitly saved before `bind_tools`
5. ✅ **REQ-YG-422** — assigned in acceptance criteria
6. ✅ **Skeleton test code** — provided in test file
