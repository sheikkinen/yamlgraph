## 2026-03-10: Inquisitor Audit — FR-178 Capability Registry & Recent Commits

**Context:** Audited the 5 most recent commits on `feat/fr-178-capability-registry` branch against the Scripture. Scope: Conventional Commits, CHANGELOG presence, ADR-001 traceability, noqa confessions, diary reflections.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow the `type(scope): description` format (`docs(diary):`, `chore:`, `chore(traceability):`). No `feat` commits without FR reference.

2. ✓ COMPLIANT — **CHANGELOG updated**: FR-178 has a detailed entry under `[Unreleased] → Added` documenting the append-only capability registry with REQ-YG-161 cross-reference.

3. ✓ COMPLIANT — **ADR-001 Requirement Traceability**: New tests in `test_capability_registry.py` carry `@pytest.mark.req("REQ-YG-161")` tags (4 decorated test classes/functions covering 19 tests). `req_coverage.py` confirms CAP-65 fully covered.

4. ✓ COMPLIANT — **noqa Confessions**: `noqa_coverage.py --strict` reports 0 undocumented suppressions. CONF-207 was added in commit `0882893` for the new `id_registry` whitelist entry.

5. ✓ COMPLIANT — **Diary Reflection**: `2026-03-10-reflection-fr-178-capability-registry.md` captures the ID collision trap (parallel enforcement assigning duplicate CAP/REQ IDs), the cure (FR-180 plan-phase reservation), and a forward-looking Seed about merging ID and capability registries.

**Heuristic:** When audit finds full compliance on a feature branch, verify it wasn't achieved by discarding a colliding FR (FR-182 was removed to resolve the ID conflict). Compliance-by-deletion is valid but should be witnessed — the diary entry does this well.

**Seed:** Should the Inquisitor audit _discarded_ FRs separately? A killed FR might carry lessons that the surviving FR's diary doesn't capture. Is the reflection on FR-182's removal sufficient, or does the discarded work deserve its own post-mortem?
