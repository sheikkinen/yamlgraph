# Authoring brief: FR-1125 ramp_rtm — `derive_reqs` declares its entry properties

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, second-wave row for
`examples/demos/ramp_rtm/prompts/derive_reqs.yaml` · `entries.items`,
consumer `graph.yaml#derive/node`; disposition option 1).

Repository boundary: **this repository**, target directory
`examples/demos/ramp_rtm/prompts/`. The graph is not touched.

## Task

Modify **exactly one file**: `derive_reqs.yaml`. Replace its `schema:`
block with the JSON-Schema `output_schema:` form (FR-1054). `path:
string` stays required; `entries` stays an array with its description
and empty-list default; its items declare exactly the description's
keys, all required: `req_id: string`, `statement: string`,
`witness_tests: array of string`, `confidence: number`,
`status: string` with `enum: [proposed]` (the description says "exactly
proposed"). Templates stay byte-identical. No `schema:` block remains.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/demos/ramp_rtm/graph.yaml`; after the
  edit, the identical command. The after set must contain no E016,
  E017, W028 or W029 (`tests/unit/test_ramp_tailoring.py` asserts lint
  is clean).
- `yamlgraph graph validate examples/demos/ramp_rtm/graph.yaml`
- `python -m pytest tests/unit -k "ramp or fr1125" -q --no-cov`
- No live smoke by brief (paid provider run). Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR); FR-1054.
