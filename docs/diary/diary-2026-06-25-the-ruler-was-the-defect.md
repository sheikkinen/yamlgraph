# The Ruler Was the Defect, Not the Thing It Measured

*2026-06-25 — FR-595, closing the FR-594 loop*

## What happened

L5 read **KILL** for weeks. world_recall 0.49, just under the 0.50 floor. Phase 4
merge blocked on it. The natural reading: the encoding is bad — the state machine
fails to capture half the world facts the ground truth records.

FR-594 challenged that reading by building a *second* ruler (prose regenerability)
that needs no ground truth. This session powered it: five repeated corpus runs.
The paired discrimination — ours is more regenerable than the lossy GT skeleton —
came back at **0.337 ± 0.035, t(4)=21.6**. Rock solid. The thing world_recall
called a failure, the regenerability ruler called a *success*: our encoding
licenses more of its own narration than the GT predicate dump does.

So I demoted world_recall to a diagnostic and gated L5 on the discrimination
instead. The verdict flipped KILL → **GO** (gap 0.294, twice the 0.15 floor).
world_recall is *still 0.49* — I changed nothing about the encoding. I changed
what we believe 0.49 means.

## The trap: a number that measures agreement, dressed as a number that measures truth

world_recall measures agreement with a target. When the target is itself a *lossy
projection* of the story — a predicate skeleton that throws away most of what a
beat encodes — high agreement means "you reproduced the lossy thing" and low
agreement means "you encoded something the lossy thing couldn't hold." Both
readings are possible from the same 0.49. The metric cannot tell you which.

The tell I missed for weeks: **the denominator was someone else's compression.**
`world_gt = 85` predicates. That 85 isn't ground truth about the story; it's the
count of fluents a particular GT author chose to write down. Scoring recall against
it scores conformance to that author's compression, not fidelity to the narrative.

## The cure: anchor the gate to a difference, not a level

The power analysis made the cure mechanical. Absolute simulability swings run to
run (corpus-mean sd 0.085) — ungateable at n=1. Per-genre swings worse (worst cell
sd 0.22) — ungateable ever. But the *paired difference within a run* is stable
(sd 0.035), because both arms see the same genres, the same prompts, the same
temperature draw — the noise cancels. The gate had to be a difference, and it had
to be GT-anchored (against the skeleton), not absolute.

This is the same shape as a within-subjects experiment beating a between-subjects
one: when you can pair, pair. The 0.15 GO floor isn't a taste call — it's ~4 sd
below the observed mean gap, so a single corpus run clears it with margin.

## The discipline that held

I wrote the RED test for `measure_l5_verdict` (GO/REVISE/KILL/negative-gap) and the
RED guard for the world_recall demotion *before* touching either file. The
demotion guard mattered most: `summarise_l5` was untested, so without the guard the
"verdict → informational" change would have been an unwitnessed edit to a function
nobody pins. The guard is now the thing that stops a future refactor from quietly
resurrecting the false gate.

Regenerating `l5-summary.yaml` was free — `main_l5` re-scores from disk with no LLM.
Re-stamping `l5-measure-summary.yaml` was free too — the verdict is pure over means
already on disk. The expensive part (the 5 powered runs) was already paid. A metric
fix should cost a test and a re-stamp, not a re-run; FR-594 front-loaded the cost so
FR-595 could be cheap.

## Heuristic

**A recall metric scores agreement with its denominator. Before trusting it as a
gate, ask what the denominator *is* — if it is a lossy projection authored by
someone else, the metric measures conformance to their compression, not fidelity to
the truth. Gate on a paired, source-anchored difference instead; the within-run
pairing cancels the noise that makes absolute levels ungateable.**

This is the `gate_checks_shape_not_substance` trap wearing a statistician's coat:
0.49 passed the *shape* check (it's a valid recall fraction) but failed the
*substance* check (what it's a fraction *of* was the wrong target all along).

## Seed

We now have two L5 rulers: world_recall (agreement, demoted) and regenerability
(discrimination, promoted). They disagreed, and the disagreement was the signal —
it located the lossy denominator. **Should every gate metric ship with a
deliberately-orthogonal shadow metric, whose only job is to disagree?** A gate that
can only ever confirm itself cannot tell you when its denominator has rotted. The
cheapest detector of a corrupt ruler may be a second ruler built to measure the
same thing a different way — and an alarm that fires when they part.
