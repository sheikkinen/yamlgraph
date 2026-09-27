# Authoring brief: FR-1123 daily_digest — type `rank_stories.stories`

Governing FR: feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md (judgement R-4 table)

## Task

Modify **exactly one prompt file**: `examples/daily_digest/prompts/rank_stories.yaml`.

1. In its inline `schema:` block, change the `stories` field's `type:` from `list[Any]` to `list[dict]`.
2. Nothing else changes: description, optional flags, messages, other fields and the graph stay byte-identical.

Reason: Anthropic constrained decoding (`json_schema`) rejects the untyped item schema `{}` produced by `list[Any]`; FR-1123 now refuses it at compile time.

## Validation

- `yamlgraph graph lint examples/daily_digest/graph.yaml` must report no E016/W028.
- Smoke: `python -c "from pathlib import Path; from yamlgraph.schema_loader import load_schema_from_yaml as L; from yamlgraph.utils.schema_walk import find_untyped_subschemas as F; p=Path('examples/daily_digest/prompts/rank_stories.yaml'); r=F(L(p).model_json_schema()); print(p, r); assert r == []"`
- Record the exact outcome in the report; do not widen the change.

**Prior art:** FR-1123 (governing), FR-998 (introduced json_schema default), FR-905 (digest formatter).
