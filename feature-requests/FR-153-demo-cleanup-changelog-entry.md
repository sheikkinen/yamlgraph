# Feature Request: Stale Demo Cleanup Missing CHANGELOG Entry

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.25 days
**Requested:** 2026-03-08

## Summary

Add the missing `### Removed` CHANGELOG entry for commit `a0e6f00` (`chore: cleanup of stale demos`), which deleted 419 lines across 3 files without recording the removal — violating Commandment 8 across three consecutive Inquisitor audits (XXXVI, XXXVIII, XXXIX).

## Value Statement

Maintainers and users get an accurate removal history, and the three-audit CHANGELOG violation is resolved.

## Problem

Commit `a0e6f00` deleted three stale demo/experiment files:

- `examples/cost-router/poc_granite.py` (188 lines)
- `scripts/loopback-poc/README.md` (56 lines)
- `scripts/loopback-poc/mcp_server.py` (175 lines)

Total: 419 lines removed, zero CHANGELOG documentation. This violates Commandment 8: *"record significant removals in commit notes."* The omission was flagged in Inquisitor Audits XXXVI, XXXVIII, and XXXIX — three consecutive audits without remediation, triggering the `audit_as_ritual` trap: *"3+ audits without fix → ritual, not process."*

FR-149 (CI CHANGELOG gate) will prevent future recurrences; this proposal fixes the existing gap.

## Proposed Solution

Add a `### Removed` section under `[Unreleased]` in CHANGELOG.md, before the existing `### Fixed` section (per [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) convention: Added → Changed → Deprecated → Removed → Fixed → Security):

```markdown
### Removed
- Stale demo files: `examples/cost-router/poc_granite.py`, `scripts/loopback-poc/` experiment (419 lines, commit a0e6f00)
```

## Acceptance Criteria

- [ ] CHANGELOG.md `[Unreleased]` contains a `### Removed` section
- [ ] Entry references the three deleted files and commit `a0e6f00`
- [ ] Entry describes the removal as stale demo cleanup
- [ ] `grep -c "poc_granite\|loopback-poc" CHANGELOG.md` returns ≥ 1
- [ ] Section ordering follows Keep a Changelog convention (Added → Changed → Removed → Fixed)

## Alternatives Considered

- **Wait for next release**: Rejected — three audits already flagged this; further delay is the `audit_as_ritual` trap.
- **Amend the original commit**: Rejected — commit is already on `main`; rewriting history violates workflow.

## Related

- Commit `a0e6f00` — the `chore: cleanup of stale demos` commit missing the entry
- `feature-requests/FR-149-ci-changelog-gate.md` — CI gate to prevent future recurrences
- `feature-requests/FR-151-fr137-changelog-entry.md` — analogous missing CHANGELOG fix
