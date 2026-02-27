# Feature Request: req_coverage.py Architecture Cross-Check

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-27

## Summary

Extend `req_coverage.py --strict` to verify that every requirement ID in `ALL_REQS` also exists as a table row in `ARCHITECTURE.md`, closing the phantom-requirement gap discovered by the Inquisitor audit of commit `38dbfb4`.

## Value Statement

Framework maintainers get automatic detection of phantom requirements — IDs that pass coverage checks but lack architectural documentation — preventing ADR-001 traceability gaps from reaching `main`.

## Problem

`req_coverage.py --strict` currently validates only the **test → requirement** mapping: it checks that every requirement in `ALL_REQS` has at least one tagged test. It does **not** verify that the requirement is **described** in `ARCHITECTURE.md`.

This creates a phantom-requirement vulnerability: a developer can add a requirement ID to `_ALL_FRAMEWORK_REQS` and tag tests with it, making `--strict` pass, while never documenting the requirement in `ARCHITECTURE.md`. The traceability chain (architecture → requirement → test) is broken at the architecture layer.

**Evidence:** REQ-YG-105 (FR-105 Copilot Session Continuations) was added to `req_coverage.py` (lines 29, 185) and tagged in two test files, but never added to the CAP-30 table in `ARCHITECTURE.md`. The `--strict` check passed, masking the violation.

**Root cause:** When the coverage script is updated in the same commit as the tests, the cross-check becomes tautological — the script validates its own additions.

## Proposed Solution

Add an architecture-presence check to `req_coverage.py` that leverages the existing `_load_req_descriptions()` function. After collecting coverage data, compare `ALL_REQS` against the set of requirement IDs parsed from `ARCHITECTURE.md` table rows.

```python
# In main(), after loading coverage data:
arch_descriptions = _load_req_descriptions(root)
arch_req_ids = set(arch_descriptions.keys())
all_req_ids = set(ALL_REQS)

undocumented = sorted(all_req_ids - arch_req_ids)
if undocumented:
    print(f"\n⚠ {len(undocumented)} requirement(s) missing from ARCHITECTURE.md:")
    for req_id in undocumented:
        print(f"    {req_id}")

if undocumented and "--strict" in sys.argv:
    sys.exit(1)
```

The existing `_load_req_descriptions()` regex (`r"^\|\s*(REQ-YG-\d{3})\s*\|\s*(.+?)\s*\|"`) already parses requirement table rows — no new parsing logic needed.

### Immediate fixes (prerequisite, same PR)

1. Add REQ-YG-105 row to the CAP-30 table in `ARCHITECTURE.md` (fixes the existing violation).
2. Remove the garbage "Git Report" diary entry from `docs/diary.md` (Commandment 8).
3. Add FR-105 implementation diary entry to `docs/diary.md` (Sermon: Distill).

## Acceptance Criteria

- [x] `req_coverage.py --strict` exits non-zero when a requirement ID in `ALL_REQS` has no corresponding table row in `ARCHITECTURE.md`
- [x] `req_coverage.py` (without `--strict`) prints a warning for undocumented requirements but exits zero
- [x] REQ-YG-105 is documented in `ARCHITECTURE.md` CAP-30 table (immediate fix)
- [x] Garbage "Git Report" entry removed from `docs/diary.md`
- [x] FR-105 implementation diary entry added
- [x] Unit test: phantom requirement detected when ID in `ALL_REQS` but absent from `ARCHITECTURE.md`
- [x] Unit test: no false positives when all IDs are present in both
- [x] `pre-commit` hook continues to gate on `--strict`
- [x] Documentation: `ARCHITECTURE.md` ADR-001 section updated to note the two-way check

## Alternatives Considered

1. **Separate script for architecture validation.** Rejected: the cross-check is inherently coupled to `req_coverage.py`'s data — splitting would duplicate the requirement ID list and ARCHITECTURE.md parsing.

2. **Parse ARCHITECTURE.md for requirement IDs independently of table format.** Rejected: the table format is the canonical structure; freeform text mentions (e.g., "see REQ-YG-087") should not count as documentation.

3. **Make the check a pre-commit hook separate from `req_coverage.py`.** Rejected: `req_coverage.py --strict` already runs in pre-commit; adding a flag or extending the existing check is simpler than a new hook.

## Related

- **Inquisitor audit:** `.chaplain/inbox/inq.md` (2026-02-27)
- **ADR-001:** Requirement Traceability (ARCHITECTURE.md)
- **FR-105:** Copilot Session Continuations (the commit that exposed the gap)
- **FR-075:** `FR-075-architecture-req-numbering-sync.md` (prior related sync work)
- **Existing function:** `_load_req_descriptions()` in `scripts/req_coverage.py:389-407`
- **Heuristic (graduated):** "A green `req_coverage.py --strict` does not prove architectural documentation exists — it only proves tests are tagged and the script's expected range includes the ID."
