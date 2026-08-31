# Authoring brief: FR-940 census graph — labels + model/provider state vars

Governing FR: feature-requests/FR-940-census-judgement-normalization.md

## Task

Modify **exactly one file**: `examples/demos/corpus_census/graph.yaml`.
No new files, no prompt changes, no node additions or removals.

Changes:

1. In the `state:` section, declare three new optional string vars:
   - `model: str`
   - `provider: str`
   - `labels: str`
2. In the `judge_items` map sub-node (`nodes.judge_items.node`), replace
   the pinned `provider: anthropic` / `model: claude-haiku-4-5` with:
   - `provider: "{state.provider}"`
   - `model: "{state.model}"`
3. In the `synthesize` node, make the same replacement:
   - `provider: "{state.provider}"`
   - `model: "{state.model}"`
4. Keep `defaults:` exactly as is (`provider: anthropic`,
   `model: claude-haiku-4-5`, `temperature: 0.0`). The framework
   (FR-940 core enablement, already present in this working tree)
   resolves the `{state.x}` references at execution time and falls
   back to these defaults when the state key is missing or empty.
5. Nothing else changes: tools, edges, config, other nodes, and the
   `reduce_ledger` node stay byte-identical. `labels` is consumed by
   the `reduce_ledger` Python tool directly from state — no node
   wiring needed beyond the state declaration.

## Validation

- `yamlgraph graph lint examples/demos/corpus_census/graph.yaml`
- Smoke: run the fixture invocation from the repo root of this working
  tree WITHOUT `--var model/provider/labels` — the default chain must
  resolve to anthropic/claude-haiku-4-5 and the run must complete and
  write the ledger + brief artifacts:

```bash
yamlgraph graph run examples/demos/corpus_census/graph.yaml --tool discover=examples/demos/corpus_census/fixtures/discover.tool.yaml --tool extract=examples/demos/corpus_census/fixtures/extract.tool.yaml --var source=examples/demos/corpus_census/fixtures/corpus --var rubric="classify each document's main topic in one word" --var output_path=tmp/fr940-smoke-ledger.md --var brief_path=tmp/fr940-smoke-brief.md --var brief_rubric="What does this corpus cover overall?"
```

**Prior art:** FR-940-census-judgement-normalization.md (governing FR — this brief executes its authorized graph surface); FR-940 judgement + FR-892/FR-895 census precedent dispositioned there.
