# Feature Request: Register REQ-YG-145 for Phantom Requirement Detection

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.25 days
**Requested:** 2026-03-08

## Summary

Register the phantom requirement detection capability (FR-145) in the requirement traceability registry. FR-145 shipped without its own `REQ-YG-145` entry in `ARCHITECTURE.md`, without registration in `ALL_REQS` / `CAPABILITIES` in `req_coverage.py`, and without a `CHANGELOG.md` entry.

## Value Statement

Maintainers get a self-consistent requirement registry where every shipped feature — including the traceability tooling itself — is properly documented, eliminating audit violations and setting the correct example for future contributions.

## Problem

Inquisitor Audits XXXVIII and XXXIX both flagged this gap:

- **Audit XXXVIII**: "Missing REQ-YG-145 in ARCHITECTURE.md (ADR-001)"
- **Audit XXXIX**: "FR-145 merged without ARCHITECTURE.md requirement" + "FR-145 missing CHANGELOG entry"

The 6 tests in `TestPhantomRequirementDetection` (`tests/unit/test_req_coverage.py`) currently tag `REQ-YG-063` (the coarse parent for requirement traceability enforcement) instead of a dedicated `REQ-YG-145`. This masks coverage gaps — `REQ-YG-063` appears over-covered while `REQ-YG-145` appears non-existent.

## Proposed Solution

Five surgical changes across four files, no new logic:

### 1. `ARCHITECTURE.md` — Add CAP-45 and REQ-YG-145

**Capability summary table** (after row 44):

```markdown
| 45 | Phantom Requirement Detection | `scripts/req_coverage.py`, `tests/unit/test_req_coverage` | REQ-YG-145 |
```

**New CAP-45 detail section** (after CAP-44):

```markdown
### 45. Phantom Requirement Detection

Detect and reject test markers that reference non-existent requirement IDs.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-145 | **Phantom requirement detection**: `req_coverage.py --strict` rejects `@pytest.mark.req` markers referencing requirement IDs absent from `ALL_REQS` or `ARCHITECTURE.md` | `scripts/req_coverage.py`, `tests/unit/test_req_coverage` |
```

### 2. `scripts/req_coverage.py` — Register in ALL_REQS and CAPABILITIES

**`_ALL_FRAMEWORK_REQS`** — add `145` after the `143` entry:

```python
    + [145]  # REQ-YG-145 (CAP-45 Phantom Requirement Detection)
```

**`CAPABILITIES`** — add entry after `CAP-44`:

```python
    "CAP-45": ("Phantom Requirement Detection", ["REQ-YG-145"]),
```

### 3. `tests/unit/test_req_coverage.py` — Re-tag tests

Change the class-level marker on `TestPhantomRequirementDetection` from:

```python
@pytest.mark.req("REQ-YG-063")
```

to:

```python
@pytest.mark.req("REQ-YG-145")
```

### 4. `CHANGELOG.md` — Add entry under `[Unreleased]`

Under `### Added`:

```markdown
- **FR-145 Phantom Requirement Detection**: `req_coverage.py --strict` rejects `@pytest.mark.req` markers referencing requirement IDs absent from `ALL_REQS` or `ARCHITECTURE.md`. (REQ-YG-145)
```

## Acceptance Criteria

- [ ] `REQ-YG-145` exists in `ARCHITECTURE.md` capability summary table (CAP-45) and in a detail section
- [ ] `REQ-YG-145` is present in `ALL_REQS` via `_ALL_FRAMEWORK_REQS` in `scripts/req_coverage.py`
- [ ] `CAP-45` entry exists in `CAPABILITIES` dict in `scripts/req_coverage.py`
- [ ] All 6 `TestPhantomRequirementDetection` tests are tagged `@pytest.mark.req("REQ-YG-145")`, not `REQ-YG-063`
- [ ] `CHANGELOG.md` `[Unreleased]` section contains FR-145 entry with `REQ-YG-145`
- [ ] `python scripts/req_coverage.py --strict` passes (no phantom IDs, no uncovered reqs)
- [ ] `pytest tests/unit/test_req_coverage.py -v` passes (all 6 phantom tests green)
- [ ] Commit message: `fix(traceability): FR-146 register REQ-YG-145 for phantom requirement detection`

## Alternatives Considered

- **Leave tests under REQ-YG-063**: Rejected — violates ADR-001's one-capability-per-requirement principle and masks coverage reporting.
- **Fold into CAP-18 without a new CAP**: Rejected — phantom detection is a distinct capability from the base `pytest_collection_modifyitems` enforcement hook. A dedicated CAP preserves the 1:1 mapping between FR and capability.

## Judgement — APPROVED

**Reviewer:** Chaplain Judge, 2026-03-08
**Verdict:** APPROVE — Scope is clear, minimal, and internally consistent. Authority granted.

### Assessment

| Criterion | Result |
|-----------|--------|
| Scope clear and minimal | ✅ Five surgical changes across four files; registration only, no new logic |
| No contradictions or ambiguities | ✅ All claims verified against codebase: REQ-YG-145 absent from ARCHITECTURE.md, 145 absent from `_ALL_FRAMEWORK_REQS`, CAP-45 absent from `CAPABILITIES`, tests tagged `REQ-YG-063`, no CHANGELOG entry for FR-145 |
| Acceptance criteria measurable | ✅ All 8 criteria mechanically verifiable via file inspection, `--strict` exit code, and pytest |
| Implementation feasible | ✅ Copy-paste-level changes at specified locations; 0.25 days realistic |
| Aligns with architecture | ✅ Follows exact pattern of all prior CAP/REQ registrations; mandated by ADR-001 |
| Single responsibility | ✅ One concern: register an unregistered capability |

### Notes for Implementer

- After re-tagging 6 tests from `REQ-YG-063` to `REQ-YG-145`, confirm `REQ-YG-063` (CAP-18) retains sufficient coverage. Current count is 74 tests; losing 6 leaves 68 — well above threshold.
- The `[Unreleased]` section in `CHANGELOG.md` exists but verify the `### Added` subsection is present before inserting.

## Related

- `feature-requests/FR-145-phantom-requirement-detection.md` — the original FR (status: Implemented)
- Inquisitor Audit XXXVIII and XXXIX — flagged the violation
- ADR-001 — Requirement Traceability mandate
- `scripts/req_coverage.py` — the script being registered
- `tests/unit/test_req_coverage.py::TestPhantomRequirementDetection` — the 6 tests to re-tag
