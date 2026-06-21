# The gate that rode the writer, not the write

**Date:** 2026-06-21
**FR:** FR-558 (DM v2 Gate-on-Write Funnel, Contract C)

## What happened

Three feature requests -- FR-525, FR-528, FR-555 -- each fixed the same class of
bug: an un-playable chapter card (a removal-and-return reversal, or a time-skip
epilogue the bounded scene can never enact) reaching the doc. Each fix bound the
SAME detector at a NEW write site: the partitioner, then the unplayable check,
then the state-aware re-outline. Whack-a-mole. The detectors were never wrong;
the *binding* was. They rode the writer (a convention each new authoring path had
to remember) instead of the write (a seam every path must pass). Contract C ends
it: bind the battery to the one typed setter, so a card cannot be committed
ungated regardless of who authored it.

## The trap: the wrong arity in the spec

The FR's own sketch proposed `gate_chapter_card(card, prior_card=...)` and named
`composition_gap` as a per-card gate. The Judge caught it: `composition_gap` is a
SEQUENCE check -- it walks every adjacent (N, N+1) pair of the whole outline for
entry/exit contradictions. It has no meaning over a single card. Binding it to a
single-card setter is a category error. The cure was to split the battery by
arity: the two genuinely per-card detectors (reversal, unplayable) bind to the
write; the sequence gate stays outline-level. The cheapest bug really is the one
killed in the spec -- had I implemented the sketch verbatim, I would have built a
setter that re-runs whole-outline composition on every single-card write, wrong
and wasteful, and only discovered it under test.

## The cycle I named one FR early

In FR-556's diary I wrote: "the gate binding is FR-558's problem, and it will need
a lazy import or a write-site bind." It did. `card_gate` composes `gap_detectors`,
which imports `chapter_nav`; a top-level import of `card_gate` into the setter
would close the cycle. The lazy import inside `write_chapter_card` dodges it, and
the cost is honest and contained: the gate touches only the cold write path, while
the read getters stay leaf-pure. Naming the hazard before it existed made it a
two-line decision instead of a debugging session.

## Where the file ceiling pushed a better seam

`gap_detectors.py` was at 449 lines -- one under the hard ceiling. I could not add
the gate there. The constraint forced a question I should have asked anyway: is
the GATE the same thing as the DETECTORS? It is not. The detectors are pure
witnesses that measure; the gate composes them and *raises*. Putting them in
`card_gate.py` is not a size workaround -- it is the separation the size limit
revealed. A boundary I would have blurred under no pressure became explicit under
pressure.

## The generalization that demanded a test

Routing `reoutline_chapter_beats` through the shared battery gave it the unplayable
check it never had (FR-555 only gated reversal there). That is a new production
branch. Commandment 7 forbids a new branch without a condemning test, so before
trusting the generalization I wrote `test_reoutline_rejects_unplayable_final_beat`.
The convenient move -- "it is just reuse, the detectors are already tested" -- would
have shipped an unwitnessed path. Reuse of a tested function through a new caller
is still a new branch.

## Heuristic

When the same fix lands at three different sites across three FRs, stop fixing the
sites and ask what seam they all bypass. Bind the check to the seam, not to each
caller. And when a refactor reuses a tested function through a *new* caller, the
new caller is a new branch -- it needs its own condemning test, however well-tested
the function is.

**Seed:** Three authoring paths now share one per-card gate; the sequence gate
(`composition_gap`) still lives only in `outline_chapters`. Is there a `reoutline`
that can alter chapter adjacency without re-running composition -- a fourth
whack-a-mole waiting at the sequence arity? Should the sequence gate get its own
funnel (a `gate_chapter_set` every adjacency-altering write must pass) before the
next bug finds the gap?
