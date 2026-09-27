# Authoring brief: FR-1125 book_translator — three prompts declare their object properties

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, rows for
`examples/book_translator/prompts/`; this brief closes that directory's
authoring run).

Repository boundary: **this repository**, target directory
`examples/book_translator/prompts/`. `examples/book_translator/graph.yaml`
is not touched (its `defaults.provider: anthropic` stays; the three
nodes are `identify_chapters`, and the map sub-nodes of
`extract_glossary` and `translate_all`).

## Task

Modify **exactly three files**, replacing each `schema:` block (the
`fields` form) with the JSON-Schema `output_schema:` form (FR-1054).
Every other field keeps its type, description and optionality; only the
open-object fields gain declared `properties`, taken verbatim from each
field's own description. Templates stay byte-identical.

1. `identify_chapters.yaml` — `markers` items declare
   `marker: string` ("exact text string (20-50 chars) from document"),
   `title: string` ("short description of this section"),
   `estimated_size: integer` ("approximate character count"); all three
   required. `total_sections: integer` and `document_type: string` stay,
   both required.
2. `extract_terms.yaml` — `terms` items declare `source_term: string`,
   `translation: string`, `context: string`, `importance: string` (the
   description's four keys; `importance` is described nowhere as a
   number, so it stays a string), all four required.
3. `translate_chunk.yaml` — `text: string`, `original: string`,
   `confidence: number` stay required; `translator_notes: array of
   string` stays optional; `difficult_passages` stays optional and its
   items declare `original: string` and `issue: string`, both required.
   Optionality is expressed by omission from the top-level `required`
   list, as FR-1054 documents.

No `schema:` block remains in any of the three files; no property is
added that the description does not name.

Related artifacts edited by the FR's enforcement, not by this run:
`tests/unit/test_fr1123_prompt_census.py` (R4 expectations for
`extract_terms.terms`, `identify_chapters.markers`,
`translate_chunk.difficult_passages`) and the FR-1125 ledger.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/book_translator/graph.yaml`; after the
  edit, the identical command. The after set must contain no E016,
  E017, W028 or W029.
- `yamlgraph graph validate examples/book_translator/graph.yaml`
- `python -m pytest tests/unit -k "fr1123 or fr1125" -q --no-cov`
- No live smoke: the translator's full run is a paid provider run and
  is not authorised by this brief. Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR); FR-1123 (the run that retyped
these three fields to `list[dict]` today, now superseded by the
spike's finding); FR-1073 H-2 rows 5–7 (the same graph's map nodes);
FR-1054 (`output_schema` nested objects).
