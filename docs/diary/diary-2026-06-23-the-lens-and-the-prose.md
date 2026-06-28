# The lens and the prose

**Date:** 2026-06-23
**FR:** none (review + corpus prep for v4 layered planner)

## What happened

Two tasks, one thread. First, a review of `plan-v4-layered-planner.md` —
appended as a chapter inside the document itself. Second, building a
`genre-synopses/` folder by converting four structured proof-of-concept
genre-plots back into free-text prose.

The review found the plan's conceptual spine sound (recognition admission,
gloss-as-pivot, layer isolation) but its YAML showcase mechanically broken:
`loop_limit`/`loop_exit` written as node-body fields when the implementation
reads them as top-level maps keyed by node name; a promised failure
diagnostic with no node to emit it; and — the deepest tension — every layer
L4–L7 writing the same `state_key: functions`, forcing the *small* model the
plan was designed around to re-serialize the whole accreting array four times,
which is the exact capacity the plan claims it cannot rely on.

## The trap: reviewing the prose, not the machine

The plan reads beautifully. The pivot diagram is elegant, the cost table is
persuasive, the seven layers have a satisfying symmetry. The temptation was to
review it at the level it was written — to engage the rhetoric and grade the
argument. That would have missed every real defect, because all of them live
*below* the prose: in the schema fields, the state-merge semantics, the linter
rules. The plan said "this is a runnable YAMLGraph showcase," and that claim is
falsifiable only by reading `graph_schema.py` and `edge_compiler.py`, not by
reading the plan.

So I read the machine. `loop_exits` keyed by node, E008/E009 linter rules,
`evaluate_condition`'s lowercase-literal handling, the fact that a returned
dict *replaces* its state key wholesale. Each verified fact turned a vague
unease into a concrete, citable correction. The §11 chapter is graded ✓ on
the claims I checked against source, and the difference between "this feels
risky" and "this overwrites `functions` at `graph_loader` merge, here's the
line" is the difference between an opinion and a review.

## The insight: the gloss pivot cuts both ways

The second task illuminated the first. Converting structured plots → prose is
the *inverse* of the v4 pipeline (prose → structured plot). Doing the inverse
by hand made the pivot claim viscerally true: the glosses ARE the story. I
reconstructed each synopsis almost entirely from the ordered function glosses —
the predicates, kinds, and JSON scaffolding contributed nothing to the prose.
A reader of the synopsis cannot tell whether `exposure` or `recognition` was
the kind; they only feel Hagen's mask fall. This is exactly the plan's C1/C2
claim (the gloss is load-bearing; the structural fields are not recoverable
from prose) — confirmed by running the conversion backwards.

Which sharpens the review's central worry. If the gloss carries all the
narrative weight, then a small model dropping a structural field during the
four-fold `functions` re-serialization is *invisible in the prose* — the beat
still reads fine, the corruption surfaces only at the SAT check, or worse, not
at all. The forward pipeline's most fragile seam is precisely the one the
backward conversion proves is least observable.

## Heuristic

**review_the_claim_at_its_own_layer:** A document that claims to be runnable
must be reviewed against the runtime, not against itself. Prose fluency is
orthogonal to mechanical correctness; the more elegant the plan reads, the
stronger the pull to grade it on rhetoric. Find the falsifiable claim ("this
YAML loads," "this is cheaper," "a small model can do this"), then go to the
source that decides it. A ✓ next to a claim means "checked against
`file.py:line`," nothing weaker.

## Seed

The genre-synopses now exist as free-text inputs, and the v4 review (§11.5)
argues the non-saga spike should run *before* building 22 nodes. But there is
no forward pipeline yet to run them through — only the backward conversion I
did by hand. Could the four genre-plots serve as a *golden-pair* corpus: each
synopsis is the input, each structured plot is the expected output, and any
future L1–L4 prototype is scored by how close its recovered functions land to
the hand-authored originals? The backward conversion I just did would become
the answer key for the forward pipeline's first falsification test — the gloss
round-trip (prose → plot → prose) as the acceptance metric the plan currently
lacks.
