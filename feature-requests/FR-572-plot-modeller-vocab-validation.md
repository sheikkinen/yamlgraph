# Feature Request: FR-572 Plot Modeller — Vocabulary validation + blind-corpus re-test

**Priority:** HIGH (KILL gate)
**Type:** Feature
**Status:** Enforced — GO (blind 0.90, overall 39/48 = 0.81; 2026-06-23)
**Effort:** 1 day
**Requested:** 2026-06-23
**Plan:** [`plan-implementation-phases.md`](../examples/plot_modeller/docs/plan-implementation-phases.md) Phase 1
**Predecessor:** FR-571 (schema extraction)
**Blocks:** FR-573–FR-580 (all pipeline construction is conditional on this GO)

## Summary

Validate the refined 17-kind / 6-affect vocabulary empirically: retrofit the 4
existing ground-truth plans with `mediation`, `hope`, and relational `toward`;
author one blind synopsis (written without seeing the kind list); run L4
classification against all 5; produce a go/no-go verdict for the full pipeline.

**This is the project's KILL gate.** No pipeline construction (FR-573+) begins
until this FR returns GO.

## Value statement

The L4 spike (FR-570) measured 0.80 on self-derived data — an upper bound. The
vision cross-check added `mediation` (17th kind) and `hope` (6th affect) based
on Todorov and OCC/MEXICA, but neither has been tested. This FR produces the
second measured number — on naturalistic data — before committing to ~2000 lines
of pipeline code.

## Problem

Three untested additions:
1. `mediation` — added by cross-check, never classified by L4
2. `hope` — added by cross-check, never exercised in a ground-truth plan
3. Relational `toward` on affects — designed, never used in any plan

And one unanswered question: does the 0.80 generalise beyond self-derived data?
The glosses were written knowing their labels. A blind synopsis — authored
without seeing the 17 kinds — is the real test.

## Proposed solution

### Phase 1a — Retrofit ground truth

**Step 0 (precondition, J:C4) — fix the affect model in vision.md first.**
[vision.md](../examples/plot_modeller/docs/vision.md) currently lists `hope`'s
closers as `betrayal, death, loss` — but `betrayal` and `loss` are *affect
kinds*, not *beats*, and the open/close model says affects are opened and closed
by **function beats** (review D4). No pipeline output emits a `betrayal`, so
"betrayal closes hope" is unsatisfiable. Before any fixture is touched, correct
vision.md so hope's closers name **beats** (`villainy`, `death`, `exposure`).
The retrofit below must encode that one consistent model — otherwise the ground
truth bakes in the contradiction.

Update the 4 existing YAML plans in `fixtures/ground-truth/`:

1. **Split `lack` → `lack` + `mediation`** where the gloss combines "hero
   discovers the problem" and "hero decides to act." This may add 1–2 functions
   per plan or reclassify existing ones.

2. **Add `hope` affect threads** where provision, donor_test, or rescue opens
   positive anticipation. Add the corresponding `op: close` on beats that
   destroy hope (villainy, death, exposure).

3. **Add `toward`** on existing affect operations where the emotion is
   relational (guilt *toward* someone, betrayal *toward* someone).

4. **Update `prompts/classify_kinds.yaml`** to include `mediation` as the 17th
   kind with its definition and a confusion-pair note (mediation vs. lack).

5. **Re-run L4** on the updated corpus to verify the self-derived score holds
   (≥ 0.75) with the expanded vocabulary.

### Phase 1b — Blind-corpus re-test

1. **Author one synopsis** (~500 words) without the 17-kind list visible.
   Write a story seed — characters, conflict, resolution — in a genre not yet
   represented (e.g., romance, comedy, historical, literary fiction). The author
   must not consult the vocabulary during synopsis writing.

2. **Hand-author the ground-truth plan** using the 17 kinds (now visible). This
   is the control: the human classifies correctly, then the model tries.

3. **Run L4** against the blind synopsis's glosses.

4. **Evaluate** using `evaluate.py` with the blind plan as ground truth.

### Deliverables

| File | What |
|------|------|
| Corrected `docs/vision.md` | hope's closers named as beats, not affect kinds (J:C4 / review D4) — done before the retrofit |
| Updated `fixtures/ground-truth/*.yaml` (4 files) | Retrofitted: mediation beats, hope threads, toward |
| `fixtures/synopses/<blind>.txt` | 5th synopsis (blind — authored without kind list) |
| `fixtures/ground-truth/<blind>.yaml` | 5th ground-truth plan |
| Updated `prompts/classify_kinds.yaml` | 17 kinds (mediation added + confusion note) |
| `results/evaluation/*-eval.yaml` (5 files) | L4 accuracy per genre (all 5, re-run) |
| `results/evaluation/summary.yaml` | Overall verdict with blind vs. self-derived split |

### Evaluation output

```yaml
# results/evaluation/summary.yaml
corpus:
  self_derived:
    genres: 4
    total: N           # may change if mediation splits add functions
    kind_accuracy: "M/N (0.XX)"
  blind:
    genres: 1
    total: K
    kind_accuracy: "J/K (0.XX)"
    corpus: blind (naturalistic)
  overall:
    kind_accuracy: "(M+J)/(N+K) (0.XX)"
verdict: GO | REVISE | KILL
conditions:
  - "blind-corpus ≥ 0.75 for GO"
  - "self-derived ≥ 0.75 for GO (directional check, not a delta vs FR-570 —
     denominators differ once mediation splits change N; J:C5)"
  - "borderline blind score 0.45–0.60 defaults to REVISE, never KILL; only a
     clear collapse (<0.45 with an incoherent confusion pattern) may KILL (J:C3)"
note: >
  Thresholds are triggers; the REVISE-vs-KILL call rests on the confusion
  analysis, not the bare number (J3 from FR-570). The blind corpus is n=1 — a
  single synopsis is ~8–12 functions, so five misclassifications flip the
  verdict; the borderline-REVISE rule guards against a high-variance KILL.
```

