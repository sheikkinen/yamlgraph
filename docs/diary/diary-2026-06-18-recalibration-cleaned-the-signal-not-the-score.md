# The recalibration that cleaned the signal but not the score

**Date:** 2026-06-18
**Context:** Regenerated one Floodmark book (`10026-BC`) under the FR-532 recalibrated
continuity prompt + FR-530 witness, to compare against the `10025-BC` baseline.

## What I did

Recreated `10025-BC`'s premise into a fresh slot `10026-BC` (turn-cap 256) so the
FR-532-labelled baseline survives for comparison. Same premise, same generator, only the
reviewer's `continuity.yaml` system prompt changed (FR-532: report reader-salient breaks,
suppress physical micro-state churn). Then reviewed and emitted the FR-530 witness.

## The result — two 1/5 scores that mean opposite things

| | breaks | break composition |
|---|---|---|
| `10025-BC` (old prompt) | 11 | ~8 rope/pouch/positional/timing micro-state, ~3 reader-real |
| `10026-BC` (recalibrated) | 6 | **6/6 reader-real** (lifecycle, identity, relationship, plot); **0 micro-state** |

Both score **1/5** — the formula `max(1, 5 - break_count)` saturates at any count >= 4. But
the scores are 1/5 for *opposite reasons*:

- `10025-BC` is 1/5 because the critic **over-counted noise** — rope grips, pouch handoffs,
  "Hilde now beside Reinmar." The book may be fine; the critic was crying wolf.
- `10026-BC` is 1/5 because the book **genuinely has six reader-breaking defects** — Arnulf
  is swept away and "no sign of him rose again" (ch3) then is alive and fighting the
  current (ch4); Witta "vanished into the flood" (ch7) then reappears arguing (ch8); a
  resolved ch5 standoff replays verbatim in ch6. Every break the recalibrated critic
  reports is one a reader would actually trip over.

## The insight

**The recalibration cleaned the signal, but the score formula hid the improvement.** The
*break list* went from mostly-noise to all-signal — a categorical quality jump. The
*scalar score* did not move, because saturation collapses 6 and 11 to the same 1/5. If I
had looked only at the witness's `continuity_score`, I would have concluded "no change."
The truth lived in `break_count` (11 -> 6) and, more importantly, in the **type
distribution** (70% micro -> 0% micro) that no scalar captures.

This is FR-532's seed — "Who calibrates the recalibrated?" — answered concretely: you
cannot judge the recalibration by the metric it feeds, because that metric saturates.
You judge it by reading the breaks and asking "would a reader notice this one?" For
`10026-BC`, the answer is yes, six times. The critic is now honest; the generator is the
defendant.

## The trap I almost fell into

**Score-as-verdict.** Seeing "1/5" again, the continuation-bias move is "recalibration
didn't help." But the score is a lossy projection of the break list, and the projection
saturates exactly in the range where books-under-test live. The witness emits
`continuity_score` *and* `break_count` for precisely this reason (FR-530 J3 — machine-
readable, both fields). The category — which the JSON does *not* yet carry — is the next
gap.

## What this exposes about the generator (the real defendant)

The recalibrated critic now points cleanly at the actual DM v2 continuity defect class
the whole FR-506->532 arc chases: **chapter-seam death/resurrection and scene replay.**
Arnulf and Witta both die at a seam and resurrect across the next one; ch5's resolved
conflict is re-emitted whole as ch6. These are not prose-polish issues — they are the
chapter-boundary generator contradicting the state it just committed. The micro-state
noise was camouflage; with it suppressed, the structural defect is unmissable.

## Heuristic

**A saturating metric cannot witness an improvement that happens inside its saturation
band.** When recalibrating a scorer, validate against the *pre-aggregation* evidence (the
break list and its categories), never against the scalar the scorer emits — the scalar is
where the information you are trying to measure was already destroyed.

## Seed

The witness emits `{continuity_score, break_count}` but not break *category*. The entire
signal of this comparison — "micro-state -> reader-real" — is invisible to any machine
consumer downstream. Should the witness emit a per-category histogram
(`{lifecycle, identity, relationship, plot, positional, prop, timing}`) so FR-531's report
can trend *composition*, not just count? **When does a witness owe its consumers the
dimensions of what it saw, not just the size?**
