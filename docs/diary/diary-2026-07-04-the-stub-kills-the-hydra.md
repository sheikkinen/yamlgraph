# Diary: The Stub Kills the Hydra

**Date:** 2026-07-04
**FRs:** FR-664, FR-665, FR-667

## Observation

The novel_fandom genesis pipeline produced parallel-invention duplicates:
`aldric` / `alric` / `aldric_stonehand` all referencing the same narrative
role. Each worldgen loop iteration invented new characters for red links
that pointed to slightly different spellings of the same entity. Previous
run: 31 genesis files → 60+ after worldgen, with ~30 ghost duplicates.

The trilogy attacked the problem at three layers:
1. **FR-667** (genesis stubs): Collapsed 8 LLM calls into 2. One synopsis
   call + one structured stub call that produces all entities with explicit
   IDs. No LLM-per-character means no per-character ID drift.
2. **FR-664** (referential integrity): Validate all cross-references
   resolve to defined IDs before persisting. Zero orphans on first run.
3. **FR-665** (semantic dedup): Deterministic merge of possessives
   (`ulfs → ulf`), articles (`the_X → X`), and stop-word prefixes.
   Runs between `collect` and `create_skeletons` in worldgen.

## Results

| Metric              | Before (FR-655) | After (FR-667 trilogy) |
|---------------------|-----------------|------------------------|
| Genesis LLM calls   | 8–9             | 2                      |
| Genesis files        | ~31             | 31                     |
| Orphan IDs           | 3–5             | 0                      |
| Worldgen duplicates  | ~30 ghosts      | 1 false positive       |
| Post-worldgen files  | 60+             | 61                     |
| Worldgen iterations  | 3               | 3                      |

Post-worldgen: 22 characters, 16 events, 14 locations, 3 factions, 4
rules. Growth was additive (30 new entities deepening red links), not
multiplicative (ghost clones).

## Trap

**`the_one_law` vindication**: The duplicate hydra was a boundary defect.
Each LLM call in the old genesis was an independent boundary crossing. Each
crossing invented its own IDs with no shared namespace. Normalizing at the
boundary (one structured call, one ID namespace) killed the hydra at birth.

Secondary trap: **false positive in possessive dedup**. `ulfs` was treated
as the possessive form of `ulf` and merged. But these were two distinct
characters: Ulf (Frida's husband, trapper, rockfall) and Ulfs/Uwe
(Gunnar's father, war-leader, feud wound). The LLM had already named them
differently in the structured output but worldgen's red link expansion
created `ulfs` as a new entity in a later iteration. The possessive
stripping then collapsed them.

Third: **parallel invention still lives**, just weakened. `gunnars_father`
(named Uwe) and `ulfs` (named Ulf) both claim to be "Gunnar's father" —
two worldgen iterations invented the same role independently. Dedup's
deterministic pass can't catch this because the IDs share no lexical
similarity. Only the LLM dedup pass (currently gated at threshold 5) or
a relationship-graph validator could.

## Heuristic

**Reduce boundary crossings to reduce boundary defects.** The old genesis
made 8 LLM calls — 8 chances for ID drift. The new one makes 2. The
duplicate count dropped from ~30 to 1. Not because dedup got smarter, but
because there was almost nothing left to dedup. The cheapest dedup is the
one that never runs.

This is `the_one_law` applied to pipeline architecture: every LLM call is
a boundary. Minimize boundaries, minimize defects. The structured output
schema acts as the normalizer — one Pydantic model enforces one namespace.

## Cure

**structured_output_as_namespace**: When multiple entities must share a
referential namespace, produce them in a single structured LLM call with
explicit IDs. Never let N independent calls invent N independent
namespaces. The schema is the normalizer.

## Seed

The possessive dedup false positive reveals a deeper question: **should
dedup operate on IDs or on narrative roles?** `ulf` and `ulfs` have
different IDs but — in the LLM's mind — might be the same character. The
LLM dedup pass could catch this, but it's gated at threshold 5. What if
relationship-graph analysis (find all X where X.relationships reference
the same target with the same role) were the dedup signal instead of
string similarity? The graph knows what strings can't: that two nodes
claiming to be "Gunnar's father" are the same node, regardless of their
IDs. FR candidate: relationship-based dedup.
