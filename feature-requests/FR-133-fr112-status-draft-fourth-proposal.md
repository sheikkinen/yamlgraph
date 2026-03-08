# FR-133: Update FR-112 Status Draft → Implemented (Fourth Proposal)

**Priority:** LOW
**Type:** Bug
**Status:** ❌ Rejected
**Rejection Reason:** Duplicate of FR-120, which is approved and already implemented. This is the fourth proposal for the same fix (FR-120 approved, FR-123 rejected, FR-129 rejected). The Inquisitor auto-propose mechanism continues to emit proposals for a resolved violation. See `audit_as_ritual` trap: "3+ audits without fix → ritual, not process" — but the fix IS applied; the ritual is the re-proposal.
**Effort:** 0 min (no action needed)
**Requested:** 2026-03-08

> **⚠️ DUPLICATE**: This issue is fully covered by **FR-120** (`feature-requests/FR-120-fr112-status-update.md`), approved 2026-03-07 and already applied. FR-123 and FR-129 were previously rejected for the same duplication. No further action required.

## Summary

The Inquisitor auto-proposed (for the fourth time) a fix for FR-112's status field. The field already reads `✅ Implemented (v0.4.60)` as of FR-120's implementation. The problem described in the inbox no longer exists.

## Value Statement

No value — the violation is already resolved. Continued re-proposals add noise, not signal.

## Problem

The Inquisitor inbox received `.chaplain/inbox/inquisitor-fr-status-draft.md` claiming FR-112 status reads "Draft". Investigation confirms:

1. **FR-112 status:** `✅ Implemented (v0.4.60)` — correct.
2. **FR-120 (canonical fix):** Approved and applied.
3. **FR-123:** Rejected as duplicate of FR-120.
4. **FR-129:** Rejected as duplicate of FR-120.

**Root cause of repeated proposals:** The Inquisitor's auto-propose mechanism does not verify whether a prior FR already resolved the flagged violation before emitting a new proposal. This is tracked by FR-126 (Inquisitor Propose Verify Resolution).

## Proposed Solution

No action needed. The fix is already applied.

**Residual housekeeping (out of scope for this FR):**
- FR-120 acceptance criteria checkboxes remain unchecked; its status reads "Approved" not "Done"
- FR-112 acceptance criteria checkboxes remain unchecked despite feature being shipped
- These are separate finalization concerns, not blockers

## Acceptance Criteria

- [x] `feature-requests/FR-112-inception-provider.md` status reads `✅ Implemented (v0.4.60)`
- [x] Covered by existing FR-120
- [ ] Inquisitor auto-propose dedup addressed (tracked by FR-126, out of scope)

## Alternatives Considered

- **Create yet another FR** — Rejected. This is the fourth proposal. The pattern itself is the problem.
- **Fix FR-120 status to Done** — Out of scope. Separate housekeeping concern.
- **Suppress Inquisitor re-proposals** — Tracked by FR-126; the correct long-term fix.

## Related

- `feature-requests/FR-120-fr112-status-update.md` — canonical FR that resolved this
- `feature-requests/FR-123-fr112-status-fix.md` — first rejected duplicate
- `feature-requests/FR-129-fr112-status-drift-resolution.md` — second rejected duplicate
- `feature-requests/FR-112-inception-provider.md` — the file that was already fixed
- `feature-requests/FR-126-inquisitor-propose-verify-resolution.md` — addresses root cause
