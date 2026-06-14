# The Enum That Was Really Free Text

*2026-06-14 — FR-482, DM v2 cumulative canonical beats*

## What happened

The director returns `beats_satisfied` — "the BEATS that have now actually
occurred." It reads like an enum: a set drawn from the scene's fixed list of
beats. But it is free text. The model copies each beat "as a short phrase," and
across a run the *same* beat appears as three spellings: "Taka pulls Jarek out of
the quicksand," "Jarek is hauled from the mud," "Taka drags Jarek to solid
ground." Worse, the field oscillated between cumulative (all beats so far) and
incremental (this turn's new one) from turn to turn. A progress signal whose
meaning and vocabulary both drift is not a signal.

FR-481's Director card had just made this visible — it rendered the raw phrases
faithfully, which is exactly how the drift became undeniable. The cure here was
to stop trusting the model's phrasing and bind it to something fixed.

## The trap: a structured field whose values are unconstrained

The judgement named the real seam: the field had the *shape* of an enum (a set of
beats) but the *substance* of free text (model-authored strings). The naive fix —
`set().union(...)` across turns — would have been wrong precisely because the
values aren't an enum: unioning paraphrases accumulates near-duplicates and the
count lies. I have written that naive union before and called it "cumulative." It
isn't; it's a pile of synonyms.

The honest fix is to manufacture the missing enum. The scene's frozen `BEATS:`
block *is* the closed vocabulary the field always implied. Parse it once, match
each free phrase onto it with `difflib`, and persist canonical strings by index.
The model keeps speaking prose; the code translates prose into the scene's own
fixed terms. Normalize at the boundary where the vocabulary is certain (the
frozen scene), not where it is invented (the model's per-turn phrasing) — the
same law that governed FR-481's phase clamp, one layer down.

## The decision I'm most glad the Judge forced

My instinct was M2: ask the director to return beat *indices* into the BEATS
list. It's elegant — no fuzzy matching, the model maps its own judgement to the
canonical vocabulary at the source. The Judge rejected it with one sentence that
stuck: the motivating defect is that this model *cannot reliably speak the
field's contract*; asking it to also count and index into a list trusts the very
faculty that already failed. Determinism beats elegance when the elegant path
routes through the component you're working around. The matching is a closed,
testable, code-side problem; the indexing is another die roll.

## The drop, not the guess

`_match_beat` accepts the best canonical beat only if it clears a floor *and*
beats the runner-up by a margin; a phrase that clears nothing is dropped. The
temptation was to always assign the nearest beat — "it's probably that one." But
a wrong-but-plausible beat in a progress tracker is worse than a missing one: it
reports a beat satisfied that wasn't. Commandment 6 — when a filter yields
nothing, drop, do not substitute. The unrelated-phrase test ("the weather turned
cold overnight" → None) is the witness that the floor actually bites.

## Seed

The thresholds `0.6 / 0.1` are tuned to terse prototype beats. A production scene
with long, clause-rich beats might see a legitimate match fall below 0.6, or two
genuinely-distinct beats land within 0.1 of each other and both get dropped.
**Seed:** is character-level `difflib` ratio the right metric for matching a
short model phrase to a longer canonical beat, or should the canonical beat be
the *containing* set (token-set / subsequence containment) so "Kara corners
Tarek" scores high against "Kara corners Tarek on the last dry ledge at dusk"
regardless of the tail? When does a fixed ratio threshold become the wrong tool,
the way a fourth regex special case signals the need for a parser?
