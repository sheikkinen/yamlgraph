# Feature Request: FR-143 Requirement Traceability for FR-134

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Judged:** 2026-03-08
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Add a dedicated `REQ-YG-134` requirement to `ARCHITECTURE.md` for the diary folder refactor capability introduced by FR-134, fix the misattributed CHANGELOG citation, update `scripts/req_coverage.py`, and tag diary-folder tests with the correct requirement ID.

## Value Statement

Maintainers get accurate requirement traceability for FR-134, closing a drift flagged across four consecutive inquisitor audits (XXVII–XXX) and restoring ADR-001 compliance.

## Problem

FR-134 (diary folder refactor) introduced a new capability — replacing monolithic `docs/diary.md` with date-prefixed folder entries — but has no dedicated `REQ-YG-XXX` in `ARCHITECTURE.md`. The CHANGELOG entry cites `(REQ-YG-131)`, which belongs to FR-131 (inquisitor commit-delta gate), not FR-134.

**Audit trail:**
- **Audit XXVII**: ✗ VIOLATION — "Missing requirement for FR-134. The CHANGELOG entry cites (REQ-YG-131) but that requirement belongs to FR-131."
- **Audit XXVIII**: Implicitly confirms the broken state.
- **Audit XXX**: ⚠ DRIFT — "FR-134 has no dedicated requirement in ARCHITECTURE.md."

ADR-001 mandates every capability have a tracked requirement. This has been unfixed across 4 consecutive audits, triggering the `audit_as_ritual` trap: "3+ audits without fix → ritual, not process."

## Proposed Solution

Four surgical changes, no new code paths:

### 1. Add REQ-YG-134 to ARCHITECTURE.md

Add a new capability section after CAP-40 (Enforce Pipeline Graph Delegation):

```markdown
### 41. Diary Folder Structure (FR-134)

Replace monolithic `docs/diary.md` with a `docs/diary/` folder of date-prefixed entry files (`YYYY-MM-DD-<type>-<id>.md`), eliminating merge conflicts from concurrent appends by `finalize_merge.sh`, `inquisitor.sh`, `diary_rotate.py`, and `examples/shared/diary.py`.

| REQ-YG-134 | Diary entries stored as individual date-prefixed files in `docs/diary/` folder; `write_diary()` creates files (never appends to monolith); `migrate_diary_to_folder.py` splits existing monolith into individual files; `diary_rotate.py` imports scheduled entries as individual files | `scripts/diary_digest.sh`, `scripts/migrate_diary_to_folder.py`, `scripts/diary_rotate.py`, `tests/unit/test_diary_digest`, `tests/unit/test_migrate_diary`, `tests/unit/test_diary_rotate` |
```

### 2. Fix CHANGELOG citation

In `CHANGELOG.md`, under `[Unreleased] / ### Added`, change:

```diff
- (REQ-YG-131)
+ (REQ-YG-134)
```

on the FR-134 entry only. The FR-131 entry retains its own `(REQ-YG-131)` citation.

### 3. Update scripts/req_coverage.py

Add `134` to `_ALL_FRAMEWORK_REQS`:

```python
+ [134]  # REQ-YG-134 (CAP-41 Diary Folder Structure)
```

Add the new capability to `CAPABILITIES`:

```python
"CAP-41": {
    "name": "Diary Folder Structure",
    "reqs": ["REQ-YG-134"],
},
```

### 4. Tag diary-folder tests with REQ-YG-134

Add `@pytest.mark.req("REQ-YG-134")` to the following tests that specifically exercise the diary folder capability:

| File | Tests to tag |
|------|-------------|
| `tests/unit/test_diary_digest.py` | `test_write_creates_individual_file`, `test_write_does_not_append_to_monolith` |
| `tests/unit/test_migrate_diary.py` | All test classes (`TestInferEntryType`, `TestExtractDate`, `TestSplitDiary`, `TestMigrate`) |
| `tests/unit/test_diary_rotate.py` | `TestImportScheduledEntries`, `TestImportGitReports` |

**Do NOT re-tag** tests already correctly tagged with other requirements (e.g., REQ-YG-072 for digest functionality, REQ-YG-125 for finalize_merge). Only add `REQ-YG-134` where the test specifically exercises diary folder structure (file creation, migration, individual-file imports).

## Acceptance Criteria

- [ ] `ARCHITECTURE.md` contains `REQ-YG-134` with description matching the diary folder capability
- [ ] `CHANGELOG.md` FR-134 entry cites `(REQ-YG-134)`, not `(REQ-YG-131)`
- [ ] `scripts/req_coverage.py` includes `134` in `_ALL_FRAMEWORK_REQS` and `CAP-41` in `CAPABILITIES`
- [ ] `python scripts/req_coverage.py --strict` passes with REQ-YG-134 covered
- [ ] At least 2 test functions carry `@pytest.mark.req("REQ-YG-134")`
- [ ] No existing REQ-YG-131 markers are removed (they correctly belong to FR-131)
- [ ] `pytest tests/unit/ -q --no-cov` passes with no regressions
- [ ] Tests added
- [ ] Documentation updated

## Alternatives Considered

1. **Re-use REQ-YG-131 for both FR-131 and FR-134**: Rejected — violates ADR-001 principle of 1:1 capability-to-requirement mapping. REQ-YG-131 specifically describes the commit-delta gate, not the diary folder structure.

2. **Use a non-sequential number (e.g., REQ-YG-140)**: Rejected — the convention aligns REQ numbers with FR numbers where possible (REQ-YG-125↔FR-125, REQ-YG-128↔FR-128, REQ-YG-131↔FR-131). REQ-YG-134 maintains this pattern.

3. **Skip the CHANGELOG fix and only add the requirement**: Rejected — the misattribution is the root cause of audit drift and would continue triggering violations.

## Related

- **FR-134**: `feature-requests/FR-134-diary-folder-refactor.md` (✅ Implemented)
- **FR-131**: `feature-requests/FR-131-inquisitor-commit-delta-gate.md` (owns REQ-YG-131)
- **ADR-001**: Requirement traceability mandate in `ARCHITECTURE.md`
- **Audits XXVII–XXX**: Cited violations in `docs/diary/2026-03-08-inquisitor-audit-*.md`
- **Trap**: `audit_as_ritual` — "3+ audits without fix → ritual, not process"
