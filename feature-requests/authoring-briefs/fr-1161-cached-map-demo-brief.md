# FR-1161 cached_map demo

Governing FR: `feature-requests/FR-1161-cached-map-warm-first.md` (read § Documentation and example and `reference/graph-yaml.md` § `type: cached_map`).

**Prior art:** `fr-1011-relocate-chaplain-live-parts-brief.md` matches only on the words "cached" and "brief". It relocates the chaplain's live parts and shares no artifact with this demo; not precedent.

Create `examples/demos/cached_map/` showing the new `type: cached_map` node:

- `graph.yaml`: one `cached_map` node `review` over `{state.items}` (4 short strings supplied as a default list in state or via `--var`), `as: item`, whose sub-node is `type: llm` with provider `anthropic`, model `claude-haiku-5-5`, `max_tokens` 16 or similar small value, `state_key: answer`, `collect: answers`. Then END. Keep it minimal; no other nodes are needed.
- Create `examples/demos/cached_map/prompts/review.yaml`: a prompt with `system_segments` whose first segment has `cache: true` and holds a long shared rules block (at least ~2,500 tokens, e.g. 50 numbered rules, so it is above Haiku's cache minimum); the user turn is the short per-item text `{{ item }}`. Follow the existing prompt YAML conventions (`reference/prompt-yaml.md`); find a precedent graph using `system_segments` with `cache: true` first.
- `README.md`: what the demo shows (item 0 runs alone and writes the prompt cache; items 1..3 run together and read it), how to run it, and the expected `--token-usage` cache read/write lines.
- `demo-output.log`: the output of ONE real run of
  `yamlgraph graph run examples/demos/cached_map/graph.yaml --token-usage` (requires `ANTHROPIC_API_KEY`). Run it exactly once; do not retry on success. It must show a cache write and cache read count on the `--token-usage` line.
- Add one line for the demo to `examples/README.md` in the demos index, matching neighbouring entries.

Validate with:

```bash
yamlgraph graph lint examples/demos/cached_map/graph.yaml
yamlgraph graph run examples/demos/cached_map/graph.yaml --token-usage
```

Spend ceiling: a single run (8 Haiku calls at most). Do not modify any file outside `examples/demos/cached_map/` and `examples/README.md`.
