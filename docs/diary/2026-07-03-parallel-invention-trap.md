# Diary: Parallel Invention Trap

**Date:** 2026-07-03
**FR:** FR-657 (agentic event deepening) — post-enforcement observation run
**Tags:** worldgen, dedup, genesis, boundary

## What Happened

Ran worldgen with FR-657's agent-based event deepening. The agent tools
(`lookup_canon_page`, `list_canon_ids`, `validate_draft`) worked correctly —
tool calls visible in the log, the agent looked up participants and locations
before deepening events. But the output was garbage: 30 genesis files grew to
60, half of them ghosts.

## The Duplicate Clusters

| Narrative Role | IDs Invented | Person Count |
|---|---|---|
| Hilde's father | bjorn, egil, leif, aldric, hermann, father_of_hilde_and_arnulf | 1 |
| Hilde's mother | astrid, egil_wife, egils_wife, gerda, helga | 1 |
| Father's death event | death_of_aschenwulf_warleader, death_of_hilde_and_arnulf_father | 1 |
| Berengar wife death | death_of_berengar_wife, wasting_fever_of_berengars_wife | 1 |
| Ulf's death | death_of_ulf, ulf_death_bear_hunt, ulf_death_in_bear_hunt | 1 |
| Ulfgar's wife | ulfgars_wife, ulfgar_wife | 1 |

## Root Cause Trace

Traced the pipeline phase-by-phase:

```
reload → anchor → select → split → deepen_events(5) → deepen_other(5) → reflect → collect → create_skeletons → gate → persist
```

**Phase 1 — Genesis (upstream, the actual weak link):**

The synopsis says "the man who killed her father" — never names him. The
`genesis_roster` prompt extracts only 2–4 principal characters. The
`structure_world` prompt then invented `aldric` as Hilde's father in her
`relationships.to` field — but never created an `aldric.yaml` page. Three
dangling refs existed from genesis:
- `hilde → to: aldric, kind: father`
- `ruedeger → to: hermann, kind: enemy killed`
- `ruedeger → to: alric, kind: brother (deceased)`

These are orphan IDs — referenced but never instantiated.

**Phase 2 — Worldgen deepen (where it multiplied):**

10 parallel map slots (5 agent, 5 LLM) each deepened an entity independently.
Each slot's `new_entities` output invented names for the same unnamed roles.
Slot 1 said "bjorn", slot 2 said "egil", slot 3 said "leif". None could see
what siblings were inventing.

**Phase 3 — collect_red_links (where it should have caught it):**

Deduplicates by exact ID only. `bjorn ≠ egil ≠ leif` → all pass. 22 "unique"
red links created, at least 10 of which are phantoms.

**Phase 4 — create_skeletons (where it materialized):**

Each red link gets a skeleton page. 22 skeleton files written. Phantoms are now
real canon pages. Next loop iteration loads them as truth.

## Trap Name: `parallel_invention`

Parallel LLM calls that independently solve the same sub-problem produce
incompatible solutions. A variant of `false_duplicate` inverted: syntactic
dedup sees no duplicates because each slot invented a different ID for the
same semantic entity.

**Pattern:** map node → each slot invents names for unnamed roles → N
different names for 1 person → ID-based dedup passes all of them.

## The Fix

The error is NOT in `deepen` or `collect`. It's in genesis `structure_world`:
it creates relationship `to:` targets it never instantiates. The constraint
must be: **every ID appearing in any `to:`, `participants:`, `references:`,
or `members:` field must be defined as a full entity in the same output.**

Two-part fix:
1. **Spec kill (immediate):** Referential integrity constraint in
   `structure_world` prompt + validation gate in `persist_genesis`.
2. **Architecture (FR):** Separate deepen from expand — deepen returns role
   descriptions (`references_needed: [{role: "father of hilde"}]`), a single
   expand node assigns canonical IDs centrally.

## Cure: `referential_integrity_at_genesis`

Every entity-creation boundary must enforce: no ID referenced without
instantiation. This is the `normalize at the boundary` law applied to the
genesis pipeline — the boundary where fictional identity enters the system.

## Seed

Can the validate_draft tool (FR-657) be repurposed as a genesis gate? It
already checks orphan refs. If structure_world output passed through
validate_draft before persist, the dangling aldric/hermann/alric would be
caught at birth instead of multiplying through worldgen iterations.
