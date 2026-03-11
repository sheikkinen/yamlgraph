## 2026-03-10: Inquisitor Audit — FR-178 remediated, FR-180 invisible

**Context:** Audited the 5 most recent commits on `feat/fr-178-capability-registry` (`f046f48..b18547a`). Window: 1 `feat` (FR-180), 1 `docs` (diary batch), 3 `chore` (FR-178 finalization, traceability markers, remediation). This follows audit 96 which flagged phantom test reference, missing CHANGELOG, and missing diary reflections.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits format on all 5 commits.** The `feat` commit includes FR-180 reference; `chore` and `docs` commits use correct type/scope. Commandment 10 format satisfied.

2. ✓ COMPLIANT — **Audit-96 phantom test remediated.** `test_capability_registry.py` (270 lines, 4 `@pytest.mark.req("REQ-YG-161")` tags) was added in `b18547a`. FR-178 CHANGELOG entry now exists under `[Unreleased]`. Previous violations corrected.

3. ✗ VIOLATION — **FR-180 is invisible to traceability.** `feat(traceability): FR-180 plan-phase ID reservation` introduced 628 lines across 5 files (`id_registry.py`, `validate_id_registry.py`, `test_id_registry.py`, pre-commit hook, registry YAML). Zero CHANGELOG entry. Zero ARCHITECTURE.md capability row or requirement ID. Tests are tagged `REQ-YG-001` (generic config loading) instead of an FR-180-specific requirement. The irony: a feature for *traceability ID reservation* has no traceable ID of its own. Commandments 7 and 10; ADR-001.

4. ✗ VIOLATION — **No diary reflection for FR-178 or FR-180.** 12 inquisitor audit entries (85–96) document the absence but are not metacognitive reflections on the work itself. The Sermon requires: trap encountered, heuristic extracted, seed planted. Auditing the absence of a diary is not writing the diary. `audit_as_ritual` trap confirmed for the 4th consecutive audit.

5. ⚠ DRIFT — **Duplicate FR-175 CHANGELOG entry.** Lines 12–13 of CHANGELOG.md both describe "FR-175 Sequential Enforcement Mode" with slightly different wording. Likely a merge conflict artifact that was resolved by keeping both sides.

**Heuristic:** A traceability feature that isn't itself traceable is the `framework_costume` trap inverted — it's not the wrong tool wearing the right name, it's the right tool wearing no name at all. The `audit_as_ritual` pattern has now appeared in 4 consecutive audits for the same missing diary entries. Per the Knowledge Graph: "3+ audits without fix → ritual, not process." The cure is not another audit; it's a blocking gate. The `diary-gate` CI job already exists for PRs — but these commits haven't reached a PR yet, so the gate hasn't fired. The gap is pre-PR enforcement.

**Seed:** Should the pre-commit hook that validates diary entries check not just `feat`/`fix` commits but also verify that any `FR-XXX` referenced in the commit message has a corresponding diary reflection file on disk — catching the gap *before* the PR is opened rather than at merge time?
