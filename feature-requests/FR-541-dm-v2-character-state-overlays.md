# Feature Request: DM v2 Character State Overlays (Origin Sheet + Per-Chapter Overlay)

**Priority:** MEDIUM (fixes flat/compressed character arcs across life-altering changes)
**Type:** Feature
**Status:** Judged — Approved with conditions (scope frozen 2026-06-19)
**Effort:** ~2 days
**Requested:** 2026-06-19

## Summary

Every turn, a character's `character_intent` node receives a **frozen** sheet
(`characters.cards[id]["text"]`) — identical in chapter 1 and chapter 7. A character who has
died and returned, or turned from enemy to lover across six chapters, still acts from their
origin sheet. The model has no *current* interior to animate, so arcs read flat or compressed
(10029-BC: Ch5 "Arnulf's arc compresses quickly", Ch6 "Arnulf is passive, a bystander"). This
FR splits the single frozen sheet into an **immutable origin sheet** (voice, backstory, speech)
plus a **per-chapter state overlay** (current status, allegiance, emotional posture, key
relationship deltas) layered on top at intent time. The overlay is **derived, not authored** —
accrued from the `character_state_deltas` the chapter close already computes into
`chapter_memory`.

This is **not** character forking. One roster id, one card, one animated actor — the cast
resolver (FR-537) and roster are untouched. Only the *context the intent node reads* gains a
current-state layer.

## Value Statement

A character acts from who they have *become*, not only who they began as — Arnulf returns
changed and grieving rather than re-running his pre-death sheet; Hilde leads the mixed
settlement from a posture her origin sheet never described — turning flat, frozen-sheet arcs
into ones that visibly carry their accumulated change.

## Problem

`character_intent.yaml` renders `{{ char.sheet }}` = `cards[id]["text"]`, set once at character
creation and never updated. The turn loop is a *local sampler*; identity-over-time is a *global*
property the sampler cannot synthesize from a static sheet plus a scene ledger that describes
the *world*, not the character's *interior*.

The raw material for the fix already exists but is unused at the character grain:
- `chapter_memory.character_state_deltas` — computed at `close_chapter`, today flowing only into
  the *scene* `world_state` ledger (world-grain), never back into the *character's own* context.
- `world_state.characters[].status/location` — a world-grain row, not the character's emotional
  posture or allegiance.

So the symptom is structural: discrete transitions (death→return) and gradual ones
(enemy→lover) are both invisible to the actor who is supposed to embody them.

## Proposed Solution

### 1. A derived per-chapter overlay

A pure `character_overlay.derive_overlay(doc, cid, char_id) -> dict` returning the character's
*current* state as the chapter `cid` opens, accrued from prior chapters' committed
`character_state_deltas` for that character:

```python
{
  "status": "alive, returned after being swept downriver",   # from lifecycle + deltas
  "allegiance": "paired with Gunnar; estranged from the old blood law",
  "posture": "grieving, angry, reluctantly cooperating",
  "key_relationships": ["Gunnar — former enemy, now ally/lover", "Hilde — ..."],
}
```

Deterministic accrual (no LLM): fold the per-chapter `character_state_deltas` for `char_id`
across chapters `1..cid-1`, last-write-wins per field, lifecycle transitions (FR-507 family)
taking precedence. Empty overlay (no deltas yet — e.g. chapter 1) → today's behavior exactly
(additive).

**Single-sourced accrual (judged Condition 1).** `lifecycle_resolver` **already folds**
`character_state_deltas` across chapters (L42, L150) to derive existence/lifecycle state.
`derive_overlay` MUST consume that existing accrual — extracting a shared helper if needed — and
MUST NOT re-implement a parallel fold. Two sites computing character-over-time state can disagree:
that is exactly the "one narrowing point, two paths" defect FR-537 was condemned for.

### 2. Layer the overlay into intent context

`turn_ops.invoke_turn` builds each cast bundle as `{name, sheet, previous}`; add an `overlay`
field rendered into `character_intent.yaml` as a clearly-labelled **CURRENT STATE** block,
distinct from the immutable **ORIGIN SHEET**:

```
ORIGIN (who you are — voice, history; unchanging):
{{ char.sheet }}

CURRENT STATE (who you are NOW, as this chapter opens — act from this):
{{ char.overlay }}
```

The prompt already separates "plan destination" from "current moment"; this applies the same
*now-vs-frozen* discipline to identity.

### 3. Discrete transitions are the easy trigger; gradual change is why an overlay beats a swap

A death→return is a clean lifecycle transition that *could* swap a sheet — but enemy→lover over
six chapters has no single threshold. A **continuous overlay derived from accumulated deltas**
covers both; a discrete sheet-swap covers only the first. Build the continuous form.

## Acceptance Criteria

- [ ] `character_overlay.derive_overlay` folds prior-chapter `character_state_deltas` for a
      character into a current-state dict; lifecycle transitions take precedence; empty → no
      overlay (additive).
- [ ] **(Condition 1)** `derive_overlay` consumes `lifecycle_resolver`'s existing delta fold
      (a shared helper), not a duplicated parallel fold; a test asserts both surfaces agree on a
      shared fixture.
- [ ] `invoke_turn` passes an `overlay` per cast member; `character_intent.yaml` renders it as a
      labelled CURRENT STATE block distinct from the ORIGIN SHEET.
- [ ] **(Condition 2)** Replaying a chapter leaves `cards[id]["text"]` (the origin sheet)
      byte-identical — the overlay is render-context only and never mutates origin.
- [ ] **(Condition 3)** A character with no prior deltas (chapter 1) reproduces today's intent
      context byte-identical (regression test asserts the cast bundle minus the empty overlay).
