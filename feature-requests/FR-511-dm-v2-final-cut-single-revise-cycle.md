# Feature Request: FR-511 - DM v2 Final Cut Prompt Hardening + Single Revise Cycle

**Priority:** HIGH
**Type:** Bugfix / Enforcement Hardening
**Status:** Judged - Granted
**Effort:** ~1-2 days
**Requested:** 2026-06-17

## Summary

Harden `final_cut` prose generation with stronger scene-cast constraints and add
one deterministic review-revise cycle after prose synthesis. If review detects
confirmed-dead active-role violations, run exactly one constrained revise pass,
re-validate, then either accept or fail chapter close.

## Judgement

Decision: **Granted**.

The redraft resolves the prior blockers B1-B4 with explicit contracts for
allowed-cast authority, machine-checkable revise invariants, typed error schema,
and witness policy alignment.

### Scope freeze

This FR is approved with the following hard boundaries:

1. Exactly one revise attempt (`max_revise_attempts = 1`).
2. Deterministic validator remains authority for acceptance.
3. Unresolved violations after revise must raise `FinalCutReviseError`.
4. No change to FR-508 witness pass criteria in this FR; dead prose remains
  measurement-only in `evaluate_fr508_a5`.

### Enforcement conditions

1. Implement `build_allowed_scene_cast(doc, cid)` exactly per B1 contract.
2. Implement all B2 invariants as executable checks, not prompt guidance.
3. Emit stable failure marker `Final cut revise failed:` with B3 payload keys.
4. Add tests proving one-attempt cap and fail-fast behavior on unresolved
  violations and invariant breaks.
5. Record rerun evidence with both:
  - dead_character_prose_violation_count
  - whether revise path was used

## Redraft Resolution

This redraft resolves B1-B4 from the blocked judgement.

### B1 resolution: allowed-cast authority and normalization

Allowed cast at chapter close is defined as:

1. Start from `doc["characters"]["roster"]` in roster order.
2. Keep only reviewed cards (`reviewed == true`).
3. Apply lifecycle filter against inherited seam packet for chapter `cid`
   using `validate_character_lifecycle(packet, chapter_id, active_cast_names)`.
4. Remove names flagged by lifecycle violations.

Normalization contract:

1. Display name source: `characters.cards[char_id].name` else `char_id`.
2. Matching key: lowercased, whitespace-collapsed name.
3. Ordering: original roster order (stable, deterministic).

### B2 resolution: machine-checkable minimal rewrite invariants

After revise pass, all invariants must hold:

1. `chapter_beats(doc, cid)` text set is preserved as substrings in revised text.
2. No new named entity outside `allowed_cast` is introduced, excluding
   punctuation-only and possessive forms already present in original text.
3. Revised text length delta is bounded: absolute delta <= 20 percent of original.
4. Non-violating excerpts are preserved verbatim for at least 90 percent of
   lines selected as safe context windows.

If any invariant fails, revise attempt is rejected and chapter close fails.

### B3 resolution: typed error contract and log marker

Add a typed error class in `chapter_ops.py`:

`FinalCutReviseError(RuntimeError)` with payload schema:

1. `code`: `FINAL_CUT_REVISE_FAILED`
2. `chapter_id`: string
3. `attempt_count`: int
4. `violations`: list[dict]
5. `invariant_failures`: list[str]
6. `revised`: bool
7. `source_pointer`: dict with `chapter_id` and optional seam hash

Log marker contract:

`Final cut revise failed: {payload}`

This marker is stable for parser consumption and review diagnostics.

### B4 resolution: witness policy alignment

Policy for this FR:

1. `dead_character_prose_violation_count` remains measurement-only in
   `evaluate_fr508_a5` (no new fail check in this FR).
2. Unresolved dead-character violations after one revise attempt raise
   `FinalCutReviseError`, causing chapter close failure and therefore witness
   failure via existing `completed_equals_planned` and
   `book_gate_opened_before_turn_cap` checks.

This keeps witness semantics stable while making unresolved violations fail the
run through deterministic runtime behavior.

## Value Statement

Story continuity reliability improves because final prose gets one targeted
correction chance while still preserving deterministic guardrails and preventing
infinite rewrite loops.

## Problem

Current state has two gaps:

1. Prompt-only constraints are probabilistic and can still produce continuity
   contradictions in final prose.
2. FR-510 validator currently logs typed violations but does not trigger a
   correction path inside chapter close.

Observed outcome:

- A run can satisfy witness fail checks while still containing prose-level
  dead-character contradictions when those contradictions are not fail-gated.

## Proposed Solution

### 1) Prompt hardening in final_cut

Strengthen the system/user instruction in `examples/dungeon_master/prompts/final_cut.yaml`:

