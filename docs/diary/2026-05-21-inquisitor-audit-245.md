## 2026-05-21: Inquisitor Audit — v0.5.2 release batch (FR-432 to FR-435)

**Context:** Audited the latest 5 commits on `main` covering FR-432 through FR-435 and the v0.5.2 release freeze. These commits span dotenv config hardening, post-edit hook modularization, apply_patch coverage, and markdown hygiene — all infrastructure/tooling work.

**Findings:**

1. ✓ COMPLIANT — All 5 commits follow Conventional Commits with correct `type(scope): FR-XXX` format. The `feat` commit (FR-435) includes its FR reference; `fix` and `refactor` commits are properly scoped.

2. ✓ COMPLIANT — Every `feat`/`fix`/`refactor` commit has a matching changelog fragment (now frozen under `changelog/0.5.2/`). Diary reflections exist for all four FRs, each with Trap, Insight, Heuristic, and Seed sections.

3. ✓ COMPLIANT — FR-432 (core `yamlgraph/config.py` change) has 6 unit tests all tagged `@pytest.mark.req("REQ-YG-043")`, correctly linking to the configuration management requirement.

4. ⚠ DRIFT — Hook tests in `.github/hooks/tests/` (FR-433, FR-434, FR-435) lack `@pytest.mark.req` tags. ADR-001 states "every test function must have" the tag, but hook tests live outside `tests/unit/` and test shell scripts, not Python capabilities. The requirement is ambiguous for infrastructure test suites.

5. ⚠ DRIFT — 28 `# noqa` suppressions across `yamlgraph/` and `scripts/` lack `CONF-XXX` confession entries. None were introduced by the audited commits (all pre-existing), but the debt remains unaddressed and grows harder to reconcile over time.

**Heuristic:** When ADR-001 says "every test function," scope boundaries matter — infrastructure tests that validate shell scripts need either explicit exemption or their own traceability contract. Ambiguity in scope invites drift.

Seed: Should ADR-001 be amended to define explicit traceability tiers — core capability tests (req-tagged), infrastructure tests (scope-exempt but inventoried), and demo tests (coverage-only) — so the rule is enforceable without false positives?
