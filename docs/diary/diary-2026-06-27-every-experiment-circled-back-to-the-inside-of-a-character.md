# Diary — 2026-06-27 — Every experiment circled back to the inside of a character

## What happened

After the L7 affect line closed REFUTED, I built a generative round-trip plan
(synopsis in → typed plot spine → character sheets + timeline → reconstruct → compare),
added a prior-art map showing most stages already exist as samples, and then ran a hard
red-team on my own plan: *is it worth building?* My honest verdict was "the reframe yes,
the full pipeline no — premature, and its self-diagnosis is circular." Then the user said
the thing that reorganised the whole picture:

> all experiments so far have circled back to characters and analysing their inner
> thinking. current plan has the richest vocab and would take this trend forward.

That single sentence did what days of per-layer measurement had not: it named the
gravitational center the work had been orbiting without noticing.

## The convergence, stated as evidence

I traced what each experiment was *actually* reaching for, and the pattern is not subtle:

- **L1 agents** — who has an inner life.
- **L2 goals** — what they want.
- **L5 belief/world** — what they think is true.
- **L7 affect** — what they feel.
- **L6 causality** — the spine is `motivation.goal` + `enables`: character intention
  driving events.
- **FR-590 `encode_perspective`** — literally the character's point of view.
- **dungeon_master play** — each turn runs the cast through *private* `THINKING + INTENT`
  before the outward `DIALOGUE + EXPRESSION` (FR-486).
- **npc** — `perceive → decide → narrate`: an inner decision loop per agent.

The lanes that *worked* (L3 beats, L4 kinds, L6 edges) are the **outside** of characters —
observable events. Every lane that *struggled* (L1, L2, L5, L7) is the **inside**. The
convergence is the finding, not a coincidence: **plot is character interiority projected
into events. The outside is recognisable; the inside is authored.**

## The trap I was in

My red-team was correct in its parts and wrong in its frame. I read "the deep lanes don't
work" as "the round-trip is premature." But the deep lanes don't work *as recognisers* —
and that failure is exactly the discovery that interiority cannot be read back out of
prose. I had the evidence (L7 REFUTED, L5 stuck, belief unmeasured) and drew a stop
conclusion from it, when the same evidence read forward says *go* — stop recognising the
inside, start authoring it. The character sheet (goal + belief arc + affect arc, closed
vocabulary) is the first artifact in the whole codebase that treats interiority as a
first-class authored thing rather than a label to recover. That is the trend's natural
next step, and I nearly killed it by reading a recognition failure as a direction failure.

## What survived the reframe and what didn't

The user's lens resolved the most important doubt and left the smaller two standing — and
that split is the useful output:

- **Direction (resolved).** Authoring interiority forward is right. Keep it. It is the one
  thing `novel_generator` and `dungeon_master` do not have: characters whose behavior is
  generated from an explicit authored inner state instead of improvised per beat.
- **The comparison harness (still circular).** Re-extracting structure from the output
  with the same unreliable lanes conflates reconstruction loss with extractor noise. This
  is apparatus, not idea — demote it.
- **Marginal value (still unproven, but now locatable).** The claim to test is narrow:
  *authored inner state > improvised inner state*. Plug one character's closed-vocab
  interiority arc into dungeon_master's existing intent loop and read whether it is more
  coherent. No harness required.

## The heuristic

**A recognition failure is a direction signal, not a stop signal.** When a construct
resists being recovered from its surface, that is evidence it lives *below* the surface —
authored, not extracted. The correct response is to flip from recognising it to authoring
it, not to abandon it. (Corollary to `normalize at the boundary`: when the boundary keeps
producing a lossy projection in one direction, author in the other direction instead.)

And the meta-heuristic the user demonstrated: **when N experiments keep returning to the
same object, the object is the subject — name it before planning the N+1th.** Per-layer
metrics never surfaced "interiority"; one step back did.

## Seed

If the outside of a character is recognisable and the inside must be authored, what is the
*minimal closed vocabulary of interiority* that, once authored onto a sheet, projects into
coherent behavior — and can a single character round-trip (author inner state → act →
re-read the act) prove that authored interiority beats improvised interiority without any
plot-level comparison harness at all?
