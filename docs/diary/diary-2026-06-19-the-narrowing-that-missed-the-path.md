# The Narrowing That Missed the Path

*2026-06-19 — Distill, FR-537 (DM v2 chapter-scoped cast)*

## What happened

A chapter should animate only the characters it is about. The plan was simple and
felt airtight: a chapter declares a focal `cast`, and `build_allowed_scene_cast` —
the function that already computes a per-chapter allowed cast consumed in three
places — threads that cast in as a first narrowing. The FR even *rejected* a parallel
`scope_roster_to_chapter_cast` helper in its "Alternatives Considered" as a
`false_duplicate`. One narrowing point. Single source of truth. Clean.

It was wrong, and the Judge caught it before a line of code was written.

## The trap: a single narrowing point that isn't on the defect's path

The measured defect — the whole reason for the FR — was that *every turn animated
the full roster*. But the per-turn intents roster is not built by
`build_allowed_scene_cast`. It is built **inline** in `invoke_turn`, a reviewed-roster
list comprehension that then passes through `filter_roster_for_lifecycle`. Threading
the cast into `build_allowed_scene_cast` would have scoped the relationship ranking,
the final cut, and the chapter close — three real consumers — and left the actual
defect, the intents map, completely untouched. The fix would have passed its own
tests and shipped the bug.

This is the `composition_bug` from Scripture, but caught at *judge* time rather than
in production: "single narrowing point" is a virtue only when the point is on the
path the defect travels. The plan single-sourced the *resolution* but assumed a
single *application* — and the one application it chose was the wrong one. An
invariant is only honored where it is applied, not where it is resolved.

## What I did right (because the Judge forced it)

The Re-judgement (R2) overturned the FR's own rejection: a `scope_roster_to_chapter_cast`
helper *was* needed — not as a duplicate resolver, but as a second *application* of the
same single-sourced resolution. The resolution (`resolve_chapter_cast`: authored cast ∪
beats-floor) lives in one leaf; both narrowing sites — the names-shape one inside
`build_allowed_scene_cast` and the ids-shape one in `invoke_turn` — call it. The tiny
intersection-with-fallback is duplicated; the *policy* is not. `false_duplicate` was the
right instinct pointed at the wrong object: two callers of one resolver are not a
duplicate, they are the point.

The RED test that mattered asserted the **actual animated cast** — the graph payload
captured from `invoke_turn` — not just `build_allowed_scene_cast`'s return. A test that
checked only the prose-control helper would have been green while the bug rode the other
path. `name_the_seam`: the test exercises the seam the defect actually crosses.

## The smaller correction

The FR's "Related" line named `chapter_ops.chapter_beats` as the beats-floor source.
That is the *satisfied* beat accumulator — empty at turn 1, exactly when a turn-1 cast
scope needs it. The authored beats live in `turn_state.chapter_beat_list`, present from
turn 1. A plausible-looking citation that names the wrong accessor is a `downstream_fix`
in disguise: it would have produced an empty floor and silently widened every first turn
back to the full roster. Reading the real source verbatim, not the FR's description of
it, surfaced the swap.

## Seed

The Judge caught a composition bug by *reading the FR against the current code* rather
than against the FR's own narrative — `build_allowed_scene_cast` has three consumers, the
intents map is a fourth path the FR never traced. Could a mechanical pre-judge step
enumerate every consumer of a function the plan proposes to modify, and flag when the
plan's claimed coverage ("scopes ranking / final-cut / close") omits a caller the defect
description implicates? The cheapest composition bug is the one the call graph reveals
before the test is written.
