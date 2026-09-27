# Feature Request: Lint knows the state fields a map node creates

**Priority:** LOW
**Type:** Bug
**Status:** Approved with revisions (folded 2026-09-27)
**Effort:** 0.5 day
**Requested:** 2026-09-27
**First consumer / first event:** `yamlgraph graph lint` on the
FR-1120 census graph, which reads `{state.executed_findings_failures}`
and `{state._map_verdict.judge_items.dispatch}` without declaring either
in `state:`. The second event is removing the `_map_verdict: dict`
workaround from `examples/demos/meta_map/graph.yaml`.
**Research:** in-body Alternatives table, with precedent, disagreement
and an `is_this_a_graph` answer (the FR-890 equivalent-record route;
judgement R-1).
**Prior art:** [FR-1073](FR-1073-map-result-contract.md) introduced the
`failures` key and `_map_verdict`. It did not update the linter.
[FR-1116](FR-1116-map-memo-file-corpus.md) hit the gap and recorded it
as a deviation ("linter gap, not fixed here"). No rejected FR covers
this territory.

## Summary

For every `type: map` node, the state builder creates five fields: the
`collect` key, the failures key (`failures:` or `<collect>_failures`),
`_map_accounting`, `_map_open` and `_map_verdict`
([state_builder.py#L262-L271](../yamlgraph/models/state_builder.py#L262-L271)).
The linter's E007 check knows only the first. A graph
that reads the other two gets a false E007 error, so authors declare the
fields in `state:` by hand. That declaration is harmless today only
because the state builder lets the node-derived field win.

## Value Statement

Graph authors who read a map's failures or verdict get no false lint
error and need no hand-written workaround in `state:`.

## Problem

[`_build_known_state_fields`](../yamlgraph/linter/checks_semantic.py#L115-L131)
adds `state_key` and `collect` for each node. The state builder also adds
the map's failures key, `_map_accounting`, `_map_open` and `_map_verdict`
([state_builder.py#L262-L271](../yamlgraph/models/state_builder.py#L262-L271);
the failures key is derived only when `collect` is set; failures default
also in
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

In `_build_known_state_fields`, for a node with `type: map` only (the
local map-only derivation, the selected alternative):
- when `collect` is a non-empty string, add
  `node.get("failures") or f"{collect}_failures"`;
- add `_map_accounting`, `_map_open` and `_map_verdict`.

A map without `collect` adds only the three shared channels and raises
nothing; schema diagnostics keep reporting the malformed node. A graph
with no map node adds none of them.

A parity test calls both `_build_known_state_fields` and the builder's
`extract_node_fields` on the same two-map fixture and asserts that every
builder key is known to E007, so the two lists cannot drift silently.

Then remove `_map_verdict: dict` from `examples/demos/meta_map/graph.yaml`
through `scripts/author.sh` (one-line brief). No other graph changes.

## Acceptance Criteria

Adopted verbatim from the judgement's revised criteria.

- [ ] AC-01: A graph with a map node that reads `{state._map_verdict.<map>.dispatch}` without declaring `_map_verdict` produces no E007.
- [ ] AC-02: Separate fixtures reading the default `<collect>_failures` field and an explicit `failures:` field without declaring them produce no E007.
- [ ] AC-03: A map graph may reference `_map_accounting` and `_map_open` without E007 because both are fields created by the state builder.
- [ ] AC-04: A graph with no map node that references `_map_accounting`, `_map_open`, or `_map_verdict` receives E007 for each referenced field.
- [ ] AC-05: For a fixture with two map nodes, one using default failures and one explicit failures, every key returned by `extract_node_fields` for those nodes is present in `_build_known_state_fields`.
- [ ] AC-06: The map-only derivation handles a malformed map lacking `collect` without raising from `_build_known_state_fields`; existing schema diagnostics remain responsible for reporting the malformed node.
- [ ] AC-07: `examples/demos/meta_map/graph.yaml` no longer declares `_map_verdict`; the change is produced through `scripts/author.sh`, `yamlgraph graph lint examples/demos/meta_map/graph.yaml` reports no E007, and `tests/unit/test_fr1113_meta_map.py` passes.
- [ ] AC-08: All new tests carry `@pytest.mark.req("REQ-YG-069")`; REQ-YG-069 in `ARCHITECTURE.md` names map `collect`, failures, accounting, open, and verdict fields; and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-09: The changelog fragment, folded FR implementation record, and Distill diary entry with a `Seed:` are present.

## Alternatives Considered

| Option | Precedent | Disposition |
|---|---|---|
| Keep declaring the fields in `state:` by hand | FR-1116 did this (`meta_map/graph.yaml:31`) | Rejected. It depends on builder precedence order, and every consumer must repeat it. |
| **Local map-only derivation in the linter** | The linter already derives `collect` per node (`checks_semantic.py:115-130`) | **Selected.** It is the smallest change, touches only map nodes, and the parity test pins it to the builder. |
| Call `extract_node_fields` for every node from the linter | The linter already imports `COMMON_INPUT_FIELDS` from `state_builder` (`checks_semantic.py:9`); `extract_node_fields` takes a node dict, not a full config (`state_builder.py:219-278`) | Rejected for this FR. It would also change E007's known fields for router, race, subgraph and other node types. That is a wider enforcement change than the defect needs. It is used as the test oracle instead. |
| Extract a shared map-field helper used by both builder and linter | None | Rejected. It changes `state_builder.py`, which the judgement puts out of scope, and it is an abstraction for two callers where a parity test already prevents drift. |
| Silence E007 for any name that starts with `_` | None | Rejected. It is too broad and hides real typos in map-less graphs (AC-04 is the negative control). |

**Preserved disagreement:** reusing `extract_node_fields` wholesale
would make E007 exact for every node type in one move and remove future
drift classes. The counter-argument, which decides it here, is that
it silently widens E007 acceptance for node types with no witnessed
defect. A later FR can take that step with its own negative controls.

**`is_this_a_graph`:** no. This is a deterministic lint rule over YAML,
and no LLM step is involved.

## Related

- [FR-1073](FR-1073-map-result-contract.md), [FR-1116](FR-1116-map-memo-file-corpus.md), [FR-1120](FR-1120-census-map-memo.md)
