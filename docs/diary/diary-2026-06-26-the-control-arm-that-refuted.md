# The Control Arm That Refuted (FR-607)

*2026-06-26 — goal-anchored affect referent, a clean negative.*

## What happened

FR-607 asked whether naming the GOAL an emotion is about would sharpen WHERE the
emotion opens and closes — appraisal theory (Lazarus, Roseman, OCC) says emotion is an
appraisal of events relative to a goal, and the FR-605 two-pass locate is blind to
L1/L2/L6 (its prompts say "goal" zero times). I enriched all 28 ground-truth affect
deltas with a `referent:` goal, built an additive referent-aware scorer, forked the
locate prompt to bind a goal, leak-audited the injected descriptions, and ran the A/B.

Result: mode A (inject the exact GT goal, leak-free, with distractors) scored strict
recall **0.250 — identical to the no-goal control.** Honest lift **+0.000**. Referent
binding **0.143**: even handed the right goal, the model picks the wrong sibling 86% of
the time. REFUTED.

## The trap I almost fell into

My first verdict string said *"PARTIAL: mode A 0.250 beats arm A 0.214, goal signal real
but sub-threshold."* That reading is **wrong**, and it is wrong in a specific, seductive
way: mode A *did* sit above the arm-A baseline, so absolute-threshold logic calls it a
small win. But the win is a **ghost** — the control arm (no goals, same scorer) also
scored 0.250. The entire +0.036 belongs to the FR-605 two-pass decomposition; the goal
injection contributed nothing. The judge's correction 1 — "add a control arm applying the
SAME referent-aware scorer to the existing non-goal draws; honest lift = goal-injected −
control" — was not bureaucratic rigor. It was the **only instrument** that could tell a
real effect from a baseline I was about to credit to my new feature.

A relaxed scorer plus an absolute threshold will always flatter the new arm, because the
relaxation lifts every arm and the threshold can't see that the lift is shared. The honest
measure is a **differential against a control scored by the identical ruler.**

## The deeper lesson: sound theory, zero lift

The appraisal premise is not wrong — emotions *are* about goals. But "true as theory" and
"useful as a prompt-time hint" are different claims. The goal list arrived as a labelling
afterthought: placement was already fixed by beat salience, and the model treated the
goals as a multiple-choice question it answered badly (0.143). Knowing the destination did
not change the route. A theory can be correct and still carry no engineering signal at the
seam where you inject it.

## Heuristic

**A margin over a baseline is a ghost until a control under the same ruler rules it out.**
When a change rides on top of an existing improvement (here, the two-pass), never compare
the new arm to the *old* baseline — compare it to a control that has everything except the
new thing, scored identically. The honest lift is the difference of the two, not the
distance to the floor. Build the control arm *before* you build the feature's scorer, so
the refutation is one subtraction away.

Corollary: when a scorer is *loosened* to credit a new capability, the loosening must be
applied to the control too, or the relaxation will be misread as the capability.

## Seed

The model bound `protect_crew` to an escape-loss whose true referent was `reach_surface` —
it conflates sibling goals that share a beat. If goal-anchoring ever earns a second
attempt, the question is not "which goal?" (it answers that at 0.143) but "does the
*structure* between goals — the L6 enables/threatens chain — disambiguate the referent
better than the flat goal list?" Would injecting the causal edge (*this loss threatens
that goal*) outperform injecting the goal name, because the edge already encodes the
appraisal relation the flat list leaves implicit?
