# Plot Modeller — L4 Kind-Classification Spike (FR-570)

Standalone YAMLGraph example that tests whether a small model can classify prose
glosses into the 16-kind Propp-derived action alphabet.

## What it does

1. Extracts beat glosses from hand-authored ground-truth plans (Mode 1: isolate L4)
2. Sends glosses to an LLM with the 16-kind vocabulary in-prompt
3. Validates the LLM's YAML output (kind ∈ vocab, subject present, all glosses covered)
4. Retries on validation failure (max 3 attempts)
5. Evaluates accuracy against ground truth across 4 genre synopses

## Structure

```
graphs/classify_kinds.yaml     # LLM → validator → retry loop
prompts/classify_kinds.yaml    # 16-kind vocab + YAML output spec
nodes/tools.py                 # validate_kinds, load_glosses, load_synopsis
evaluate.py                    # CLI: compare results to ground truth
fixtures/                      # Frozen corpus (4 synopses + 4 ground-truth plans)
results/                       # Pipeline output (gitignored)
tests/                         # Validator + evaluator tests
```

## Test corpus

| Synopsis | Functions | Kinds exercised |
|----------|-----------|----------------|
| Detective thriller | 8 | villainy, lack, pursuit, donor_test, provision, exposure, recognition, punishment |
| Quest adventure | 8 | lack, departure, donor_test, provision, struggle, victory, return, liquidation |
| Horror survival | 7 | villainy, departure, pursuit, death, struggle, rescue, return |
| Sci-fi hybrid | 12 | villainy, lack, departure, donor_test, provision, pursuit, recognition, struggle, reconciliation, death, return, liquidation |

35 glosses covering 15 of 16 kinds. Corpus is **self-derived** (upper bound) —
see `fixtures/README.md` for details.

## Go/no-go gate

| Outcome | Kind accuracy | Action |
|---------|--------------|--------|
| **GO** (optimistic) | ≥75% overall, ≥60% per genre | Proceed to full v5 pipeline |
| **REVISE** | 50–75% overall | Analyze confusions; revise prompt or merge kinds |
| **KILL** | <50% overall or any genre <40% | Redesign approach |

## Related

- [FR-570](../../feature-requests/FR-570-plot-modeller-l4-spike.md) — feature request
- [v5 plan](../dungeon_master/docs/plan-v5-yaml-native-planner.md) — pipeline design
- [Inventory](../dungeon_master/docs/inventory-2026-06-23.md) — full project audit
