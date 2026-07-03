# Feature Request: Converge dual error/errors state fields on errors list

**Priority:** LOW
**Type:** Bug
**Status:** Rejected
**Effort:** 1 day
**Requested:** 2026-07-03

## Summary

State declares both a singular `error` field (last_value reducer) and an
`errors` list (add reducer). Direct inspection did not verify the claimed
state-level divergent writers: the cited tool-node writes are nested
tool-result payload fields, not top-level `state["error"]` writes. The
singular state field appears unused except for default initialization and
summary export.

## Value Statement

Graph authors benefit from a simpler error-state contract, but the originally
claimed parallel-map branch-loss bug is not proven by the cited code.

## Problem

`yamlgraph/models/state_builder.py:66` declares:

```python
"error": Annotated[Any, last_value],
```

alongside the accumulating `errors` list. Verified code facts:

- `yamlgraph/node_factory/tool_nodes.py` writes nested payload keys under
   `state_key` (`{state_key: {"error": ...}}`), not top-level state
- LLM, race, map, guard, and timeout paths append `PipelineError` objects to
   top-level `errors`
- `yamlgraph/storage/export.py` reads top-level `state.get("error")`
- `yamlgraph/models/state_builder.py` initializes top-level `error` to `None`

The originally claimed divergent top-level writers were not found. This means
the parallel fan-out loss scenario is unproven. The remaining issue is a
small contract cleanup: an apparently unused top-level `error` field exists
beside the real accumulated `errors` list.

## Proposed Solution

Reject this FR as a HIGH-priority bug. If cleanup is still desired, file a
new LOW-priority FR with a narrower scope:

1. Prove no top-level writers of `state["error"]` exist outside
   `state_builder.py` initialization and `storage/export.py` summary read.
2. Decide whether summary export should expose latest `errors[-1]` or omit
   the singular `error` field entirely.
3. Remove `error` from `BASE_FIELDS` only after tests prove no public graph
   output relies on it.

## Acceptance Criteria

- [ ] No enforcement under this FR; rejected as written
- [ ] Replacement FR, if created, includes a grep/audit proving top-level
   state writers and readers separately from JSON payload `error` fields

## Alternatives Considered

- **Keep both fields, document semantics** — rejected: two fields with
  overlapping meaning is the entropy the Scripture forbids; documentation
  does not stop divergent writers.
- **Make `error` a computed view** — rejected: LangGraph state is a
  TypedDict, not a model with properties; adds machinery for no gain.

## Related

- docs/2026-07-03-review-fable.md (Issue 1)
- yamlgraph/models/state_builder.py:66
- yamlgraph/node_factory/tool_nodes.py:75-86
- yamlgraph/storage/export.py:170

## Judgement

**REJECTED AS WRITTEN.** The review artifact overclaimed the evidence. Both
fields exist in `state_builder.py`, and `storage/export.py` reads the singular
field, but the cited `tool_nodes.py` writes are nested response payloads under
`state_key`, not top-level `state["error"]` writes. Grep did not identify a
parallel fan-out path writing top-level `error`, so the claimed last-write-wins
branch-loss bug is unproven.

**Replacement direction:** create a smaller cleanup FR only if desired:
remove the unused top-level singular `error` field or make export derive a
summary from `errors`. That FR should not mention tool-result payload fields
as state-level writers and should not claim a parallelism correctness bug
without a failing RED test that reproduces it.
