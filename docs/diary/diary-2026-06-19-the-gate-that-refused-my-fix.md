# The gate that refused my fix was the finding

**Date:** 2026-06-19
**Context:** Enforcing FR-533 — a spike to hand-author a "truthful" dead-Witta lifecycle
and re-play chapter 8, to settle whether projecting a lifecycle starves the turn engine of
vividness. The spike never reached the vividness question. The deterministic precedence
gate refused the injection pre-LLM, and that refusal taught me more than a prose sample
would have.

## What happened

I judged FR-533 myself the day before. My Judgement (J1) asserted with confidence: "the bug
is purely that ch7's close-time extractor wrote `alive` for a character it had just
drowned — the reconstruction lie." I named the lever precisely: edit the seam to
`confirmed_dead`, re-play ch8, watch the gate drop Witta. I was certain the continuity axis
was "a near-foregone conclusion."

I built the driver on the existing FR-522 replay harness, edited ch7's seam packet, ran it.
It raised `ContinuityMemoryConflictError`: `alive conflicts with confirmed_dead`,
`higher_source: chapter_memory`, `lower_source: seam_packet`. I had edited the *lowest*-
precedence of *three* lifecycle sources. The ledger refused.

So I traced all the sources. Six of them — `world_state`, `chapter_memory` deltas,
`irreversible_facts`, `forbidden_regressions`, `seam_packet`, and `live_synopsis` —
unanimously said Witta was alive. Two of them were explicit guards the system had
*manufactured*: "Witta is alive at the end of the chapter, not dead or swept away" and
"FORBID: Witta is dead." Witta is the plan's ritual-keeper antagonist; the synopsis needs
her alive for the rest of the arc. Then I read the actual turns: turn 7 sweeps her off, but
turns 8–16 keep her alive and physically restrained — a no-progress tail replaying one
beat. The chapter's *final-cut composition* chose a dramatic death; everything else chose
the plan.

## The trap I was in

**`quick_confidence`, and I had even written it into a Judgement.** I was so sure of the
"extractor mis-classified a death" story that I encoded it as a frozen J1 and built the
spike to *confirm* it rather than to *test* it. The spike's value turned out to be exactly
that it could not be steered — the deterministic gate is indifferent to my hypothesis. The
Scripture says "when I feel certain, let that be the sign to Judge." I had judged, but I
judged the *execution plan*, not the *premise*. The premise — "the prose death is the
truth the ledger failed to record" — went unchallenged. It was half-wrong.

**`downstream_fix` wearing investigation clothing.** My intended correction (write the
death into the ledger) was a downstream patch at the bookkeeping boundary. The real defect
is upstream: nothing stopped the turn engine from killing a plan-protected character on the
page in the first place. I was about to normalize at the symptom again, the very thing the
projection plan accuses the whole FR-506→532 arc of doing.

## The insight

**The architecture already enforces the principle I thought was missing — in one place but
not the other.** `_enforce_memory_precedence_gate` is plan-over-prose, fully working, for
bookkeeping: it refused to let a prose-derived death overwrite a plan-derived survival. The
gap is not the absence of plan-over-prose; it is its *asymmetry*. Bookkeeping has it;
prose generation does not. The turn director and the final-cut can narrate the death of a
character the ledger is sworn to keep alive, and the ledger then — correctly, faithfully —
refuses to record it, producing a reader-visible resurrection. The break is the seam
between a prose layer with no plan constraint and a ledger layer that has one.

This **inverts the fix and strengthens the refactor.** For a plan-protected character the
prose death is the error to *prevent*, not the truth to *record*. The expensive asset (a
typed ledger with working precedence) already exists; the refactor is one additive edge —
feed the protected-character set into the turn director and final-cut — not a rewrite onto
`novel_generator`, which would re-pay for the precedence the gate already provides.

## Heuristic

**When you build an instrument to confirm a diagnosis, the most valuable outcome is the one
that refuses to confirm it.** A deterministic gate that blocks your intended fix is not an
obstacle to route around — it is a second opinion from the architecture, and it outranks
your hypothesis because it is made of code, not confidence. Before forcing past it (here:
editing all six sources to make the death "stick"), ask what the gate *knows* that the plan
encoded and you forgot. The brute-force path (override every guard) would have produced a
prose sample *and* silently contradicted the synopsis — a measurement of the wrong fix.

## Distinction worth keeping

There are two kinds of "wrong state": a *careless* lie (the extractor was sloppy) and a
*principled* conflict (two layers faithfully serve two different truths). I had filed Witta
under the first. She belongs under the second. The cure for a careless lie is a better
extractor; the cure for a principled conflict is to decide which layer is authoritative and
enforce that decision *at the point the other layer is generated*. Misfiling the kind of
wrong leads directly to the wrong fix.

## Seed

The plan-over-prose precedence is enforced at chapter open (the gate) but not at prose
generation. **What would it cost to make the turn director consult the same precedence the
gate does — a single shared "who is protected, who may die, from which chapter" resolver
called by both the gate and the director?** If one resolver fed both boundaries, could the
resurrection class disappear without any new extraction at all — and would that same
resolver be the seed of the authored lifecycle ledger the projection plan wants?
