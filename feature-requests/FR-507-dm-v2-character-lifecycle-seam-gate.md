# Feature Request: FR-507 - DM v2 Character Lifecycle Seam Gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged - Granted
**Effort:** ~2 days
**Requested:** 2026-06-17

## Summary

FR-506 added typed chapter seam packets, but run 10008 showed a critical continuity
failure: Arnulf is marked presumed dead at chapter 2 end, then appears physically
in chapter 3 before the planned chapter 5 return event. This FR adds a deterministic
character lifecycle gate so reveal arcs cannot be violated by chapter opening prose.

## Redraft Response To Judgement

This redraft resolves the five blocking judgement issues explicitly:

1. Non-overlapping lifecycle FSM is now defined.
2. Earliest reappearance source and precedence are now defined.
3. Deterministic validator inputs are structured, not free-prose matching.
4. Fail-fast error type, payload, and propagation path are now defined.
5. Parse/normalize responsibilities are separated from semantic validation.

## Re-Judgement

Decision: **Granted.**

Judgement check against prior blockers:

1. **Lifecycle state overlap resolved** - non-overlapping FSM now defined via
   `existence_state` plus explicit reappearance transition.
2. **Earliest reappearance source clarified** - chapter indexing, null semantics,
   and precedence are now explicit.
3. **Deterministic detection surface clarified** - validator inputs are structured
   (`lifecycle map + chapter id + candidate active cast`), not prose-only.
4. **Fail-fast contract clarified** - typed `LifecycleGateError`, payload shape,
   logging, and propagation path are defined.
5. **Normalization vs semantic validation separated** - parse-time shape safety vs
   validator-time contract safety are explicitly split.

Grant scope notes:
- FR-507 is approved for implementation as a deterministic lifecycle gate on
  chapter turn-1 entry.
- Resurrection from `confirmed_dead` remains out of scope (explicitly terminal in
  this FR).
- Witness criteria (A5) remain required for closure, but do not block starting
  enforcement work.

## Value Statement

Writers get reliable reveal pacing: characters cannot reappear before the planned
return chapter, preserving causality and narrative trust across chapter seams.

## Problem

Current continuity contracts are prose-oriented and too permissive for reveal-state
transitions:
- Character sheet text describes intent ("survives and returns") but is not a hard
  timeline gate.
- Seam packet must-carry facts are free text and checked with literal substring
  matching, which is brittle and does not enforce lifecycle transitions.
- Chapter opening generation can reintroduce a character physically before the
  return beat, even when chapter outline says return happens later.

Observed in run 10008:
- Chapter 2 prose says Arnulf is "presumed dead".
- Chapter 3 opening shows Arnulf present and acting.
- Chapter 5 is titled as return, but return has already happened in prose.

This is a causality defect, not merely stylistic roughness.

## Proposed Solution

Add a typed character lifecycle contract that is emitted at chapter close and
validated at next chapter opening before turn generation proceeds.

### 1) Add lifecycle state to seam packet (in scope)

Extend seam packet with optional per-character lifecycle entries:
- `character_lifecycle`: list[dict]
  - `name`: str
  - `existence_state`: one of `alive`, `missing_presumed_dead`, `confirmed_dead`
  - `visibility_mode`: one of `present`, `absent`, `rumor_only`
  - `allowed_reappearance_from_chapter`: int | null
  - `source_chapter`: int  # chapter that emitted this lifecycle record

Finite state machine (canonical axis):
- `alive -> missing_presumed_dead`
- `alive -> confirmed_dead`
- `missing_presumed_dead -> alive` (reappearance transition)
- `confirmed_dead` is terminal in FR-507 (no resurrection path in scope)

`allowed_reappearance_from_chapter` semantics:
- 1-based chapter id (same indexing as `chapters.order`).
- `null` means no delayed reappearance gate is active.
- Precedence: chapter outline beat intent (if explicit) > previous chapter seam
  lifecycle carry > runtime default (`null`).

Boundary normalization rules (parse-time only):
- Unknown/invalid values normalize to safe shape defaults.
- Duplicate character lifecycle entries dedupe by lowercased name, keeping first.
- Lists are bounded (same limits as seam packet lists) and strings truncated.

Semantic invalidity is not handled in parse-time normalization; it is reported by
the lifecycle validator in step 2.

### 2) Add deterministic lifecycle validator (in scope)

Add pure validator over structured deterministic inputs:
- previous chapter lifecycle map,
- target chapter id,
- candidate turn-1 active cast ids (before map fanout),
- chapter metadata (title/summary/beats text only for optional hint diagnostics,
  not as primary truth source).

Primary violations:
- `early_return_violation`: character appears physically before
  `allowed_reappearance_from_chapter`.
- `state_contradiction_violation`: lifecycle transition violates FSM.
- `visibility_contradiction_violation`: candidate active cast conflicts with
  lifecycle `visibility_mode`.

Validation output must be typed and exact (character name + offending claim).

### 3) Gate turn-1 generation on lifecycle violations (in scope)

