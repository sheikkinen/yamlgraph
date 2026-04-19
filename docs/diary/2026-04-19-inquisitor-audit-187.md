## 2026-04-19: Inquisitor Audit — FR-240 a2a_call branch & FR-238 merge

**Context:** Audited the 5 most recent commits on `feat/fr-240-a2a-call-node-type` (718cc90..392ac26), covering FR-240 (a2a_call node type), FR-241 (worktree teardown FR), and FR-238 (user-configurable reducers, merged to main).

**Findings:**

1. ✓ COMPLIANT — All 5 commits follow Conventional Commits format. Both `feat` commits reference their FR number. ARCHITECTURE.md updated with new CAP and REQ entries. Tests carry `@pytest.mark.req` markers. Diary entries written for both features. No undocumented noqa suppressions.

2. ⚠ DRIFT — **Stale REQ ID in changelog fragment.** `changelog/unreleased/fr-240-a2a-call-node-type.md` references `REQ-YG-239` in both YAML front matter and body text. After the collision fix commit (`172b4189`), ARCHITECTURE.md and tests were renumbered to `REQ-YG-243`, but the changelog fragment was missed. When `aggregate_changelog.py` runs, the generated CHANGELOG will cite the wrong REQ ID.

3. ✓ COMPLIANT — FR-238 (392ac26a) is a clean squash merge on main: diary included in the commit, changelog fragment present with correct `REQ-YG-241`, tests tagged, ARCHITECTURE.md updated.

4. ✓ COMPLIANT — The CAP ID collision (CAP-96→101) was detected by pre-commit and corrected before merge, validating the registry validator gate.

5. ⚠ DRIFT — **FR-241 is a docs(FR) commit only** (4a128d72) — a feature request file was created but no implementation, tests, changelog, or diary exist yet. Acceptable as work-in-progress on a branch, but the FR numbering now collides with the main-branch REQ-YG-241 (which belongs to FR-238 reducers). If FR-241 is implemented, its REQ-YG ID will need careful assignment to avoid a second collision.

**Heuristic:** When a collision-fix commit renumbers IDs across ARCHITECTURE.md and tests, mechanically grep all `changelog/unreleased/` fragments for the old ID and update them in the same commit. The rename is atomic only if every reference is swept.

**Seed:** Could `scripts/req_coverage.py` be extended to cross-check changelog fragment `req:` fields against ARCHITECTURE.md, catching stale references before release?
