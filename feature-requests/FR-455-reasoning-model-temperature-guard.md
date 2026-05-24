# Feature Request: FR-455 Reasoning Model Temperature Guard

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-05-24

## Summary

`llm_factory.create_llm()` should detect reasoning models (e.g., OpenAI `o4-mini`, `o3`, `o1`) and omit the `temperature` parameter, which these models reject with a 400 error.

## Value Statement

Reasoning models are increasingly common. Currently, any YAMLGraph graph with `temperature: 0` (standard for deterministic tasks like judging) crashes immediately on reasoning models. This blocks multi-model evaluation and limits provider portability.

## Problem

OpenAI reasoning models (`o4-mini`, `o3`, `o1-*`) do not accept the `temperature` parameter — only the default (1) is supported:

```
Error code: 400 - {'error': {
  'message': "Unsupported value: 'temperature' does not support 0.0 with this model.
              Only the default (1) value is supported.",
  'type': 'invalid_request_error',
  'param': 'temperature',
  'code': 'unsupported_value'
}}
```

Discovered during FR-453 eval: `o4-mini` failed on first API call before any tool use.

The resolution chain (FR-451) correctly resolves `temperature: 0` from graph config. The bug is that `create_llm()` passes it unconditionally to the provider, which rejects it.

## Proposed Solution

In `yamlgraph/utils/llm_factory.py`, detect reasoning models by prefix and omit temperature:

```python
REASONING_MODEL_PREFIXES = ("o1", "o3", "o4")

def create_llm(provider, model=None, temperature=None, **kwargs):
    # ...
    if provider == "openai" and any(model.startswith(p) for p in REASONING_MODEL_PREFIXES):
        temperature = None  # Reasoning models reject temperature
        logger.info(f"Omitting temperature for reasoning model: {model}")
    # ...
```

### Considerations

- Only OpenAI reasoning models are known to reject temperature. Other providers may add similar models later — keep the guard extensible.
- Log when temperature is omitted so users know their config was overridden.
- The guard should apply to all callers of `create_llm()`, not just agent nodes.

## Acceptance Criteria

- [x] `create_llm(provider="openai", model="o4-mini", temperature=0)` succeeds without 400 error
- [x] Temperature is silently omitted for `o1-*`, `o3-*`, `o4-*` model prefixes
- [x] Log message emitted when temperature is omitted
- [ ] Non-reasoning OpenAI models (gpt-4o, gpt-4.1) still accept temperature normally
- [ ] Unit test covers reasoning model temperature guard

## Related

- FR-451 — Temperature zero bug (resolved resolution chain, not provider compatibility)
- FR-453 — Judge model evaluation (discovered this bug)
- `yamlgraph/utils/llm_factory.py` — File to modify
