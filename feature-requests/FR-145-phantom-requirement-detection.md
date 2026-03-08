# Feature Request: Phantom Requirement Detection in Pre-Commit Gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Extend `scripts/req_coverage.py` with reverse-direction checking: detect `@pytest.mark.req` markers in tests that reference requirement IDs absent from `ALL_REQS` or `ARCHITECTURE.md`. Wire into existing `--strict` pre-commit gate.

## Value Statement

Framework developers get immediate pre-commit rejection of phantom requirement IDs, converting a recurring two-audit violation into an automated gate.

## Problem

FR-107 closed the forward direction (ALL_REQS → tests, ALL_REQS → ARCHITECTURE.md) but left the reverse direction unguarded. Tests can reference requirement IDs that:

1. **Don't exist in `ALL_REQS`** — e.g., `REQ-YG-UTIL` (Audit XXXII, FR-139)
2. **Don't exist in `ARCHITECTURE.md`** — e.g., `REQ-YG-141` used in FR-136 tests before registration (Audit XXXIII)

These phantom IDs satisfy the syntactic `@pytest.mark.req` presence check while defeating the semantic purpose: traceability to a defined capability. Inquisitor Audits XXXII and XXXIII flagged this consecutively, triggering the `audit_as_ritual` cure from the Knowledge Graph: "3+ audits without fix → ritual, not process."

### Root Cause

The `partial_remediation` trap — FR-107 addressed one direction of the bidirectional integrity constraint, leaving the reverse direction as an unguarded gap.

## Proposed Solution

Add a reverse-check phase to `scripts/req_coverage.py` that runs as part of the existing `--strict` mode. No new CLI flags needed.

### Implementation

In the existing main flow of `req_coverage.py`, after markers are collected from test files:

```python
# --- Reverse check: phantom requirement detection ---
all_reqs_set = set(ALL_REQS)
phantom_ids = sorted(set(all_markers.keys()) - all_reqs_set)

if phantom_ids:
    print("\n⚠ Phantom requirement IDs (in tests but not in ALL_REQS):")
    for pid in phantom_ids:
        tests = all_markers[pid]
        print(f"  {pid} referenced by {len(tests)} test(s):")
        for t in tests:
            print(f"    - {t}")
```

Then in the `--strict` exit block, include `phantom_ids` alongside `uncovered` and `undocumented`:

```python
if (uncovered or undocumented or phantom_ids) and "--strict" in sys.argv:
    sys.exit(1)
```

### What Changes

| File | Change |
|------|--------|
| `scripts/req_coverage.py` | Add phantom-ID collection after marker scan; include in `--strict` exit condition |
| `.pre-commit-config.yaml` | No change needed — already runs `--strict` |

### What Does NOT Change

- `ALL_REQS` definition and forward-check logic remain untouched
- `--detail` and `--implementation` modes unaffected
- No new CLI flags; reverse check is integral to `--strict`

## Acceptance Criteria

- [ ] `req_coverage.py --strict` exits 1 when any `@pytest.mark.req("REQ-YG-XXX")` marker references an ID not in `ALL_REQS`
- [ ] Output lists each phantom ID with the test file(s) and test function(s) referencing it
- [ ] Existing forward checks (uncovered reqs, undocumented reqs) continue to work unchanged
- [ ] Pre-commit hook rejects commits containing phantom requirement markers
- [ ] Known phantoms (`REQ-YG-UTIL` in FR-139 tests) are either registered properly or replaced with valid IDs before merge
- [ ] Tests added for the reverse-check logic itself
- [ ] `req_coverage.py --detail` output is unaffected

## Alternatives Considered

1. **New `--reverse` flag**: Rejected — adds cognitive overhead. The reverse check is a natural part of `--strict` integrity validation, not an optional mode.
2. **Separate script**: Rejected — the marker-scanning infrastructure already exists in `req_coverage.py`. Duplicating it would violate DRY and create drift risk.
3. **conftest.py runtime check**: Rejected — catching phantoms at test-run time is too late; the gate must be pre-commit to prevent the violation from entering the repository.

## Judgement — APPROVED

**Reviewer:** Chaplain Judge, 2026-03-08
**Verdict:** APPROVE — Scope is clear, minimal, and internally consistent. Authority granted.

### Assessment

| Criterion | Result |
|-----------|--------|
| Scope clear and minimal | ✅ Single script change, no new flags, no new files |
| No contradictions or ambiguities | ✅ REQ-YG-141 correctly cited as historical evidence; REQ-YG-UTIL confirmed as current phantom |
| Acceptance criteria measurable | ✅ All mechanically testable via `--strict` exit code |
| Implementation feasible | ✅ `all_markers` dict already available; 6 lines of logic + exit condition update |
| Aligns with architecture | ✅ Extends existing `req_coverage.py` in its natural direction |
| Single responsibility | ✅ One concern: reverse-direction integrity check |

### Notes for Implementer

- `REQ-YG-UTIL` in `tests/unit/test_enforce_worktree_bare_guard.py` line 28 is the only current phantom. Decide: register it in `ALL_REQS` + `ARCHITECTURE.md`, or replace with the correct existing requirement ID.
- The `all_markers` dict from `extract_req_markers()` provides the key set needed. The reverse check is a set-difference operation: `set(all_markers.keys()) - set(ALL_REQS)`.

## Related

- **FR-107**: Implemented forward-direction cross-check (ALL_REQS → ARCHITECTURE.md)
- **Audit XXXII**: `REQ-YG-UTIL` phantom in FR-139 tests (`docs/diary/2026-03-08-inquisitor-audit-xxxii.md`)
- **Audit XXXIII**: `REQ-YG-141` phantom in FR-136 tests (`docs/diary/2026-03-08-inquisitor-audit-xxxiii.md`)
- **Knowledge Graph**: `audit_as_ritual` cure, `partial_remediation` trap
- **`scripts/req_coverage.py`**: Target file for implementation
- **`.pre-commit-config.yaml`**: Pre-commit hook (no changes needed)
