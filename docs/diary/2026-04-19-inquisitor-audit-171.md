## 2026-04-19: Inquisitor Audit — Changelog REQ Cross-Wiring

**Context:** Audited the 5 most recent commits (a25efc08..39b7640a) covering FR-233, FR-234, FR-235, FR-236 work delivered 2026-04-18/19. Checked Conventional Commits, changelog fragments, ARCHITECTURE.md requirements, test req tags, diary entries, and noqa confessions.

**Findings:**

1. ✗ **VIOLATION — FR-234 changelog fragment references wrong REQ.** `changelog/unreleased/fr-234-parallel-fan-out-edges.md` says `req: REQ-YG-235` but ARCHITECTURE.md maps FR-234 → REQ-YG-237. The commit body also cites REQ-YG-162 (a much older requirement). Tests are correctly tagged `@pytest.mark.req("REQ-YG-237")`, so the error is isolated to the changelog fragment and commit message.

2. ✗ **VIOLATION — FR-235 changelog fragment references wrong REQ.** `changelog/unreleased/fr-235-compile-time-pipeline-templates.md` says `req: REQ-YG-235` (same as FR-234's fragment) but ARCHITECTURE.md maps FR-235 → REQ-YG-236. Tests are correctly tagged `@pytest.mark.req("REQ-YG-236")`. Copy-paste origin likely.

3. ✓ **COMPLIANT — All 5 commits follow Conventional Commits.** Types: chore, feat, fix. FR references present on feat/fix commits.

4. ✓ **COMPLIANT — All new tests carry `@pytest.mark.req` tags.** ~30 new test functions across FR-234/235/236, all correctly tagged against ARCHITECTURE.md requirements.

5. ✓ **COMPLIANT — Diary entries, noqa confessions, and demo-output.logs present.** CONF-126 documented. Reflections exist for all four FRs.

**Heuristic:** Changelog fragments are written at enforcement time, after ARCHITECTURE.md requirements are assigned. When two FRs are enforced in the same session, the second fragment inherits the first's REQ by copy-paste. A pre-commit check cross-referencing `changelog/unreleased/*.md` front-matter `req:` against ARCHITECTURE.md capability table would catch this mechanically.

**Seed:** Could `req_coverage.py` be extended to also validate that changelog fragment `req:` fields match the capability table in ARCHITECTURE.md, closing the loop between the three traceability artifacts (tests, changelog, architecture)?
