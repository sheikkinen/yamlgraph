## 2026-03-10: Inquisitor Audit — Traceability sprint: tests exemplary on FR-180, absent on FR-178

**Context:** Audited the 5 most recent commits on `feat/fr-178-capability-registry` (bf76dfe..0882893). Window contains 2 `feat`, 2 `chore`, 1 `docs`. All five relate to the traceability infrastructure sprint (FR-177, FR-178, FR-180, FR-182 cleanup). Prior audits (88–94) flagged FR-178 for missing tests, CHANGELOG, and diary. This audit checks whether those violations persist and evaluates the full sprint.

**Findings:**

1. ✗ VIOLATION — **FR-178 shipped 2,304 insertions across 64 files with zero test files.** `scripts/migrate_capabilities.py` (511 lines) and `scripts/validate_capabilities.py` (243 lines) have no tests. Commandment 7 (TDD): "No new production branch shall be merged without a witness test." This is now a recurring finding across multiple audits — the audit is becoming ritual without remediation (trap: `audit_as_ritual`).

2. ✗ VIOLATION — **No CHANGELOG entries for FR-177, FR-178, or FR-180.** Three traceability commits introduced `yamlgraph/utils/id_registry.py`, a pre-commit validation hook, 30+ capability YAML files, and two new scripts — none documented in `[Unreleased]`. Commandment 10: "let the CHANGELOG bear witness to the evolution of the Word."

3. ✗ VIOLATION — **No diary entries for FR-178 or FR-180.** Two `feat` commits with significant architectural decisions (append-only registry design, plan-phase reservation protocol) lack metacognitive reflection. Sermon: "After completing a task list, add a metacognitive entry to docs/diary/."

4. ✓ COMPLIANT — **FR-180 tests are exemplary.** 21 test functions in `tests/unit/test_id_registry.py`, all with `@pytest.mark.req` tags. ADR-001 and Commandment 7 both satisfied.

5. ✓ COMPLIANT — **All noqa suppressions confessed.** Every `# noqa` in `yamlgraph/` and `scripts/` has a corresponding CONF-XXX entry in `docs/confessions.md`. HEAD commit (`0882893`) added CONF-207, demonstrating active hygiene.

**Heuristic:** Infrastructure scripts registered in `.pre-commit-config.yaml` are production code — they guard correctness on every commit. The trap: classifying them as "tooling" exempts them from TDD. Cure: treat any script in `.pre-commit-config.yaml` as subject to Commandment 7.

**Seed:** Should the pre-commit hook refuse to register a new script in `.pre-commit-config.yaml` unless a corresponding `tests/unit/test_<script>.py` file exists with at least one `@pytest.mark.req` tag?