## Acceptance criteria

1. All 4 retrofitted plans parse into `PlotPlan` (FR-571 schema) without error
2. At least 2 plans contain a `mediation` function
3. At least 2 plans contain a `hope` affect thread
4. At least 3 plans use relational `toward` on at least one affect operation
5. The blind synopsis was authored without the kind list visible (stated in
   `fixtures/README.md` — the honesty is in the process, not verifiable by CI)
6. L4 accuracy on the self-derived corpus (with mediation) ≥ 0.75, reported as a
   **directional sanity check** alongside FR-570's 0.80 — not a regression
   delta, since the `lack → lack + mediation` split changes N; both denominators
   are shown side by side, not hidden inside a single ratio (J:C5)
7. L4 accuracy on the blind corpus is measured and reported
8. The summary verdict is one of GO / REVISE / KILL with the confusion analysis;
   a borderline blind score (0.45–0.60) yields REVISE, not KILL (J:C3)
9. vision.md's hope closers name beats, not affect kinds, *before* the fixtures
   are retrofitted (J:C4 / review D4)

## Go/no-go gate

| Outcome | Blind accuracy | Self-derived accuracy | Action |
|---------|---------------|----------------------|--------|
| **GO** | ≥ 0.75 | ≥ 0.75 | Proceed to FR-573 (L1 extraction) |
| **REVISE** | 0.45–0.75 | any | Analyze confusions; revise prompt or merge confused kinds; re-run this FR |
| **KILL** | < 0.45 *and* incoherent confusion pattern | any | Stop pipeline construction; redesign vocabulary, prompt, or approach |

The KILL band is deliberately narrow (J:C3): with an n=1 blind corpus of ~8–12
functions, a bare score near 0.50 is within sampling noise. A KILL requires
*both* a clear collapse (< 0.45) *and* a confusion pattern that does not point
to a fixable cluster — otherwise the outcome is REVISE. A REVISE loops back to
this FR (revise and re-test). A KILL halts FR-573–FR-580 and redirects to a
different approach (larger model, two-step classification, vocabulary
reduction, or abandon layered pipeline).

## What this FR does NOT do

- Does not build any pipeline layers (that's FR-573+)
- Does not modify the schema (that's FR-571)
- Does not test L1–L3, L5–L7 — only L4 classification
- Does not add the `mediation` prompt guidance for cause-vs-outcome (FR-570
  identified this cluster; this FR adds `mediation` but the disambiguation
  paragraph is a prompt refinement, done here if needed)

## Judgement (2026-06-23)

**Verdict: GRANTED with conditions.** This is the project's KILL gate and it is
structured correctly — thresholds as triggers, confusion analysis as the real
decision (J3 inherited from FR-570). Three conditions.

### C3 — one blind plan is a statistically weak basis for a KILL (strengthen it)

A single blind synopsis yields ~8–12 functions. At the 0.50 KILL threshold,
**five misclassifications flip the verdict.** A KILL halts FR-573–FR-580 — an
expensive, hard-to-reverse decision resting on a high-variance n=1 sample.
Require **either**:

- **two** blind synopses in different genres (≈ doubles the sample, halves the
  variance), **or**
- an explicit variance caveat in the verdict: a borderline blind score
  (0.45–0.60) defaults to **REVISE**, never **KILL** — only a clear collapse
  (< 0.45 *with* an incoherent confusion pattern) may KILL.

The second is cheaper and consistent with FR-570's "the number is a trigger, the
confusion analysis carries the verdict." Fold one in.

### C4 — this FR's affect model is correct; vision.md is not (align them)

Phase 1a step 2 says hope is closed by **beats** — `villainy`, `death`,
`exposure`. That is the right model (beats open/close affects). But
[vision.md](../examples/plot_modeller/docs/vision.md) still lists hope's closers
as `betrayal, death, loss` — two of which are *affect kinds*, not beats, and
unsatisfiable by any pipeline output (review D4). Before this FR retrofits the
fixtures, **correct vision.md to match this FR**, so the ground truth is authored
against one consistent model. Otherwise the retrofit encodes the contradiction.

### C5 — the self-derived "regression" check is apples-to-oranges (state it)

AC#6 requires self-derived ≥ 0.75 "with mediation," but splitting
`lack → lack + mediation` changes N. A 0.78 on the *new* corpus is not strictly
comparable to FR-570's 0.80 on the *old* one. Keep the ≥ 0.75 floor, but label
it a **directional sanity check**, not a regression delta — and report both N's
side by side so the change in denominator is visible, not hidden inside a ratio.

### Folded conditions

C3 → add the borderline-defaults-to-REVISE rule (or a 2nd blind plan). C4 →
fix vision.md D4 *before* the retrofit. C5 → relabel AC#6 as a directional
check and surface both denominators. The go/no-go table, deliverables, and
blind-authoring honesty clause are all sound. Proceed once C4 is applied (it
guards the fixtures this FR produces).
