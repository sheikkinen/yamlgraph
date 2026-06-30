# Compaction Pattern Demo (FR-616)

Demonstrates context compaction using existing YAMLGraph primitives — no custom
node type required.

## Pattern

A storytelling loop that accumulates history, estimates token count, and
conditionally summarizes when the budget is exceeded:

1. **generate_turn** (llm) — appends a new story segment to history
2. **count_tokens** (python) — estimates token count via char/3.5 heuristic
3. **compact** (llm + guard) — summarizes history only when `token_estimate > 400`

The guard's `on_fail: skip` means no LLM call (and no cost) when below threshold.

## Run

```bash
yamlgraph graph run examples/demos/compaction/graph.yaml \
  --var topic="a lighthouse keeper discovering messages in bottles" \
  --full
```

## Key Primitives Used

- **Guards** (`on_fail: skip`) — conditional LLM execution
- **Python tool** — deterministic token estimation
- **Conditional edges** — loop termination via `_loop_counts`
- **List reducer** — accumulating state with `reducer: add`

## See Also

- `reference/compaction-pattern.md` — full pattern documentation
