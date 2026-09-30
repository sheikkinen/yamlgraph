# Authoring brief: FR-1144 race thinking A/B test bed (image-that-speaks)

Governing FR: feature-requests/FR-1144-race-node-thinking-budget.md (race nodes honour `thinking_budget`; merged as #747)

## Task

Create **exactly two new graph files** beside the existing demo, each a copy of
the existing `examples/demos/image-that-speaks/graph.yaml` that differs from it
only as listed below. Both reuse the demo's existing `prompts/`, `data/` and
`gate.py` unchanged (same directory, so `prompts_relative`, `data_files` and the
tool `path` resolve identically).

1. `examples/demos/image-that-speaks/FR-1144-Thinking.yaml`
   - `name: image-that-speaks-fr1144-thinking`
   - The `image_judges` race node does **not** set `thinking_budget`, and
     `defaults:` does not set it. This is the control arm: gemini-3.5-flash
     uses its provider-default dynamic thinking.
2. `examples/demos/image-that-speaks/FR-1144-No-Thinking.yaml`
   - `name: image-that-speaks-fr1144-no-thinking`
   - The `image_judges` race node sets `thinking_budget: 0` (node level,
     directly after `timeout: 30`). This is the treatment arm.

Allowed differences from `graph.yaml`, and no others:
- `name:` as above.
- `description:` and the header comment may state that the file is one arm of
  the FR-1144 race thinking A/B and name the other arm.
- The header comment's run command must be prefixed with
  `GOOGLE_CLOUD_LOCATION=global` (gemini-3.5-flash returns 404 NOT_FOUND on
  vertex `europe-north1`, the `.env` default; it answers at `global`).
- The single `thinking_budget: 0` line in the No-Thinking arm.
- `image_judges.candidates` in **both** arms is exactly, in this order:
  ```yaml
      - provider: vertex
        model: gemini-3.5-flash
      - provider: azure
        model: aaa-gpt-5.4-mini
  ```
  (The original google/openai pair cannot run here: `GOOGLE_API_KEY` returns
  `API_KEY_INVALID`. Probe 2026-09-30: vertex gemini-3.5-flash @ global,
  budget unset 3.7s / 203 reasoning tokens, budget 0 2.4s / none; azure
  aaa-gpt-5.4-mini 0 reasoning tokens either way.)

The two files already exist from a previous run of this brief with the old
candidates; modify them in place to match this brief.

Do not change models of other nodes, temperatures, timeouts, prompts, edges,
tools, state or data. Do not edit `graph.yaml`, `prompts/*`, `gate.py` or `data/*`.

Constraint (do not work around it): an explicit `thinking_budget` of 1024 or more
is **not** a valid Thinking arm. `yamlgraph/utils/llm_factory.py` raises for
budgets >=1024 on providers outside `THINKING_PROVIDERS`, which would disarm the
azure candidate. The Thinking arm therefore leaves the field unset.

## Validation

```bash
yamlgraph graph lint examples/demos/image-that-speaks/FR-1144-Thinking.yaml
yamlgraph graph lint examples/demos/image-that-speaks/FR-1144-No-Thinking.yaml
diff examples/demos/image-that-speaks/graph.yaml examples/demos/image-that-speaks/FR-1144-Thinking.yaml
diff examples/demos/image-that-speaks/graph.yaml examples/demos/image-that-speaks/FR-1144-No-Thinking.yaml
```

- Lint: record every warning verbatim. The original `graph.yaml` lint output is
  the baseline; no new warning class may appear.
- Diff: record both diffs. Only the allowed differences may appear.
- No-LLM check that the budget reaches the race node config:
  `python -c "from yamlgraph.compile.graph_loader import load_graph_config as L; import sys; [print(p, L(p).nodes['image_judges'].get('thinking_budget')) for p in sys.argv[1:]]" examples/demos/image-that-speaks/FR-1144-Thinking.yaml examples/demos/image-that-speaks/FR-1144-No-Thinking.yaml`
  must print `None` for Thinking and `0` for No-Thinking.
- Live runs are **out of scope** for this brief; the requesting session runs the
  A/B measurement afterwards.

**Prior art:** FR-666 (image-that-speaks demo), FR-232 (race node), FR-272
(router race candidates), FR-1144 (race `thinking_budget`).
