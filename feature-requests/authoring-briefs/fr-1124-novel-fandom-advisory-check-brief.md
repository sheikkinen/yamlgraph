# Authoring brief: FR-1124 novel_fandom create_* — advisory check tolerates failure

Governing FR: feature-requests/FR-1124-llm-node-default-on-error.md (S-5 class B; ledger docs/issues-2026-09-27-fr1124-census.md)

## Task

Modify **exactly six graph files**. In each, add one line `on_error: skip` to the top-level `check` node (the `type: llm` node with `prompt: ref_check_entity`), directly after its `state_key: check_result` line, at the same indentation:

1. `examples/novel_fandom/create_character.yaml`
2. `examples/novel_fandom/create_event.yaml`
3. `examples/novel_fandom/create_faction.yaml`
4. `examples/novel_fandom/create_location.yaml`
5. `examples/novel_fandom/create_premise.yaml`
6. `examples/novel_fandom/create_rule.yaml`

Nothing else changes: no other node, edge, comment, state field, prompt or tool is edited. Do not add `defaults.on_error`.

Reason: FR-1124 changes the unset `llm` policy to `fail`. The `check` node runs after `persist` and before `END`. Its prompt header (`examples/novel_fandom/prompts/ref_check_entity.yaml`) says the output is an "advisory ≤2-line verdict". A failed advisory check must not fail an entity creation whose page is already persisted. `skip` records the failure as tolerated and the run ends normally.

## Validation

- `yamlgraph graph lint <file>` for each of the six files. W022 (skip without verification) is an expected warning; record it and do not add a verification block.
- Smoke (no LLM call): `python -c "from yamlgraph.compile.graph_loader import load_graph_config as L; import sys; [print(p, L(p).nodes['check'].get('on_error')) for p in sys.argv[1:]]" examples/novel_fandom/create_{character,event,faction,location,premise,rule}.yaml`. Every line must print `skip`.
- Record the exact outcomes in the report. Do not widen the change.

**Prior art:** FR-1124 (governing), FR-686, FR-689 (the create_* pipelines), FR-1097 (tolerated errors exit 0).
