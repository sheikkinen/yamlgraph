## 2026-04-19: Inquisitor Audit — FR-247 changelog-req gate & FR-249 guardrails docs

**Context:** Audited the 5 most recent commits on `feat/fr-247-changelog-req-cross-validation-gate` against the Scripture. Commits span FR-247 (changelog REQ cross-validation gate), FR-249 (guardrails pattern docs squash-merged to main), and FR-251 (feature request draft).

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow format. `feat(changelog): FR-247`, `docs(patterns): FR-249`, `chore(changelog):`, `docs(diary):`, `docs(FR):`. FR reference present on the feat commit.

2. ✓ COMPLIANT — **Changelog & Requirements (Commandment 10, ADR-001)**: FR-247 has a changelog fragment (`changelog/unreleased/fr-247-changelog-req-cross-validation-gate.md`) with correct `req: REQ-YG-255` front-matter. CAP-108 registered in `capabilities/`. REQ-YG-255 defined in `ARCHITECTURE.md`. All 17 tests in `test_check_changelog_req.py` carry `@pytest.mark.req("REQ-YG-255")`. FR-249 tests carry `@pytest.mark.req("REQ-YG-254")`.

3. ✓ COMPLIANT — **Diary reflections (Sermon: Distill)**: FR-247 has `2026-04-20-reflection-fr-247-changelog-req-cross-validation-gate.md` with trap identification (detection-without-enforcement), heuristic, and seed. FR-249 had its diary entry in the squash-merged commit.

4. ⚠ DRIFT — **Module size (Commandment 8)**: `scripts/check_changelog_req.py` is 418 lines — above the 400-line target, within the 450-line max. The script handles mechanical validation, LLM graph invocation, CLI argument parsing, and YAML front-matter parsing. A split into `check_changelog_req.py` (CLI + orchestration) and a helper module for the mechanical parsing logic would bring both under 400.

5. ✓ COMPLIANT — **No unconfessed noqa**: No `# noqa` suppressions found in any new files.

**Heuristic:** Enforcement scripts that combine CLI, parsing, and external-system integration (LLM graph) tend to grow past the module-size target. Apply the same three-layer split to enforcement tooling: CLI entry point → validation logic → external calls.

**Seed:** Could `scripts/check_changelog_req.py` be restructured as a YAML graph itself — eating its own dog food? The mechanical phase is pure validation (no LLM), but the multi-REQ phase already delegates to a graph. If the orchestration layer were also graph-defined, the script would shrink to a thin CLI wrapper, and the enforcement pipeline would demonstrate the framework it guards.
