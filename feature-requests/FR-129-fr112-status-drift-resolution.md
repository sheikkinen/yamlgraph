# FR-129: Resolve FR-112 Status Drift (Inquisitor Auto-Propose)

**Priority:** LOW
**Type:** Bug
**Status:** ❌ Rejected
**Rejection Reason:** Duplicate of FR-120, which is approved and already implemented. FR-112 status field already reads `✅ Implemented (v0.4.60)`. This is the third proposal for the same fix (FR-120 approved, FR-123 rejected as duplicate). See `audit_as_ritual` trap.
**Effort:** 5 min
**Requested:** 2026-03-07

> **⚠️ DUPLICATE**: This issue is fully covered by **FR-120** (`feature-requests/FR-120-fr112-status-update.md`), approved 2026-03-07 and already applied. FR-123 was previously rejected for the same duplication. No further action required.

## Summary

The Inquisitor auto-proposed a fix for FR-112's status field reading "Draft" instead of reflecting its shipped state (v0.4.60). Investigation shows the fix was already applied via FR-120.

## Value Statement

Maintainers get accurate audit reports by eliminating a stale violation — but the violation is already eliminated.

## Problem

The Inquisitor flagged `feature-requests/FR-112-inception-provider.md` status as "Draft" despite FR-112 shipping in v0.4.60. This was flagged as ✗ VIOLATION in Audits I–VIII and ⚠ DRIFT in Audits IX–XII.

**Current state (as of 2026-03-07):** FR-112 status already reads `✅ Implemented (v0.4.60)`. The problem described in the inbox proposal no longer exists.

## Research Findings

| FR | Status | Purpose |
|---|---|---|
| FR-120 | Approved (implemented) | The canonical FR for this fix. Fix applied. |
| FR-123 | ❌ Rejected | First duplicate of FR-120. |
| FR-129 (this) | ❌ Rejected | Second duplicate of FR-120. |

**Root cause of repeated proposals:** The Inquisitor's auto-propose mechanism does not check whether an existing approved FR already covers a flagged violation before drafting a new proposal. This is a separate concern tracked implicitly by FR-126 (Inquisitor Propose Verify Resolution).

## Proposed Solution

No action needed. The fix is already applied.

**Residual housekeeping (out of scope):** FR-120's acceptance criteria checkboxes are still unchecked and its status reads "Approved" rather than "Done". A future audit pass should finalize FR-120.

## Acceptance Criteria

- [x] `feature-requests/FR-112-inception-provider.md` status reads `✅ Implemented (v0.4.60)`
- [x] Inquisitor audit no longer flags FR-112 status as a violation
- [x] Covered by existing FR-120

## Alternatives Considered

- **Create new FR for the fix** — Rejected. FR-120 already provides the paper trail and the fix is applied.
- **Fix FR-120 status to Done in this FR** — Out of scope. FR-120 finalization is a separate housekeeping concern.
- **Suppress Inquisitor re-proposals for resolved violations** — Tracked by FR-126.

## Related

- `feature-requests/FR-120-fr112-status-update.md` — the canonical FR that resolved this
- `feature-requests/FR-123-fr112-status-fix.md` — first rejected duplicate
- `feature-requests/FR-112-inception-provider.md` — the file that was already fixed
- `feature-requests/FR-126-inquisitor-propose-verify-resolution.md` — addresses root cause of repeated proposals
- `CHANGELOG.md` — v0.4.60 entry confirming FR-112 shipment
