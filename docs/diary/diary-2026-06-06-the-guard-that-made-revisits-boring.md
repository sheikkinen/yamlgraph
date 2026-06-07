# The Guard That Made Revisits Boring — 2026-06-06 (FR-471)

## What happened

Phase B of the DM web UI v2 turned the inert chapter skeleton into a browseable,
inline-editable outline. The whole phase hinged on one small decision that the
judge had already frozen: **do not add a `beats` node to `preplan.yaml`**. The
original acceptance criteria asked for exactly that. The judgment overruled it
in favor of lazy, on-demand materialization on the first chapter visit.

Writing the code proved the judgment right for a reason I hadn't fully felt at
plan time: a preplan-time `beats` node would have to run for *every* chapter
eagerly — the exact "eager weave" anti-pattern Phase A had just deleted one layer
up. The same purpose-drift, one ring out.

## The trap

**`materialized` as an afterthought.** My first instinct was to generate stubs
in `navigate` and write them back — clean enough. But the witness test
`test_beat_stubs_not_rerolled_on_revisit` forced the question: what happens on
the *second* visit? Without a guard, every revisit re-rolls the stubs and
silently discards the DM's edits. The bug wouldn't crash; it would just quietly
erase work — a *plausible wrong answer*, the hardest kind to catch.

The cure was a one-field guard (`ch["materialized"]`) checked at the boundary
where generation happens (`_materialize`), not downstream where the symptom
(lost edits) manifests. Normalize at the boundary, again.

## The insight

**The idempotency test is the spec.** I wrote `test_beat_stubs_not_rerolled_on_revisit`
not to check a feature but to pin an invariant: *navigation is a read that may
fill once, never a re-roll*. That single RED test is worth more than the three
edit-persistence tests combined, because persistence is obvious and re-roll is
invisible until it bites. The boring revisit is the proof the guard works.

## Seed

The `materialized` flag is per-chapter boolean state living in the same document
as the content it guards. Phase C will add per-beat status (`planned →
generated → committed`). **Seed:** when does a flat status flag stop being enough
and demand a real state machine — and would a YAMLGraph FSM over the beat's
lifecycle be clearer than scattered string comparisons in the session layer?
