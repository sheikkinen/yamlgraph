# Authoring brief: FR-1125 icpc-2-rfe — `reason_cluster` declares its candidate properties

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, second-wave row for
`examples/icpc-2-rfe/prompts/reason_cluster.yaml` · `candidates.items`,
consumer `examples/icpc-2-rfe/graph.yaml#classify_clusters/node`;
disposition option 1, keys named by the field's own description).

Repository boundary: **this repository**, target directory
`examples/icpc-2-rfe/prompts/`. The graph is not touched.

## Task

Modify **exactly one file**: `reason_cluster.yaml`. Replace its `schema:`
block with the JSON-Schema `output_schema:` form (FR-1054). `candidates`
stays an array with its description and its default of an empty list;
its items declare exactly the description's keys, all required:
`code: string`, `title: string`, `verdict: string` with
`enum: [match, partial_match, not_applicable]`, `confidence: number`,
`reasoning_short: string`, `evidence_spans: array of string`,
`missing_signals: array of string`. Every other field keeps its type,
description and optionality. Templates stay byte-identical. No
`schema:` block remains.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/icpc-2-rfe/graph.yaml`; after the edit,
  the identical command. The after set must contain no E016, E017, W028
  or W029.
- `yamlgraph graph validate examples/icpc-2-rfe/graph.yaml`
- `python -m pytest tests/unit -k "icpc or fr1125" -q --no-cov`
- No live smoke by brief (paid provider run). Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR); FR-1054; the sibling brief for
`examples/cwe-classifier`.
