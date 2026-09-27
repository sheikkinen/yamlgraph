# Authoring brief: FR-1123 codegen — type five output fields

Governing FR: feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md (judgement R-4 table)

## Task

Modify **exactly two prompt files**, inline output `schema:` blocks only:

1. `examples/codegen/prompts/plan_discovery.yaml`: field `tasks` `type: Any` → `list[dict]`.
2. `examples/codegen/prompts/synthesize.yaml`:
   - `target_files` `type: Any` → `list[dict]`
   - `dependencies` `type: Any` → `list[str]`
   - `test_coverage` `type: Any` → `dict`
   - `patterns_to_follow` `type: Any` → `list[str]`

Nothing else changes: descriptions, optional flags, messages, other fields and graphs stay byte-identical.

Reason: Anthropic constrained decoding rejects properties with no type; FR-1123 refuses them at compile time.

## Validation

- `yamlgraph graph lint examples/codegen/impl-agent.yaml` must report no E016/W028.
- Smoke: `python -c "from pathlib import Path; from yamlgraph.schema_loader import load_schema_from_yaml as L; from yamlgraph.utils.schema_walk import find_untyped_subschemas as F; ps=sorted(Path('examples/codegen/prompts').glob('*.yaml')); r={str(p): F(L(p).model_json_schema()) for p in ps if L(p)}; print(r); assert not any(r.values())"`
- Record the exact outcome in the report; do not widen the change.

**Prior art:** FR-1123 (governing), FR-998.
