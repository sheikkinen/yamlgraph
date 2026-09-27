# Authoring brief: FR-1125 cwe-classifier — `reason_cluster` declares its candidate properties

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, second-wave row for
`examples/cwe-classifier/prompts/reason_cluster.yaml` · `candidates.items`,
consumer `examples/cwe-classifier/graph.yaml#classify_clusters/node`;
disposition option 1, keys named by the field's own description).

Repository boundary: **this repository**, target directory
`examples/cwe-classifier/prompts/`. The graph is not touched.

## Task

Modify **exactly one file**: `reason_cluster.yaml`. Replace its `schema:`
block with the JSON-Schema `output_schema:` form (FR-1054). `candidates`
stays an array with its description and its default of an empty list;
its items declare exactly the description's keys, all required:
`code: string`, `title: string`, `verdict: string` with
`enum: [match, partial_match, not_applicable]` (the description's closed
set), `confidence: number`, `reasoning_short: string`,
`evidence_spans: array of string`, `missing_signals: array of string`.
Every other field in the schema keeps its type, description and
optionality. Templates stay byte-identical. No `schema:` block remains.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/cwe-classifier/graph.yaml`; after the
  edit, the identical command. The after set must contain no E016,
  E017, W028 or W029.
- `yamlgraph graph validate examples/cwe-classifier/graph.yaml`
- `python -m pytest tests/unit -k "cwe or fr1125" -q --no-cov`
- No live smoke by brief (paid provider run). Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR; second-wave ledger rows after the
census was made host-independent); FR-1054 (`output_schema` nested
objects and enums); the sibling brief for `examples/icpc-2-rfe`, whose
prompt has the same shape.
