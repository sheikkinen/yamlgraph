# Feature Request: Lint knows the state fields a map node creates

**Priority:** LOW
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-27
**First consumer / first event:** `yamlgraph graph lint` on the
FR-1120 census graph, which reads `{state.executed_findings_failures}`
and `{state._map_verdict.judge_items.dispatch}` without declaring either
in `state:`. The second event is removing the `_map_verdict: dict`
workaround from `examples/demos/meta_map/graph.yaml`.
**Research:** in-body Alternatives table (the FR-890 equivalent-record
route). The defect is a single lint function checked against the
single state builder, and the fix is the copy of one rule.
**Prior art:** [FR-1073](FR-1073-map-result-contract.md) introduced the
`failures` key and `_map_verdict`. It did not update the linter.
[FR-1116](FR-1116-map-memo-file-corpus.md) hit the gap and recorded it
as a deviation ("linter gap, not fixed here"). No rejected FR covers
this territory.

## Summary

For every `type: map` node, the state builder creates three fields: the
`collect` key, the failures key (`failures:` or `<collect>_failures`),
and `_map_verdict`. The linter's E007 check knows only the first. A graph
that reads the other two gets a false E007 error, so authors declare the
fields in `state:` by hand. That declaration is harmless today only
because the state builder lets the node-derived field win.

## Value Statement

Graph authors who read a map's failures or verdict get no false lint
error and need no hand-written workaround in `state:`.

## Problem

[`_build_known_state_fields`](../yamlgraph/linter/checks_semantic.py#L115-L131)
adds `state_key` and `collect` for each node. The state builder also adds
the map's failures key and `_map_verdict`
([state_builder.py#L271](../yamlgraph/models/state_builder.py#L271);
failures default in
[map_compiler.py#L322](../yamlgraph/compile/map_compiler.py#L322)).

Witnessed:
- FR-1116's adapter run hit E007 on
  `{state._map_verdict.summarize.dispatch}` and "repaired" it by declaring
  `_map_verdict: dict` in `meta_map`'s `state:`
  (`examples/demos/meta_map/graph.yaml:31`). That line overrides nothing
  only because of the builder's precedence order. If that order ever
  changes, the declaration silently drops the `merge_by_key` reducer.
- FR-1120's census graph reads `executed_findings_failures` (a default
  failures key) and `_map_verdict`. It would need the same workaround
  twice.

## Ideal Result

Lint accepts a reference to any field the state builder creates for a
map node, and it still rejects `_map_verdict` in a graph that has no map
node. The linter's list and the builder's list cannot drift without a
test failing.

## Proposed Solution

In `_build_known_state_fields`, for a node with `type: map`, also add:
- `node_config.get("failures") or f"{collect}_failures"`;
- `_map_verdict`.

That is the same expression as `map_compiler.py:322`, copied rather than
imported so that the linter does not import the compile layer. A parity
test pins the copy to the state builder.

Then remove `_map_verdict: dict` from `examples/demos/meta_map/graph.yaml`
through `scripts/author.sh` (one-line brief). No other graph changes.

## Acceptance Criteria

- [ ] AC-01: A graph with a map node that reads `{state._map_verdict.<map>.dispatch}` and does not declare `_map_verdict` lints with no E007.
- [ ] AC-02: A graph that reads a map's default failures key (`<collect>_failures`), or an explicit `failures:` key, without declaring it lints with no E007.
- [ ] AC-03: A graph with no map node that reads `{state._map_verdict.x}` still gets E007.
- [ ] AC-04: Parity test: for a fixture graph with two map nodes (one with explicit `failures:`, one with the default), every field the state builder adds for those nodes is in `_build_known_state_fields`.
- [ ] AC-05: `examples/demos/meta_map/graph.yaml` no longer declares `_map_verdict`. The change goes through `scripts/author.sh`, `yamlgraph graph lint` passes, and `tests/unit/test_fr1113_meta_map.py` passes.
- [ ] AC-06: Tests carry an existing linter REQ ID (or a new one via a CAP entry), `python scripts/req_coverage.py --strict` passes, and the changelog fragment, FR record and diary entry are present.

## Alternatives Considered

| Option | Disposition |
|---|---|
| Keep declaring the fields in `state:` | Rejected. It is a workaround that depends on builder precedence order, and it has to be repeated in every consumer. |
| Linter imports the state builder and asks it for the fields | Rejected. That crosses the lint→compile/models boundary and needs a full config load. One copied expression plus a parity test is smaller. |
| Silence E007 for any name that starts with `_` | Rejected. It is too broad and hides real typos. |

## Related

- [FR-1073](FR-1073-map-result-contract.md), [FR-1116](FR-1116-map-memo-file-corpus.md), [FR-1120](FR-1120-census-map-memo.md)
