## 2026-03-15: Inquisitor Audit — FR-202 Image Generation Pipeline

**Context:** Audited the 5 most recent commits on `feat/fr-202-image-generation-pipeline` branch: `cbce001`, `9b9064c`, `f6464d6`, `74c078c`, and `06b93c4` (FR-109 on main). Assessed compliance against Conventional Commits, ADR-001 requirement traceability, TDD discipline, changelog fragments, and diary reflections.

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits.** All 5 commits follow `type(scope): description` format. `feat` commits reference FR numbers. RED/GREEN are separated (`test(image-pipeline): FR-202 RED`, `feat(examples): FR-202 GREEN`). Co-authored-by trailers present on all 5.

2. ✓ **COMPLIANT — Changelog & ARCHITECTURE.** `changelog/unreleased/FR-202-image-generation-pipeline.md` exists with correct YAML front matter. REQ-YG-198 added to ARCHITECTURE.md (line 1083) and CAP-77 registered in `capabilities/`.

3. ✗ **VIOLATION — ADR-001 req tag coverage.** `tests/unit/test_image_pipeline.py` has 34 test functions but only 6 carry `@pytest.mark.req("REQ-YG-198")`. The remaining 28 test functions (82%) lack the required tag. ADR-001 states: "Every test function must have `@pytest.mark.req`." This is a `partial_remediation` trap — the class-level markers were applied to only some test classes, leaving the majority untagged.

4. ✓ **COMPLIANT — TDD discipline.** RED commit (`f6464d6`) adds 403 lines of tests. GREEN commit (`9b9064c`) adds implementation. Separate commits with clear labels — Commandment 7 honored.

5. ✓ **COMPLIANT — Diary reflection.** `docs/diary/2026-03-15-reflection-fr-202.md` exists with Context, Trap Avoided, Insight, Heuristic, and Seed sections. Quality entry naming the `intent_drift` trap and the coupled-registries heuristic.

**Heuristic:** Class-level `@pytest.mark.req` decorators only propagate if placed on the class itself, not individual methods. When a test file mixes standalone functions and classes, or has multiple classes, audit each `def test_*` individually — the `partial_remediation` trap is that applying the tag to one class creates the illusion of full coverage.

**Seed:** Should `scripts/req_coverage.py --strict` be extended to report the exact test functions missing `@pytest.mark.req`, so violations surface in CI output rather than requiring manual grep?
