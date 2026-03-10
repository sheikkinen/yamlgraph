## 2026-03-10: Inquisitor Audit — Persistent CHANGELOG and diary gaps in traceability series

**Context:** Audited the 5 most recent commits on HEAD (`b4ef9a9..f2bf5ca`). Window contains 2 `feat` (FR-178, FR-180), 2 `chore` (FR-177, capability markers), and 1 `docs` (diary batch). This is the third consecutive audit covering the FR-177/178/180 traceability series. Prior audits (88, 89) flagged identical violations; this audit checks for remediation.

**Findings:**

1. ✓ COMPLIANT — **noqa confessions are complete.** `noqa_coverage.py` reports 54/54 suppressions documented, including `migrate_capabilities.py:352` (E402) confessed since audit-88. Commandment 6 satisfied.

2. ✓ COMPLIANT — **FR-180 tests are thorough and tagged.** 21 test functions in `test_id_registry.py`, all carrying `@pytest.mark.req("REQ-YG-001")` or `REQ-YG-004`. ADR-001 and Commandment 7 satisfied for this commit.

3. ✗ VIOLATION — **FR-178 and FR-180 have no CHANGELOG entries.** Neither `feat` commit appears under `[Unreleased]`. FR-178 adds 754 lines of scripts (`migrate_capabilities.py`, `validate_capabilities.py`); FR-180 adds `id_registry.py` (243 lines) and 21 tests. Commandment 10: "let the CHANGELOG bear witness." Third audit citing this — now matches the Knowledge Graph trap `audit_as_ritual`.

4. ✗ VIOLATION — **FR-178 ships ~750 lines of script code with zero tests.** `migrate_capabilities.py` (511 lines) and `validate_capabilities.py` (243 lines) have no corresponding test files. Commandment 7: "No new production branch shall be merged without a witness test." Second consecutive audit citing this.

5. ✗ VIOLATION — **No diary reflection for FR-178 or FR-180.** The Sermon requires a metacognitive entry after completing a task list. The `diary-gate` CI job exists to enforce this, but these commits bypassed the PR workflow (direct pushes). Knowledge Graph trap: `audit_as_ritual` — "3+ audits without fix → ritual, not process."

**Heuristic:** Three audits have now cited the same three violations (CHANGELOG, tests, diary) for the same commits. This is the `audit_as_ritual` trap incarnate. The audit itself has become the remediation theatre — each entry documents the gap, but nothing blocks the next commit from repeating it. The cure is not another audit; it is a blocking gate. Either enforce the PR workflow (which already has `diary-gate`, `test`, and `commitlint` checks) or add a local pre-commit hook that refuses `feat` commits without a CHANGELOG diff.

**Seed:** Should the `.pre-commit-config.yaml` include a hook that verifies `CHANGELOG.md` is modified whenever a `feat` or `fix` commit is staged — mirroring what `diary-gate` does for diary entries?
