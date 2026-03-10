## 2026-03-10: Inquisitor Audit — Remediation begins but CHANGELOG and diary debt compounds

**Context:** Audited 5 most recent commits on `feat/fr-178-capability-registry` branch (`b4ef9a9..0882893`). Window contains 2 `feat` (FR-178, FR-180), 2 `chore` (FR-177, cleanup), 1 `docs` (diary batch). Prior audits 88–92 flagged missing CHANGELOG, diary, and tests for FR-178. Commit `0882893` shows partial remediation (CONF-207 confessed, FR-182 cleanup). This audit checks whether the debt is shrinking or growing.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits and noqa confessions.** All 5 commits follow CC format. Both `feat` commits reference FR numbers. The `noqa: E402` in `migrate_capabilities.py:352` is confessed as CONF-207 in `docs/confessions.md`. Commandment 10 and noqa Confessions satisfied.

2. ✓ COMPLIANT — **FR-180 tests are exemplary.** 21 test functions in `test_id_registry.py`, all tagged with `@pytest.mark.req("REQ-YG-001")` or `@pytest.mark.req("REQ-YG-004")`. ADR-001 and Commandment 7 both satisfied. This is the standard other commits should match.

3. ✗ VIOLATION — **FR-178 has no tests for 754+ lines of new script code.** `scripts/migrate_capabilities.py`, `scripts/validate_capabilities.py`, `scripts/aggregate_capabilities.py` were added (2304 insertions across 64 files) with zero `@pytest.mark.req` tags. Commandment 7 ("No new production branch shall be merged without a witness test") and ADR-001 both violated. Third consecutive audit flagging this.

4. ✗ VIOLATION — **No CHANGELOG entries for FR-178 or FR-180.** Two `feat` commits adding a capability registry system and ID reservation have no entries under `[Unreleased]`. Commandment 10: "let the CHANGELOG bear witness." Third consecutive audit flagging this.

5. ✗ VIOLATION — **No reflective diary entries for FR-178 or FR-180.** Only audit entries mention these FRs. Sermon of the Chaplain: "After completing a task list, add a metacognitive entry." The diary-gate CI job would catch this on PR — but no PR has been opened yet.

**Heuristic:** Three consecutive audits flagging the same violations is the "audit as ritual" trap from the Knowledge Graph. The cure is not more audits — it is a blocking gate. The branch cannot be merged without CHANGELOG and diary entries (diary-gate CI exists for this). The real risk is that the branch grows so large that writing the diary and CHANGELOG retroactively becomes a chore rather than a reflection. Write the diary *during* the work, not after.

**Seed:** Should `pre-commit` enforce that any commit touching `scripts/*.py` with more than 100 new lines must include a corresponding `tests/unit/test_*.py` file in the same commit?
