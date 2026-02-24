# Feature Request: Fix Stale REQ-YG-087–089 Range Notation

**Priority:** LOW
**Type:** Bug
**Status:** Implemented
**Effort:** 15 min
**Requested:** 2026-02-24

## Summary

Replace stale `REQ-YG-087 – REQ-YG-089` range notation with explicit `REQ-YG-087, REQ-YG-089` in ARCHITECTURE.md and CHANGELOG.md, since REQ-YG-088 was removed during FR-082 teardown.

## Value Statement

Maintainers and auditors get accurate requirement traceability, eliminating a drift signal flagged by 6+ consecutive Inquisitor audits.

## Problem

FR-082 dropped the sampling backend and cleanly removed REQ-YG-088 from:
- `ARCHITECTURE.md` requirement rows (lines 565–566 correctly list only 087 and 089)
- `scripts/req_coverage.py` (skips 088, comments explain why)
- Test files (no `@pytest.mark.req("REQ-YG-088")` remains)

However, two summary references still use range notation that implies three requirements:

1. **ARCHITECTURE.md line 291** — capability summary table says `REQ-YG-087 – REQ-YG-089`
2. **CHANGELOG.md line 20** — `[0.4.56]` entry says `REQ-YG-087–089` and mentions `backend: sampling — deferred` which no longer exists

This creates a contradiction: the detail rows correctly show 2 requirements, but the summary tables imply 3. The diary has flagged this as ⚠ DRIFT and ✗ VIOLATION across multiple audits.

## Proposed Solution

### ARCHITECTURE.md (line 291)

```diff
-| 30 | Copilot Node | `node_factory/copilot_node`, `node_compiler` | REQ-YG-087 – REQ-YG-089 |
+| 30 | Copilot Node | `node_factory/copilot_node`, `node_compiler` | REQ-YG-087, REQ-YG-089 |
```

### CHANGELOG.md (line 20)

```diff
-- **FR-081 Copilot Node Type** (CAP-30, REQ-YG-087–089): New `copilot` node for delegating to GitHub Copilot CLI
+- **FR-081 Copilot Node Type** (CAP-30, REQ-YG-087, REQ-YG-089): New `copilot` node for delegating to GitHub Copilot CLI
```

Also remove the `backend: sampling — deferred` sub-bullet from the CHANGELOG entry if it still exists, since the sampling backend was deleted entirely.

## Acceptance Criteria

- [x] ARCHITECTURE.md capability summary table (line 291) lists `REQ-YG-087, REQ-YG-089` (no range)
- [x] CHANGELOG.md `[0.4.56]` entry lists `REQ-YG-087, REQ-YG-089` (no range)
- [x] CHANGELOG.md `[0.4.56]` entry does not reference `backend: sampling` or `deferred`
- [x] `python scripts/req_coverage.py --strict` passes (no change expected — already correct)
- [x] No remaining `REQ-YG-088` references in ARCHITECTURE.md or CHANGELOG.md
- [x] `grep -r 'REQ-YG-087.*089' ARCHITECTURE.md CHANGELOG.md` returns no range-notation matches

## Alternatives Considered

1. **Re-number REQ-YG-089 → REQ-YG-088** — Rejected: would require updating tests, `req_coverage.py`, and multiple docs. Higher risk for no functional benefit. Gaps in requirement IDs are normal after feature removal.
2. **Do nothing** — Rejected: the drift has been flagged by 6+ audit cycles. Leaving it contradicts Commandment 10 (preserve and improve the doctrine).

## Related

- FR-081: Copilot Node Type (original feature that created REQ-YG-087–089)
- FR-082: Sampling Backend (teardown that removed REQ-YG-088)
- `docs/diary.md` lines 114–116, 147–149, 165–168: Repeated audit flags
- `scripts/req_coverage.py` line 22–26: Already correctly excludes REQ-YG-088
