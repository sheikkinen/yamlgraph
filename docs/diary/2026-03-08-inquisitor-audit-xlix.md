## 2026-03-08: Inquisitor Audit — CHANGELOG Requirement Traceability Mismatch

**Context:** Audited the latest 5 commits (4fa18d6…d40a331) covering FR-162, FR-164, FR-165, and two `docs(FR)` planning commits. Checked Conventional Commits format, CHANGELOG entries, ARCHITECTURE.md requirements, `@pytest.mark.req` tags, diary reflections, and noqa confessions.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits (`feat(scope): FR-XXX ...`, `docs(FR): ...`). Commandment 10 satisfied.
- ✓ COMPLIANT — All `feat` commits (FR-162, FR-164, FR-165) have CHANGELOG entries under `[Unreleased]`. Requirements added to ARCHITECTURE.md (REQ-YG-046, REQ-YG-154, REQ-YG-114). Diary reflections exist for all four FRs.
- ✓ COMPLIANT — All test files carry `@pytest.mark.req` tags: `test_verification.py` → REQ-YG-154, `test_linter_contracts.py` → REQ-YG-114/REQ-YG-061/REQ-YG-003, `test_dead_code_guard.py` → REQ-YG-046. ADR-001 satisfied.
- ✓ COMPLIANT — Both `yamlgraph/` noqa suppressions (ANN001 in `executor_async.py`, ARG002 in `token_tracker.py`) are documented in `docs/confessions.md`. No unconfessed suppressions.
- ✗ VIOLATION — FR-164 CHANGELOG entry cites `(REQ-YG-064, REQ-YG-065)` but the actual requirement is `REQ-YG-154`. REQ-YG-064 is token usage tracking and REQ-YG-065 is native streaming — neither relates to verification gates. The tests correctly use `REQ-YG-154` and ARCHITECTURE.md correctly defines it. Only the CHANGELOG has stale/wrong REQ IDs. This breaks requirement traceability (ADR-001) at the documentation layer.

**Heuristic:** CHANGELOG REQ citations are copy-paste hazards. When a feature request creates a *new* requirement ID (REQ-YG-154), the CHANGELOG entry may still carry the REQ IDs from the template or a previous draft. The fix: `req_coverage.py` currently validates test→ARCHITECTURE linkage but does not cross-check CHANGELOG citations. A CHANGELOG→ARCHITECTURE consistency check would catch this class of ghost reference.

**Seed:** Should `req_coverage.py --strict` be extended to parse CHANGELOG.md requirement citations and verify they exist in ARCHITECTURE.md, closing the traceability loop from documentation back to spec?
