# Authoring brief: FR-1123 book_translator — type three list fields

Governing FR: feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md (judgement R-4 table)

## Task

Modify **exactly three prompt files**, inline `schema:` blocks only:

1. `examples/book_translator/prompts/extract_terms.yaml`: field `terms` `type: list[Any]` → `list[dict]`.
2. `examples/book_translator/prompts/identify_chapters.yaml`: field `markers` `type: list[Any]` → `list[dict]`.
3. `examples/book_translator/prompts/translate_chunk.yaml`: field `difficult_passages` `type: list[Any]` → `list[dict]` (keep `optional: true`).

Nothing else changes: descriptions, optional flags, messages, other fields and the graph stay byte-identical.

Reason: Anthropic constrained decoding rejects the untyped item schema `{}`; FR-1123 refuses it at compile time.

## Validation

- `yamlgraph graph lint examples/book_translator/graph.yaml` must report no E016/W028.
- Smoke: `python -c "from pathlib import Path; from yamlgraph.schema_loader import load_schema_from_yaml as L; from yamlgraph.utils.schema_walk import find_untyped_subschemas as F; ps=sorted(Path('examples/book_translator/prompts').glob('*.yaml')); r={str(p): F(L(p).model_json_schema()) for p in ps if L(p)}; print(r); assert not any(r.values())"`
- Record the exact outcome in the report; do not widen the change.

**Prior art:** FR-1123 (governing), FR-998.
