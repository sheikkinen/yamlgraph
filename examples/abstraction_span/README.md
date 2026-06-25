# Abstraction-span (FR-589)

An LLM estimates a prompt's **abstraction-span** — how many *distinct kinds* of
cognitive operation it asks for in one output — and a **deterministic gate**
decides whether that estimate is trustworthy by checking it reproduces known
monolith/clean labels. If it cannot, the metric is KILLed as a documented null
result.

This example also demonstrates the YAMLGraph **`map` node + `python` tool**
pattern: orchestration lives in `graph.yaml`; Python holds only file I/O and the
deterministic verdict; the single LLM call sits inside the map node.

## Run

```bash
PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
  yamlgraph graph run examples/abstraction_span/graph.yaml --full
```

The run prints a ranking table and the verdict (GO / KILL). Confirm the
`Creating LLM: anthropic/claude-haiku-4-5` log line — the **actual** model is set
by `ANTHROPIC_MODEL`, not a `--model` flag.

## Flow

```
load (python: read corpus)
  └─> score (map: LLM scores each prompt's span)
        └─> verdict (python: deterministic separation gate)
```

- **`load_corpus`** reads `corpus/manifest.yaml`, which references the **live
  plot_modeller prompts by path** (single source of truth — no duplicated bodies),
  and returns `[{name, text, label}]`.
- **`score`** maps over the corpus; for each prompt the `abstraction_span` scorer
  (inline-schema structured output) returns `{level_count, levels, rationale}`.
- **`separation_verdict`** aligns scores to corpus items by `_map_index` and runs
  the gate.

## Ground truth (the labels the LLM must reproduce)

| label | prompts |
|-------|---------|
| monolith | `assign_pre_eff`* `assign_causality` `assign_affects` `extract_agents` |
| boundary | `extract_goals` |
| clean | `extract_glosses` `classify_kinds` |

\* `assign_pre_eff` is the only prompt with a measured L5 failure rate
(FR-585, precision ≈ 0.30) — it must land in the monolith band.

## The Gate (Gate 1 — decides GO/KILL)

**PASS** only when every monolith scores strictly above both clean prompts
(`min(monolith) > max(clean)`, gap ≥ 1), the boundary prompt lands between the
two bands, and the measured-failure anchor sits in the monolith band. Otherwise
**KILL**: the LLM cannot reproduce the hand tagging — keep this example as a
documented null result; static W026 (FR-586) stands. The scorer prompt is tuned
**at most once** (FR-584 fourth-iteration-ritual lesson).

The verdict logic is pure compute and unit-tested without an LLM:
`tests/unit/test_abstraction_span_separation.py`
(`@pytest.mark.req("REQ-YG-020", "REQ-YG-040")`).

## Boundaries

- **No linter integration — permanently.** The metric is a standalone example; the
  `linter-llm-free` import-linter contract (`.importlinter`, FR-588) keeps the LLM
  out of the linter.
- **No build-gating on the score.** The verdict gates only this FR's GO/KILL
  decision, never a merge.
