## 2026-04-19: Inquisitor Audit — FR-243/FR-248 branch compliance

**Context:** Audited the 5 most recent commits on `feat/fr-243-github-issues-remote-inbox` branch (11156737..48c4d2ee) covering FR-248 (A2A Consumer Phase 2), FR-243 (GitHub Issues remote inbox), FR-249 planning doc, a CAP renumbering chore, and a merge commit. Checked Conventional Commits, changelog fragments, requirement traceability, diary entries, and noqa confessions.

**Findings:**

1. ✓ COMPLIANT — **FR-248 `feat(a2a)`**: Full doctrine compliance. Conventional Commit with FR ref in squash-merged PR #116, changelog fragment present, REQ-YG-250–253 added to ARCHITECTURE.md, 58 tests with `@pytest.mark.req` tags, diary reflection written (`2026-04-19-reflection-fr-248-a2a-consumer-phase2.md`), no new noqa suppressions.

2. ✓ COMPLIANT — **FR-243 `feat(chaplain)`**: Changelog fragment present, REQ-YG-247 added to ARCHITECTURE.md, 25 tests across 6 classes all inheriting class-level `@pytest.mark.req("REQ-YG-247")`, diary reflection written (`2026-04-20-reflection-fr-243-github-issues-remote-inbox.md`), no noqa suppressions.

3. ✓ COMPLIANT — **`docs(FR)` commit 42d83107**: Planning document for FR-249 — `docs` type correctly exempt from changelog, tests, and diary requirements.

4. ⚠ DRIFT — **CAP collision churn**: Two commits in the last 8 (`0a1c6af3` and `11156737`) fix capability/requirement ID collisions (CAP-103→104→106, REQ-YG-245→246). This is the second time a CAP/REQ renumbering has required a fixup commit. The root cause is manual ID assignment without a reservation mechanism — IDs collide when parallel FRs merge in unpredictable order.

5. ⚠ DRIFT — **Audit-200 findings unaddressed**: The previous audit flagged mixed-concern commits and audit saturation (45% of diary entries are audits). Neither has been remediated. The Knowledge Graph trap `audit_as_ritual` applies: repeated audits surfacing the same drift without corrective action degrades the audit's credibility.

**Heuristic:** **Reserve, don't assign.** Capability and requirement IDs should be reserved at FR creation time (e.g., via a monotonic counter file or CI-assigned sequence), not assigned at implementation time when collisions with concurrent work are likely. This is a boundary normalization problem — the ID enters at FR creation, not at merge.

**Seed:** Could `scripts/req_coverage.py` be extended to detect and reject duplicate CAP/REQ IDs at CI time, shifting collision detection from post-merge fixup to pre-merge gate?
