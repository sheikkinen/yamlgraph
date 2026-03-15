## 2026-03-14: Inquisitor Audit — FR-109/FR-201 Requirement Traceability

**Context:** Routine audit of the latest 5 commits on `feat/109-batch-image-prompt-generation` and `main`. Commits span FR-109 (batch image prompts — RED phase) and FR-201 (horoscope demo — complete).

**Findings:**

1. **✗ VIOLATION (ADR-001):** `test_batch_image_prompts.py` has 21 test functions but only 4 carry `@pytest.mark.req` tags. 17 tests lack requirement traceability. The Scripture is explicit: "Every test function must have `@pytest.mark.req`."

2. **⚠ DRIFT (ADR-001):** The 4 tagged tests all reference `REQ-YG-003` ("Perform linting and pattern validation"). FR-109 is an example graph — most of its tests validate graph structure, prompt schemas, and map-node configuration, not linting. A more specific requirement (or a new one for example graphs) would improve traceability signal.

3. **✓ COMPLIANT (Commandment 10):** All 5 commits follow Conventional Commits format. `feat` commits include `FR-XXX` references. RED test commit is separate from production code (Commandment 7 honored).

4. **✓ COMPLIANT (Commandment 10 / FR-179):** Changelog fragments exist for both FR-109 (`fr-109-batch-image-prompts.md`) and FR-201 (`fr-201-horoscope-demo.md`, `fr-201-horoscope-dated-output.md`).

5. **✓ COMPLIANT (Sermon: Distill):** Diary entries written for both FR-109 and FR-201. FR-109 diary correctly identifies the `plausible_wrong_answer` trap (FR spec had wrong `prompts_dir` path). FR-201 diary graduates the "run full test suite" heuristic.

**Heuristic:** When a RED commit introduces N test functions, verify N `@pytest.mark.req` tags before committing — the pre-commit hooks check for *presence* of the marker on changed files but not *completeness* across all functions.

**Seed:** Should `req_coverage.py` gain a `--strict-per-function` mode that fails when any `def test_*` function in a changed file lacks a `@pytest.mark.req` decorator? This would catch the 17/21 gap at commit time rather than audit time.
