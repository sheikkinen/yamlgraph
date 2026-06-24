# Feature Request: FR-575 Plot Modeller — L3 extract glosses spike

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — Authority GRANTED (C5–C6 folded; 2026-06-24)
**Effort:** 1.5 days
**Requested:** 2026-06-23
**Plan:** [`plan-implementation-phases.md`](../examples/plot_modeller/docs/plan-implementation-phases.md) Phase 2c
**Predecessor:** FR-574 (L2 extract goals)
**Blocks:** FR-576–FR-578 (L5–L7), FR-579 (merge/pipeline)
**Data dependency:** Synopsis text (L3 reads the synopsis directly, not L2's output; J:N1)
**Scheduling dependency:** FR-574 (risk-control sequence)

## Summary

Build the beat decomposition layer: given a prose synopsis, decompose it into
~7–12 discrete story beats, each with an id, gloss (one-paragraph prose
summary), and chapter number. This is the **creative pivot** — the hardest
extraction layer — because the model must decide where one beat ends and another
begins.

## Value statement

L3 is the hinge of the entire pipeline. Every formalization layer (L4–L7)
operates on glosses. If beat decomposition fails, the whole pipeline fails —
not because the downstream layers are wrong, but because they have nothing
meaningful to work with. The L4 spike (FR-570) proved that classification works
*given good glosses*. L3 must produce those glosses from prose.

## Problem

The L4 spike uses hand-authored glosses extracted from ground-truth plans
(Mode 1). The full pipeline needs glosses extracted from raw prose (Mode 2).
Beat decomposition from narrative prose is a subjective task — two humans may
reasonably disagree on beat boundaries. The evaluation metric must account for
this subjectivity.

## Proposed solution

### Graph: `graphs/extract_glosses.yaml`

Same LLM-validator-retry pattern.

**State keys:**
- `synopsis` (input): prose synopsis
- `glosses_raw` (LLM output): raw YAML text
- `glosses` (validated output): parsed gloss list
- `validation`: `{ok: bool, flaws: list[str]}`

### Prompt: `prompts/extract_glosses.yaml`

Instructions:
1. Read the synopsis and decompose it into discrete story beats
2. A beat is a narrative event where something *changes* — a character acts,
   discovers, decides, suffers, or achieves
3. Each beat gets:
   - `id`: sequential (F1, F2, F3, ...)
   - `gloss`: a one-paragraph prose summary (~30–80 words) capturing the beat's
     essential action, who is involved, and what changes
   - `chapter`: a logical chapter number (group related beats)
4. Aim for 7–12 beats for a ~500-word synopsis
5. Every major plot point should be a beat; minor transitions can be absorbed
   into adjacent beats
6. Output: a YAML list of `{id, gloss, chapter}` objects

The prompt should include guidance on common decomposition errors:
- **Over-splitting:** breaking one beat into setup + execution (merge them)
- **Under-splitting:** combining two independent events into one beat (split them)
- **Missing the pivot:** the beat where the protagonist commits to action is
  often the most important and the most easily missed

### Validator: `validate_glosses` in `nodes/tools.py`

Checks:
1. Output is valid YAML, a list of mappings
2. Each entry has `id`, `gloss`, `chapter`
3. IDs are sequential (F1, F2, ...) with no gaps
4. Glosses are non-empty strings of reasonable length (10–200 words)
5. Chapters are positive integers in non-decreasing order
6. At least 5 beats (a synopsis shorter than 5 beats is suspicious)
7. At most 20 beats (over-splitting)

### Evaluation

Beat matching is the core challenge. Exact string match is too strict (the model
will paraphrase). The evaluation uses **semantic overlap**:

1. For each ground-truth beat, find the extracted beat with the highest semantic
   similarity (by normalized text overlap or embedding cosine, TBD)
2. A match is counted if similarity exceeds a threshold (0.5 for text overlap)
3. Report:
   - **Beat recall:** fraction of ground-truth beats that have a match
   - **Beat precision:** fraction of extracted beats that match a ground-truth beat
   - **Count delta:** |extracted count - ground-truth count| (a structural metric)

The primary gate metric is **beat recall** — every major plot point should
appear in the decomposition.

**Evaluation approach — start simple:** Use normalized token overlap
(`|intersection| / |union|` on lowercased word sets) for the spike. If this
proves too noisy, upgrade to sentence embeddings in a follow-up. The spike's
goal is to measure whether beat decomposition works at all, not to build a
production evaluator.

## Deliverables

| File | What |
|------|------|
| `graphs/extract_glosses.yaml` | L3 graph |
| `prompts/extract_glosses.yaml` | L3 prompt |
| `nodes/tools.py` (extended) | `validate_glosses` function |
| `run.py` (extended) | Mode 2: `--mode extract-glosses` |
| `evaluate.py` (extended) | L3 evaluation (semantic beat matching) |
| `tests/test_l3_validator.py` | Unit tests for `validate_glosses` |
| `results/l3/*.yaml` | Extracted glosses per genre |
| `results/evaluation/l3-summary.yaml` | Beat recall/precision |

## Acceptance criteria

1. `validate_glosses` catches: missing keys, non-sequential IDs, empty glosses,
   out-of-range chapter numbers, too few/many beats
2. L3 graph follows the LLM-validator-retry pattern (max 3 retries)
3. Beat recall ≥ 0.80 across the 5-synopsis corpus (gate metric)
4. No hardcoded provider/model
5. Extracted glosses are valid input for L4 (the `classify_kinds` graph can
   consume them directly — same `{id, gloss, chapter}` shape)
6. Existing tests unchanged

## Go/no-go gate

| Outcome | Beat recall | Action |
|---------|-----------|--------|
| **GO** | ≥ 0.80 | Proceed to FR-576 (L5 pre/eff) |
| **REVISE** | 0.55–0.80 | Analyze mismatches; revise prompt or decomposition strategy |
| **KILL** | < 0.55 *and* incoherent pattern | Re-evaluate beat decomposition approach |

The REVISE band is wider than other layers because beat boundaries are
subjective. A recall of 0.65 with coherent beat structure (beats cover the
right events but at different granularity) is a REVISE, not a KILL. Thresholds
trigger; the analysis decides (J:N2).

## Risk assessment

**Medium-high.** This is the hardest extraction layer. Beat decomposition
requires:

1. **Narrative understanding** — knowing what counts as a "beat"
2. **Granularity judgment** — neither too coarse nor too fine
3. **Boundary placement** — where one beat ends and another begins

The risk is not that the model produces garbage — it is that the model produces
a *different but valid* decomposition that scores poorly against a fixed ground
truth. The evaluation metric must distinguish "different decomposition" from
"wrong decomposition."

**Mitigation:** The semantic overlap metric is deliberately loose. If the
spike shows that the model consistently produces valid decompositions that
don't match ground truth at the beat level but do match at the plot-point
level, that is a measurement problem (need a better metric), not a pipeline
problem (the layer works but the test doesn't see it).

## What this FR does NOT do

- Does not classify beats into kinds (that's FR-570/L4, already done)
- Does not assign pre/eff, causality, or affects (that's FR-576–578)
- Does not use L1/L2 output — the spike reads the synopsis directly
- Does not build a production-quality semantic similarity evaluator — the spike
  uses token overlap as a minimum viable metric

## Judgement (2026-06-24)

**Verdict: GRANTED with conditions.** The best-reasoned of the three — the risk
section explicitly names the "different-but-valid decomposition scores poorly"
measurement hazard and the wider REVISE band answers it. But the metric *as
defined* contradicts that mitigation in two places. Two conditions, both on the
evaluator, not the layer.

### C5 — the matching cardinality is unspecified, and the default breaks the mitigation

Beat recall is "for each ground-truth beat, find the extracted beat with highest
similarity > threshold." If matching is **1:1** (bipartite), then when the model
produces 7 beats against 12 ground-truth beats, at most 7 can match — recall is
structurally capped at 7/12 = 0.58, *below the 0.80 gate*, purely for being
coarser. That is precisely the "valid coarse decomposition punished by the
metric" failure the risk section promises to avoid — but the metric, unspecified,
defaults to producing it. **Fold:** make matching explicitly **many-to-one** — a
single coarse extracted beat that semantically covers two ground-truth beats
counts both as recalled. State this in the evaluator spec; it is the difference
between measuring decomposition quality and measuring count agreement.

### C6 — a 0.5 Jaccard threshold is too high for paraphrase; calibrate it

`|intersection| / |union|` on lowercased word sets between a 40-word gloss and a
semantically-equal paraphrase rarely clears 0.3–0.4 — content words diverge even
when meaning is identical. A 0.5 threshold will reject true matches, deflate
recall, and manufacture false REVISE/KILL outcomes. **Fold:** (a) strip
stopwords before the set operation, and (b) **calibrate** the threshold on one
known-good gloss pair (a ground-truth beat vs a hand-paraphrase of it) *before*
the full run, rather than hardcoding 0.5. The spec already says "start simple" —
starting simple still requires the one anchor measurement that proves the
threshold admits genuine paraphrase.

### Folded

C5 → many-to-one beat matching, stated in the evaluator. C6 → stopword-strip +
calibrate the overlap threshold on a known-good pair. The validator bounds
(5–20 beats, non-decreasing chapters, sequential ids) are excellent falsifiable
checks and need no change. Proceed to Enforce — but write the evaluator's
matching test (C5) as RED first; it is the spike's true measuring instrument,
and a miscalibrated instrument (C6) would have silently produced a wrong KILL.
