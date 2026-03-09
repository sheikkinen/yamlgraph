## 2026-03-09: Inquisitor Audit — Recent Commits (3b1294c..2fd081e)

**Context:** Routine audit of the 5 most recent commits on `main`, checking adherence to the Scripture (Conventional Commits, CHANGELOG, ADR-001 traceability, diary entries, noqa confessions).

**Commits audited:**
- `3b1294c` docs(FR): add FR-169-enforce-reflexion-loop
- `ecd2e96` docs(FR): add FR-176-audit-parallelism-theatre
- `e9af9f7` chore: add inquisitor audit diary entries
- `8856a67` feat(chaplain): FR-175 sequential enforcement mode (#44)
- `2fd081e` docs(FR): add FR-175-sequential-enforcement-mode

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits use correct `type(scope):` format. The feat commit references FR-175 and includes Co-authored-by trailer.

2. ✓ COMPLIANT — **CHANGELOG**: FR-175 has a thorough entry under `[Unreleased] → Added` with REQ-YG-158 citation. Docs/chore commits correctly omit CHANGELOG entries.

3. ⚠ DRIFT — **ADR-001 req tags on new tests**: FR-175 introduced ~14 new test functions in `test_watch_sequential_enforcement.py`. Only 3 carry `@pytest.mark.req("REQ-YG-158")`. The remaining 11 (`test_enforce_not_nohup`, `test_bugfix_not_nohup`, `test_enforce_not_backgrounded`, `test_bugfix_not_backgrounded`, `test_exit_code_captured_for_enforce`, `test_exit_code_printed_after_enforce`, `test_no_pid_echo`, `test_nonzero_exit_logs_failure_message`, etc.) lack req markers. Systemically, 549 of 2369 test functions (~23%) are untagged.

4. ✓ COMPLIANT — **Diary entry**: FR-175 has a dedicated reflection (`2026-03-09-reflection-fr-175-sequential-enforcement.md`) with a named trap ("Parallelism Theatre"), heuristic, and seed.

5. ✓ COMPLIANT — **noqa Confessions**: Both active suppressions in `yamlgraph/` (CONF-003 for `executor_async.py:310`, CONF-002 for `token_tracker.py:51`) are documented with sin and penance.

**Heuristic:** When a feature adds a test file with a class-level `@pytest.mark.req` decorator, individual methods inherit it — but methods in *separate* test files or classes don't. The req-tagging discipline must be enforced per-function, not per-file. A pre-commit hook or `req_coverage.py --strict` gate could catch this at commit time.

**Seed:** Could `req_coverage.py` be promoted from advisory script to a required CI status check, blocking merges when new test functions lack `@pytest.mark.req` tags — similar to how `diary-gate` blocks merges without diary entries?
