# Feature Request: Remove dead top-level error state field

**Priority:** LOW
**Type:** Enhancement
**Status:** Judged
**Effort:** 0.5 days
**Requested:** 2026-07-03

## Summary

The top-level `error` state field is declared, initialized, and exported —
but written by no production code. Remove it from `BASE_FIELDS` and make
export derive its error summary from the `errors` list. Successor to
rejected FR-668, narrowed per the Judgement: no parallelism claim, no bug
framing — pure Commandment 8 entropy removal.

## Value Statement

The state contract stops advertising a field that can never carry
information, and export consumers stop parsing a permanently-`None` value.

## Problem

Verified (2026-07-03 session, grep across `error_handlers.py`,
`node_factory/*.py`, `map_compiler.py`):

- `yamlgraph/models/state_builder.py:66` declares
  `"error": Annotated[Any, last_value]` in `BASE_FIELDS`
- `yamlgraph/models/state_builder.py:289` initializes it to `None`
- `yamlgraph/storage/export.py:170` exports `state.get("error")`
- **No production code writes it.** The only `"error"` writers are nested
  tool-result payloads under `state_key`
  (`node_factory/tool_nodes.py:58,75,86`), which the comment at
  `tool_nodes.py:50` explicitly marks as "nested inside the tool result
  dict, not top-level state"

A field that is declared, initialized, exported, and never written is a
phantom claim in the state contract — the same class FR-465/FR-466 retired
from the capability registry. Every export ships `"error": None`: plausible
shape, zero information (`plausible_wrong_answer` surface for consumers).

## Proposed Solution

1. Remove `error` from `BASE_FIELDS` and from the initial-state dict in
   `state_builder.py`.
2. `storage/export.py`: derive the summary from the `errors` list —
  `errors[-1] if errors else None` — keeping the export key name so export
  consumers now receive real information where they previously always
  received `None`. Serialize `PipelineError`/Pydantic values with
  `model_dump(mode="json")` rather than leaking model objects into a summary
  intended for export.
3. Fix any tests/fixtures referencing top-level `error`.

No compat shim; no deprecation period — the field never carried data, so no
consumer can be depending on anything but `None`.

## Acceptance Criteria

- [ ] Failing test first (RED): export of a state whose `errors` list holds
      a `PipelineError` yields that error in the export summary (currently
      yields `None`)
- [ ] Export summary remains JSON-serializable when the latest error is a
  `PipelineError`
- [ ] `error` absent from `BASE_FIELDS` and `create_initial_state`
- [ ] `grep -rn '\"error\"' yamlgraph/` shows only nested tool-result
      payloads and the export derivation
- [ ] All unit tests green
- [ ] Changelog fragment in `changelog/unreleased/` (type: removal)

## Alternatives Considered

- **Keep the field, add writers** — rejected: this was FR-668's converge
  direction; the Judgement found no proven need. Subtraction is the honest
  fix (`growth_as_default`).
- **Remove the export key entirely** — rejected: deriving from `errors`
  preserves the export shape while making the value truthful; removing the
  key is a wider consumer-facing change with no added benefit.

## Related

- FR-668 (rejected predecessor — see its Judgement for the replacement
  direction this FR follows)
- docs/diary/diary-2026-07-03-the-subagents-confident-inventory.md
- yamlgraph/models/state_builder.py:66,289
- yamlgraph/storage/export.py:170
- yamlgraph/node_factory/tool_nodes.py:50-86

## Judgement

**APPROVED.** This is the correct successor to rejected FR-668: a narrow
entropy-removal FR with no unproven parallelism claim. The code facts check
out: top-level `error` is declared in `BASE_FIELDS`, initialized to `None`,
and read by `export_summary`; grep did not reveal production state-level
writers. The `tool_nodes.py` `"error"` fields are nested tool-result payloads,
not top-level state.

**Amendments:**
1. The export-derived `error` value must be JSON-serializable. If the latest
  entry is a `PipelineError`/Pydantic model, export `model_dump(mode="json")`
  or an equivalent plain dict.
2. Keep the export key name `error` as proposed; removing the key would widen
  the consumer-facing change without adding value.
3. Do not touch nested payload `"error"` keys in MCP responses, progress
  reports, or tool results; they are different contracts.
