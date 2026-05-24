# Feature Request: OpenAI strict JSON schema additionalProperties guard

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-05-24

## Summary

OpenAI's structured output API requires `additionalProperties: false` on all nested objects in the JSON schema. Pydantic models with `list[dict]` fields generate schemas without this property, causing 400 errors on OpenAI models (gpt-5.3-codex, o4-mini).

## Value Statement

Graph authors using inline YAML schemas with nested objects get working structured output on OpenAI models without manually tweaking JSON schema properties.

## Problem

When `with_structured_output()` sends a Pydantic model to OpenAI, OpenAI's strict mode validates the JSON schema and rejects it if any nested object lacks `additionalProperties: false`. This breaks the judge demo (and any graph with nested dict schemas) on all OpenAI models.

Error from eval:
```
Error code: 400 - {'error': {'message': "Invalid schema for response_format 'JudgeVerdict':
In context=('properties', 'criteria_results', 'items'),
'additionalProperties' is required to be supplied and to be false.",
'type': 'invalid_request_error', 'param': 'text.format.schema',
'code': 'invalid_json_schema'}}
```

The langchain warning also suggests `method="function_calling"` as an alternative.

Root cause: `list[dict]` in YAML schema generates a Pydantic field with untyped dict items. OpenAI strict mode requires every object to explicitly declare `additionalProperties: false`.

## Proposed Solution

In `_try_structured_output()` (agent.py), when the `with_structured_output()` call raises and the error contains `invalid_json_schema` or `additionalProperties`, retry with `method="function_calling"` which uses the more lenient function-calling API instead of strict JSON schema validation.

This is a boundary fix: catch the provider-specific schema rejection at the callsite, not downstream in the schema builder. The `list[dict]` type is valid Python/Pydantic — the problem is OpenAI's strict mode requirement, not the schema itself.

```python
try:
    structured_llm = llm_base.with_structured_output(output_model)
    result = structured_llm.invoke(retry_msgs)
    return result.model_dump()
except Exception as reinvoke_err:
    err_str = str(reinvoke_err)
    # FR-458: OpenAI strict mode rejects schemas without additionalProperties
    if "invalid_json_schema" in err_str or "additionalProperties" in err_str:
        structured_llm = llm_base.with_structured_output(
            output_model, method="function_calling"
        )
        result = structured_llm.invoke(retry_msgs)
        return result.model_dump()
    # FR-456: If extract_json found a dict, use lenient construction
    if isinstance(parsed, dict):
        ...
    raise
```

## Acceptance Criteria

- [x] OpenAI models (gpt-5.3-codex, o4-mini) can produce structured output from schemas with nested dicts
- [x] Judge demo eval passes for openai-codex (APPROVE in 19s)
- [x] Existing structured output behavior unchanged for other providers
- [x] Tests added (3 tests in TestOpenAIStrictSchemaFallback)
- [x] No regression on Anthropic/Google/Mistral structured output (4024 passed)

## Out of Scope

- `executor.py:162` and `race_node.py:64` also call `with_structured_output()` without the FR-456/458 fallback chain. Separate FR if needed.
- Rewriting the schema builder to convert `list[dict]` → typed sub-models (Option B from original proposal). Valid improvement but separate concern.

## Alternatives Considered

- Make graph authors manually define Pydantic models with proper `additionalProperties` config — violates YAML-first principle.
- Always use `method="function_calling"` — loses benefits of native structured output on providers that support it.

## Related

- FR-456: Structured output JSON fallback (adjacent fix for provider rejection)
- `yamlgraph/tools/agent.py` L166: `with_structured_output()` call in `_try_structured_output()`
- `yamlgraph/schema_loader.py`: inline schema → Pydantic model via `build_pydantic_model()`
- `examples/demos/judge/prompts/judge.yaml`: `criteria_results: list[dict]`
