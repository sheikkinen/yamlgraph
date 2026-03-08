# Feature Request: Inquisitor Architecture Provider Count Mismatch

**Priority:** LOW
**Type:** Bug
**Status:** Rejected — Duplicate of FR-121 (architecture provider count guard)
**Judgment:** REJECT. This FR documents a problem already independently tracked and resolved by FR-121 and `108-architecture-provider-count-drift.md`. The doc fix (commit `55b890b`) and guard test (`test_architecture_provider_count.py`, REQ-YG-121) are both in place. No new work, code, or requirements needed. Archiving as rejected duplicate.
**Effort:** 0 days (no work needed)
**Requested:** 2026-03-07

## Summary

The Inquisitor flagged a provider count mismatch in ARCHITECTURE.md ("7 providers" vs "8 providers") across 12 consecutive audits. This was independently tracked and resolved by FR-121 and `108-architecture-provider-count-drift.md`.

## Value Statement

No additional value — the fix and guard test already landed.

## Problem

ARCHITECTURE.md module table row for `llm_factory.py` previously read "7 providers" while the overview section read "8 providers." The drift was introduced when the Inception provider was added (FR-112) and the module table was not updated (partial remediation trap).

## Proposed Solution

No action required. The fix has already been applied:

1. **Doc fix**: ARCHITECTURE.md line ~1154 now reads "8 providers" (commit `55b890b`).
2. **Guard test**: `tests/unit/test_architecture_provider_count.py` (REQ-YG-121) asserts the module table count equals `len(get_args(ProviderType))`, preventing future drift.

## Acceptance Criteria

- [x] ARCHITECTURE.md module table says "8 providers" — verified at line 1154
- [x] ARCHITECTURE.md overview section says "8 providers" — verified at line 219
- [x] Guard test REQ-YG-121 exists and passes
- [x] REQ-YG-121 registered in ARCHITECTURE.md requirements table (line 650)

## Alternatives Considered

N/A — this is a duplicate of completed work.

## Related

- **Duplicate of:** `feature-requests/FR-121-architecture-provider-count.md`
- **Also tracked in:** `feature-requests/108-architecture-provider-count-drift.md` (Status: Completed)
- **Guard test:** `tests/unit/test_architecture_provider_count.py`
- **Requirement:** REQ-YG-121
- **Origin:** Inquisitor Audits I–XII provider count violation
