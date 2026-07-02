# FR-654: Re-deepen seed characters with structured fields

**Priority:** LOW
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.25 days
**Requested:** 2026-07-02

## Summary

Seed characters (kaelen, maren, voss) have rich prose descriptions but 0 structured `relationships` entries. The select_thin filter correctly identifies them as "thin" but they compete with brand-new skeleton pages for deepening slots, so seeds often get skipped.

## Value Statement

The three protagonists are the narrative core — without structured relationships they're disconnected from the entity graph that secondary characters build around them.

## Problem

After 3 loops:
- kaelen: 0 relationships, no backstory field (prose is in `description`)
- maren: 0 relationships, no backstory field
- voss: 0 relationships, no backstory field
- Meanwhile commander_taris (depth 1): 5 relationships, full backstory

The seed data predates the deepening schema. Seeds have `description` (prose) but no `backstory`, `relationships` list, `triggers`, or `fears`. The select_thin scorer correctly flags them, but with 5-7 candidates per loop and a map limit of 5, seeds compete with new entities.

## Proposed Solution

Add priority weighting in `select_thin`: pages with `lane: dynamic` and `depth: 0` (or missing depth) that are `character` type get a thin_score bonus, ensuring seed characters are deepened before new skeletons.

Alternative: Run a one-time "seed enrichment" pass before the main loop that deepens only seed characters.

## Acceptance Criteria

- [ ] Seed characters are prioritized for deepening
- [ ] After pipeline run, seed characters have structured relationships
- [ ] Test covers priority weighting for seed characters

## Related

- [nodes/select_thin.py](../examples/novel_fandom/nodes/select_thin.py)
- Seed files: canon/character/kaelen.yaml, maren.yaml, voss.yaml

## Judgement

**Verdict: Granted with amendments.**

### What's sound
- The problem is real — protagonists are thinnest but lose to skeletons.
- Fixing in select_thin is the right place.

### Amendments

1. **Bonus, not override.** Don't force seeds first — add +2 to thin_score for pages with `depth: 0` or missing depth. This keeps the sort deterministic and audit-friendly.
2. **Drop the alternative** (one-time seed enrichment pass). Adding a graph node for a one-time operation is over-engineering. The thin_score bonus handles it within existing loop mechanics.
3. **All types, not just character.** Seeds of any type (faction, event) also lack structured fields. Apply the depth-0 bonus universally.

### Scope freeze
One file: `select_thin.py`. One constant (depth-0 bonus value). One test.
