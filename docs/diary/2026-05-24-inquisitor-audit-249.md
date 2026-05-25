## 2026-05-24: Inquisitor Audit — Diary Gate Bypass and Type Evasion

**Context:** Audited the 5 most recent commits on `main` (86008283..17951323). Two are on `origin/main` (FR-450 feat, FR-451 fix), three are local-only (FR-452/FR-453 docs). Focused on gate compliance, commit type accuracy, and diary coverage.

**Findings:**

1. ✗ VIOLATION — **FR-450 and FR-451 merged without diary reflections.** Commits `0b98ae97` (`feat(demos): FR-450`) and `86008283` (`fix(agent): FR-451`) are on `origin/main` but neither includes a diary entry in its diff. The `diary-gate` requires feat/fix PRs with `FR-XXX` to include a reflection file. Either the gate failed to catch these or an undocumented admin bypass occurred. A subsequent `docs:` commit (`baad9244`) added audit/report diary files but no FR-450 or FR-451 reflection. Commandment 10 (Distill) and the Sermon's Distill step are unmet.

2. ⚠ DRIFT — **Commit c84f9cd4 typed as `docs:` but makes functional changes.** Adds `test_no_hardcoded_model` to `test_fr447_judge_demo.py` and modifies `examples/demos/judge/graph.yaml` (removing hardcoded model). These are behavioral changes — a new test enforces a structural constraint, and the graph config changed accordingly. Typing this as `docs:` sidesteps `changelog-gate` and `diary-gate`, which only trigger on `feat`/`fix`. Trap: commit type as escape hatch from enforcement gates.

3. ✓ COMPLIANT — **Requirement traceability and noqa confessions.** `req_coverage.py` reports full coverage. `noqa_coverage.py` confirms 95/95 suppressions documented with CONF-XXX entries. All new tests in `test_agent_llm_config.py` (8 functions) and `test_fr447_judge_demo.py` (13+ functions) carry `@pytest.mark.req` tags.

4. ✓ COMPLIANT — **FR-450 and FR-451 changelog fragments are well-formed.** Both exist in `changelog/unreleased/` with correct `req:` front-matter (`REQ-YG-018` for FR-451). Conventional Commits format correct on both.

5. ✓ COMPLIANT — **Lifecycle verb drift diary (FR-453) is genuine reflection.** `diary-2026-05-24-lifecycle-verb-drift.md` identifies `continuation_bias` + `intent_drift` traps, provides a verb→artifact mapping table, and plants a seed about automated lifecycle verb parsing. Meets Distill standard.

**Heuristic:** When a `docs:` commit adds test functions or modifies runtime configs, the commit type is doing double duty as a gate bypass. The `changelog-gate` and `diary-gate` are scoped to `feat`/`fix` types, creating a perverse incentive to miscategorize. A complementary check — flagging `docs:` or `chore:` commits that touch `tests/` or modify `.yaml` files under `yamlgraph/` or node configs — would close this loophole. The diary-gate bypass on FR-450/FR-451 needs root-cause investigation: was it a CI gap, an admin override, or a timing issue with gate deployment?

**Seed:** Should the diary-gate expand its scope beyond commit type — inspecting the *diff content* for test additions and config changes regardless of prefix — to prevent type-based gate evasion?
