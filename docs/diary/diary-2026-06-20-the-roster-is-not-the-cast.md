# Diary — 2026-06-20 — The Roster Is Not the Cast

**FR-547** — DM v2 fact-reversal witness flagged two different people as one fact.

## What happened

The `fact_reversal` witness exists to catch a resolved fact being silently un-resolved.
In 10032-BC it reported a reversal between `Reinmar arrived at the flood zone by the
salt road` (Ch4) and `Arnulf is still missing in the flood zone` (Ch5) — two facts
about two different people that merely share the *place* "flood zone." A reviewer
scoring the same book reported 0 breaks. A false positive: the subject matcher bound on
a shared locative token, not on the entity the fact is about.

The fix went through **three** mechanisms before it held:

1. **Locative stopword set** (the FR's first plan). Judged and rejected: premise-fragile
   (scene vocabulary is open-ended, tuned to the floodmark saga) and — worse — it
   re-introduced an FR-543-class false *negative* on the inherently-locative
   `closed <-> reopened` antonym pair (a sealed *ford* reopened is a real reversal whose
   subject IS a place). Killed in the spec.

2. **Roster-disagreement veto** (judged APPROVED, enforced to unit-green). Suppress a
   reversal when both lines name distinct *roster* characters. All 12 unit tests passed,
   all 17 siblings passed — and the live witness *still reported 1*.

3. **Corpus proper-noun entity source** (the fix that held). Derive the entity set from
   tokens capitalized non-sentence-initial >=2x across the prose, unioned with the
   roster. The live witness dropped to 0.

## The trap

`inventory_by_visibility` / `working_system_inertia`, but the sharp edge was a **premise
falsified only by measuring the live artifact**. The Judgement-v2 table confidently wrote
"`{reinmar}` / `{arnulf}` -> disjoint -> suppress." It was wrong: `Arnulf` is **not in
the roster** (`roster == [hilde, gunnar, reinmar, alva]`), though he appears 434 times in
the doc. The roster is the *reviewed* cast, not the *named* cast. I had assumed
roster == cast — the third time this exact off-roster-Arnulf class has bitten a DM
deterministic witness (FR-538 twice, now here). Each time, fixtures scoped to the roster
pass while reality, carrying off-roster NPCs, exposes the scope gap.

## What saved it

Not the unit tests — they were green on a broken mechanism, because the fixtures
encoded the same false premise as the plan (I wrote `roster={reinmar, arnulf}` into the
test, baking in the lie). What caught it was re-running the witness against the **live
book** the FR cites, the same discipline that corrected the FR-545 baseline to 0. The
green suite was a mirror of my assumption; the artifact was the witness.

When the third mechanism was proposed, I did not trust the reasoning — I measured first.
I built the candidate lexicon from the real prose and checked the one failure mode that
would silently re-break the fix: *is any locative capitalized mid-sentence?* If `Flood`
ever appeared as a capitalized event-name, both lines would share `{flood}` as an
entity, the veto would not fire, and the witness would lie again — green tests and all.
It was empirically absent (`flood/zone/ford/road/ledge/bundle/water/salt`: none in the
lexicon; `arnulf` and `aschenwulf`: both present). Only then did I approve.

## The heuristic

**`roster_is_not_cast`** — a DM deterministic witness scoped to `characters.roster` is
structurally blind to off-roster named NPCs. The roster is who the reviewer tracks, not
who the story names. Before scoping any entity-aware witness to the roster, derive the
*named* cast from the prose (proper-noun capitalization) and check the off-roster
frequency. And: **green unit tests written from the same premise as the plan cannot
falsify the plan** — when a fix turns on a factual claim about the data ("Arnulf is
rostered"), the condemning evidence must come from the artifact, not from a fixture I
authored to encode the claim.

## Seed

The proper-noun lexicon recovered the named cast for *free* from capitalization. Three
roster-blind witnesses now exist (entrance, allegiance, fact-reversal). **Should the
named-cast derivation be promoted to a shared `world_codex` the seams read, so the
roster/cast distinction is resolved once at the boundary rather than re-discovered, one
painful witness at a time?** And what is the cheapest standing test that would have
failed the *roster* mechanism — a fixture asserting that an off-roster named character
participates in the collision — that I should reach for first next time, before trusting
any roster-scoped suppression?
