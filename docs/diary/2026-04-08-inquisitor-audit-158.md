## 2026-04-08: Inquisitor Audit — Mixed Commit & Doctrine Hygiene

**Context:** Audited the 5 most recent commits on `main` (f08d4ef → 34e0920) against the Scripture's Commandments, ADR-001, noqa Confessions, and the Sermon of the Chaplain.

**Findings:**

1. **✗ VIOLATION — Mixed commit erodes auditability (9718e27).** PR #81 titled `fix(ci): exclude examples/demos/tests/ from demo-gate check` contains 25 changed files: the CI fix *and* the entire FR-215 research agent demo (graph, prompts, tests, capability, changelog fragment, FR update, diary). The Knowledge Graph names this trap: `mixed_commits_erode_auditability — One concern per commit → clear blame, clear revert`. Because squash merge is mandatory, the FR-215 feature and the CI fix are permanently fused. Reverting the CI fix reverts the demo; reverting the demo reverts the fix.

2. **✓ COMPLIANT — Conventional Commits format.** All 5 commits use valid types: `chore:`, `fix(ci):`, `docs(FR):`. The `fix` commit includes scope and PR reference.

3. **✓ COMPLIANT — Changelog fragment for fix (9718e27).** `changelog/unreleased/fix-ci-demo-gate-tests-exclusion.md` exists with correct YAML front matter (`type: fix`, `scope: ci`). FR-215 also has its own fragment.

4. **✓ COMPLIANT — ADR-001 traceability (9718e27).** REQ-YG-217 exists in ARCHITECTURE.md. All 19 tests in `test_research_agent_demo.py` carry `@pytest.mark.req("REQ-YG-217")`. Capability file `CAP-83-research-agent-demo.yaml` registered.

5. **⚠ DRIFT — Diary saturation.** 154 inquisitor audit entries exist. The volume itself risks `audit_as_ritual` — audits without action become ceremony. The previous audit (157) was recorded just hours ago. Frequency without findings dilutes signal.

**Heuristic:**

> Squash merge amplifies mixed-commit damage: what enters the PR as separate logical units exits as one irreversible atom. The PR is the commit boundary — scope the PR as you would scope the commit.

**Seed:**

Could a CI gate detect mixed concerns in a PR — e.g., flagging when both `fix` changelog fragments and `feat` changelog fragments coexist in the same diff — and require explicit justification before merge?
