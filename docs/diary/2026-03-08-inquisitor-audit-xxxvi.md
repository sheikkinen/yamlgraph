## 2026-03-08: Inquisitor Audit XXXVI — Post-Remediation Compliance Check

**Context:** Audited the 5 most recent commits on `main` (b9e77a8..c71b12d). These span three PR-merged remediation commits (FR-151, FR-152, FR-153) and two direct-push docs-only commits from the enforce pipeline. The prior audit cycle (XXXIV–XXXV, referenced in FR-152) triggered the remediation wave; this audit checks whether the remediations themselves followed doctrine.

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits & ADR-001**: All 5 commits follow Conventional Commits format with FR references on feat/fix types. New test files (`test_changelog_fr137.py`, `test_demo_cleanup_changelog.py`, `test_diary_reflections_fr152.py`) all carry `@pytest.mark.req` tags. Both `# noqa` suppressions in `yamlgraph/` have CONF entries in `docs/confessions.md`.

2. ⚠ **DRIFT — `feat` type for remediation work**: Commits 01b75e7 (`feat(changelog): FR-151`) and 8afdd75 (`feat(diary): FR-152`) use `feat` for adding missing CHANGELOG entries and diary reflections — remediation, not new capability. Meanwhile b9e77a8 correctly uses `fix(changelog)` for identical work (FR-153). The `feat` type inflates semver signals and misrepresents the nature of the change.

3. ⚠ **DRIFT — Missing diary reflection for FR-153**: FR-153 merged as PR #29 but has no diary entry in `docs/diary/`. FR-151 (a structurally identical changelog-fix FR) *does* have a reflection, creating asymmetry. Mechanical fixes still benefit from the Distill step — even a two-line entry documents the pattern.

4. ⚠ **DRIFT — Enforce pipeline commits bypass squash-merge**: Commits c334b69 and c71b12d (authored "Test \<test@test.com\>") pushed directly to `main` without PRs. Both are docs-only (FR status updates, new FR file), so risk is low, but they bypass the squash-merge convention and CI gates established in FR-127.

**Heuristic:** Remediation commits that fix audit violations should use `fix` type, not `feat`. A `feat` commit implies new capability and triggers semver MINOR expectations. When the work is "add the thing we forgot," the honest type is `fix` — and honesty in commit metadata is what makes `git log` trustworthy.

**Seed:** Should the enforce pipeline route its docs-only commits through PRs (even auto-merged ones) to maintain the squash-merge invariant, or is a carve-out for zero-risk docs changes an acceptable pragmatic exception?
