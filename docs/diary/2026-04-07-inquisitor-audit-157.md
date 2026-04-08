## 2026-04-07: Inquisitor Audit — Mixed-commit drift in FR-215 branch

**Context:** Audited the 5 most recent commits (2987777..8fc47ae) spanning the FR-215 research-agent-demo feature branch and main. Checked Conventional Commits, changelog fragments, requirement traceability (ADR-001), diary entries, and noqa confessions.

**Findings:**

1. ✗ VIOLATION — **mixed_commits_erode_auditability**: Commit `2987777` (`fix(ci): exclude examples/demos/tests/ from demo-gate check`) bundles 25 files / 739 insertions including the entire research-agent demo (tests, FR updates, graph YAML, prompts, demo output) into a commit labeled as a CI fix. One concern per commit is violated — the CI fix, the demo itself, and the test suite are three distinct concerns. A revert of the "fix" would destroy the demo.

2. ⚠ DRIFT — **mixed_commits_erode_auditability**: Commit `34e0920` (`chore: image pipeline batch scripts`) bundles 17 files across diary entries, git reports, and batch scripts. Lower severity since all are chore-like, but git blame clarity suffers.

3. ✓ COMPLIANT — All 5 commits follow Conventional Commits format (`fix(ci):`, `docs(FR):`, `chore:`, `chore(release):`).

4. ✓ COMPLIANT — Changelog fragments exist for both the feat (`fr-215-research-agent-demo.md`) and fix (`fix-ci-demo-gate-tests-exclusion.md`) in `changelog/unreleased/`. REQ-YG-217 is registered in ARCHITECTURE.md and `capabilities/CAP-83-research-agent-demo.yaml`. All 19 test functions in `test_research_agent_demo.py` carry `@pytest.mark.req("REQ-YG-217")`.

5. ✓ COMPLIANT — Diary reflection exists (`2026-04-07-reflection-fr-215-research-agent-demo.md`) with cognitive trap identification (infrastructure_self_exempt), heuristic, and seed.

**Heuristic:** A commit message is a contract — when the diff exceeds the message's declared scope, the commit is a lie. The `fix(ci):` label promised a surgical change; 739 insertions delivered a feature. Squash-merge workflow on the branch will collapse this, but the branch history itself becomes untraceable. Separate RED/GREEN/REFACTOR commits even on feature branches.

**Seed:** Should pre-commit enforce a max-diff-size heuristic per commit type (e.g., `fix` commits exceeding N files trigger a warning), or would that be the infrastructure_self_exempt trap eating its own tail?
