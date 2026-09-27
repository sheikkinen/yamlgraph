# Authoring brief: FR-1119 meta_map — drop the `_map_verdict` state workaround

Governing FR: feature-requests/FR-1119-lint-map-owned-state-fields.md (AC-07)

## Task

Edit `examples/demos/meta_map/graph.yaml` only: delete the single line
`  _map_verdict: dict` from the `state:` block. Nothing else changes —
keep `summary_failures: list` and every node, edge and comment
byte-identical. No prompt, subgraph, tools or README changes.

Why: FR-1119 taught the linter (E007) that every `type: map` node creates
`_map_verdict`, so the hand declaration added by FR-1116 is no longer
needed. It only worked because the state builder lets node-derived
fields win over declared ones.

Then regenerate `examples/demos/meta_map/demo-output.log` with the output
of the validate command below (the file already holds `graph validate`
output; keep that convention).

## Validation

- `yamlgraph graph lint examples/demos/meta_map/graph.yaml` (must report no E007)
- `yamlgraph graph validate examples/demos/meta_map/graph.yaml`
- `pytest tests/unit/test_fr1113_meta_map.py tests/unit/test_fr1119_lint_map_fields.py -q --no-cov`

No real-provider smoke: the change removes one redundant state
declaration and does not alter runtime state (the builder already
creates `_map_verdict` with its reducer). Record the exact outcome of
each command; do not widen the change.

**Prior art:** FR-1119 (governing FR); FR-1116 added the workaround
(`feature-requests/authoring-briefs/fr-1116-meta-map-memo-brief.md`);
FR-1113 created the demo.
