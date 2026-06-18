# Feature Request: FR-509 - DM v2 Lifecycle Source-Of-Truth Cast Filter

**Priority:** HIGH
**Type:** Bugfix / Enforcement Hardening
**Status:** Judged - Granted
**Effort:** ~1-2 days
**Requested:** 2026-06-17

## Summary

Close the remaining lifecycle continuity defect by enforcing lifecycle constraints
at cast assembly time (before turn graph invocation), using the canonical seam
source from chapter N-1 as the single event-timing authority for chapter N turn 1.

## Judgement

Decision: **Granted.**

Rationale:
- Problem statement is concrete and witnessed (10012 completion parity with
  residual lifecycle violations).
- Proposed fix targets boundary normalization (cast admission) rather than
  weakening existing lifecycle gate enforcement.
- Scope is small enough for a focused enforcement slice while preserving
  FR-507/FR-508 contracts.

Grant conditions (scope freeze):
1. The cast filter must consume the same normalized lifecycle map helper used by
  lifecycle gate evaluation to prevent policy drift.
2. Character identity matching must be deterministic (`roster_id -> canonical
  display name`) and case-insensitive where needed.
3. Turn-1 filter must be authoritative; turn `n > 1` behavior remains unchanged
  in this FR except for explicit lifecycle-forbidden presence.
4. If filtering would admit no active cast at chapter-open, surface a typed
  lifecycle gate error (no silent fallback to unfiltered roster).
5. Enforcement must not change witness metric definitions; only runtime behavior
  may change.

Out-of-scope (explicit):
- New resurrection semantics.
- Prompt-only lifecycle fixes.
- Rewriting FR-508 witness scoring logic.

## Value Statement

FR-508 improved pacing/completion (run 10012 reached completion parity), but
continuity still fails due to repeated `LIFECYCLE_GATE_VIOLATION` events.
This FR removes the leak path that lets lifecycle-invalid characters enter
candidate active cast, reducing violation count to zero without weakening gates.

## Problem

Current flow in `turn_ops.invoke_turn` builds candidate active cast from reviewed
roster first, then runs lifecycle gate:
- reviewed roster -> candidate cast
- lifecycle gate validates candidate cast

This means lifecycle-invalid membership is detected late and repeatedly, causing:
- repeated turn-1 gate failures in mid-book chapters,
- wasted generation attempts,
- witness failure despite otherwise successful chapter completion.

Observed in run 10012:
- Completion parity: `completed_chapter_count == planned_chapter_count` (7/7)
- Remaining blocker: `lifecycle_gate_violation_count = 5`
- Violations concentrated at chapter opens before planned Arnulf return chapter.

## Scope

In scope:
- deterministic cast filtering from canonical lifecycle seam source
- hard enforcement of planned reappearance floors at cast-assembly boundary
- targeted tests for early-return suppression and no-regression on valid casts
- witness rerun criteria for closure

Out of scope:
- resurrection semantics beyond existing lifecycle FSM
- prompt-only mitigations as primary fix
- changing witness thresholds

## Proposed Solution

### 1) Add deterministic lifecycle-aware cast filter

Add a pure helper in `turn_ops.py` that derives the **allowed active cast ids** for
chapter `cid`, turn `n`, from:
- reviewed roster ids
- canonical seam lifecycle map (chapter `cid-1` seam packet)
- chapter index + allowed reappearance metadata

Behavior:
- if `n == 1`, exclude characters that violate lifecycle timing/visibility
  (`missing_presumed_dead`, `confirmed_dead`, `absent`, `rumor_only`,
  early reappearance before `allowed_reappearance_from_chapter`)
- if `n > 1`, preserve current behavior unless lifecycle still explicitly forbids
  active presence

The lifecycle gate remains in place and must still fail if invalid state leaks.

### 2) Make source pointer explicit for cast filtering

Cast filter must use the same canonical source pointer contract as FR-508:
- chapter N opening reads only chapter N-1 committed seam packet
- no chapter N in-progress state used as opening lifecycle authority

If prior seam is missing, use deterministic empty seam defaults and record warning
`CONTINUITY_MIGRATION_DEFAULT_APPLIED`.

### 3) Enforce reappearance floor as boundary normalization

At cast-filter boundary, apply deterministic floor check:
- if planned return chapter for character is `k`, character cannot enter active
  cast before chapter `k`
- this rule is enforced regardless of lower-priority narrative text

### 4) Keep gate strict (no fallback)

Do not relax `LifecycleGateError` behavior.
Gate remains fail-fast and typed. This FR removes leak frequency by preventing
invalid cast admission, not by muting violations.

## Acceptance Criteria

- [x] **A1 - Cast filter exists and is deterministic.**
  A pure helper returns allowed active cast ids from reviewed roster + canonical
  lifecycle seam inputs, with stable output for identical inputs.
  The helper must reuse shared lifecycle normalization logic (no duplicated
  policy tables).

