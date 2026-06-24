# The flood and the miss are one gesture — FR-584

*2026-06-24 — enforcing FR-584 (Plot Modeller L5 salience suppression + typed
argument roles)*

## What happened

FR-583's post-mortem framed the L5 wound precisely: **84 false positives vs 34
misses**, the FPs dominated by location flooding (56 of 84 were `at` predicates,
67%). The model snapshots every character's position at every beat; the ground
truth records only the one fluent the beat turns on. Precision 0.30, not recall,
was the bleeding. FR-584 proposed three prompt levers to staunch it, attacking
the failure modes in rank order:

- **A** — salience suppression: "emit a `pre_world` fluent only if the beat is
  impossible without it."
- **B** — typed `rel` roles: name SOURCE and TARGET before writing the args.
- **C** — non-character subjects: objects and locations can be the subject of
  `at`.

I committed the FR-583 throwaway confusion-dump as a real measurement witness
(`analyze_l5_confusion.py`), captured the no-lever RED (84 FP / 34 MISS / 56
at-flood), then ran the Judgement-mandated controlled A/B: full A+B+C, then a
control with Lever A removed, same temperature, same model (haiku-4-5, verified
each run via the `Creating LLM` log line).

The experiment was clean and it falsified the hypothesis:

| metric | baseline | control (B+C) | full (A+B+C) |
|---|---|---|---|
| world recall | 0.60 | 0.58 | 0.51 |
| precision | 0.30 | 0.29 | 0.30 |
| at-flood | 56 (67%) | 78 (74%) | 44 (59%) |
| rel-FP | 15 | 16 | 17 |
| catastrophic 0-beat | 0 | 0 | 1 |

Lever A *did* move its target — isolating it cut the flood 78→44. But the `at`
**misses rose 12→20 in lockstep**, precision stayed flat (0.29→0.30), recall
fell, and the salt-road fixture collapsed to **0 beats** at the validator
loop-limit — the same catastrophic failure the FR-583 vocab lever produced.
Lever B did nothing to directionality (rel-FP 15→16→17). Lever C made the flood
*worse* (more object-`at` noise that misses the answer key). All three reverted.

## The trap

I had read the 84-FP / 34-MISS split as two independent dials: turn down the
flood (the big one) and recall barely suffers. **They are not independent.** A
suppression instruction is a single gesture applied to the model's whole output
distribution. When the model has no internal notion of *which* precondition a
beat depends on, its over-emission (FP) and its omission (FN) are the **same
defect viewed from two sides** — both are "I cannot tell salient from incidental."
So "emit only if impossible without it" prunes the true precondition and the
snapshot noise in the same proportion. The flood dropped, the misses rose, and
precision — the ratio — did not move a point.

The tell was right there in the table: **at-FP fell 56→44 while at-MISS rose
12→20.** Δ-FP ≈ −12, Δ-MISS ≈ +8. The lever moved predicates from "emitted" to
"omitted" wholesale; it never moved one from "wrong" to "right." That is the
signature of a missing *discrimination* capability, not a tuning knob.

## The heuristic

**When a suppression lever moves false-positives and false-negatives in the same
direction-pair (FP down, FN up) while precision stays flat, the defect is a
missing discrimination, not a verbosity problem.** No amount of "say less"
wording will fix it, because the model is not choosing *what* to cut — it is
cutting uniformly. The fix is an architectural gate that *decides* salience
(a dedicated node, or a model that can), not a sterner instruction. Prompt
wording can change *how much* a model emits; it cannot install a faculty the
model lacks.

Corollary, carried from FR-583: a lever that introduces a **catastrophic
zero-output run** the baseline never had is disqualified regardless of its
aggregate numbers. Stability is a precondition of the metric, not a line in it.

## Why this is a KILL, not a fourth iteration

Best variant recall (0.58) sits in the REVISE band, but the Judgement said the
*confusion analysis* carries the verdict, and the stop rule forbade a fourth
prompt-wording pass. One lever net-negative, one dead, one counter-productive,
precision immovable at 0.30 — the prompt-only approach is exhausted. The honest
output is the same shape as FR-583 Part 1: "this changed the wrong numbers and
not the right one," escalated to a true two-node decode (a salience-gate call
feeding an argument-fill call) as a new FR. The cheapest bug is the one killed
in the spike, not iterated into a fifth log file.

## Seed

If FP and FN collapsing together is the fingerprint of a missing discrimination,
could the evaluator itself emit that fingerprint automatically — a per-lever
"discrimination delta" (did any predicate move from *wrong* to *right*, or only
from *present* to *absent*?) — so the next agent sees "this lever only changed
verbosity" before it spends two full spikes proving it by hand?