- Explicitly list allowed scene cast and forbidden dead characters.
- Add instruction priority:
  1) continuity constraints
  2) beat fidelity
  3) prose quality
- Require no new character actions outside allowed cast.

### 2) Single review-revise cycle in chapter close

In `examples/dungeon_master/api/chapter_ops.py` `close_chapter(...)`:

1. Generate final text via `invoke_final_cut(...)`.
2. Run deterministic validator `detect_dead_character_prose_violations(...)`.
3. If no violations: accept text unchanged.
4. If violations exist:
  - call a new revise path once (max one attempt), passing:
     - original text
     - violating excerpts
     - allowed cast list
     - forbidden dead-character list
    - instruction: minimal rewrite only; preserve non-violating content
5. Re-run validator on revised text:
   - if clean: accept revised text
  - if still violating: raise `FinalCutReviseError` (fail-fast)
6. Run post-revise invariants (B2):
  - if any invariant fails: raise `FinalCutReviseError` (fail-fast)

### 3) No loop policy

- Hard cap revise attempts at `1`.
- No recursive or repeated retries.
- Error payload must follow B3 schema.

### 4) Keep deterministic authority

- Deterministic validator remains source of truth.
- LLM revise output is accepted only after deterministic re-validation.

### 5) Allowed-cast builder helper

Add a deterministic helper used by both prompt context and revise path:

`build_allowed_scene_cast(doc, cid) -> list[str]`

The helper implements B1 source and normalization contract.

## Acceptance Criteria

- [ ] **A1 - Prompt hardening is implemented.**
  `final_cut.yaml` includes explicit allowed-cast and forbidden dead-character
  constraints with priority order.

- [ ] **A2 - Single revise cycle is implemented.**
  `close_chapter` runs at most one revise attempt when validator detects
  dead-character active-role violations.

- [ ] **A3 - Deterministic re-validation gates acceptance.**
  Revised text is accepted only if validator returns zero violations.

- [ ] **A4 - Fail-fast on unresolved violations.**
  If revised text still violates constraints, chapter close raises a typed error;
  no silent fallback to original violating prose.

- [ ] **A5 - Retry cap enforced.**
  Unit/integration tests prove exactly one revise attempt and no loop behavior.

- [ ] **A6 - Tests cover machine-checkable invariants.**
  Tests verify B2 invariants and fail behavior when invariants break.

- [ ] **A7 - Witness and run evidence recorded.**
  Fresh rerun report includes both:
  - dead_character_prose_violation_count
  - whether revise path was used

- [ ] **A8 - Typed error and log contract implemented.**
  `FinalCutReviseError` payload matches B3 schema and logs with marker
  `Final cut revise failed:`.

- [ ] **A9 - Allowed-cast helper contract implemented.**
  Builder output is deterministic, normalized, and stable-order per B1.

## Alternatives Considered

1. Prompt-only hardening with no revise path
- Rejected: insufficient for deterministic reliability.

2. Multi-pass revise until clean
- Rejected: drift risk and non-deterministic loop behavior.

3. Immediate hard fail with no revise
- Deferred: safer than loops but misses low-cost recoverable cases.

## Risks and Mitigations

1. Risk: revise introduces beat drift
- Mitigation: minimal-rewrite instruction + post-revise beat/structure checks.

2. Risk: validator false positives force unnecessary fail
- Mitigation: keep heuristic exclusions explicit and tested; record examples.

3. Risk: hidden second retries through utility reuse
- Mitigation: expose and assert `max_revise_attempts = 1` in code and tests.

## Test Plan (TDD)

1. RED: test allowed-cast builder source, normalization, and ordering (B1).
2. RED: test revise path triggered exactly once on synthetic violation.
3. RED: test unresolved violation raises `FinalCutReviseError` after one attempt.
4. RED: test invariant failures raise `FinalCutReviseError` (B2).
5. GREEN: implement prompt hardening, helper, revise path, and typed error.
6. GREEN: add tests for log marker and payload schema (B3).
7. VERIFY: run DM tests, lint, and witness rerun.

## Enforce Sequence

1. Add `build_allowed_scene_cast(doc, cid)` and tests.
2. Update final-cut prompt/context with allowed and forbidden cast fields.
3. Add revise function, one-attempt policy, and typed error class.
4. Wire revise, re-validation, and invariants into chapter close.
5. Add unit/integration tests for B1-B3 contracts.
6. Run full validation and record witness evidence.

## Implementation Status

Completed.

Completed in this enforcement pass:

1. `examples/dungeon_master/api/turn_ops.py`
  - Added `build_allowed_scene_cast(doc, cid)` with deterministic source,
    normalization, and stable roster order.
  - Added `allowed_cast` field to `final_cut_context` payload.

2. `examples/dungeon_master/prompts/final_cut.yaml`
  - Hardened prompt with explicit allowed-cast constraint and instruction
    priority ordering.

