# Authoring brief: FR-1125 req_witness_audit — `audit_batch` declares its verdict properties

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, row for
`examples/demos/req_witness_audit/prompts/audit_batch.yaml`; this brief
closes that directory's authoring run).

Repository boundary: **this repository**, target directory
`examples/demos/req_witness_audit/prompts/`. The graph
(`examples/demos/req_witness_audit/graph.yaml`, `defaults.provider:
anthropic`, map `audit_batches` with an `llm` sub-node) is not touched.

## Task

Modify **exactly one file**: `audit_batch.yaml`. Replace its `schema:`
block with the JSON-Schema `output_schema:` form (FR-1054). `verdicts`
stays an array, required, with its description; its items declare
exactly the four keys the description names, all required:
`req_id: string` ("copied verbatim"), `witnessed: string` (the
description's closed set `yes`, `partial`, `no` — declare it as
`enum: [yes, partial, no]`, which is the description's own contract, not
an invention), `gap: string` ("one sentence"), `suggestion: string`
("one sentence"). Templates stay byte-identical.

Related artifacts edited by the FR's enforcement, not by this run: the
FR-1125 ledger and any focused test under `tests/unit/` for this demo
that pins the prompt's field types.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/demos/req_witness_audit/graph.yaml`;
  after the edit, the identical command. The after set must contain no
  E016, E017, W028 or W029.
- `yamlgraph graph validate examples/demos/req_witness_audit/graph.yaml`
- `python -m pytest tests/unit -k "req_witness or fr1125" -q --no-cov`
- No live smoke by brief (paid provider run). Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR); FR-1054 (`output_schema` nested
objects and enums); the demo's own FR for the verdict contract.
