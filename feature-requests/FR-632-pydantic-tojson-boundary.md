# FR-632: Pydantic Models Break Jinja2 tojson Filter

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented (2026-07-01) — commit `4742576d` (Option A; three boundary fixes from the FR-628 wiki-memory demo).
**Effort:** 0.5 day
**Requested:** 2026-07-01
**Surfaced by:** FR-628 wiki-memory demo

## Summary

LLM structured outputs (Pydantic BaseModel instances) stored in state crash
when a downstream Jinja2 prompt uses `{{ state.field | tojson }}`. Python's
`json.dumps()` cannot serialize BaseModel objects.

## Root Cause

In `yamlgraph/node_factory/llm_nodes.py`, the result from `execute_prompt()`
with a schema is a Pydantic model stored directly into state:

```python
cfg.state_key: result,  # result is a BaseModel instance
```

When a downstream prompt renders `{{ state.drafted_page | tojson }}`, Jinja2
calls `json.dumps(state["drafted_page"])` which raises:
`TypeError: Object of type WikiPage is not JSON serializable`

## Options

### Option A: Normalize at LLM output boundary (preferred)

In `llm_nodes.py`, call `model_dump()` before storing:

```python
if hasattr(result, "model_dump"):
    result = result.model_dump()
return {cfg.state_key: result, ...}
```

**Pro:** Fixes all downstream consumers at once. Consistent with Scripture
("normalize at the boundary where external data enters").
**Con:** Consumers lose access to model validation methods.

### Option B: Custom Jinja2 tojson filter

Register a filter that handles BaseModel:

```python
def pydantic_tojson(value, indent=None):
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    return json.dumps(value, indent=indent)
```

**Pro:** Non-breaking — models stay in state for programmatic access.
**Con:** Only fixes Jinja2; other json.dumps calls still break.

### Option C: Custom JSON encoder on Environment

**Pro:** Zero changes to template syntax.
**Con:** Global state, harder to test.

## Recommendation

Option A. The Scripture says normalize at entry boundary. Pydantic models in
state serve no purpose beyond the node that created them — downstream nodes
access fields via `state.field.subfield` which works identically on dicts via
`resolve_state_path()`. The `write_data_file` tool already had to add its own
`model_dump()` guard — proving consumers keep hitting this independently.

## Acceptance Criteria

- [ ] `{{ state.structured_output | tojson }}` works in prompts
- [ ] Structured output fields still accessible via `{state.X.field}` syntax
- [ ] `write_data_file` tool's `model_dump()` guard becomes redundant (keep as defense-in-depth)
- [ ] Condition evaluation on structured output fields still works
- [ ] Add regression test: LLM node with schema → downstream Jinja2 prompt with tojson

## Judgement

**Verdict: GRANTED — Option A (normalize at boundary).**

The Scripture is explicit: normalize at the boundary where external data enters.
No consumer in the codebase calls Pydantic methods on state values (verified via
grep). `resolve_state_path()` handles both dict access and `getattr` — so
downstream path resolution works identically on dicts. The `write_data_file`
tool's independent `model_dump()` guard proves consumers keep hitting this.

**Decision:** Option A. One-line change in `llm_nodes.py`.

**Constraints:**
- Keep `write_data_file`'s `model_dump()` as defense-in-depth (no removal)
- Keep `ref_gate.py`'s guard (user code should be self-contained)
- Do NOT touch streaming nodes in this FR (separate concern, separate blast radius)

**Enforcement order:**
1. RED: Test that mocks LLM returning a Pydantic model, asserts state value is dict
2. GREEN: Add `if hasattr(result, "model_dump"): result = result.model_dump()` in `_build_result_tuple()`
3. RED: Integration test — prompt with `{{ state.X | tojson }}` after schema node
4. GREEN: Should pass with the boundary fix
5. Verify all tests pass
6. Commit
