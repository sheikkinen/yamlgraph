# Feature Request: FR-116 Missing CHANGELOG Entry

**Priority:** HIGH
**Type:** Bug
**Status:** Duplicate — resolved by FR-122 (commit `2a4f61c`)
**Verdict:** APPROVED as duplicate closure. All three claims independently verified:
  CHANGELOG.md line 13 ✓, FR-122 Status: Approved ✓, commit 2a4f61c ✓.
  No further action required. Filed to prevent Inquisitor re-flagging.
**Effort:** 5 min
**Requested:** 2026-03-07

## Summary

Inquisitor Audit XI flagged FR-116 (Watch→Enforce Integration) as missing from `CHANGELOG.md [Unreleased]`. This is a duplicate of FR-122, which was already approved, implemented, and merged.

## Value Statement

Maintainers and the Inquisitor get accurate release notes; Commandment 10 is upheld.

## Problem

FR-116 (commit `4765fdc`) added CAP-35, REQ-YG-116, 5 tagged test classes, and a demo script but originally had no CHANGELOG entry. Flagged in Inquisitor Audits VIII–XI (4 consecutive audits). Escalated to release-blocker in Audit XI.

## Proposed Solution

No action required. FR-122 already resolved this:

- **FR-122 feature request:** `feature-requests/FR-122-fr116-changelog-entry.md` (Status: Approved)
- **Implementation commit:** `2a4f61c` — `feat: FR-122 implementation (#8)`
- **CHANGELOG line 13** now contains:

```markdown
- **FR-116 Watch→Enforce Spawn**: `watch.sh` snapshots `feature-requests/` before graph execution,
  diffs after via `comm -13`, skips rejected FRs (`Status.*Rejected`), and spawns
  `enforce_worktree.sh` via `nohup ... &` for approved FRs. (REQ-YG-116)
```

## Acceptance Criteria

All criteria inherited from FR-122 and already satisfied:

- [x] `CHANGELOG.md` `[Unreleased] → Added` contains FR-116 entry with `(REQ-YG-116)` tag
- [x] Commit `2a4f61c` follows convention: `feat: FR-122 implementation (#8)`
- [x] Inquisitor violation resolved

## Alternatives Considered

- **Create a new FR** — Rejected. FR-122 already covers this exact scope with identical acceptance criteria.
- **Re-implement** — Unnecessary. The fix is already on `main`.

## Resolution

This inbox item arrived from Audit XI after FR-122 was already written (Audits VIII–X) but before the Inquisitor re-scanned post-merge. The `audit_as_ritual` diary trap applied: 4 consecutive audits flagged the same violation. FR-122 broke the cycle. No further action needed.

## Related

- `feature-requests/FR-122-fr116-changelog-entry.md` — the FR that resolved this
- `CHANGELOG.md` line 13 — the entry that was added
- Inquisitor Audits VIII, IX, X, XI — escalation trail
