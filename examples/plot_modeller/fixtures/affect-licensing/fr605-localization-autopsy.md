# FR-605 Localization Autopsy — why L7 recall floors at 0.214

**Source:** FR-604 arm B draw1 per-kind dumps
(`results/l7_perkind/throughlines/draw1/<genre>/<kind>.yaml`), classified against
`fixtures/ground-truth/<genre>.yaml`, protagonist-pinned, supported kinds only
(loss/hope/guilt/betrayal). Committed here because it is the central justification
for FR-605 and the raw dumps are gitignored (J: correction 4). Reproduced
independently by the Judge from the same dumps — counts exact.

## Method

For each protagonist GT affect delta `(beat, op, kind)` in a supported kind, find
the same `(kind, char)` predictions and classify the miss:

- **hit** — exact `(beat, op, kind, char)` present in predictions.
- **op_flipped** — right beat + kind, wrong open/close.
- **off_by_one** — same op, adjacent beat (|index difference| = 1).
- **wrong_beat** — kind emitted for the protagonist, but on a far beat.
- **dropped** — the kind was never emitted for the protagonist at all.

## Result (draw1, protagonist, kinds loss/hope/guilt/betrayal)

| | count |
|---|---|
| supported-kind GT deltas | 26 |
| hits | 9 |
| misses | 17 |

| miss bucket | count | share of misses |
|---|---|---|
| **wrong_beat** (right kind, far beat) | **12** | **71%** |
| dropped (kind never emitted) | 2 | 12% |
| off_by_one (adjacent beat) | 2 | 12% |
| op_flipped (right beat, wrong open/close) | 1 | 6% |

**The dominant failure is `wrong_beat` (71%): right emotion, wrong location.** Only
2/17 misses are adjacent near-misses, so a ±1 tolerance window recovers almost
nothing — the failure is genuine mis-placement, not a fence-post error.

## The mechanism — collapse onto the salient beat

Reading the wrong_beat cases, a single pattern recurs: the model identifies the
protagonist's emotion correctly but **collapses its open and close onto the single
most dramatic beat**, instead of tracking each endpoint to its true structural
position.

- **quest, `F6 close hope`:** the model emitted `F4 open` + `F8 close` — hope's
  endpoints pinned to the two crown beats; it never placed the close at F6 where
  Eira actually relinquishes the crown. The arc was *shifted onto the climax*.
- **horror, `F1 open loss` and `F6 close loss`:** two distinct deltas spanning the
  whole story were **fused into a single `F4 open`** — a story-length arc
  compressed to one dramatic beat.
- **detective, `F5 close loss`:** caught "loss exists" but emitted it as `F2 open`
  — both endpoints lost to one early beat.

## Why model scale does not fix it

The same single-pass prompt on `claude-sonnet-4-5` (one full corpus pass,
`logs/fr604-sonnet-ceiling.log`):

| model | affect_recall | kind-blind beat placement |
|---|---|---|
| haiku-4-5 | 0.214 (6/28) | higher |
| sonnet-4-5 | **0.071 (2/28)** | 0.29 (8/28) |

A larger model localized **worse**, not better. This is a task-framing problem
(do what + where + open/close in one shot over a flat beat list), not a capability
ceiling — which is why FR-605 splits *what* (pass 1) from *where* (pass 2).
