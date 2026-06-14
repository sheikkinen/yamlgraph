# The Cut That Could Be Counted

*Diary — 2026-06-14 — FR-485 (DM v2 turn-structured Final Cut)*

## The trap: a feature justified by its readership, earned by its witness

FR-485 sold itself on a reader-need: "someone wants Turn 3 cleanly written, kept
in turn order." When I judged it, that framing nearly killed it. For a prototype,
"a second, nicer finish" is exactly the speculative extensibility the doctrine
purges — and no live evidence said anyone wanted it. Had I taken the FR's stated
value at face value, I'd have approved a costume feature.

The justification was hiding one clause down. FR-484's Final Cut **dissolves** the
turns into one flowing scene — and its de-repetition guarantee ("the ledge is
established once, not five times") could only be witnessed by *reading the prose
and judging it by eye*. The Implementation Status literally quoted paragraphs and
asserted "established once at the open." That is `gate_checks_shape_not_substance`
inverted: the substance was real, but unprovable, because the output had no
structure a test could grip.

Keeping the turn skeleton changes the epistemics, not just the aesthetics. One
polished segment per played turn makes *alignment to the arc* a pure function:
exactly one segment per turn, the emitted `n`-set equal to the played set. The
deliverable was never "a finish." It was **a Final Cut with a deterministic
witness FR-484 could not have.** I re-seated the verdict on that and bound scope
to the validator, not the prose.

## The insight: the value of a generative feature can live in its checkable seam

The whole FR-482/483/484 lineage taught "ask the model only for what only the
model can do." FR-485 adds a corollary: *the way you shape the model's output can
manufacture a deterministic guarantee where there was none.* The continuous blob
and the turn list contain the same prose knowledge; only the second is countable.
Choosing the structured output was the entire engineering act — everything
downstream (the validator, the four raise-modes, the additive coexistence) is
mechanical once the shape is right.

## Two boundary lessons paid for in enforcement

1. **The `KeyError '"turns"'`.** The first live run died because the prompt
   renderer picks Jinja2 only when it sees `{{`/`{%`, else falls back to
   `str.format`. My system prompt's literal JSON example `{"turns": […]}` had no
   Jinja markers, so `.format` read it as a replacement field. The fix was to
   describe the shape in words and let `output_schema` enforce it. The bug lived
   at the template boundary and was normalized there — the one law, again.

2. **The empty cut was not a code bug — it was the validator working.** Against
   the cited explicit-seeded run, the provider intermittently returned empty
   content. My instinct was to debug my consumer. But the validator *correctly
   raised* `missing turns [1…9]`: a refusal is a defect, and surfacing it is the
   judged behaviour (OQ3, Commandment 6). The "failure" was the guarantee firing.
   I moved the generative witness to a neutral arc rather than engineer around a
   content refusal — the validator had already proven the point I was about to
   over-investigate.

## Seed

The validator gives me a cheap, true signal the continuous cut lacks: *which
segment a standing fact lands in.* The live witness showed "ledge" collapsing
from 4/4 raw recaps to 1/4 polished segments — measured, not eyeballed. I
declined to gate on it (OQ5: choosing the "standing fact" phrase is a fragile
heuristic). But the structure now makes a **cross-finish diff** possible: compose
both finishes, and compare the turn-aligned cut's per-segment fact-distribution
against the raw recaps' to *quantify* de-repetition without ever judging prose.
Could a finish's quality be witnessed entirely by the redistribution of facts
across a structure it preserves — emphasis as a measurable shape, not a read?
