## 2026-04-20: Inquisitor Audit — Latest 5 commits doctrine compliance

**Context:** Routine audit of the 5 most recent commits against the Scripture: three `docs(FR)` proposals (FR-260, FR-261, FR-262), one `fix(chaplain)` (ecosystem search), and one `feat(chaplain)` (FR-258 post-merge finalization). Checked Conventional Commits, changelog fragments, requirement traceability, diary reflections, and noqa confessions.

**Findings:**

1. ✓ COMPLIANT — `feat(chaplain): FR-258` follows full doctrine: Conventional Commits with FR reference, changelog fragment, CAP-114/REQ-YG-261 registered in ARCHITECTURE.md, 10 `@pytest.mark.req("REQ-YG-261")` test markers, and diary reflection written.

2. ✓ COMPLIANT — `fix(chaplain)` ecosystem search has changelog fragment (`research-prompt-ecosystem-search.md`), diary entries included in the commit, and no requirement needed (fix to existing FR-257 prompt).

3. ✓ COMPLIANT — All 86 noqa suppressions documented in confessions.md (0 undocumented). The noqa coverage script confirms full confession coverage.

4. ⚠ DRIFT — Three `docs(FR)` commits (b564aafd, 7fd5f406, a2816f5e) authored by `Test <test@test.com>` (Chaplain pipeline identity) lack `Co-authored-by: Copilot` trailers. While docs-only FR proposals don't require changelog or diary entries, the automated pipeline should include provenance trailers on all machine-generated commits for audit traceability.

5. ✓ COMPLIANT — All 5 commits follow Conventional Commits format. The three `docs(FR)` commits correctly use the `docs` type, avoiding false changelog gate triggers.

**Heuristic:** Automated pipelines that create commits inherit the same trailer obligations as interactive agents. A missing `Co-authored-by` on machine-generated commits erodes provenance auditing silently — the `Test <test@test.com>` author masks whether the content was human-authored or AI-generated.

**Seed:** Should the Chaplain pipeline's commit-creation step be hardened with a mandatory Co-authored-by injection, or should a pre-commit hook validate that `Test <test@test.com>`-authored commits always carry a provenance trailer?
