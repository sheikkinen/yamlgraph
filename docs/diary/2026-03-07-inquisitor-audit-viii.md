## 2026-03-07: Inquisitor Audit VIII — the ritual persists, a new gap opens

**Context:** Eighth audit covering commits `eeb0aa7`..`92e0a37` (5 commits: FR-114 merge+revert, FR-115/FR-116 chore, FR-116 feat PR merge, enforce worktree exclusion fix). Primary question: did the FR-116 implementation follow full doctrine, and have the persistent wounds from seven prior audits survived an eighth cycle?

**Findings:**

1. **✗ VIOLATION — ARCHITECTURE.md line 1125: "7 providers" (8th audit).** Line 219 says "8 providers." Line 1125 says "7 providers." Eight consecutive audits have flagged this one-character fix. The `audit_as_ritual` trap threshold (3) has been exceeded by 167%. The Inquisitor will no longer re-flag this finding — it is hereby **formally accepted as a known deviation** per Audit VII's Seed. If unfixed by v0.5.0 release, escalate to release-blocker.

2. **✗ VIOLATION — FR-112 Status: "Draft" (8th audit).** Feature shipped in v0.4.60. Same analysis as finding #1. **Formally accepted as known deviation.** Deadline: v0.5.0 release.

3. **✗ VIOLATION — FR-116 missing CHANGELOG entry.** `4765fdc` (`feat: FR-116 implementation`) added a new capability (watch→enforce spawn detection) with ARCHITECTURE.md requirement (REQ-YG-116, CAP-35), 5 tests with `@pytest.mark.req("REQ-YG-116")`, and a demo script — but zero CHANGELOG entry under `[Unreleased]`. Commandment 10 requires the CHANGELOG to bear witness.

4. **✓ COMPLIANT — FR-116 requirement traceability.** ADR-001 fully observed: REQ-YG-116 in ARCHITECTURE.md, `req_coverage.py` updated, all 5 test functions tagged `@pytest.mark.req("REQ-YG-116")`. FR-116 status correctly at "Approved." noqa confessions intact (CONF-002, CONF-003 cover both existing suppressions).

5. **⚠ DRIFT — `eeb0aa7` Conventional Commit violation persists in window.** The FR-114 merge (`FR-114: Feature Request: ...`) still lacks a type prefix and remains in the 5-commit audit window. Its revert (`63db5d3`) uses git's auto-format. Two commits with zero Conventional Commit compliance — but both are net-zero (merge + revert), so the codebase impact is nil.

**Heuristic:** *A feature with tests, requirements, and ARCHITECTURE entries but no CHANGELOG is 90% compliant — and the missing 10% is the part users read.* Internal traceability (ADR-001) was perfect; external communication (CHANGELOG) was forgotten. The pipeline that generated the PR (`enforce_worktree.sh`) automates code changes but not release notes. Automation that covers implementation but not communication creates a new class of drift.

**Seed:** Should `enforce_worktree.sh` — or a pre-commit hook — verify that any commit containing `feat:` also touches CHANGELOG.md? A mechanical gate at commit time would catch the exact gap this audit found, shifting enforcement from audit-after to prevent-before.
