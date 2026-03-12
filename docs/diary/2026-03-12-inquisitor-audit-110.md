## 2026-03-12: Inquisitor Audit — REQ Traceability Mismatch in FR-187

**Context:** Audited the 5 most recent commits on `main` (7c5f590..bd5434e) against the Scripture's Commandments, ADR-001 traceability, and Sermon obligations. Commits span release v0.4.63, a philosopher bugfix, FR-187 CI security scan, and FR-185 copilot node migration.

**Findings:**

1. **✗ VIOLATION — REQ-YG traceability mismatch in FR-187 (ADR-001).** ARCHITECTURE.md capability table row for CAP-68 (CI Dependency Security Scan) references `REQ-YG-185` — which is the philosopher copilot nodes requirement. The correct ID is `REQ-YG-186`. The changelog fragment `FR-187-ci-dependency-security-scan.md` repeats the same wrong ID (`req: REQ-YG-185`). Meanwhile, the capability YAML file `CAP-68-ci-dependency-security-scan.yaml` and the test file `test_ci_security_scan.py` correctly use `REQ-YG-186`. Root cause: likely a copy-paste error from the FR-185 work that immediately preceded FR-187.

2. **⚠ DRIFT — Two direct-to-main commits without PR numbers.** Commits `09c8077` (fix) and `7fc04c0` (docs) lack the `(#XX)` PR suffix. Branch protection mandates PRs for all pushes to `main`. Likely admin override. Both commits are otherwise well-formed: conventional format, changelog fragment present for the fix, diary written, tests updated with `@pytest.mark.req` tags.

3. **✓ COMPLIANT — FR-185 exemplary TDD trail.** Squash commit preserves RED/GREEN separation. 26 new tests with `@pytest.mark.req('REQ-YG-185')`, 19 existing with `REQ-YG-184`. Diary entry names cognitive trap (`plausible_wrong_answer`). Capability, requirement, and changelog all present.

4. **✓ COMPLIANT — Conventional Commits and noqa confessions.** All 5 commits follow `type(scope):` format. Both `# noqa` suppressions in `yamlgraph/` are documented in `docs/confessions.md`.

5. **✓ COMPLIANT — Philosopher fix follows Rite of Correction.** Commit `09c8077` fixes at the callsite (not the utility), includes a changelog fragment, and the diary entry `2026-03-12-philosopher-fix.md` correctly names the "Phantom State Key" trap from prior doctrine.

**Heuristic:** When two feature branches are implemented in rapid succession, copy-paste of requirement IDs is the most common traceability error. The capability YAML and tests may be correct while the prose artifacts (ARCHITECTURE.md table, changelog) carry the stale ID. Cross-check the *number*, not just the presence.

**Seed:** Could `scripts/req_coverage.py` be extended to parse capability YAML files and verify that the REQ-YG-XXX in ARCHITECTURE.md's capability table matches the `requirements[].id` in the corresponding `capabilities/CAP-*.yaml` file?