3. `examples/dungeon_master/api/chapter_ops.py`
  - Added `FinalCutReviseError` typed error.
  - Added one-pass revise orchestration (`_revise_final_cut_once`) with hard
    cap of one attempt.
  - Added machine-checkable post-revise invariants and fail-fast behavior.
  - Added stable error log marker: `Final cut revise failed:`.
  - Added success marker for measurement: `Final cut revise applied:`.

4. `examples/dungeon_master/api/witness_metrics.py`
  - Added `final_cut_revise_applied_count` metric parsed from revise-applied
    log marker (measurement only).

5. Tests
  - Extended `test_dead_character_prose.py` for allowed-cast builder/context.
  - Added `test_final_cut_revise_cycle.py` for one-attempt cap, invariant fail,
    and clean revise acceptance.
  - Extended `test_witness_metrics.py` for revise-applied metric parsing.

Validation evidence:

1. Targeted tests:
  - `pytest examples/dungeon_master/tests/test_dead_character_prose.py examples/dungeon_master/tests/test_final_cut_revise_cycle.py examples/dungeon_master/tests/test_witness_metrics.py --no-cov -q`
  - Result: `19 passed`

2. Full DM suite:
  - `pytest examples/dungeon_master/tests --no-cov -q`
  - Result: `159 passed`

3. Ruff checks on changed files:
  - Result: clean

4. Witness score (available artifacts):
  - `witness_continuity_metrics.py --log logs/gen-10014-azure.log --story outputs/dungeon-master/10014-BC/story/story.json --json`
  - Included metric: `final_cut_revise_applied_count: 0`

5. Fresh rerun after FR-511 implementation:
  - `generate.py --out outputs/dungeon-master/10015-BC --turn-cap 128`
  - `witness_continuity_metrics.py --log logs/gen-10015-azure.log --story outputs/dungeon-master/10015-BC/story/story.json --json`
  - Snapshot result highlights (non-authoritative; run later terminated):
    - `dead_character_prose_violation_count: 0`
    - `final_cut_revise_applied_count: 0`
    - `completed_chapter_count: 0`
    - `planned_chapter_count: 9`
    - `total_turns_used: 14`
  - Log scan for revise/violation markers returned no matches for:
    - `Final cut revise applied:`
    - `Final cut revise failed:`
    - `Dead character prose violation:`

6. Second fresh rerun to increase chapter-close opportunity:
  - `generate.py --out outputs/dungeon-master/10016-BC --turn-cap 512`
  - `witness_continuity_metrics.py --log logs/gen-10016-azure.log --story outputs/dungeon-master/10016-BC/story/story.json --json`
  - Snapshot result highlights (non-authoritative; run later terminated):
    - `dead_character_prose_violation_count: 0`
    - `final_cut_revise_applied_count: 0`
    - `completed_chapter_count: 0`
    - `planned_chapter_count: 8`
    - `total_turns_used: 11`
  - Log scan for revise/violation markers returned no matches for:
    - `Final cut revise applied:`
    - `Final cut revise failed:`
    - `Dead character prose violation:`

7. Authoritative completed rerun after fix:
  - `generate.py --premise "A survivor and a rival must cross one flooded ravine before nightfall." --out outputs/dungeon-master/10018-smoke --turn-cap 96`
  - Output artifacts produced:
    - `outputs/dungeon-master/10018-smoke/story.json`
    - `outputs/dungeon-master/10018-smoke/story.md`
    - `outputs/dungeon-master/10018-smoke/story/story.json`
  - Witness:
    - `witness_continuity_metrics.py --log logs/gen-10018-smoke.log --story outputs/dungeon-master/10018-smoke/story/story.json --json`
    - `pass: true`
    - `completed_chapter_count: 8`
    - `planned_chapter_count: 8`
    - `dead_character_prose_violation_count: 0`
    - `final_cut_revise_applied_count: 0`
  - Log markers:
    - Multiple `Node final_cut completed successfully` entries present.
    - No `Node final_cut failed` marker.
    - No `Final cut revise failed:` marker.
    - No `Dead character prose violation:` marker.

Pending for full closure:

1. None. A7 runtime evidence now captured from completed run 10018-smoke.

## Previous Judgement Snapshot

Previous decision on earlier draft: Blocked. This redraft addresses B1-B4 for
re-judge.

## Related

- `feature-requests/FR-507-dm-v2-character-lifecycle-seam-gate.md`
- `feature-requests/FR-508-dm-v2-layered-narrative-memory-contract.md`
- `feature-requests/FR-509-dm-v2-lifecycle-source-of-truth-cast-filter.md`
- `feature-requests/FR-510-dm-v2-confirmed-dead-prose-exclusion.md`
- `docs/process.md`
