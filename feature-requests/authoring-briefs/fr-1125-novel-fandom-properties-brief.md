# Authoring brief: FR-1125 novel_fandom — six prompts declare their properties; `compare` moves to Mistral

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, second-wave rows under
`examples/novel_fandom/`; operator decisions 2026-09-27: `extract_consequences.ops`
declares the union shape (option 1); `semantic_dedup.merge_map` keeps its
open map and its node moves to Mistral (option 2); the rest are option 1).

Repository boundary: **this repository**, target directory
`examples/novel_fandom/`. Seven files change: six prompts and one graph.

## Task

Prompts: replace each `schema:` block with the JSON-Schema
`output_schema:` form (FR-1054). Every other field keeps its type,
description and optionality; templates stay byte-identical; no
`schema:` block remains in any of the six.

1. `prompts/extract_consequences.yaml` — `ops` items declare
   `op: string` with `enum: [add_event, add_edge, update_valence, invalidate_edge]`
   (required) plus every op-specific field the description names, all
   optional: `id: string`, `window: string`, `participants: array of string`,
   `consequences: array of string`, `references: array of string`,
   `character: string`, `to: string`, `kind: string`, `valence: string`,
   `new_valence: string`. `required: [op]` only. Nothing not in the
   description is added.
2. `prompts/find_plot_path.yaml` and 3. `prompts/fix_plot_path.yaml` —
   `window: string` stays required; `beats` items declare
   `actors: array of string`, `action: string`, `moves_tension: object`
   with `properties` `edge: string`, `toward: string` (both required),
   `references: array of string`; all four required.
4. `prompts/reconcile_threads.yaml` — `threads` items declare
   `id: string`, `kind: string` with `enum: [feud, bond, belief, survival, succession]`,
   `carriers: array of string`, `sources: array of string`,
   `opposition: string`, `stakes: string`, `raises: array of string`,
   `releases: array of string`, `status: string` with
   `enum: [open, escalating, released, latent]`, `justification: string`;
   all required. `dropped` items declare `id: string`, `reason: string`,
   both required.
5. `prompts/threads_from_synopsis.yaml` — `threads` items declare
   `id: string`, `kind: string` (same enum), `carriers: array of string`,
   `opposition: string`, `stakes: string`, `raises: array of string`,
   `releases: array of string`, `status: string` (same enum); all
   required.
6. `prompts/throughlines.yaml` — `throughlines` items declare
   `character: string`, `arc_taut: boolean`, `entries: array` whose
   items declare `event: string`, `emotion: string`, `delta: string`
   with `enum: [gain, loss, none]`, `slack: boolean` (all four
   required); the three top-level keys required.

Graph: `semantic_dedup.yaml`, node `compare` (prompt `semantic_dedup`)
gains one line `provider: mistral` with the comment
`# FR-1125: merge_map is an open map (dropped_id -> surviving_id); Anthropic constrained decoding cannot express it.`
Nothing else in that graph changes; `prompts/semantic_dedup.yaml` is
**not** edited.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint <graph>` for each of `examples/novel_fandom/close.yaml`,
  `find_path.yaml`, `story_extract.yaml`, `semantic_dedup.yaml`; after
  the edit, the identical commands. The after sets must contain no
  E016, E017, W028 or W029.
- `yamlgraph graph validate` on the same four graphs.
- `python -m pytest tests/unit -k "novel or fandom or fr1125" -q --no-cov`
- No live smoke by brief (paid provider runs). Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR; operator decisions recorded in its
Judgement fold); FR-1054 (`output_schema` nested objects and enums);
`fr-1125-questionnaire-provider-brief.md` (the first option-2 precedent).