- [x] **A2 - Chapter-open early return is prevented at source.**
  For chapter turn 1, characters with delayed reappearance cannot appear in
  candidate active cast before allowed chapter index.

- [x] **A3 - Lifecycle gate remains strict and mostly silent.**
  Gate code path is unchanged semantically; witness run shows
  `lifecycle_gate_violation_count == 0` for Floodmark 128-cap rerun.

- [x] **A4 - Valid cast paths remain valid.**
  Characters legitimately alive/present at chapter-open are still admitted.
  No false exclusions introduced.
  Identity matching must be deterministic for roster ids vs display names.

- [x] **A5 - Tests cover leak and non-regression.**
  Add unit tests for cast filter edge cases and integration test that verifies
  chapter-open flow for pre-return vs post-return chapters.

- [x] **A6 - FR-508 witness closure compatibility.**
  Combined witness checks pass: zero lifecycle violations + completed/planned
  parity + no dead/alive contradiction regressions.

## Test Plan (TDD)

1. RED: add unit tests for lifecycle-aware cast filter:
   - pre-return excluded
   - at/after-return admitted
   - absent/rumor-only excluded
   - valid alive/present retained
2. RED: integration test covering chapter-open turn 1 where reviewed roster
   includes a character that must still be excluded by lifecycle floor.
3. GREEN: implement cast filter and wire it into `invoke_turn` before cast build.
4. GREEN: preserve existing lifecycle gate invocation and payload behavior.
5. GREEN: run DM test suite and witness metrics tests.
6. WITNESS: rerun Floodmark with cap 128 and validate A6 metrics.

## Implementation Status

Completed.

Completed in this enforcement pass:
- Added deterministic chapter-open roster filtering in
  `examples/dungeon_master/api/turn_ops.py` via `_filter_roster_for_lifecycle(...)`.
- Wired filter into `invoke_turn(...)` before cast assembly while retaining the
  strict lifecycle gate as backstop.
- Added regression coverage in
  `examples/dungeon_master/tests/test_lifecycle_gate.py`:
  - invalid early-return character is filtered from cast when valid cast remains,
  - identity matching remains case-insensitive,
  - chapter-open with only invalid cast still raises `LifecycleGateError`.

Validation evidence:
- `python -m pytest examples/dungeon_master/tests/test_lifecycle_gate.py --no-cov -q`
  -> `3 passed`
- `python -m pytest examples/dungeon_master/tests --no-cov -q`
  -> `144 passed`
- `python -m ruff check examples/dungeon_master/api/turn_ops.py examples/dungeon_master/tests/test_lifecycle_gate.py`
  -> clean.

Witness evidence (fresh rerun):
- `PYTHONPATH="$PWD" .venv/bin/python examples/dungeon_master/scripts/generate.py --out outputs/dungeon-master/10013-BC --turn-cap 128 ...`
- `PYTHONPATH="$PWD" .venv/bin/python examples/dungeon_master/scripts/witness_continuity_metrics.py --log logs/gen-10013-azure.log --story outputs/dungeon-master/10013-BC/story/story.json --json`
  -> `pass: true`, `lifecycle_gate_violation_count: 0`, `completed_chapter_count: 7`, `planned_chapter_count: 7`, `dead_alive_opening_contradiction_count: 0`, `continuity_memory_conflict_count: 0`.

Delta vs prior witness run:
- 10012: `lifecycle_gate_violation_count = 5`, `pass: false`
- 10013: `lifecycle_gate_violation_count = 0`, `pass: true`.

## Risks & Mitigations

1. Risk: false exclusions due to seam/source mismatch.
- Mitigation: enforce explicit source-pointer rule and add deterministic tests.

2. Risk: behavior drift between cast filter and lifecycle gate logic.
- Mitigation: share normalized lifecycle map helper; keep gate as backstop.

3. Risk: test flakiness from long witness runs.
- Mitigation: isolate logic in unit tests; keep witness run as final acceptance.

## Enforce Sequence

1. Implement helper and tests in `examples/dungeon_master/api/turn_ops.py` and
   `examples/dungeon_master/tests/test_lifecycle_gate.py`.
2. Run:
   - `python -m pytest examples/dungeon_master/tests/test_lifecycle_gate.py --no-cov -q`
   - `python -m pytest examples/dungeon_master/tests --no-cov -q`
   - `python -m ruff check examples/dungeon_master/api/turn_ops.py examples/dungeon_master/tests/test_lifecycle_gate.py`
3. Witness rerun:
   - generate Floodmark with `--turn-cap 128`
   - score via `witness_continuity_metrics.py`
   - record metrics in FR implementation status.

## Related

- FR-507 - lifecycle seam gate
- FR-508 - layered memory contract
- Witness runs: 10010, 10011, 10012
