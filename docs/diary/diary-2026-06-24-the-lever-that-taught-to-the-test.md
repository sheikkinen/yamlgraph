# The lever that taught to the test — FR-583

*2026-06-24 — enforcing FR-583 (Plot Modeller evaluator tolerance + L5 vocabulary grounding)*

## What happened

Two levers, frozen as two commits.

**Part 1 (Jaccard arg tolerance)** produced a perfect null result: L2 stayed
13/18 (0.72), L5 stayed 43/85 (0.51), precision flat on both. The existing
substring check already covered every multi-word *subset* the proposal cited.
The residual misses were genuine single-word synonyms (`together`/`lovers`) that
no string metric should bridge. I kept the helper — it is a zero-false-positive
safety net — but it moved nothing. The honest report was "this changed zero
numbers," not a manufactured win.

**Part 2 (vocabulary grounding)** was the load-bearing hypothesis: feed the
model the ground-truth tokens so it stops paraphrasing. The first vocab run came
back at 21/85 (0.25) with one fixture collapsing to zero beats. My first instinct
was *temp=0.7 noise — haiku is jittery, re-run it.* The second run was 15/85
(0.18) with **two** fixtures at zero. Still I could have shrugged it off as
variance against a single 0.51 baseline.

## The trap

**Attributing a regression to noise instead of isolating the variable.** I had
one baseline sample and two treatment samples, all at temp=0.7, and the
per-fixture numbers swung 0.00–0.82 between runs. The noise was real and large
enough to *rationalise away* the lever's effect. Continuation bias wanted me to
write "inconclusive, probably noise, ship the machinery" and move on.

## The cure

**Run the control: same config minus the one lever.** I reverted the vocab block
and ran the no-vocab baseline once more. It came back 51/85 (0.60) — and, the
decisive signal, **zero** validation exhaustions. Both vocab runs had driven two
fixtures each into the 3-retry loop limit, dropping their entire beat set. The
control had none. That is not a recall metric drowning in noise; it is a
*categorical* difference in failure behaviour that variance cannot explain. The
lever doesn't fail to help — it actively destabilises the assign node, because a
model told to use a fixed token list forces those tokens into the wrong
predicate slots and the validator rejects the lot.

This is the same shape as FR-578's lesson, one layer up: there I changed model
tier and held everything else; here I changed the prompt lever and held the
model. **Controlled isolation turns "noisy and ambiguous" into "decisive."** The
noise floor didn't shrink — I stopped trying to read signal *through* it and
measured the difference *across* a clean A/B instead.

## The second, quieter lesson

Injecting the **ground-truth** vocabulary into the prediction is
teaching-to-the-test. Even if recall had risen, the gain would have been partly
leakage — the model echoing the answer key — not capability. The lever was
methodologically suspect before it was empirically dead. A spike that feeds the
oracle's own tokens back into the predictor measures plumbing, not understanding.
When a "grounding" lever draws from the same artifact you score against, suspect
leakage before you celebrate a lift.

## Heuristic

- When a treatment looks worse but the metric is noisy, **do not argue from the
  noisy metric — run the control and compare a categorical behaviour** (here:
  catastrophic-failure count, 0 vs 2) that variance cannot fake.
- A negative spike result is a *success*: the lever was falsified for the price
  of three LLM runs instead of a shipped regression. Revert without mourning.
- If a grounding signal is extracted from the same ground truth you score
  against, treat any improvement as leakage until proven otherwise.

## Seed

Both FR-578 and FR-583 were salvaged by the same move — change exactly one thing,
hold the rest, compare. Could the spike harness *enforce* this? A `--control`
flag that runs N samples of (treatment) and N of (treatment minus the named
lever) at the same seed/temp, and reports not just mean recall but the
**catastrophic-failure delta** and a variance band — so "is this signal or
noise?" is answered mechanically, and a lever that widens the failure band is
auto-flagged KILL before a human rationalises it as jitter?
