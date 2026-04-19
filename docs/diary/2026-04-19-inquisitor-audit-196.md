## 2026-04-19: Inquisitor Audit — Recent Commits (e32b88e..712c382)

**Context:** Audit of the 5 most recent commits on `main` against the Scripture. Covers 3 docs(FR) commits adding feature requests (FR-244, FR-245, FR-246), one fix correcting cross-wired changelog `req:` front-matter (FR-242, PR #112), and one fix enabling multilingual voice cloning (PR #111).

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits**: All 5 commits follow the `type(scope): description` format. The 3 docs commits use `docs(FR):`, both fixes use `fix(scope):`. FR-242 includes `FR-XXX` reference as required for feat/fix.

2. ✓ **COMPLIANT — TDD & Requirement Traceability (ADR-001)**: FR-242 added condemning tests in `test_changelog_req_cross_wiring.py` with `@pytest.mark.req("REQ-YG-162", "REQ-YG-161")`. Chatterbox tests carry proper `@pytest.mark.req` tags across 5 classes. No new `# noqa` suppressions found.

3. ✓ **COMPLIANT — Diary (Sermon: Distill)**: FR-242 has a quality reflection (`2026-04-19-reflection-fr-242-changelog-req-cross-wiring.md`) identifying the `plausible_wrong_answer` trap and proposing Chaplain auto-population as a Seed.

4. ⚠ **DRIFT — Missing changelog fragment for FR-242**: The `fix(changelog)` commit corrected 38 existing fragments but has no dedicated fragment describing the fix itself. CI likely passed because modified fragments satisfied the gate, but the fix action itself is unrecorded in the changelog. Low impact — this is a meta-fix to the changelog system, not a user-facing change.

5. ⚠ **DRIFT — Chatterbox fix (#111) has no FR reference or diary**: Commit `fix(chatterbox): enable multilingual voice cloning via --ref` carries no `FR-XXX` in the title, exempting it from the diary-gate. The Sermon's Distill step recommends reflection on every task. A nearby diary exists (`fr-239-chatterbox-multilingual-cli.md`) covering related work, but the specific insight (guard incorrectly rejected valid API capability) goes unrecorded.

**Heuristic:** Meta-fixes (fixes to enforcement infrastructure itself) slip through the gates they enforce — the changelog-gate passes when fragments are *modified* but doesn't check whether the *modification action* is itself documented. This is a specific instance of the `infrastructure_self_exempt` trap from the Knowledge Graph.

**Seed:** Should the changelog-gate distinguish between "fragment exists in diff" and "fragment *added* in diff" to catch meta-fixes that modify but don't create fragments?
