## 2026-03-08: Inquisitor Audit XXXIII — Phantom Requirements Recur

**Context:** Thirty-third audit. Examined 5 most recent commits on `feat/fr-136-judge-split-verdict` (`54b3d73..1a9ae7e`): FR-136 judge SPLIT verdict, FR-140 clean GIT_* test fixture, housekeeping chore, FR-139 bare=true corruption guard, and FR-140 diary update. Audited against Conventional Commits, Co-authored-by trailers, ADR-001 requirement traceability, diary reflections, and noqa confessions.

**Findings:**

1. **✗ VIOLATION — FR-136 tests reference phantom requirement `REQ-YG-141` (ADR-001).** Commit `1a9ae7e` adds `test_judge_split_verdict.py` with 3 tests tagged `@pytest.mark.req("REQ-YG-141")`, but `REQ-YG-141` is not defined in `ARCHITECTURE.md` nor registered in `scripts/req_coverage.py`. The CHANGELOG mentions it parenthetically but ARCHITECTURE.md has no entry. This is the same class of violation as `REQ-YG-UTIL` flagged in Audit XXXII — phantom requirements that satisfy syntactic checks while defeating traceability. Two consecutive audits with the same violation pattern confirms the `partial_remediation` trap.

2. **✗ VIOLATION — 3 of 5 commits missing Co-authored-by trailer.** Commits `4bdabbe`, `0c74848`, `54b3d73` lack the required `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` trailer. Only `1a9ae7e` and `ad246b5` include it. Same violation as Audit XXXII (3 of 5 missing). Two consecutive audits = `audit_as_ritual` trap: the finding is noted but not fixed.

3. **⚠ DRIFT — No diary reflections for FR-136 or FR-139 (Sermon: Distill).** Neither `reflection-fr-136.md` nor `reflection-fr-139.md` exists in `docs/diary/`. FR-139's absence was flagged in Audit XXXII; FR-136 is new. The Distill obligation remains unfulfilled for both features.

4. **✓ COMPLIANT — Conventional Commits and CHANGELOG discipline.** All 5 commits follow `type(scope): description` format. Both `feat` commits reference FR numbers. CHANGELOG entries present for FR-136 (Added) and FR-139 (Fixed). `chore` commits correctly omit CHANGELOG entries.

5. **✓ COMPLIANT — noqa confessions fully covered.** `noqa_coverage.py` reports 55 suppressions, 57 documented confessions, 0 undocumented. Clean.

**Heuristic:** *A recurring audit finding that isn't fixed is a ritual, not a process.* Phantom requirements and missing trailers have now appeared in two consecutive audits (XXXII, XXXIII). The `audit_as_ritual` trap applies: flagging without fixing degrades the audit's authority. Either automate the guard (CI rejects phantom reqs, pre-commit enforces trailer) or accept the finding as policy and remove it from the checklist.

**Seed:** Should `req_coverage.py --strict` cross-reference test markers against `ARCHITECTURE.md` definitions, and should the pre-commit `commit-msg` hook enforce the Co-authored-by trailer — converting both recurring violations into automated gates?
