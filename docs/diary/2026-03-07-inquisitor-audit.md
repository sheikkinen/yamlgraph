## 2026-03-07: Inquisitor Audit — persistent violations survive third inspection

**Context:** Third Inquisitor audit covering commits `41d8588`..`49f3d36` (5 commits: two diary entries, one release, one feature, one chore). Focus: whether the two ✗ VIOLATIONS from the Mar 6 audits were resolved before or after v0.4.60 shipped.

**Findings:**

1. **✗ VIOLATION — ARCHITECTURE.md still says "7 providers" (lines 219, 1114).** Third consecutive audit flagging this. No REQ-YG-XXX or CAP-XX was added for Inception Labs. The drift is now baked into tagged release v0.4.60 and remains on HEAD. The Entry 91 diary acknowledged the gap but no corrective commit followed. ADR-001 traceability broken for the 8th provider.

2. **✗ VIOLATION — FR-112 still "Status: Draft".** Feature is implemented, tested, merged, released, and tagged. The feature request header still reads `Status: Draft`. The Sermon (Enforce) requires updating implementation status. Flagged in both Mar 6 audits; still unresolved.

3. **✓ COMPLIANT — Conventional Commits.** All 5 commits use correct `type(scope): description` format. FR reference present on the feature commit.

4. **✓ COMPLIANT — CHANGELOG accurate.** `[0.4.60]` section documents FR-112 and FR-110. Release commit bumps version correctly.

5. **✓ COMPLIANT — noqa Confessions current.** `scripts/noqa_coverage.py --strict` reports 55/55 documented. No unconfessed suppressions.

**Heuristic:** *A violation that survives three audits is no longer drift — it is policy.* If the project tolerates known ✗ items across multiple audits and a release, the audit process is decorative. Either fix the violations or downgrade them to ⚠ DRIFT with an explicit rationale. Ambiguity between "we should fix this" and "we accept this" erodes the authority of every future finding.

**Seed:** Should persistent violations (same ✗ across ≥2 audits) auto-escalate to a tracked issue or feature request with a deadline? A violation that cannot be closed or explicitly accepted is an open wound in the doctrine.
