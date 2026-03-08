## 2026-03-07: Inquisitor Audit XVIII — FR-118 lands clean, CHANGELOG debt grows

**Context:** Eighteenth audit covering commits `b58eaa7`..`dc344fb` (5 commits: `feat` ×1, `docs(chaplain)` ×1, `chore(precommit)` ×1, `chore(tests)` ×1, `chore(graph)` ×1). First `feat:` commit in the window since FR-116. `fe170bf feat: FR-118 implementation (#5)` adds Inquisitor auto-propose capability with script, tests, ARCHITECTURE.md requirement, and req_coverage update — a textbook ADR-001 delivery.

**Findings:**

1. **✓ COMPLIANT — FR-118 ADR-001 exemplary.** `fe170bf` adds CAP-36 + REQ-YG-118 to ARCHITECTURE.md, extends `req_coverage.py`, and all 3 test functions carry `@pytest.mark.req("REQ-YG-118")`. Requirement → capability → tests chain intact.

2. **✗ VIOLATION — FR-118 missing from CHANGELOG.** The [Unreleased] section documents FR-113, FR-106, but not FR-118. A new capability shipped without a CHANGELOG witness. Commandment 10 violated.

3. **✗ CALCIFIED-3 persists (10th consecutive audit).** ARCHITECTURE.md line 1134: "7 providers" → "8". FR-116 CHANGELOG entry absent. Per Audit XVII's Seed: the next invocation should be a fix, not another audit. The Inquisitor will not redescribe these again.

4. **⚠ DRIFT — No implementation diary entry for FR-118.** The Sermon's Distill step mandates metacognitive reflection after completing a task. FR-118 was planned, judged, and implemented — but the cognitive process was not recorded. The audit entries mentioning FR-118 are not a substitute for an implementation reflection.

5. **✓ COMPLIANT — Conventional Commits, noqa confessions, Co-authored-by.** All 5 commits use valid prefixes. Both noqa suppressions (ANN001, ARG002) confessed. PR merge commit carries Copilot trailer.

**Heuristic:** *ADR-001 compliance and CHANGELOG compliance are independent gates — passing one does not imply the other.* FR-118 perfectly traced from requirement to capability to tests, yet skipped the CHANGELOG. The root cause: `enforce_worktree.sh` automates the code pipeline but does not enforce CHANGELOG updates. A pre-merge checklist or linter rule (`feat:` commit → CHANGELOG entry required) would close this gap.

**Seed:** Should `enforce_worktree.sh` or a pre-commit hook verify that every `feat:` or `fix:` commit in a PR has a corresponding CHANGELOG entry in [Unreleased]? The manual discipline has failed for FR-116 (now 10 audits) and FR-118 (day zero).
