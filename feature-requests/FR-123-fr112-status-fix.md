# FR-123: Update FR-112 Status Draft → Implemented

**Priority:** LOW
**Type:** Bug
**Status:** ❌ Rejected
**Rejection Reason:** Duplicate of FR-120, which is already approved and implemented. This FR adds no new information, no new acceptance criteria, and no new scope beyond what FR-120 already covers. Accepting it would violate the `audit_as_ritual` trap by creating bureaucratic artifacts that track already-resolved work.
**Effort:** 5 min
**Requested:** 2026-03-07

> **⚠️ DUPLICATE**: This issue is fully covered by **FR-120** (`feature-requests/FR-120-fr112-status-update.md`), which was approved on 2026-03-07 and already implemented. FR-112's status field now correctly reads `✅ Implemented (v0.4.60)`. No further action is required.

## Summary

FR-112 (Inception Labs Mercury-2 Provider) shipped in v0.4.60 with full implementation, tests, and CHANGELOG entry, but its status field read "Draft." The Inquisitor flagged this in eight consecutive audits (I–VIII).

## Value Statement

Maintainers and the Inquisitor get accurate project status, eliminating a persistent audit violation from consecutive reports.

## Problem

`feature-requests/FR-112-inception-provider.md` status field read `Draft` despite the feature being fully shipped in v0.4.60. This:

1. Triggered ✗ VIOLATION in every Inquisitor audit (I–VIII), adding noise.
2. Misled readers about the feature's actual state.
3. Violated the `audit_as_ritual` trap: "3+ audits without fix → ritual, not process."

## Proposed Solution

**Already applied.** FR-112 status was changed from `Draft` to `✅ Implemented (v0.4.60)` as part of FR-120.

## Acceptance Criteria

- [x] `feature-requests/FR-112-inception-provider.md` status reads `✅ Implemented (v0.4.60)`
- [x] Inquisitor audit no longer flags FR-112 status as a violation
- [x] Covered by existing FR-120

## Alternatives Considered

- **Create new FR** — Rejected. FR-120 already exists and is approved/implemented.
- **Apply fix without FR** — Rejected. FR-120 already provides the paper trail.

## Related

- `feature-requests/FR-120-fr112-status-update.md` — the existing FR that resolved this
- `feature-requests/FR-112-inception-provider.md` — the file that was fixed
- `CHANGELOG.md` — v0.4.60 entry confirming FR-112 shipment
