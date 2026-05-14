# Feature Request: FR-380 Pre-commit diary Seed marker parity with CI gate

**Priority:** HIGH
**Type:** Bug
**Status:** ✅ Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-14

## Summary

Extend `.pre-commit-config.yaml` `diary-reflection-check` so it also rejects diary reflection files missing the literal `Seed:` marker, matching current CI `diary-gate` semantics.

## Value Statement

Contributors get fast local failure for missing `Seed:` markers instead of discovering the issue only after opening a PR, reducing avoidable CI churn.

## Problem

`diary-reflection-check` and CI `diary-gate` currently enforce different contracts:

1. `.pre-commit-config.yaml` `diary-reflection-check` only blocks unfilled stub placeholders (`[What cognitive trap`, `[What lesson`, `[What question`).
2. CI `diary-gate` (via `scripts/gate_artifact_semantics.sh`) additionally requires a literal `Seed:` marker in matching diary reflections.

Impact: a reflection can pass local pre-commit and still fail CI with `diary reflection missing Seed: marker`, as observed in PR #379.

## Research: Existing Patterns, Prior Art, and Gaps

1. **CI already has authoritative Seed validation.**
   - `scripts/gate_artifact_semantics.sh` → `validate_diary_reflection_file()` fails when `Seed:` is absent.
   - `tests/unit/test_ci_diary_gate.py` includes `test_diary_reflection_missing_seed_fails`.
2. **Pre-commit hook is narrower than CI.**
   - `.pre-commit-config.yaml` `diary-reflection-check` only greps for unfilled placeholder stubs.
   - `tests/unit/test_precommit_hooks.py` validates only placeholder rejection/pass behavior; no test asserts missing-`Seed:` rejection.
3. **This mismatch is a known architecture seam.**
   - FR-373 strengthened CI diary/changelog substance checks and explicitly left pre-commit hook changes out of scope.
4. **Feature source discrepancy in this worktree.**
   - Requested source `.chaplain/processing/gh-380.md` is not present; canonical source used: GitHub issue #380.

## Objectives

1. Add local enforcement for missing `Seed:` marker in `diary-reflection-check`.
2. Ensure pre-commit and CI agree on `Seed:` marker requirement.
3. Add focused tests that lock this parity behavior.

## Constraints

1. **Single responsibility:** only close the `Seed:` parity gap between pre-commit and CI for diary reflections.
2. Preserve existing FR-144 placeholder enforcement behavior.
3. Do not change CI `diary-gate` semantics or scope in this FR.
4. Keep implementation shell-first and local-hook compatible (no new external tools/services).

## Proposed Solution

### In scope

1. Update `.pre-commit-config.yaml` `diary-reflection-check` entry to add a missing-Seed check over tracked `docs/diary/*reflection*.md` files:
   - fail when any tracked reflection file lacks `Seed:`,
   - emit actionable error output listing offending files.
2. Extend `tests/unit/test_precommit_hooks.py` diary hook coverage with `Seed:` parity scenarios.
3. Update requirement/capability wording for REQ-YG-144 to describe both enforced conditions:
   - reject unfilled placeholders,
   - reject missing `Seed:` marker.

### Out of scope

1. Expanding pre-commit to enforce all CI diary substance rules (>100 bytes, `##` header, etc.).
2. Refactoring hook logic into a shared script framework.
3. Broad gate harmonization across non-diary artifacts.

## Acceptance Criteria

- [x] **AC-01:** `diary-reflection-check` fails when a tracked diary reflection file is missing literal `Seed:`.
- [x] **AC-02:** `diary-reflection-check` still fails when placeholder stubs are present.
- [x] **AC-03:** `diary-reflection-check` passes when reflection content has no stub placeholders and includes `Seed:`.
- [x] **AC-04:** Unit tests cover AC-01..AC-03 in `tests/unit/test_precommit_hooks.py` (or FR-scoped equivalent).
- [x] **AC-05:** REQ-YG-144 text in `ARCHITECTURE.md` and `capabilities/CAP-45-diary-reflection-enforcement.yaml` reflects `Seed:` enforcement.

## Failing Acceptance Tests (RED plan)

RED test artifact:

- `tests/unit/test_fr380_precommit_seed_marker_red.py`

Planned RED tests:

1. `test_ac01_precommit_rejects_reflection_missing_seed_marker`
2. `test_ac02_precommit_still_rejects_unfilled_stub_placeholders`
3. `test_ac03_precommit_accepts_reflection_with_seed_and_filled_content`
4. `test_ac04_precommit_hook_entry_includes_seed_marker_check`
5. `test_ac05_reqyg144_docs_reference_seed_marker_enforcement`

RED command:

```bash
pytest tests/unit/test_fr380_precommit_seed_marker_red.py -q --no-cov
```

Targeted regression command (post-implementation):

```bash
pytest tests/unit/test_precommit_hooks.py tests/unit/test_ci_diary_gate.py -q --no-cov
```

## Alternatives Considered

1. **Do nothing (CI-only detection)**
   - Rejected: preserves late failure and avoidable PR iteration.
2. **Import shared CI semantic validator into pre-commit**
   - Rejected for scope/minimality: would broaden local enforcement beyond requested `Seed:` parity.
3. **Enforce `Seed:` only in docs/process guidance**
   - Rejected: guidance without a hook remains advisory and regresses enforcement quality.

## Related

- Issue #380: <https://github.com/sheikkinen/yamlgraph/issues/380>
- `.pre-commit-config.yaml` (`diary-reflection-check`)
- `scripts/gate_artifact_semantics.sh` (`validate_diary_reflection_file`)
- `tests/unit/test_precommit_hooks.py`
- `tests/unit/test_ci_diary_gate.py`
- `feature-requests/FR-144-enforce-diary-reflection-content.md`
- `feature-requests/FR-373-substance-validation-diary-changelog-gates.md`
