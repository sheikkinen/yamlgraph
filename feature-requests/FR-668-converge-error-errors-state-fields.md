# Feature Request: Converge dual error/errors state fields on errors list

**Priority:** HIGH
**Type:** Bug
**Status:** Judged
**Effort:** 1 day
**Requested:** 2026-07-03

## Summary

State declares both a singular `error` field (last_value reducer) and an
`errors` list (add reducer). Writers diverge: tool nodes write singular
`error`, LLM nodes append to `errors`. In parallel map fan-out,
last-write-wins on `error` silently loses branch failures. Deprecate the
singular field and converge all writers/readers on the `errors` list.

## Value Statement

Graph authors debugging parallel map failures see every branch error instead
of only the last one, eliminating a class of invisible failure loss.

## Problem

`yamlgraph/models/state_builder.py:66` declares:

```python
"error": Annotated[Any, last_value],
```

alongside the accumulating `errors` list. Divergent writers:

- `yamlgraph/node_factory/tool_nodes.py:75,86` — writes singular `error`
- `yamlgraph/node_factory/llm_nodes.py` / `llm_execution.py` — appends
  `PipelineError` to `errors`
- `yamlgraph/storage/export.py:170` — reads singular `error`

Under parallel map fan-out, multiple branches writing `error` race; the
last_value reducer keeps only the final write. A user inspecting
`state["error"]` after a map node sees one failure and misses the rest.
This is `downstream_fix` territory: the defect is at the state-schema
boundary, not in any single writer.

## Proposed Solution

1. Migrate all writers of singular `error` to append `PipelineError` to
   `errors` (tool_nodes, any error_handlers paths).
2. Migrate readers (`storage/export.py:170`, any CLI/output paths) to derive
   the latest error: `errors[-1] if errors else None`.
3. Remove `error` from `BASE_FIELDS` in `state_builder.py`. No compat shim
   (Commandment 8) — this is an internal state contract, and grep shows a
   bounded writer/reader set.
4. Run full test suite; fix all fixtures referencing singular `error`.

## Acceptance Criteria

- [ ] Failing test first (RED): parallel map with two failing branches
      asserts both failures present in `errors`
- [ ] `grep -rn '"error"' yamlgraph/` shows no state-level singular writes
      (nested tool-result `{"error": ...}` payloads are a different pattern
      and out of scope)
- [ ] `storage/export.py` derives latest error from `errors` list
- [ ] `error` removed from `BASE_FIELDS`
- [ ] All unit tests green
- [ ] Changelog fragment in `changelog/unreleased/`

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

**APPROVED.** All claims verified against codebase. Both fields exist at
state_builder.py:66-67. tool_nodes.py writes singular `error` at lines 75
and 86. export.py reads it at line 170. The parallel-map error-loss bug is
real and the fix is mechanical.

**Amendments:**
1. The tool_nodes `error` writes are NESTED inside the tool-result dict
   (stored under `state_key`), not top-level state. Audit whether these
   are true state-level writes or payload-internal fields. If payload-internal,
   they are out of scope — only the top-level state field removal matters.
2. Also grep `mcp_server.py` and `progress.py` — they have `"error"` fields
   in JSON response payloads, which are NOT state fields and must be
   excluded from the migration.
3. Sequencing: land FR-674 module splits first if state_builder.py (471
   lines, already over ceiling) needs edits.
