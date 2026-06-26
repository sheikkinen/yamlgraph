# The ruler I built to confirm my hypothesis refuted it

**Date:** 2026-06-26
**FR:** FR-597 (L7 affect-regenerability ruler) — enforce phase
**Lineage:** FR-596 ("numbers lie" manual inspection) → FR-597 (regenerability probe)

## What happened

Two days ago, manual inspection of the detective genre's L7 affect output convinced
me that `affect_recall = 0.09` was the same pathology as L5's demoted `world_recall`:
a sparse, under-determined GT skeleton penalizing valid alternative readings. The
witness was vivid — the model encoded `guilt → Pell` where GT encoded
`betrayal → Hagen`, and I judged both "equally licensed" by an under-determined
skeleton. I wrote that into FR-596 as the "corrected root cause" and planned FR-597 as
the ruler that would *confirm* it and authorize a demotion (the FR-595 analog).

The Judge, granting FR-597, did one thing that saved me from myself: it made the exit
**binary and anti-deferral** (C1) and forced the headline to be **corpus-pooled, not
per-genre** (C3). It also demanded the witness ride the **deterministic channel** (C2),
not the noisy fidelity judge.

I built the ruler. I ran it. It refuted me.

- Corpus-pooled GT under-determination: **0.464** — well below the 0.70 confirmation
  floor. The GT affect skeleton *is* regenerable.
- The load-bearing witness: feeding the GT detective skeleton back, the
  `betrayal → Hagen` beat regenerated **cleanly, with no `[UNDERDETERMINED]` marker**.
  The skeleton pins betrayal→Hagen. My "equally licensed guilt→Pell" premise did not
  survive contact with the probe.

The single-genre detective ratio that seeded my hypothesis (0.667) turned out to be
the corpus **maximum**. Pooling — the exact correction C3 mandated — exposed the
over-reach.

## The trap

`single_genre_inspection_overreach` — I generalized a root cause from one hand-read
artifact (the most extreme one, as it happened) and felt the certainty of having
"seen it with my own eyes." Manual inspection is a powerful antidote to trusting a
metric blindly (the FR-596 win was real), but it is itself a sample of size one, and
the human eye anchors on the most vivid case. The vividness of the detective
guilt-vs-betrayal reading was exactly what made it *feel* like the general truth.

This is the mirror image of `attributed_number_still_lies` (the FR-596 diary entry):
there, a decomposed number still lied. Here, a decomposed *inspection* still lied —
because I inspected the loudest genre and pooled nothing.

## The cure that worked

The cure was not mine — it was the Judge's. **C3 (pool, don't average) and C1 (binary
two-way exit) were premise-checks disguised as reporting conventions.** Pooling forced
the loud genre to compete with the quiet ones; the binary exit made "refuted" a
first-class, un-blocking outcome rather than a disappointment to be explained away.
Without them I would have run only the detective genre (it was my smoke test, and it
read 0.667 — *just* under threshold, close enough to fudge), declared confirmation,
and opened a demotion FR against a hypothesis the corpus disproves.

**Heuristic:** When manual inspection of one artifact yields a root-cause hypothesis,
the confirming probe must run the **whole corpus pooled**, and the analyst's hypothesis
must be the **refutable** branch — never run the probe only on the genre that seeded
the hypothesis. A ruler built to confirm is worthless; a ruler built to refute is the
only kind worth building. (Red-Hat premise check, OQ#1, operationalized.)

## What this leaves standing

`affect_recall = 0.09` is *not* dominated by under-determination. The residual drivers
are the harness artifact (full-cast map vs mono-protagonist GT) and **genuine encoding
divergence** — our pooled under-determination (0.583) is *worse* than GT's (0.464),
with lower fidelity and 3× the inversions. That ours-worse-than-gt gap is a real,
actionable signal. The encoder work resumes against the standing ≥0.50 gate, now
pointed at a defect that actually exists.

## Seed

Both L5 (world_recall, demoted) and L7 (affect_recall, *upheld*) have now been put to
the regenerability probe — opposite verdicts. The probe is becoming a general
**ruler-validation primitive**: before trusting *or* demoting any `X_recall vs GT
skeleton` gate, feed the GT skeleton back and measure if it regenerates itself. Seed:
should every GT-anchored recall metric in the evaluation suite carry a standing
"GT self-regenerability" companion measurement, computed once and cached, so no future
analyst can demote a gate on a single-artifact inspection without the corpus-pooled
probe contradicting or confirming them first?
