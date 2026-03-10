## 2026-03-10: Inquisitor Audit — Traceability burst ships without bookkeeping

**Context:** Audited the 5 most recent commits on HEAD (b4ef9a9..f2bf5ca). Window contains 2 `feat` (FR-178, FR-180), 2 `chore` (FR-177, capability markers), 1 `docs` (audit entries 85–88). All five are part of a traceability infrastructure sprint. Prior audit-89 already flagged missing CHANGELOG and diary for FR-180; this audit checks whether the pattern persists across the full burst.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits format.** All 5 commits follow the format. Both `feat` commits include `FR-XXX` references. Commandment 10 satisfied at the syntax level.

2. ✗ VIOLATION — **No CHANGELOG entries for FR-178 or FR-180.** Two `feat` commits introducing 871+ lines of new infrastructure (capability registry, ID reservation, pre-commit hooks, 21 tests) have zero entries under `[Unreleased]`. Commandment 10: "let the CHANGELOG bear witness." This is the second consecutive audit flagging this — the debt is compounding.

3. ⚠ DRIFT — **FR-180 test req tags are generic.** All 21 tests in `test_id_registry.py` use `@pytest.mark.req("REQ-YG-001")` (Config Loading & Validation). ID reservation is not config loading — it's a new capability that deserves its own requirement. ADR-001 letter satisfied (tags present), spirit violated (tags don't trace to the actual feature). FR-178 has REQ-YG-161 in ARCHITECTURE.md but FR-180 has no dedicated requirement.

4. ✗ VIOLATION — **No diary entries for FR-177/178/180.** Three consecutive commits forming a coherent traceability sprint produced zero reflections. The diary-gate CI job exists precisely for this — but direct pushes to main bypassed it. Sermon: "After completing a task list, add a metacognitive entry to docs/diary/."

5. ⚠ DRIFT — **`scripts/aggregate_capabilities.py` (176 lines) has no tests.** Introduced in 95bcc64 as `chore`, but this script generates ARCHITECTURE.md content — production infrastructure. Commandment 7: no new production branch without a witness test.

**Heuristic:** Infrastructure-for-infrastructure creates a blind spot. When the work *is about* traceability tooling, the temptation is to treat the tooling itself as exempt from the traceability it enforces. The cure: apply the same gates to meta-tooling that the meta-tooling applies to features. Audit-89 named this; audit-92 confirms it's a pattern, not an incident.

**Seed:** Should `scripts/aggregate_capabilities.py` and `yamlgraph/utils/id_registry.py` be promoted from "scripts/utils" to first-class capabilities with their own CAP/REQ entries — enforcing that the traceability system is itself traceable?
