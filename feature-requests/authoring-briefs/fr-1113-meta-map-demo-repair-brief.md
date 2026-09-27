# Authoring brief: FR-1113 meta-map demo — repair: poison declared once

Governing FR: feature-requests/FR-1113-meta-map-demo.md
Parent brief: feature-requests/authoring-briefs/fr-1113-meta-map-demo-brief.md

## Task

Edit exactly one file: `examples/demos/meta_map/graph.yaml`.

1. Delete the `init_poison` passthrough node. It duplicates the list in
   `poison.yaml`, so the graph declares the poison twice.
2. Replace the edges `START → init_poison` and `init_poison → discover`
   with a single `START → discover` edge.

Keep everything else byte-identical, including `data_files: poison:
poison.yaml`, `state.poison`, and every other node and edge. Do not
edit `poison.yaml`, the subgraph, the prompts, `tools.py` or the tests.

Why the passthrough is unnecessary: the CLI merges `data_files` into
the initial state (`yamlgraph/cli/graph_run_helpers.py`,
`_build_run_config`). The unit test harness now merges
`load_graph_config(...).data` the same way, so a raw `invoke` sees
`state.poison` without a graph node.

## Validation

- `yamlgraph graph lint examples/demos/meta_map/graph.yaml`
- `pytest tests/unit/test_fr1113_meta_map.py -q --no-cov` — all tests
  must pass, including `test_poison_declared_once_in_data_file`.
- No LLM smoke is needed for this edit; the enforcing session re-runs
  the real smoke for `demo-output.log` afterwards. Record it under
  Blocked validation as deferred to the enforcing session.

**Prior art:** the parent brief; `examples/demos/data-files/graph.yaml`
(`data_files` with no seeding node).
