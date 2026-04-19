## 2026-04-19: Inquisitor Audit — FR-250 A2A gaps, FR-247 REQ gate, FR-249 guardrails, FR-252 draft

**Context:** Audited the 5 most recent commits on `main` against the Scripture. Commits span FR-252 (feature request draft), FR-250 (A2A server protocol gaps), FR-247 (changelog REQ cross-validation gate), FR-249 (guardrails pattern documentation), and FR-250's FR draft.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits (Commandment 10)**: All 5 commits follow `type(scope): description`. Both `feat` commits reference `FR-XXX`. The `docs` commits correctly omit FR references where they're only drafts.

2. ✓ COMPLIANT — **Requirement traceability (ADR-001)**: FR-250 tests carry `@pytest.mark.req` for REQ-YG-210 (3 tests), REQ-YG-211 (10 tests), REQ-YG-213 (3 tests). FR-249 tests carry REQ-YG-254 (5 tests). FR-247 tests carry REQ-YG-255 (verified in prior audit-208). All noqa suppressions documented — CONF-004 confirmed in `docs/confessions.md`.

3. ✓ COMPLIANT — **Diary reflections (Sermon: Distill)**: FR-250 has `2026-04-20-reflection-fr-250-a2a-server-complete-gaps.md` (trap: partial implementation as shipped feature). FR-247 has `2026-04-20-reflection-fr-247-changelog-req-cross-validation-gate.md` (trap: detection without enforcement). FR-249 has `2026-04-19-reflection-fr-249.md`.

4. ⚠ DRIFT — **Changelog fragment missing `req:` front-matter (FR-250)**: The fragment `changelog/unreleased/FR-250-a2a-server-complete-gaps.md` references REQ-YG-210, REQ-YG-211, REQ-YG-213 in its prose but declares no `req:` in the YAML front-matter. Per FR-247's design, fragments without `req:` are silently skipped by `changelog-req-gate`. This is defensible for multi-REQ fragments (deferred scope per FR-247 diary), but creates a gap: the REQ traceability chain from test → changelog → capability is broken for these three requirements at the changelog layer.

5. ✓ COMPLIANT — **TDD discipline (Commandment 7)**: FR-249 shows explicit RED/GREEN separation in squash commit messages (`SKIP=pytest` on RED, "All 14 tests pass" on GREEN). FR-250 added 17 new tests before shipping protocol changes. FR-247 added 11 tests for the validation script.

**Heuristic:** Multi-REQ changelog fragments expose a traceability gap: the `changelog-req-gate` skips them silently, meaning the test→changelog→capability chain is broken at precisely the fragments with the richest requirement surface. The workaround (defer to LLM graph) exists but is not wired as a blocking gate. Either pick a primary REQ for the `req:` field, or extend the gate to require `req:` on all `feat` fragments.

**Seed:** Could the `changelog-req-gate` enforce that every `feat`-type fragment must have at least one `req:` in its front-matter — even for multi-REQ changes — using the first/primary REQ? The semantic validation of additional REQs could remain deferred, but the mechanical minimum of "feat implies req" would close the silent-skip gap.
