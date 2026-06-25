# Diary — 2026-06-25 — Numbers lie even after you attribute them

## What happened

Yesterday's entry (*The cure that did not transfer*) closed FR-596 with what felt
like a finished diagnosis: the per-agent decomposition that healed L5 did not heal
L7, because L7 affect is mono-protagonist, and mapping over the full cast manufactured
~N× noise. The sub-axis instrument had turned a flat `affect_recall 0.09` into an
*attributed* KILL — detection 0.55, precision collapsed to 0.03, cause named:
cast-flood. I recorded it, deferred the protagonist-throughline reframe to a new FR,
and considered the root cause found.

Then the user asked one question — *"the L5 question was: can the prose be generated
from the results? numbers lie. analyze"* — and pointed the regenerability lens at L7.

I pulled the detective artifacts and laid the model's deltas beside ground truth **by
hand**, restricting to the protagonist alone — i.e. *granting* the cast-flood fix in
advance. The recall still missed on every sub-axis. The model had narrated Marren's
**empathy toward the witness she protects** (`guilt → Pell`); GT encodes her **moral
relation to the antagonist** (`betrayal → Hagen`). Both readings are coherent. Both
regenerate the same beats. The 8-token affect skeleton cannot distinguish them. The
cross-genre pull confirmed it: 5–8 deltas, ~3–4 paired arcs, one character — an
emotional skeleton *far* sparser than L5's world-state, encoding interior states with
no unique grounding in prose.

`affect_recall = 0.09` is not measuring whether the model captured the emotional
story. It is the **`world_recall` pathology one layer over** — token-agreement against
a sparse, under-determined skeleton — the exact defect FR-595 demoted at L5. Cast-flood
was real, but it was the *shallower* of two failures. The deeper one demotes the gate.

## The trap

`attributed_number_still_lies`: I had decomposed the failing scalar into attributed
sub-axes (detection / precision) and treated the attribution as bedrock. But a
sub-axis is still a number, and a number can name a *true-but-shallow* cause while
concealing a deeper structural one. The precision collapse (0.03) was genuine and it
*felt* like the root cause — it had a mechanism, a `Counter`, a clean story. That
sufficiency is the hazard. The decomposition made the metric *more* trustworthy, which
made it *easier* to stop. I almost shipped "cast-flood → build the protagonist
throughline" as the whole answer, which would have spent a model-effort FR chasing
0.09 → 0.50 on a ruler that cannot move.

What broke the spell was not a better number. It was **reading the artifacts** — the
prose throughline and the delta table, side by side with GT, by hand. The same
discipline that demoted `world_recall` at L5 (*can the prose be regenerated from the
results?*) was sitting one layer up, unused, because the attributed KILL had felt
final.

## What saved it

An external question, not an internal check. The user re-applied the L5 regenerability
frame I had not thought to port. That is uncomfortable to record: the instrument that
should have caught this (the regenerability test) already existed; I had just filed
it under "L5" and not asked whether L7's gate was the same kind of defect. The
`framework_costume` / `working_system_inertia` family again — a well-instrumented
KILL is a *working system*, and "it produced an attributed cause" blocked seeing that
the cause was incomplete.

The repair was three artifacts, all honest about the correction: FR-596's Gate-1
section now records the manual-inspection finding as the *corrected* (deeper) root
cause, re-sequences the follow-up to put the ruler reframe first; FR-597 drafts the
L7 affect-regenerability ruler as the node-for-node port of FR-594, with a Red-Hat
acceptance criterion that will **refute** the thesis if GT regenerates its own arc;
and the repo memory note is rewritten so the next reader inherits the deeper cause,
not the shallow one.

## Heuristic

> An attributed sub-axis is still a number. After you decompose a failing scalar into
> a mechanism, **read the artifacts by hand against ground truth before declaring root
> cause** — the decomposition can name a true-but-shallow cause and conceal a deeper
> one. When the gate is `X_recall vs a GT skeleton`, presume the skeleton guilty of
> under-determination until a regenerability probe (*can the result regenerate the
> source?*) clears it. The cheapest deeper bug is the one the eye catches that the
> Counter cannot.

This is the second time in two days the ruler itself proved to be the defect
(`the-ruler-was-the-defect` at L5, now at L7). If a third GT-overlap gate is found
under-determined, graduate `attributed_number_still_lies` to Scripture under the
`evaluation` boundary, paired with the standing rule: **regenerability is a
precondition for trusting any GT-overlap metric**, not an afterthought.

## Seed

The pathology recurred one layer down and was nearly missed because an attributed
cause felt final. Every L-layer gate in this arc is some `X_recall` against a
hand-authored GT skeleton. If `world_recall` (L5) and `affect_recall` (L7) are both
under-determined, what is the prior on L6 causality and L4 subject? Should the next
move not be another encoder FR at all, but a **single regenerability sweep across
every layer's GT** — presuming each skeleton guilty until it regenerates its own
stories — so the arc stops lifting numbers that cannot move and starts replacing the
rulers that cannot measure?
