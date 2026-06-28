# Gate 1 result — GO (PASS)

Measurement artifact for FR-589. Produced by:

```bash
PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
  yamlgraph graph run examples/abstraction_span/graph.yaml --full
```

Model (verified from the run log): `Creating LLM: anthropic/claude-haiku-4-5`.
Date: 2026-06-24. One scorer iteration (no retuning).

```
=== Abstraction-span separation gate ===
span  label      prompt
----  ---------  ------
   8  monolith   assign_pre_eff
   7  monolith   assign_affects
   5  monolith   assign_causality
   5  monolith   extract_agents
   4  boundary   extract_goals
   4  clean      extract_glosses
   3  clean      classify_kinds

min(monolith)=5  max(clean)=4  gap=1  goals_between=True  anchor_in_band=True
Verdict: GO (PASS)
```

## Reading

- Every labelled monolith (5, 5, 7, 8) scores strictly above every clean prompt
  (4, 3): `min(monolith)=5 > max(clean)=4`, gap = 1 (the minimum required).
- The measured-failure anchor `assign_pre_eff` (FR-585, precision ≈ 0.30) ranks
  **highest** (span 8) — the prompt that empirically overloads the model also reads
  as the most abstraction-fused.
- The boundary prompt `extract_goals` (4) lands in the gap, tying the clean ceiling
  but strictly below the monolith floor.

The LLM reproduces the hand tagging on the first iteration: the abstraction-span
metric **separates** the corpus by kind of cognitive work, not by size (recall
line counts do not separate it: `assign_causality` 61 = `extract_goals` 61; clean
`extract_glosses` 58 < monolith `extract_agents` 66). GO.
