# The Outline That Had No Face

**Date:** 2026-06-15
**FR:** FR-490 (DM v2 → chapters need a face)
**Seam:** presentation / navigation (deterministic)

## What happened

FR-488 built the chapter outline as *data* and as a *navigation model* — and gave
it no surface. The single most important artifact of book scope, the plan you read
as a whole, was the one thing the writer could not see. The character-roster UI had
been copied "one level up" to chapters, and in the copy the table-of-contents view
silently evaporated, because a roster of characters and a roster of chapters *look*
alike but are *for* different things: you visit characters one at a time; you read a
plan all at once.

## The trap, sharpened

The FR-488 diary already named "it's just the old feature one level up." This FR is
the same trap biting a **different seam**. Last time it bit the data model (chapters
rhymed with characters, so the storage was copied). This time it bit
**presentation**: the rhyme is so strong that the *card* UI was reused wholesale,
and reuse-by-default dropped exactly the one view (the whole-plan overview) where
chapters and characters diverge. The rhyme is a sound the structure makes; the
purpose is what it means. Copy the sound and you lose the meaning.

## The judgement that paid for itself

The proposal's central premise was *false*: it asked to **add** a new `chapters`
overview stage. Judgement (J1) found a `chapters` stage already existed in `STAGES`
— as **dead code**: a non-visitable roster with a seed nothing ever read, zero
references, `_expand_chapters` calling `chapter_ops` directly and bypassing it
entirely. The honest move was not to add a parallel stage (which would shadow in
`STAGE_BY_NAME`) but to **repurpose** the corpse: flip its `kind`, remove its seed
(load-bearing — a seedless stage never auto-drafts), and let the generic parent
gate carry navigation with **zero** new branches in `navigation.py`. The cheapest
code was the code already written and abandoned; the second cheapest was the code I
*didn't* write because the generic path already covered it (J6).

## What confirmed it

Three deletions-that-weren't:
- `can_visit` needed no special branch — the repurposed `kind` simply stops matching
  the `roster` early-return and falls through to the `parent="synopsis"` gate.
- `_entry("chapters")` needed no new branch — it already aliases the FR-488 group
  dict, and a purity test (navigating must not mutate order/cards) passed *at RED*,
  proving the alias was already harmless.
- The forward-carried `world_state` needed no new plumbing — it was already in the
  document; the card just had to *render* it.

The live `vertex` witness made the point visible: chapter 2's card shows Hilde's
shield gone and Gunnar's sword lost to the flood — the state inherited from chapter
1, surfaced at exactly the place a writer decides what happens next.

## Heuristic

When a feature "rhymes" with an existing one, the reuse instinct fires on the
**shape**. Before copying the UI/storage/route, ask what the new thing is *for* that
the old thing is not — and protect that difference first, because it is precisely
the part the copy will silently drop. And before adding a stage/route/handler,
`grep` for its name: the thing you're about to build may already exist as a corpse,
and repurposing a corpse beats spawning a twin that shadows it.

## Seed

The `chapters` stage was dead code that the FR's own premise assumed didn't exist —
nobody noticed the corpse until a judgement walked the `STAGES` tuple by hand. What
would a *mechanical* "dead stage" check look like — a test that asserts every entry
in `STAGES` is reachable (referenced by `STAGE_BY_NAME` lookups, resolvable, and
either visitable or explicitly marked terminal) — so the next abandoned stage fails
a gate instead of waiting for a future feature to trip over it?
