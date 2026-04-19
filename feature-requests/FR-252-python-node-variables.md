# Feature Request: Extend type: python nodes with variables: expression support

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-19

## Summary

Add `variables:` expression resolution to `type: python` nodes, making them consistent with every other node type (llm, router, race, streaming, a2a_call).

## Value Statement

Graph authors can use declarative `variables:` mappings on python nodes instead of manually extracting state fields inside Python functions, enabling python nodes to serve as general-purpose drop-in replacements for specialized node types.

## Problem

`type: python` nodes receive raw `state` and do not resolve `variables:` expressions (`{state.field}`, arithmetic, etc.) before calling the function. Every other node type calls `resolve_node_variables()` before execution. This inconsistency:

1. Prevents `type: python` from being used as a general-purpose node with declarative variable mapping
2. Forces Python functions to know about state structure instead of receiving pre-resolved arguments
3. Blocks the A2A-to-python refactoring identified in the April 2026 audit

**Current behavior:**
```yaml
nodes:
  my_node:
    type: python
    tool: my_func
    variables:
      url: "{state.agent_url}"   # IGNORED — func receives raw state
```

The `variables:` field is parsed by the YAML loader but never resolved or merged into the state dict passed to the function.

## Proposed Solution

In `create_python_node()` (`yamlgraph/tools/python_tool.py`), add variable resolution before the function call — identical to the pattern in llm, race, streaming, and a2a nodes:

```python
# At closure scope (line ~161, alongside other config reads)
variable_templates = node_config.get("variables", {})

# Inside node_fn, before func(state) call (line ~181)
from yamlgraph.utils.expressions import resolve_node_variables
resolved = resolve_node_variables(variable_templates, state)
effective_state = {**state, **resolved} if resolved else state
result = func(effective_state)
```

**After the change:**
```yaml
nodes:
  call_agent:
    type: python
    tool: send_a2a_request
    state_key: agent_response
    variables:
      url: "{state.agent_url}"
      message: "{state.user_query}"
```

The function receives `state` with `url` and `message` already resolved from expressions.

## Acceptance Criteria

- [ ] `type: python` nodes resolve `variables:` expressions before calling the function
- [ ] Resolved variables override same-named state keys (consistent with llm/race/streaming nodes)
- [ ] Empty `variables: {}` preserves current behavior (no regression)
- [ ] `variables:` omitted entirely preserves current behavior (no regression)
- [ ] Unit test: python node with `variables:` config resolves `{state.field}` expressions
- [ ] Unit test: resolved variables are accessible in the function's state dict argument
- [ ] Unit test: resolved variables override existing state keys
- [ ] Existing python node tests pass unchanged
- [ ] Linter validates `variables:` references on python nodes (existing E007 coverage via `{state.X}`)

## Alternatives Considered

1. **Pass resolved variables as a separate argument** — Would break the existing `func(state)` contract. Every existing python tool function would need a signature change. Rejected.
2. **Resolve inside each Python function** — Pushes framework responsibility to user code. Violates "normalize at the boundary" principle. Rejected.
3. **Do nothing, document the gap** — The inconsistency is a genuine defect, not a design choice. The inbox file traces this to protocol enthusiasm during a2a_call implementation. Rejected.

## Implementation Notes

- Import `resolve_node_variables` from `yamlgraph.utils.expressions` (same as llm_nodes, race_node, streaming, a2a_nodes)
- ~7 lines of change in `python_tool.py`
- Extract `variable_templates` at closure scope (line ~161), resolve inside `node_fn` before `func()` call
- Pattern is identical to `streaming.py` lines 47/54 — simplest reference implementation
- Existing linter rule E007 already validates `{state.X}` references in `variables:` — no linter changes needed

## Related

- **REQ-YG-020**: Python tool integration and execution
- **REQ-YG-051**: Expression language — `resolve_node_variables` contract
- **REQ-YG-054**: Python nodes with retry/fallback error handling
- **Inbox source**: `.chaplain/inbox/gh-124.md` (A2A consumer audit, April 2026)
- **Prerequisite for**: A2A-to-python refactoring (replacing `type: a2a_call` with `type: python` + contrib function)
- **Reference implementation**: `yamlgraph/node_factory/streaming.py` lines 47, 54
