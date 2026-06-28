# Diary — The gate that could not resolve its own threshold

**2026-06-25 · FR-593 · commit → two-run corpus gate → KEEP**

## What happened

FR-593 reframed the rejected FR-592 (a tail "suppress beats whose tokens are
absent from the vocabulary" filter) into a head-of-pipeline naming normalizer:
`extract_vocab` (LLM) → `validate_vocab` → `canonicalize`, the last writing an
**additive** `canonical_gloss` per beat while leaving the original `gloss`
byte-identical. The deterministic core (`StoryVocab` + `canonicalize_glosses`) was
already RED→GREEN (20/20). This session committed it (`fe413479`), ran the
explicit PRIMARY/REVERT gate, and recorded the verdict.

The gate was specified with hard numbers: corpus `world_recall ≥ 0.47` over two
runs; horror ≥ 0.71 falsification cell. So I ran it twice.

| | Run 1 | Run 2 |
|---|---|---|
| Overall world_recall | **0.46** | **0.49** |
| horror (falsification) | **0.47** | **0.71** |
| Evaluator verdict | KILL | KILL |

The two runs straddle **every** threshold. Run 1 fails both primary criteria;
run 2 passes both. The mean (0.475) clears 0.47 by 0.005. Horror swung ±0.24.

## The cognitive trap

**`gate_underpowered_for_its_margin`.** I treated a numeric gate as a decision
oracle without first asking whether its *measurement variance* was smaller than
its *decision margin*. It was not: run-to-run noise (±0.03 overall, ±0.24 on the
horror cell) dwarfs the 0.005 margin the gate was trying to resolve. With n=2 and
variance ≥ margin, the "verdict" is simply whichever run you stop on. The gate
produced the *shape* of a decision (numbers, thresholds, a table) while carrying
no decisional information — compliance theatre with a metric instead of a
checkbox. Two faithful runs, zero resolution.

The mechanism read confirmed it was noise, not signal: scifi held 0.17→0.22
*despite* the probe proving 9/13 of its glosses were canonicalized. Recall only
moves when a canonical token tolerant-matches the GT token, and LLM alias
**over-mapping** (`the nightstand → Mara's apartment`, `the maze → Vantari Labs`)
replaces a GT-matching literal with a non-matching canonical — so the active,
visible change bought no measurable recall. The change *did* something; it didn't
*mean* anything to the metric.

## The second trap: letter vs intent of the gate

I recommended **REVERT** — the Red-hat call: two KILL verdicts, a margin inside
the noise, complexity added at a new LLM boundary for no demonstrated win. The
author chose **KEEP**, on the gate's *letter*: the spec said `world_recall ≥ 0.47`
and the mean meets it. Both readings are defensible, and that is the lesson — I
had silently imported a stricter gate (both runs must pass; honor the evaluator's
own KILL) than the one written down. When I present a verdict, the criterion I
apply must be the criterion that was authored, not the one I wish had been. The
author owns the threshold's letter; the agent owns surfacing that the letter and
the intent diverge. I did surface it, then let the author decide — that part was
right.

## What I did well

- Completed *both* runs before declaring, instead of stopping at run 1's 0.46 and
  calling it KILL (which would have been the same single-run fallacy in the other
  direction).
- Separated the deterministic substituter (faithful, tested, kept regardless)
  from the LLM aliasing boundary (where the actual defect lives), so KEEP retains
  an audited primitive rather than a black box.
- Recorded the over-mapping as a *named, falsifiable* future lever (constrain
  aliases to co-occur with their canonical in the synopsis), not a vague TODO.

## Heuristic

Before trusting a numeric gate, estimate the measurement's run-to-run variance
and compare it to the decision margin. If variance ≥ margin, the honest verdict
is **"indistinguishable from baseline"** — a policy keep/revert, not a number.
Reporting `0.475 ≥ 0.47` as a pass without its ±0.03 noise band is a plausible
wrong answer dressed as precision.

**Seed:** Should a gate declare its *minimum detectable effect* and the *n*
required given observed variance, so a straddle auto-escalates to "UNDERPOWERED —
rerun with N or tighten the metric" instead of silently rounding to GO/KILL? A
gate that cannot resolve its own threshold should say so, not pick a side.
