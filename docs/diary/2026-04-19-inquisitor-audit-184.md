## 2026-04-19: Inquisitor Audit — FR-240 branch & recent main merges

**Context:** Audited the latest 5 commits spanning FR-240 (a2a_call node type, in-progress branch), FR-238 (user-configurable reducers), FR-237 (race/pipeline docs), and FR-069 (map timeout). Checked Conventional Commits, changelog fragments, requirement traceability, test tagging, diary entries, and noqa confessions.

**Findings:**

1. **⚠ DRIFT — FR-240 missing diary reflection.** `feat(graph): FR-240` introduces a new node type (535-line test file, node factory, linter patterns, demo) but no diary entry exists. The `diary-gate` CI check will block the PR at merge. Must be written before PR.

2. **⚠ DRIFT — Triple confession for `check_state_declarations` C901.** CONF-001, CONF-008, and CONF-044 all document the same C901 suppression on `check_state_declarations` in `checks.py`. FR-240 added CONF-001 without recognizing the two pre-existing confessions. Three confessions for one sin is entropy, not thoroughness — consolidate to one.

3. **✓ COMPLIANT — Conventional Commits.** All 5 commits follow format: `feat(graph)`, `feat(state-builder)`, `docs(reference)`, `feat(map)`, `chore`. FR references present on all feat commits.

4. **✓ COMPLIANT — Requirement traceability.** REQ-YG-243 added to ARCHITECTURE.md for FR-240. All 25 test functions in `test_a2a_call_node.py` carry `@pytest.mark.req("REQ-YG-243")`. CAP-101 capability file registered.

5. **✓ COMPLIANT — Changelog and diary for merged work.** FR-238 and FR-069 each have changelog fragments and diary reflections. FR-237 is `docs` type (diary-gate exempt). All changelog fragments present in `changelog/unreleased/`.

**Heuristic:** Before adding a new CONF-XXX entry, grep `docs/confessions.md` for the file path and error code — the suppression may already be documented under a different ID.

**Seed:** Should the confessions pre-commit hook enforce uniqueness — one CONF per (file, line, code) tuple — to prevent confession duplication from accreting silently?
