# Feature Request: FR-451 Fahrenheit 451 — Temperature Adjustments

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-05-24

## Summary

Agent nodes silently ignore `temperature: 0` due to Python falsy evaluation. `0 or 0.7` evaluates to `0.7`, so any agent configured for deterministic output (`temperature: 0`) runs at the default temperature instead.

## Value Statement

Agent nodes respect their configured temperature, enabling deterministic verdicts, reproducible outputs, and correct tool-calling behavior.

## Problem

In `yamlgraph/tools/agent.py` lines 259-263:

```python
resolved_temperature = (
    node_config.get("temperature")
    or defaults.get("temperature")
    or prompt_config.get("temperature")
    or 0.7  # Default temperature for agents
)
```

`temperature: 0` is falsy in Python. The `or` chain skips it and falls through to `0.7`. This affects **all agent nodes** with `temperature: 0`, not just the judge demo.

Confirmed by demo-output.log: graph specifies `temperature: 0`, log shows `temp=0.7`.

### Root Cause

The `or`-chain pattern for config resolution treats `0` as `None`. Same pattern may exist in other node types.

## Proposed Solution

Replace the `or` chain with explicit `None` checks:

```python
def _resolve_config(node_config, defaults, prompt_config, key, fallback):
    for source in (node_config, defaults, prompt_config):
        val = source.get(key)
        if val is not None:
            return val
    return fallback

resolved_temperature = _resolve_config(
    node_config, defaults, prompt_config, "temperature", 0.7
)
```

Or inline:

```python
resolved_temperature = next(
    (v for src in (node_config, defaults, prompt_config)
     if (v := src.get("temperature")) is not None),
    0.7,
)
```

### Audit scope

Check if the same `or`-chain pattern exists for other numeric configs (`max_iterations`, `timeout`, etc.) in:
- `yamlgraph/tools/agent.py`
- `yamlgraph/node_factory/llm_nodes.py`
- `yamlgraph/executor.py`

## Acceptance Criteria

- [ ] Agent node with `temperature: 0` creates LLM with `temperature=0` (unit test)
- [ ] Agent node with `temperature: 0.5` still works (regression test)
- [ ] Agent node with no temperature config falls back to `0.7` (regression test)
- [ ] No other `or`-chain config resolution patterns with numeric values remain in agent.py
- [ ] `examples/demos/judge/demo-output.log` shows `temp=0` after fix

## Related

- FR-450 — Judge demo hardening (split from: temperature was bundled with tool fixes)
- FR-447 — Judge agent node
- `yamlgraph/tools/agent.py:259-263` — bug location
- Scripture: `downstream_fix` — guard added where symptom manifests; normalize at entry boundary
