# Authoring brief: FR-1123 yamlgraph_gen — type three output fields

Governing FR: feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md (judgement R-4 table)

## Task

Modify **exactly three prompt files**, inline output `schema:` blocks only:

1. `examples/yamlgraph_gen/prompts/generate_tools.yaml`: field `tools` `type: list[Any]` → `list[dict]`.
2. `examples/yamlgraph_gen/prompts/assemble_graph.yaml`: output-schema field `node_list` `type: Any` → `list[dict]`. (The `tools:` blocks earlier in this file are example graph text inside the prompt — do not touch them.)
3. `examples/yamlgraph_gen/prompts/generate_prompts.yaml`: field `prompts` `type: Any` → `list[dict]`.

Nothing else changes: descriptions, optional flags, messages, other fields and the graph stay byte-identical.

Reason: Anthropic constrained decoding rejects properties with no type; FR-1123 refuses them at compile time.

## Validation

- `yamlgraph graph lint examples/yamlgraph_gen/graph.yaml` must report no E016/W028.
- Smoke: `python -c "from pathlib import Path; from yamlgraph.schema_loader import load_schema_from_yaml as L; from yamlgraph.utils.schema_walk import find_untyped_subschemas as F; ps=sorted(Path('examples/yamlgraph_gen/prompts').glob('*.yaml')); r={str(p): F(L(p).model_json_schema()) for p in ps if L(p)}; print(r); assert not any(r.values())"`
- Record the exact outcome in the report; do not widen the change.

**Prior art:** FR-1123 (governing), FR-998.
