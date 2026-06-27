# The rubric already had an opinion

**Date:** 2026-06-27
**Context:** A "genre generalization" probe of the interiority A/B refuted the
unconditional GO, and chasing the refutation led — through a taxonomy detour —
back to a single sentence in a prompt I had written myself.

## What happened

The interiority A/B was a GO on a fantasy scene (Floodmark) and a REVISE on a
scifi scene (the Loom). The obvious frame was **genre dependence**: maybe
authored interiority only helps in some genres. I named the gap "adrenaline-rush
vs touchy-feely," researched it, and found it was a folk re-derivation of Swain's
sixty-year-old Scene/Sequel — proactive vs reactive scenes. So the confound was
not genre at all; it was **scene type**. One scene spends a feeling through a
choice; the other resolves it internally, in dialogue or thought.

Then, deciding where to put the new `scene_type` dimension, I read the L7
`affect_throughline` close-op prompt — the layer that has been AMBER-RED for
weeks with "dangling opens." There it was, in prose I had authored: a close is
"a forceful or positive **action** that ENDS an earlier negative feeling." The
rubric only recognises resolution-through-action. A feeling that closes by being
recognised, named, or decided in dialogue matches nothing and emits nothing — so
the open dangles. The bug was not a missing dimension to add and measure. It was
an opinion my own prompt had already encoded and never disclosed.

## The trap

Two layers of misdirection, both the same shape — **naming a defect by its most
salient surface, not its operative cause.**

1. The first surface was **genre**. Scifi and fantasy were the visible variables,
   so the refutation looked like genre dependence. The operative variable was the
   scene's affect-closure mode, which is orthogonal to genre.
2. The second, sharper surface was **measurement**. L7 was RED, so my reflex was
   to treat scene_type as a new thing to *classify and measure* — more apparatus.
   But the layer was not under-measured; it was **mis-instructed**. The bias was a
   declarative sentence sitting in plain text in the rubric, asserting that
   feelings close through action. I almost added a measurement to detect a
   property my own prose had already excluded by construction.

The pull in both cases was outward — toward a new axis, a new classifier, a new
metric — when the cause was a sentence already on disk, readable in ten seconds.

## Heuristic

**When a layer mis-grades a whole *class* of inputs, read its rubric prose before
you add a dimension.** A systematic, one-sided error is rarely a missing feature;
it is usually an undisclosed assumption written into the instruction. The
close-op did not lack scene awareness — it had a hidden *opinion* about how
feelings resolve, stated as if it were a definition. The fix begins by finding
the sentence that holds the opinion, not by building the instrument that would
have rediscovered it. This is `read_raw_output_first` turned on the prompt
itself: before measuring why a stage is wrong, read what you *told* it to do.

A corollary on naming: a confound named after the most visible variable (genre)
will send you to build the wrong control. Name it after the variable that
actually moves the verdict (scene type), and the cheap experiment falls out — here,
widen the close-op and re-measure the dangling-open rate, no new classifier required.

## Seed

If undisclosed opinions hide inside rubric prose as confident definitions, could a
prompt-lint pass flag *closed-class assertions* — sentences that define an open
behaviour ("a close is an action that...") as if exhaustive — and demand they
enumerate their alternatives or admit they are one branch? The close-op would have
tripped it: it asserted a single resolution mode in the grammar of a definition.
What other rubrics in the stack quietly define away half of what they grade?

## Addendum — the field shares the blind spot

Re-reading the novel-generation framework survey
(`docs/research/llm-novel-generation-frameworks.md`) after this, I noticed the
trap is not just mine. The whole literature controls one measurable axis at a time
with a specialised judge — coherence (Re3), pacing (CONCOCT), continuity
(lorebooks) — and **every survey treats those judges as trustworthy by
construction.** None asks whether the validator's own instruction smuggles a bias.
CONCOCT proved "pacing is a measurable axis, not an emergent accident"; this
session's mirror is "a validator's bias is a readable sentence, not an emergent
accident." The heuristic generalises beyond plot_modeller: *the cheapest audit of
any specialised judge is to read its rubric for closed-class assertions before you
trust a single score it emits.* The field measures judge **outputs**; almost
nobody reads judge **instructions**. That gap is where our close-op hid for weeks.
