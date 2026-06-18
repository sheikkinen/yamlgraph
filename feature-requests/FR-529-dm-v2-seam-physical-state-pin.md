# Feature Request: FR-529 — DM v2: Seam-Level Physical-State Pin (positional/prop continuity)

**Priority:** MEDIUM
**Type:** Enhancement (continuity — the untracked physical lane)
**Status:** **JUDGED — scope tightened, authorized for enforce AFTER FR-532 (2026-06-18).**
The seam pin is a pure projection of fields that already exist (`Character.location`,
`WorldObject.holder/location` — verified). Scope frozen to **project existing coarse
world_state fields only**; the FR's own examples (rope knot-count, which hand holds the
pouch) are FINE-GRAINED facts NOT in world_state and are struck from claim — the pin
closes Gap 3 (coarse seam jumps) and the coarse half of Gap 1, nothing finer. Sequenced
after FR-532 (calibration decides whether finer tracking is even reader-real). See
Judgement (J1-J5).
**Effort:** ~1 day
**Requested:** 2026-06-18

## Summary

The forward-carried ledger tracks `characters[].location` and `objects[].holder/location`
([`world_state.py`](../examples/dungeon_master/api/world_state.py)) but only at **chapter
grain**, as coarse labels ("the ledge", "high valley"). It was never designed to pin the
*physical blocking* the next chapter must open from — who is above/below on the ridge,
which line configuration the rope is in, who holds which prop at the seam. So at each
chapter boundary the model re-improvises that micro-state with no ledger to contradict it,
and the independent reviewer (which reads across seams) catches the drift the generation
pipeline cannot see. This is the bulk of the `10025-BC` continuity 1/5 (Gap 1) and the
seam half of Gap 3. This FR extends `seam_packet` with a small, deterministically-rendered
**`physical_state`** block committed at chapter close and injected as a hard turn-1
opening constraint into the next chapter — the same pattern that fixed lifecycle (FR-507).

## Value Statement

A chapter opens with its characters and props in the physical configuration the prior
chapter left them in — no rope that silently re-knots, no character who was on the ridge
"emerging from the water" next chapter — closing the largest remaining share of the
continuity score.

## Problem

The continuity program's "upstream march" hardened **identity state** (lifecycle,
faction, relationships) — every win shares a property: low-cardinality, slow-changing,
discrete, and given a *typed lane the LLM never regenerates whole*. **Physical state has
no such lane.** The reviewer's complaints are almost entirely in that untracked space.
The seam is the highest-leverage, lowest-cost place to pin it: a reader (and the critic)
notices physical discontinuity most at the chapter boundary, where the prior physical
context is entirely dropped.

**Scope discipline (the category trap).** Physical micro-state is the *opposite* category
from the Wave-2 wins: high-cardinality, fast-changing, near-continuous. A full
turn-grained physical delta-ledger is effectively a physics engine and risks rebuilding
the world-simulation the LLM already performs. This FR deliberately scopes to the **seam
pin only** — a coarse snapshot at the boundary, not per-turn tracking. The turn-grained
ledger is explicitly out of scope and gated behind evidence (see Alternatives).

## Proposed Solution

### Extend `seam_packet` with a deterministically-rendered `physical_state`

At chapter close, render a bounded snapshot from the chapter's committed `world_state` —
no new LLM call; pure projection of existing typed fields:

```yaml
seam_packet:
  # ...existing resolved_events / open_threads / must_carry_facts / character_lifecycle...
  physical_state:
    characters:
      - name: Hilde
        position: "on the high ledge"        # coarse token from characters[].location
      - name: Gunnar
        position: "on the high ledge"
    props:
      - name: "the rope line"
        holder: "anchored to the ridge stake"  # from objects[].holder/location
      - name: "the food pouch"
        holder: Hilde
```

Inject it into the next chapter's turn-1 `running_scene` as a **hard opening constraint**
(the FR-507 pattern): the opening must place each named character/prop as pinned. Bounded
to a small set (on-stage characters + tracked props named in the chapter) so the snapshot
stays coarse and deterministic.

## Judgement (2026-06-18 — scope tightened, authorized after FR-532)

The mechanism is sound and the "pure projection" claim is verified against the schema.
The judgement tightens what the pin can honestly claim and orders it behind the
calibration that decides whether anything finer is worth building.

