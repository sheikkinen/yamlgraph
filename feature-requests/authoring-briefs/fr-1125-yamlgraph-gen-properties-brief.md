# Authoring brief: FR-1125 yamlgraph_gen — three prompts declare their object properties

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, rows for
`examples/yamlgraph_gen/prompts/`; this brief closes that directory's
authoring run).

Repository boundary: **this repository**, target directory
`examples/yamlgraph_gen/prompts/`. `examples/yamlgraph_gen/graph.yaml`
is not touched (nodes `assemble_graph`, `generate_prompts`,
`generate_tools`, Anthropic by default).

## Task

Modify **exactly three files**, replacing each `schema:` block with the
JSON-Schema `output_schema:` form (FR-1054). Every other field keeps its
type and description; only the open-object fields gain declared
`properties`, taken verbatim from each field's own description.
Templates stay byte-identical.

1. `assemble_graph.yaml` — `graph_yaml: string` stays required;
   `node_list` items declare `name: string`, `type: string`,
   `prompt_path: string` (the description's `[{name, type, prompt_path}]`),
   all three required.
2. `generate_prompts.yaml` — `prompts` items declare `filename: string`,
   `content: string`, `explanation: string` (the description's
   `{filename, content, explanation}`), all three required.
3. `generate_tools.yaml` — `tools` items declare `filename: string`,
   `content: string`, `tool_name: string`, `description: string` (the
   description's four keys), all four required; the array's description
   keeps "Empty list if only built-in tools." `uses_builtin_websearch:
   boolean` stays required.

No `schema:` block remains in any of the three files; no property is
added that the description does not name.

Related artifacts edited by the FR's enforcement, not by this run:
`tests/unit/test_fr1123_prompt_census.py` (R4 expectations for
`generate_tools.tools`, `assemble_graph.node_list`,
`generate_prompts.prompts`) and the FR-1125 ledger.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/yamlgraph_gen/graph.yaml`; after the
  edit, the identical command. The after set must contain no E016,
  E017, W028 or W029.
- `yamlgraph graph validate examples/yamlgraph_gen/graph.yaml`
- `python -m pytest tests/unit -k "fr1123 or fr1125 or yamlgraph_gen" -q --no-cov`
- No live smoke: the generator's full run is a paid provider run and is
  not authorised by this brief. Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR); FR-1123 (retyped these fields to
`list[dict]` today); FR-1054 (`output_schema` nested objects).
