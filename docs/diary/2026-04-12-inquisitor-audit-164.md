## 2026-04-12: Inquisitor Audit — Missing diary reflections for merged feat PRs

**Context:** Audited the latest 5 commits on `main` against the Scripture. Scope: Conventional Commits, changelog fragments, requirement traceability (ADR-001), test `@pytest.mark.req` tags, diary reflections, and noqa confessions.

**Commits audited:**
- `efb5e75` feat(node-factory): FR-223 (#90)
- `30710b4` feat(a2a): FR-225 (#89)
- `a687eb7` feat(lint): FR-221 (#87)
- `1346e5d` test(cli): FR-224
- `9cd76e6` docs(FR): FR-225 docs prep

**Findings:**

1. ✗ VIOLATION — **FR-223 and FR-225 merged without diary entries.** Both are `feat` PRs with `FR-XXX` references — the diary-gate CI check is a required status check, yet no `docs/diary/*reflection*fr-223*` or `*fr-225*` files exist on `main`. Either the gate was bypassed (admin override) or the regex match failed silently. The diary-gate grep pattern (`docs/diary/.*reflection.*fr-${FR_NUM}[^0-9]`) should be investigated for edge cases (e.g., FR number at end of filename before `.md`).

2. ✗ VIOLATION — **Direct commits on `main` without PR.** Commits `1346e5d` and `9cd76e6` lack the `(#XX)` PR suffix that GitHub squash merges add. Branch protection requires PRs for `main`. If these are Chaplain automation pushes, the bypass should be documented in `reference/break-glass.md` per emergency bypass policy.

3. ✓ COMPLIANT — **All noqa suppressions documented.** `noqa_coverage.py` reports 71 suppressions, 76 confessions, 0 undocumented. CONF-005 and CONF-006 properly marked as resolved by FR-223.

4. ✓ COMPLIANT — **Test requirement traceability.** FR-223 tests tagged `REQ-YG-223` (18 tests), FR-225 tests tagged `REQ-YG-207`. All new test files follow ADR-001.

5. ✓ COMPLIANT — **Conventional Commits and changelog fragments.** All 5 commits follow format. `feat` commits (FR-221, FR-223, FR-225) have corresponding fragments in `changelog/unreleased/`. `test` and `docs` types correctly omit fragments.

**Heuristic:** A CI gate that can be bypassed without an audit trail is advisory, not enforcement. The diary-gate passes silently when it should block — either the regex has a boundary bug, or admin overrides leave no trace. Both outcomes violate `detection_without_enforcement`. Fix: add a post-merge webhook that verifies diary existence for merged feat/fix PRs and auto-opens an issue when missing.

**Seed:** If the Chaplain automation pipeline can push directly to `main`, does it inherit the same doctrine gates as human contributors? Should automation commits be tagged (e.g., `[chaplain]`) to distinguish them from human bypasses in audit?
