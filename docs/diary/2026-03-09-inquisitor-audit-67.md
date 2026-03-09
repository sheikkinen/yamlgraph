## 2026-03-09: Inquisitor Audit — FR-167 through FR-170, persistent violations

**Context:** Audited the 5 most recent commits on `main` (e92cf88..5bfb672): one `feat(ci): FR-167` removing the Copilot trailer, three `docs` commits adding FR-168/169/170 planning and reference material, and one `chore` batching prior audit diary entries. This is the first audit since audit-66 flagged a `@pytest.mark.req` gap on the FR-167 replacement test.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits & CHANGELOG**: All 5 commits follow `type(scope): description`. The `feat` commit references FR-167 and has a CHANGELOG entry under `### Removed` citing REQ-YG-125. The `docs` and `chore` commits correctly omit CHANGELOG entries.

2. ✗ VIOLATION — **Persistent @pytest.mark.req gap (ADR-001)**: `test_commit_excludes_co_author_trailer` in `tests/unit/test_finalize_merge.py` still lacks `@pytest.mark.req("REQ-YG-125")`. First flagged in audit-66, unfixed across 5 subsequent commits. This is now the second consecutive audit citing the same defect — triggering the `audit_as_ritual` trap.

3. ⚠ DRIFT — **Diary file in legacy location**: `docs/diary-2026-03-05.md` was added in the recent batch at the old root-level `docs/diary-*.md` path instead of inside `docs/diary/`. Fifteen legacy files remain at `docs/` root. New entries should use `docs/diary/` exclusively; the old location creates discoverability ambiguity.

4. ✓ COMPLIANT — **noqa confessions**: Both production `# noqa` suppressions (`executor_async.py` ANN001, `token_tracker.py` ARG002) remain documented in `docs/confessions.md` with CONF-XXX IDs. No new undocumented suppressions.

5. ✓ COMPLIANT — **Diary reflection for FR-167**: `docs/diary/2026-03-09-reflection-fr-167.md` exists with a well-formed metacognitive entry identifying `audit_as_ritual` as the cognitive trap and questioning inherited tool conventions.

**Heuristic:** A violation appearing in consecutive audits without a fix commit between them is the `audit_as_ritual` trap manifesting. The remedy: the commit immediately following an audit that flags a code-level violation should be the fix, not more documentation. Audit → Fix → Next audit confirms. Break the loop.

**Seed:** Should unresolved audit violations be tracked in a machine-readable backlog (e.g., `scripts/audit_backlog.json`) so that `req_coverage.py --strict` or a dedicated CI gate can fail when a flagged defect persists beyond one release cycle?
