## 2026-05-25: Inquisitor Audit — Eval-Driven Bugfix Batch (FR-455/456/458/459)

**Context:** Audited the 5 most recent commits on `main` (41bbfb76..4186ec3f), covering four bugfix FRs discovered through multi-model eval and one docs commit. All work occurred in a single session.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow the format. Scopes are accurate (`agent`, `llm,agent`, `judge`). FR references present on all fix commits.

2. ✓ COMPLIANT — **Changelog & REQ tags**: Four changelog fragments exist in `changelog/unreleased/`. All 13 new tests carry `@pytest.mark.req("REQ-YG-010")`. The `noqa: C901` on `create_agent_node` (agent.py:188) is documented as CONF-007.

3. ⚠ DRIFT — **Mixed commit (FR-455 + FR-456)**: Commit `e66ab039` bundles two independent fixes. The knowledge graph warns: `mixed_commits_erode_auditability: One concern per commit → clear blame, clear revert.` Both fixes touch different files (`llm_factory.py` vs `agent.py`) and could have been separate commits. Impact is low — both are small, well-tested fixes — but the pattern weakens revert granularity.

4. ⚠ DRIFT — **FR-459 lacks condemning test**: Scripture #7 says "No bug shall be fixed unless first condemned by a failing test." FR-459 changed a YAML prompt in a demo (`examples/demos/judge/prompts/judge.yaml`) and was verified only via the eval harness. The diary honestly notes "Eval-verified" rather than "unit-tested." The fix is a prompt wording change with no Python code path to unit-test, so the traditional RED-GREEN flow doesn't apply cleanly — but the Scripture makes no exception for prompt-only fixes. A future eval-as-CI gate (seeded in the diary) would close this gap.

5. ✓ COMPLIANT — **Diary & reflection**: `diary-2026-05-25-eval-as-bug-finder.md` covers all four FRs with traps (brace collision, model calibration, timeout false negatives), a heuristic (eval-as-fuzzer), and a forward seed (eval-as-CI-gate). Quality is high — it documents cognitive traps, not just outcomes.

**Heuristic:** When a fix targets a declarative artifact (YAML prompt, config) rather than executable code, the TDD commandment needs a declarative equivalent. The eval harness *is* the test for prompts — but it's not integrated into the automated gate. Until it is, prompt-only fixes occupy a doctrinal gray zone.

**Seed:** Should the Scripture codify a distinction between *executable fixes* (must have RED test) and *declarative fixes* (must have eval or integration verification)? Or does that distinction create a loophole that erodes the testing culture?
