## 2026-03-14: Inquisitor Audit — FR-201 / FR-196 Compliance Review

**Context:** Routine audit of the 5 most recent commits on `main`, covering FR-201 (horoscope demo), FR-196 (portable chaplain), and supporting docs/chore commits. Checked Conventional Commits, changelog fragments, requirement traceability (ADR-001), test tagging, diary entries, and noqa confessions.

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits**: All 5 commits follow the format. `feat` commits reference `FR-XXX`. Squash merges (#63, #64) preserve PR title as commit message.

2. ✓ **COMPLIANT — Requirement Traceability**: CAP-75 (REQ-YG-196) and CAP-76 (REQ-YG-197) registered with full module lists. `req_coverage.py` reports 11 tests each. All test functions carry `@pytest.mark.req` tags. `noqa_coverage.py` confirms 0 undocumented suppressions.

3. ✓ **COMPLIANT — Changelog & Diary**: Both FRs have changelog fragments in `changelog/unreleased/`. FR-201 has two fragments (demo + dated output). Diary reflections exist for both (`reflection-fr-201.md`, `reflection-fr-196.md`).

4. ⚠ **DRIFT — Mixed Concerns in d6850b7**: Commit `d6850b7` bundles horoscope feature changes (graph.yaml, tools.py, tests) with unrelated inquisitor audit diary entries (audit-124, audit-125) and a chaplain diary. The `mixed_commits_erode_auditability` pattern from the Knowledge Graph applies — one concern per commit for clear blame and clean revert.

5. ⚠ **DRIFT — Direct Push Without PR (d6850b7)**: This `feat` commit reached `origin/main` without a PR number in the title, unlike the squash merges for #63 and #64. Branch protection requires PRs for `main`. Either admin override was used (should be documented per `reference/break-glass.md`) or the gate was bypassed. Also missing the `Co-authored-by` trailer.

**Heuristic:** Batch diary/audit files into their own `chore(docs)` commit rather than mixing them into feature commits. The audit trail is cleaner when the commit that adds the feature is *only* the feature, and the commit that records the reflection is *only* the reflection.

**Seed:** Should a pre-commit hook enforce single-concern commits by detecting when both `docs/diary/` and non-docs files appear in the same `feat`/`fix` staged set?
