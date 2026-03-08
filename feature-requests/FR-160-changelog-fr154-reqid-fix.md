# Feature Request: CHANGELOG FR-154 REQ-ID Correction

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.25 days
**Requested:** 2026-03-08

## Summary

Correct the wrong `(REQ-YG-146)` reference on CHANGELOG.md line 13 to the correct `(REQ-YG-150)` for the FR-154 entry (Architecture Capability Count Guard, CAP-52).

## Value Statement

Maintainers and auditors get an accurate CHANGELOG that matches ARCHITECTURE.md, eliminating a known transcription error flagged in two consecutive Inquisitor audits.

## Problem

CHANGELOG.md line 13 cites `(REQ-YG-146)` for the FR-154 entry, but ARCHITECTURE.md and `@pytest.mark.req` tags both use `REQ-YG-150` for the Architecture Capability Count Guard (CAP-52). `REQ-YG-146` belongs to a different capability entirely — CHANGELOG Removal Completeness (CAP-48, FR-153).

This transcription error was flagged in **two consecutive Inquisitor audits** (XLV → XLVI) with zero remediation, triggering the Scripture's `audit_as_ritual` trap: "3+ audits without fix → ritual, not process."

The authoritative source is ARCHITECTURE.md. No other files are affected — tests and architecture already use the correct ID.

## Proposed Solution

Single-line correction in `CHANGELOG.md`:

```diff
- - **FR-154 Architecture Capability Count Guard**: Fix stale capability/requirement counts in ARCHITECTURE.md summary sentence (19→46 capabilities, 68→109 requirements) and add CI guard test to prevent future drift. (REQ-YG-146)
+ - **FR-154 Architecture Capability Count Guard**: Fix stale capability/requirement counts in ARCHITECTURE.md summary sentence (19→46 capabilities, 68→109 requirements) and add CI guard test to prevent future drift. (REQ-YG-150)
```

## Acceptance Criteria

- [ ] CHANGELOG.md FR-154 entry references `(REQ-YG-150)` instead of `(REQ-YG-146)`
- [ ] `python scripts/req_coverage.py --strict` passes (no phantom requirement drift)
- [ ] No other files require changes (verified by grepping for the incorrect pairing)

## Alternatives Considered

1. **Bundle with FR-159**: FR-159 (CHANGELOG REQ-ID Cross-Validation) lists this micro-fix as its first acceptance criterion. Rejected as a delivery vehicle because the structural prevention work in FR-159 is larger scope (1 day) and should not block a 5-minute correction that has already been deferred across two audit cycles.

2. **No FR, just fix**: Rejected because the Scripture requires traceability — even micro-fixes warrant an audit trail when flagged by the Inquisitor.

## Related

- **FR-159**: CHANGELOG REQ-ID Cross-Validation (structural prevention — extends `req_coverage.py --strict` to validate CHANGELOG REQ-IDs)
- **Inquisitor Audits XLV, XLVI**: Flagged this error in consecutive cycles
- **ARCHITECTURE.md CAP-52**: Architecture Capability Count Guard (`REQ-YG-150`)
- **ARCHITECTURE.md CAP-48**: CHANGELOG Removal Completeness (`REQ-YG-146`) — the incorrectly cited requirement
- **Scripture trap**: `audit_as_ritual` — "3+ audits without fix → ritual, not process"
- **Scripture trap**: `partial_remediation` — "Fix all occurrences, not just cited one"