For chapter N+1 turn 1 in `turn_ops.invoke_turn`:
- Build candidate active cast from reviewed roster.
- Run deterministic lifecycle validator before map fanout.
- If lifecycle violations exist, raise `LifecycleGateError` (new typed exception)
  with payload:

  ```json
  {
    "code": "LIFECYCLE_GATE_VIOLATION",
    "chapter_id": "3",
    "turn_n": 1,
    "violations": [
      {
        "type": "early_return_violation",
        "name": "Arnulf",
        "detail": "present before chapter 5"
      }
    ]
  }
  ```

- Log at warning level with the same payload.
- Propagate to existing session error-banner surface via exception path; do not
  silently continue generation.

Note: this FR is strict by design (Commandment 6: no silent fallback).

### 4) Prompt contract tightening for return arcs (in scope)

Update turn-direct and character-intent prompt instructions:
- If lifecycle says `missing_presumed_dead`, allow only memory/rumor mentions; no physical
  presence/action.
- Allow physical presence only when validator has admitted cast at chapter index.

Prompt updates are secondary; deterministic gate is primary.

## Acceptance Criteria

- [x] **A1 - Lifecycle schema exists and is normalized.**
  Seam packet supports `character_lifecycle` entries with
  `existence_state`, `visibility_mode`, `allowed_reappearance_from_chapter`,
  and `source_chapter`; parse-time normalization is shape-safe and
  migration-safe.

- [x] **A2 - Deterministic validator enforces return timing.**
  Validator consumes structured inputs (lifecycle map + chapter id + candidate
  active cast) and emits typed lifecycle violations (`early_return_violation`,
  `state_contradiction_violation`, `visibility_contradiction_violation`) with
  character-level payload.

- [x] **A3 - Turn-1 gate blocks contradictory openings.**
  Chapter turn-1 generation raises `LifecycleGateError` with code
  `LIFECYCLE_GATE_VIOLATION`, logs payload, and surfaces via existing error
  banner path when lifecycle violations are present.

- [x] **A4 - Regression proof on 10008 pattern.**
  A fixture reproducing chapter 2 `missing_presumed_dead` -> chapter 3 active
  Arnulf cast now fails deterministically before map fanout and prose
  continuation.

- [ ] **A5 - Floodmark witness non-regression.**
      New witness run shows zero early-return lifecycle violations and no regression
      in FR-505 prose quality signals.

- [x] **A6 - Tests and docs updated.**
  Unit tests for lifecycle parse normalization and semantic validator (separate
  suites), integration tests for turn-1 gate exception/log payloads, and DM
  architecture docs updated with lifecycle FSM + gate contract.

## Implementation Status (2026-06-17)

Completed in this enforcement pass:
- Added typed `character_lifecycle` support to seam packet parsing and defaults.
- Implemented deterministic `validate_character_lifecycle(...)` with typed
  violations (`early_return_violation`, `state_contradiction_violation`,
  `visibility_contradiction_violation`).
- Added turn-1 lifecycle gate in `turn_ops.invoke_turn` with new
  `LifecycleGateError` payload contract (`code=LIFECYCLE_GATE_VIOLATION`).
- Added regression fixture for 10008-style early return gate failure in
  `test_lifecycle_gate.py`.
- Updated chapter-open prompt guidance and DM architecture docs for lifecycle
  seam behavior.

Validation evidence:
- `python -m pytest examples/dungeon_master/tests/test_seam_packet.py examples/dungeon_master/tests/test_lifecycle_gate.py --no-cov -q`
  -> `9 passed`
- `python -m pytest examples/dungeon_master/tests --no-cov -q`
  -> `133 passed`
- `python -m ruff check ...` on changed FR-507 files -> clean.

Pending for full FR closure:
- A5 Floodmark witness non-regression run and recorded evidence.

Witness reflection (run 10009):
- Narrative causality improved versus 10008 (no chapter-open dead->alive snap).
- Structured lifecycle metadata drift remained: chapter-close emitted
  `allowed_reappearance_from_chapter` earlier than the intended outline return
  chapter for Arnulf.
- Follow-up fix implemented in this FR: chapter-close now clamps lifecycle
  reappearance floor to the first chapter-plan return signal (title/summary/beats)
  for the same character, preventing provider-proposed early return windows.

## Alternatives Considered

1. Keep lifecycle only in character sheet text.
Result: rejected. Character sheet is descriptive profile, not temporal authority.

2. Rely on reviewer post-hoc detection only.
Result: rejected. Detection after generation is too late for causal correctness.

3. Soft warning instead of fail-fast gate.
Result: rejected. Continuity defects must block progression, not be advisory.

## Enforce Sequence (TDD)

1. RED: add fixtures for early-return contradiction and expected typed violations.
2. RED: add integration test asserting chapter turn-1 generation is blocked on
   lifecycle violation.
3. GREEN: implement lifecycle parse normalization (shape only).
4. GREEN: implement semantic validator (FSM + reappearance timing + visibility).
5. GREEN: wire validator into turn-1 gate path with `LifecycleGateError` payload.
6. GREEN: tighten prompt instructions for lifecycle awareness.
7. WITNESS: run next Floodmark generation and record lifecycle-violation count,
   plus prose non-regression evidence.
8. Distill: diary reflection on lifecycle-state boundaries vs prose-only constraints.

## Related

- FR-506 - DM v2 chapter seam continuity contract
- FR-505 - final cut prose de-gridding
- Run evidence: outputs/dungeon-master/10008-BC/story.md and
  outputs/dungeon-master/10008-BC/story.json
