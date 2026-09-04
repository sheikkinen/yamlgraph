# Authoring brief: FR-984 person-profile census — `config.max_concurrency: 4`

Governing FR: feature-requests/FR-984-map-fan-out-max-concurrency.md

## Task

Modify **exactly two files** under `examples/demos/person_profile_census/`:
`graph.yaml` and `README.md`. No new files, no prompt changes, no node
additions or removals, no tool changes.

`graph.yaml`:

1. Add a top-level `config:` block (FR-027 execution-safety block; the
   framework reads it in `yamlgraph/compile/graph_loader.py`) containing
   exactly one key: `max_concurrency: 4`. If a `config:` block already
   exists, add the key to it; do not alter any existing key.
2. Nothing else changes: `state`, `defaults`, `tools`, every node
   (including the `judge_items` map, its `max_items: 500`, and its
   `on_error: skip`), and `edges` stay byte-identical.

`README.md`:

3. In the corp invocation block, add one line showing the operator
   override: `--max-concurrency 2 \` with a one-sentence note that the
   CLI value overrides the graph's `config.max_concurrency: 4` and that
   the key bounds how many map items run at once (LangGraph
   `RunnableConfig["max_concurrency"]`), not how many items exist
   (`max_items`).
4. Nothing else in the README changes.

## Validation

- `yamlgraph graph lint examples/demos/person_profile_census/graph.yaml`
- Smoke: the README's committed public smoke path (the `SMOKE_ONLY.yaml`
  sed rewrite binding `smoke_preflight.tool.yaml`, source
  `sheikkinen@sheikkinen`, `visibility='["public"]'`,
  `AZURE_MODEL='none-public-smoke'` override) must complete and write
  `demo-output.log`; the log must contain zero corp identifiers. Record
  the exact outcome or blocker in the report; do not widen the change
  to make the smoke pass.

**Prior art:** FR-984-map-fan-out-max-concurrency.md (governing FR — this
brief executes its authorized D-6 graph surface); FR-983 judgement and
FR-030 (Won't Fix) dispositioned there; fr-940-census-labels-model-brief.md
is the format precedent for a two-line census graph edit.
