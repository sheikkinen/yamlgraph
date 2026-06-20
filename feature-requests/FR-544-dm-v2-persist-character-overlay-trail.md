# Feature Request: DM v2 Persist Character Overlay Trail for Review

**Priority:** MEDIUM (review observability gap, not a generation defect)
**Type:** Feature
**Status:** Enforced (RED d1889a7c, GREEN this commit) -- `overlay_trail` block live in the witness
**Effort:** ~0.25 day
**Requested:** 2026-06-20

## Summary

The FR-541 derived per-chapter character overlay (`character_overlay.derive_overlay`) is
computed at intent time, injected into the `character_intent` prompt's CURRENT STATE block,
and then **discarded** — it is never written to `story.json` (verified: `grep -c '"overlay"'`
on a story doc returns 0). A reviewer auditing a finished book cannot answer "what CURRENT
STATE did this character carry into chapter N?" without re-running `derive_overlay` in a
Python shell. This FR persists the overlay **trail** — every character's per-chapter derived
state — into the existing continuity witness artifact so it travels with the run and is
readable during review.

## Value Statement

A reviewer (human or `book_reviewer`) can open one machine-readable file and see, per chapter,
what state each character was acting from — turning the FR-541 overlay from an invisible
intermediate into an auditable trail. This makes overlay drift (e.g. a character who died in
Ch2 still acting alive in Ch4 because no delta was committed) visible at review time, exactly
where continuity breaks are diagnosed.

## Problem

The overlay is correctly designed as a **derived projection** (`the_one_law`: derived state is
recomputed at the consumption boundary, never stored, so it cannot drift from its source). That
is right for the generation path — but it leaves a **review-time observability gap**:

- `derive_overlay(doc, cid, name)` is the only place the overlay exists, and only in memory
  inside `turn_ops.invoke_turn` (the `cast["overlay"]` bundle field).
- `story.json` persists the *source* (`chapter_memory` / `character_state_deltas`) but not the
  *fold* the LLM actually saw.
- So a reviewer reading `review.md` against `story.json` cannot reconstruct the overlay the
  intent node consumed without writing code.

This is NOT a request to persist overlay as authored state (that would invite drift). It is a
request to **emit the derived trail as a witness**, the same posture already established for
the seam-entrance and fact-reversal witnesses (FR-538 / FR-542 B): measurement-first,
visibility-not-gate, additive, recomputed from the committed source.

## Proposed Solution

Add a deterministic overlay-trail summary to the continuity witness, mirroring the existing
`seam_entrance_summary` / `fact_reversal_summary` aggregators.