- [ ] A returned-from-death fixture surfaces the transition in the overlay; an enemy→ally delta
      chain surfaces the accumulated relationship change.
- [ ] Unit tests: deterministic accrual (fold order, last-write-wins, lifecycle precedence),
      empty-overlay fallback, intent-context layering.
- [ ] `ARCHITECTURE.md` notes the origin/overlay split as the character-grain twin of the
      world-grain `world_state` ledger.

## Alternatives Considered

- **Fork the character into two cards on a life-altering change**: rejected — double-animates
  the actor, breaks the roster and the FR-537 cast resolver, and cannot represent gradual
  change. Versioning context, not forking identity, is the correct shape.
- **Mutate the origin sheet in place at each close**: rejected — destroys the immutable voice/
  backstory the intent node relies on for consistent characterization, and makes a chapter
  replay (FR-522) non-deterministic (the sheet would depend on play history). Keep origin
  immutable; derive the overlay.
- **Author the overlay in the outline**: rejected — current state is a *consequence* of played
  turns, not an authored plan; deriving it from committed `character_state_deltas` keeps it
  truthful and replay-stable.

## Related

- [FR-537](FR-537-dm-v2-chapter-scoped-cast.md) — cast scope (untouched; overlay is per-actor
  context, not roster)
- FR-507 / FR-509 / FR-510 / FR-526 — lifecycle transition family (the discrete trigger and
  precedence source)
- FR-508 — `chapter_memory` / `character_state_deltas` (the delta source this folds)
- [turn_ops.py](../examples/dungeon_master/api/turn_ops.py) — `invoke_turn` cast-bundle build
- [chapter_ops.py](../examples/dungeon_master/api/chapter_ops.py) — `close_chapter` delta
  emission (`character_state_deltas`, chapter_ops.py ~L124)
- [lifecycle_resolver.py](../examples/dungeon_master/api/lifecycle_resolver.py) — **already folds
  `character_state_deltas`** (L42, L150); `derive_overlay` must build ON this fold, not duplicate it
- `examples/dungeon_master/prompts/character_intent.yaml` — the frozen-sheet render this layers
- `outputs/dungeon-master/10029-BC/review.md` — Ch5/Ch6 flat/compressed-arc evidence

## Judgement (2026-06-19) — APPROVED with conditions

**Verified against the codebase (claims hold):** `chapter_ops` emits `character_state_deltas` at
close (~L124); `character_intent.yaml` renders the frozen `{{ char.sheet }}`; `invoke_turn` builds
the per-cast bundle. The frozen-sheet premise and the delta source are real. The scope is genuinely
distinct — per-actor *context*, not roster (FR-537), not ledger (FR-542). No `false_duplicate`.

**Condition 1 — single-source the delta fold (the FR-537 lesson, applied).** `lifecycle_resolver`
already folds `character_state_deltas` across chapters (L42, L150) to derive existence/lifecycle
state. `derive_overlay` must **consume that existing accrual**, not re-implement a parallel fold —
otherwise two sites compute character-over-time state and can disagree (precisely the
"one narrowing point, two paths" defect FR-537 was condemned for). Extract a shared accrual helper
if lifecycle_resolver's is not directly reusable; do not copy it.

**Condition 2 — overlay is render-context only; never mutates origin.** The immutability of
`cards[id]["text"]` is the invariant that keeps replay (FR-522) deterministic. The AC forbidding
origin mutation must be a test that re-plays a chapter and asserts the origin sheet is byte-identical.

**Condition 3 — the empty-overlay regression AC is load-bearing.** "Chapter 1 reproduces today's
intent context byte-identical minus the empty overlay" must be a real assertion on the cast bundle,
not prose. This is the additive-safety proof.

**Scope frozen.** Effort (~2d) accepted. This is the lowest-risk of the three (pure additive
context layer, no gate, no re-roll). Authority granted once Conditions 1–3 are in the ACs.

**Sequencing note:** FR-541 reads cleanest *after* FR-542's close-boundary reconciliation lands —
an overlay derived from an un-reconciled ledger would faithfully render a resurrection. Not a
blocker, but enforce FR-542 part A first for best signal.

## Implementation (2026-06-19) — ENFORCED

Enforced AFTER FR-542 Part A, per the sequencing note.

- **Overlay derivation:** new leaf `api/character_overlay.py`. `derive_overlay(doc, cid, name)`
  walks the chapters BEFORE `cid` in `chapters.order`, folds each committed `chapter_memory`, and
  records every state transition for `name`; returns `{status, history}` (last-write-wins) or `{}`
  when no prior transition exists.
- **Condition 1 (reuse the fold):** `derive_overlay` imports and calls
  `lifecycle_resolver._state_map_from_memory` — the existing per-chapter delta fold — rather than
  duplicating it (the FR-537 "one narrowing point, two paths" lesson).
  `test_overlay_reuses_lifecycle_resolver_fold` asserts the overlay status agrees with the direct
  fold output.
- **Intent layering:** `turn_ops.invoke_turn` carries `overlay` in each cast bundle;
  `character_intent.yaml` renders it as a `CURRENT STATE` block that OVERRIDES past-tense origin
  detail, ALONGSIDE the relabeled `ORIGIN SHEET` (never replacing it).
- **Condition 3 (additive):** an empty overlay renders no block, so a chapter with no prior delta
  reproduces today's intent context exactly (`test_invoke_turn_chapter_one_overlay_is_empty`).
- 7 tests (`test_character_overlay.py`); 364 DM tests green; all gates clean.