- **J1 — the projection is real and cheap (CONFIRMED).** `Character` carries `location`
  and `inventory`; `WorldObject` carries `holder` and `location` (`world_state.py`). The
  `physical_state` block is a deterministic projection of fields that already exist — no
  new LLM call, as claimed. Correct boundary, mirrors FR-507's turn-1 injection.

- **J2 — the pin can only carry what world_state records (claim NARROWED).** The FR's
  motivating examples — rope knot-count, which hand holds the pouch, above/below on the
  ledge — are FINE-GRAINED facts that do NOT exist in world_state (only a coarse
  `location` string per character, a coarse `holder` per object). The pin therefore
  closes **Gap 3 (coarse seam jumps: "on ridge" vs "emerging from water")** and the
  coarse half of Gap 1. It does NOT fix the fine-grained micro-state. Those examples are
  struck from the acceptance claim to prevent a plausible-wrong "we fixed Gap 1".

- **J3 — sequenced AFTER FR-532 (the option-2 gate).** Option 2 (turn-grained physics
  ledger) is already OUT here; even option 1 should land only once FR-532 confirms the
  continuity 1/5 is reader-real and not a seam-differ artifact. If calibration shows the
  critic over-weights physical micro-state, this FR may shrink further or be deferred.

- **J4 — RED must condemn a recorded seam, not a synthetic one.** The witness test asserts
  the pin carries the prior chapter's committed `location` into the next chapter's
  opening constraint, condemned on the actual `10025-BC` Arnulf ridge→water seam so the
  test proves the real defect, not a toy.

- **J5 — bounded by construction.** Only on-stage characters and chapter-named props are
  pinned (no whole-cast snapshot), keeping the seam packet coarse and the projection
  deterministic. Example-scoped (FR-474 J3): NO `@pytest.mark.req`; `feat(dungeon_master)`
  + changelog `type:feat scope:examples` no `req:` + diary entry.

**Scope frozen:** project existing coarse `world_state` fields into a `seam_packet.
physical_state` block + FR-507-style turn-1 hard constraint. NOT fine-grained tracking,
NOT option 2. Authorized for enforce once FR-532 reports.

## Acceptance Criteria

- [ ] `seam_packet` gains a typed `physical_state` (characters: name+position; props:
      name+holder), rendered purely from committed `world_state` at close (no LLM).
- [ ] Next chapter's turn-1 `running_scene` includes the pin as an opening constraint.
- [ ] RED condemns a recorded seam jump (e.g. `10025-BC` Arnulf ridge→water): the pin
      asserts the carried position; pre-fix the next opening is unconstrained.
- [ ] Bounded: only on-stage characters and chapter-named props are pinned (no unbounded
      growth across the book).
- [ ] Example-scoped (FR-474 J3): NO `@pytest.mark.req`; changelog `type:feat
      scope:examples`, no `req:`.
- [ ] **Corroboration (FR-522 posture, NOT a gate):** regenerate the floodmark premise;
      `scan_seam_gaps.py` reports fewer positional seam violations and the reviewer's
      continuity axis rises.

## Alternatives Considered

- **Turn-grained prop/position delta-ledger (option 2 in the doc)** — full fidelity but
  near-continuous, high-cardinality state; a delta-ledger for it is a physics engine.
  OUT OF SCOPE; revisit only if the seam pin proves insufficient on a re-witnessed run.
- **Instruct the prompt to "remember the rope"** — the FR-521 S1 trap; an instruction in
  the scene is not a gate. The pin is a deterministic constraint, not a reminder.
- **Do nothing / accept drift** — viable IF FR-532 calibration shows the critic
  over-weights physical micro-state relative to a human reader (see Related).

## Related

- `examples/dungeon_master/api/seam_packet.py`, `api/world_state.py`,
  `api/chapter_ops.py` (close + turn-1 injection), `scripts/scan_seam_gaps.py`.
- FR-507 (lifecycle hard-block at turn 1 — the pattern), FR-514/515 (delta ledger).
- FR-532 (reviewer calibration — decides whether this is reader-real before the costlier
  option 2).
- `examples/dungeon_master/docs/continuity-issues.md` §5.3, Gap 1, Gap 3, "meta-pattern".
