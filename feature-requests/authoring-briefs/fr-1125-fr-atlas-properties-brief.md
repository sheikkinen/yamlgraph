# Authoring brief: FR-1125 fr-atlas — two prompts declare their theme properties

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, second-wave rows for
`examples/demos/fr-atlas/prompts/chunk_themes.yaml` · `themes.items`
(consumer `graph.yaml#theme_chunks/node`) and
`merge_themes.yaml` · `themes.items` (consumer `graph.yaml#merge_themes`);
disposition option 1).

Repository boundary: **this repository**, target directory
`examples/demos/fr-atlas/prompts/`. The graph is not touched.

## Task

Modify **exactly two files**, replacing each `schema:` block with the
JSON-Schema `output_schema:` form (FR-1054); every other field keeps its
type, description and optionality; templates stay byte-identical; no
`schema:` block remains.

1. `chunk_themes.yaml` — `chunk_id: string` stays required; `themes`
   stays an array with its description and empty-list default; items
   declare `name: string`, `arc: string`, `fr_ids: array of string`,
   all required.
2. `merge_themes.yaml` — `themes` stays an array with its description
   and empty-list default; items declare `name: string`, `arc: string`,
   `merged_from: array of string`, all required.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/demos/fr-atlas/graph.yaml`; after the
  edit, the identical command. The after set must contain no E016,
  E017, W028 or W029.
- `yamlgraph graph validate examples/demos/fr-atlas/graph.yaml`
- `python -m pytest tests/unit -k "atlas or fr1125" -q --no-cov`
- No live smoke by brief (paid provider run). Record "no smoke, by brief".
  The demo's `demo-output.log`, if the CI demo gate requires it, is the
  enforcement's concern, not this run's.

**Prior art:** FR-1125 (governing FR); FR-1054.