1. **`overlay_trail_summary(story_doc) -> dict`** in
   `examples/dungeon_master/scripts/emit_continuity_witness.py`. Walk `chapters.order`; for each
   chapter, for each reviewed roster character, call the existing
   `character_overlay.derive_overlay(doc, cid, name)` (REUSE — no new derivation logic) and
   collect the non-empty results. Shape (additive to the witness JSON):

   ```json
   "overlay_trail": {
     "transition_count": 3,
     "by_chapter": [
       {"chapter": "3", "characters": [
         {"name": "Arnulf", "status": "alive, hauled out far downstream",
          "history": ["chapter 2: swept downstream", "chapter 3: alive, hauled out far downstream"]}
       ]}
     ]
   }
   ```

   Chapters/characters with an empty overlay (`{}`) are omitted (additive — an empty trail
   reproduces today's silence). Roster lens only, matching `seam_entrance_summary`.

2. **Wire into `write_witness`** alongside the existing summaries, so `continuity_witness.json`
   gains the `overlay_trail` block on every run. No change to `story.json`; no change to the
   generation path; no gate.

## Acceptance Criteria

- [ ] RED test (committed separately, `SKIP=pytest`) over a fixture story doc with prior
      committed `character_state_deltas`: `overlay_trail_summary` returns the per-chapter
      derived status + history for each character with a transition, and omits characters with
      an empty overlay. Asserts `transition_count` and a specific `{chapter, name, status,
      history}` row.
- [ ] `overlay_trail_summary` reuses `derive_overlay` (no duplicated accrual logic) and is pure
      (never mutates the doc).
- [ ] `write_witness` includes the `overlay_trail` block in `continuity_witness.json`; the
      witness regression test asserts the key is present.
- [ ] Posture is `visibility-not-gate`: a non-empty trail never fails the run or CI.
- [ ] `story.json` is unchanged (the overlay remains a derived projection, not authored state).
- [ ] Existing FR-538 / FR-542 witness fixtures still pass.
- [ ] Changelog fragment (`type: feat`, `scope: examples`, no `req:` — example-exempt).
- [ ] Distill diary entry.

## Alternatives Considered

- **Persist overlay into `story.json` per chapter card**: rejected. The overlay is a derived
  fold of `chapter_memory`; storing it duplicates the source and invites drift (the exact
  `downstream_fix` / stored-derived-state trap `the_one_law` warns against). The witness is the
  correct home for derived measurements.
- **A standalone `dump_overlay_trail.py` script** the reviewer runs on demand: rejected as the
  primary path — it does not travel with the run, so a reviewer reading an archived book still
  has no trail. (It could be added later as a convenience, but the witness JSON is the durable
  record.)
- **Render the overlay into `story.md`**: rejected — `story.md` is the reader-facing prose; the
  derived state trail is a review/debug artifact and belongs in the witness, not the book.

## Related

- `examples/dungeon_master/api/character_overlay.py` — `derive_overlay` (the source projection)
- `examples/dungeon_master/api/turn_ops.py` — `invoke_turn` (the only current consumer)
- `examples/dungeon_master/scripts/emit_continuity_witness.py` — `seam_entrance_summary`,
  `fact_reversal_summary`, `write_witness` (the witness pattern to mirror)
- `feature-requests/FR-541-dm-v2-derived-character-state-overlay.md` (the overlay this exposes)
- `feature-requests/FR-538-dm-v2-seam-entrance-witness.md` (the visibility-not-gate posture)
- Evidence: `outputs/dungeon-master/10031-BC/continuity_witness.json` (target artifact),
  `review.md` (the review surface the trail supports)

## Judgement (2026-06-20) — APPROVED (minor conditions)

**Premise verified, scope is minimal and correctly layered.** Confirmed against the live code:
the overlay is wired and consumed (`turn_ops.invoke_turn` L200 → `cast["overlay"]` →
`character_intent.yaml` CURRENT STATE block) but **never persisted** (`grep -c '"overlay"'` on a
story doc = 0). The witness home (not `story.json`) is the right call — storing a derived fold
would duplicate `chapter_memory` and invite drift (`the_one_law`). The reuse-`derive_overlay`,
roster-lens, visibility-not-gate, RED-first ACs mirror the FR-538/542 witnesses exactly. No
over-scope. Approve.

**Condition 1 — set expectations: the trail will be SPARSE, and that is the point.** Verified
against real 10031-BC data: `character_state_deltas` (the overlay's only source via
`_state_map_from_memory`) records **only** `Arnulf → missing_presumed_dead`, the same delta every
chapter; several chapters have zero deltas. So `derive_overlay` returns `{}` for nearly every
character, and the emitted `overlay_trail` will contain essentially one character. The implementer
must NOT treat a near-empty trail as a bug — a thin trail is a **true** measurement, and surfacing
that thinness is precisely the diagnostic value (it shows the overlay carries almost nothing
because the deltas are thin). Add a one-line note in the emitter docstring to this effect.

**Condition 2 — this FR is the cheap evidence FR-545 actually needs (sequence it first).** The
same sparsity finding that conditions this FR is the load-bearing reason FR-545's allegiance-reset
detector cannot work as specified (its inputs are stable/empty where the prose flips). Landing
FR-544 first makes the delta thinness visible in every run's witness, turning an ad-hoc Python
probe into a standing signal — exactly the observability FR-545's redesign will depend on. No
change to this FR's scope; just sequence FR-544 before any FR-545 rework.

**Verdict.** APPROVED for enforce as written, with the two notes folded into the emitter docstring
(sparse-is-truth) and the RED test asserting a `{}`-overlay character is omitted (already an AC).
Effort holds at ~0.25d.

## Implementation (2026-06-20) — Enforced

- **RED** `d1889a7c` (`SKIP=pytest`): four failing tests in
  `examples/dungeon_master/tests/test_emit_continuity_witness.py` — per-(chapter, character)
  overlay rows, empty-overlay characters omitted, no doc mutation, additive `overlay_trail` block
  in `write_witness`.
- **GREEN** (this commit): `overlay_trail_summary(story_doc)` in `emit_continuity_witness.py`
  reuses `character_overlay.derive_overlay` (no duplicated accrual), roster-lens, omits `{}`
  overlays, stamps `posture: visibility-not-gate`; wired into `write_witness` alongside
  `seam_entrance` / `fact_reversal`. Sparse-is-truth note folded into the emitter docstring (J1).
  `story.json` unchanged (J: derived projection stays out of the store). 9/9 witness tests pass.
- Changelog: `changelog/unreleased/fr544-overlay-trail-witness.md`. Diary:
  `docs/diary/diary-2026-06-20-the-trail-meant-to-be-thin.md`.
- **Deviation:** none. Scope held exactly as judged.
