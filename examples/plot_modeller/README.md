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

## Running it

```bash
# Classify all four synopses and evaluate (resolves provider from PROVIDER env).
PROVIDER=anthropic python examples/plot_modeller/run.py

# A single genre.
PROVIDER=anthropic python examples/plot_modeller/run.py \
  --genre quest-adventure-the-sunken-crown

# Re-score existing results without re-running the model.
python examples/plot_modeller/evaluate.py --provider anthropic

# Lint the graph.
yamlgraph graph lint examples/plot_modeller/graphs/classify_kinds.yaml

# Tests (no API key needed).
pytest examples/plot_modeller/tests/ -q --no-cov
```

The graph hard-codes **no provider or model** — both resolve from the `PROVIDER`
env var at run time, so the spike's model choice is a deployment decision, not a
graph constant.

## Go/no-go gate

| Outcome | Kind accuracy | Action |
|---------|--------------|--------|
| **GO** (optimistic) | ≥75% overall, ≥60% per genre | Proceed to full v5 pipeline |
| **REVISE** | 50–75% overall | Analyze confusions; revise prompt or merge kinds |
| **KILL** | <50% overall or any genre <40% | Redesign approach |

## Measured result (first run) — **GO (optimistic)**

Provider `anthropic`, model `claude-haiku-4-5`, Mode 1, 35 functions. Thresholds
are *triggers*; the verdict rests on the confusion analysis (J3).

| Genre | Kind accuracy |
|-------|---------------|
| Detective thriller | 7/8 (0.88) |
| Quest adventure | 8/8 (1.00) |
| Horror survival | 5/7 (0.71) |
| Sci-fi hybrid | 8/12 (0.67) |
| **Overall** | **28/35 (0.80)** |

Subject accuracy: 24/35 (0.69) — below the 0.90 aspiration; a flag for the
role-assignment layer, not the central bet.

### Confusion analysis

| Expected → Predicted | Genre | Reading |
|----------------------|-------|---------|
| pursuit → provision | detective | chase beat also carried an aid |
| death → villainy | horror | a death framed as the antagonist's act |
| rescue → provision | horror | a rescue read as receiving aid |
| pursuit → recognition | sci-fi | mixed-signal beat |
| reconciliation → rescue | sci-fi | emotional close read as physical save |
| death → victory | sci-fi | a death that resolves the conflict |
| liquidation → villainy | sci-fi | restoration misread as harm |

The errors are **not** concentrated in the vocabulary pairs the prompt warns
about. They cluster around **cause-vs-outcome** distinctions (a `death` or
`liquidation` outcome misread as the `villainy` or `victory` that produced it) —
a coherent, addressable failure mode, not a sign the vocabulary is wrong-shaped.

**Two conditions on the GO (J2/J3):**

1. **Blind-corpus re-test first** — this number is an upper bound on self-derived
   data. Proceed to the full v5 pipeline (FR-571+) only after a synopsis authored
   *without* seeing the target kinds reproduces ≥ 0.75.
2. **Add cause-vs-outcome disambiguation** to the L4 prompt before the re-test,
   targeting the death/villainy and liquidation/victory cluster.

The evaluation YAML files in `results/evaluation/` are the evidence (regenerate
with `run.py`).

## Related

- [FR-570](../../feature-requests/FR-570-plot-modeller-l4-spike.md) — feature request
- [v5 plan](../dungeon_master/docs/plan-v5-yaml-native-planner.md) — pipeline design
- [Inventory](../dungeon_master/docs/inventory-2026-06-23.md) — full project audit
