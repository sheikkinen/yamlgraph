## 2026-03-08: Inquisitor Audit XLIV — FR-157/FR-158 Requirement Cross-Wiring

**Context:** Audited the latest 5 commits spanning FR-157 (conflict marker CI gate), FR-158 (diary-gate RED tests), and three docs(FR) additions (FR-158, FR-160, FR-161). The audit focused on Conventional Commits compliance, CHANGELOG entries, ADR-001 requirement traceability, diary reflections, and noqa confessions.

**Findings:**

1. ✗ VIOLATION — **Wrong requirement tag in diary-gate tests**: `test_ci_diary_gate.py` marks both tests with `@pytest.mark.req("REQ-YG-151")` (conflict marker gate's requirement) instead of `REQ-YG-152` (diary gate's own requirement per ARCHITECTURE.md table). This is a traceability defect: the diary-gate capability appears tested but its actual requirement ID has zero coverage.

2. ✗ VIOLATION — **Duplicate section number in ARCHITECTURE.md**: Both "CI Conflict Marker Gate (FR-157)" and "CI Diary Existence Gate (FR-158)" are headed `### 53.` in the detailed requirements section. The capability table correctly assigns 53 and 54 respectively, but the prose sections both say 53. This contradicts the table and will confuse automated tooling.

3. ⚠ DRIFT — **Missing diary reflection for FR-157**: The `feat(ci): FR-157` commit merged without a diary entry. FR-157 introduced a new CI gate — a non-trivial capability — yet the Sermon's Distill step was skipped. This is the same pattern flagged in Audits XXXIV–XXXV for FR-137/FR-145, now recurring despite FR-152's remediation.

4. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow the format. The feat commit includes FR-XXX reference. Co-authored-by trailers present.

5. ✓ COMPLIANT — **noqa confessions**: Both existing suppressions (ANN001 in `executor_async.py`, ARG002 in `token_tracker.py`) are documented in `docs/confessions.md`.

**Heuristic:** When scaffolding a new capability (CAP-N+1) alongside a sibling (CAP-N), copy-paste of requirement IDs and section numbers is the most likely error vector. A CI check that validates ARCHITECTURE.md section numbers match the capability table, and that `@pytest.mark.req` IDs map to the correct capability, would catch this at commit time. *partial_remediation* trap: fixing the table but not the prose (or tests) creates a false sense of correctness.

**Seed:** Could `req_coverage.py --strict` be extended to cross-validate that each test file's `@pytest.mark.req` IDs match the capability listed in ARCHITECTURE.md's table for the file's test subject? A "req-wiring" check would catch the REQ-YG-151/152 swap at commit time rather than audit time.
