## 2026-03-09: Inquisitor Audit — FR-167 through FR-169, diary batch

**Context:** Audited the 5 most recent commits on `main` (6efebb2..0c58a96): three `docs(FR):` planning commits from the Chaplain pipeline, one `feat(ci): FR-167` removing the Copilot trailer requirement, and one `chore: diary updates` batching prior audit entries.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow the `type(scope): description` format correctly. The feat commit includes `FR-167` reference as required.

2. ✓ COMPLIANT — **CHANGELOG + Diary for FR-167**: The feat commit adds a `### Removed` entry in CHANGELOG.md citing REQ-YG-125, and includes `docs/diary/2026-03-09-reflection-fr-167.md` with a well-structured metacognitive reflection identifying `audit_as_ritual` as the cognitive trap.

3. ✗ VIOLATION — **Missing `@pytest.mark.req` on new test (ADR-001)**: `test_commit_excludes_co_author_trailer` in `tests/unit/test_finalize_merge.py` was introduced by FR-167 but lacks `@pytest.mark.req("REQ-YG-125")`. Six of the 12 tests in the same file have the marker; this new test does not.

4. ⚠ DRIFT — **Diary audit numbering inconsistency**: The `chore: diary updates` commit (0c58a96) batched entries using both Roman numerals (l, li, ..., lviii) and Arabic numerals (54, 57, ..., 62). Mixed schemes break lexicographic sort and make "next number" discovery unreliable. The 2026-03-09 entries have stabilized on Arabic numerals (64, 65, 66).

5. ✓ COMPLIANT — **noqa confessions**: Both production `# noqa` suppressions (`executor_async.py:310` ANN001, `token_tracker.py:51` ARG002) are documented in `docs/confessions.md` with CONF-XXX IDs.

**Heuristic:** When a commit adds or replaces a test, the `@pytest.mark.req` tag must transfer to the replacement. Deletion of a tagged test without tagging its successor is a traceability leak — the requirement appears covered by the old test in git history but is actually uncovered on HEAD.

**Seed:** Could `req_coverage.py --strict` be extended to detect *removed* req-tagged tests whose requirement still exists but now has fewer covering tests than before?
