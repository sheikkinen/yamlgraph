## 2026-03-08: Inquisitor Audit XXVI — Post-FR-134 merge hygiene

**Context:** Audit of the latest 5 commits (fa0d217..85c5ea9), spanning FR-134 diary folder refactor completion, git bare corruption workaround, and pending FR housekeeping. Triggered by Rite: after significant branch work merges into the feature branch.

**Findings:**

1. **✗ VIOLATION — Merge commit breaks Conventional Commits.** `fa0d217` uses `merge: resolve conflict...` — `merge` is not a valid Conventional Commit type. Should use `chore(diary):` or similar. This would fail `commitlint.yml` enforcement on a PR title. The merge also lacks a Co-authored-by trailer.

2. **⚠ DRIFT — Two chore commits lack Co-authored-by trailer.** `818bd9a` (fix_bare.sh) and `cac3f8d` (inbox FR) have no trailer. If these were manual human commits without Copilot assistance, this is acceptable — but the CLAUDE.md convention states "always include" the trailer on git commits. Ambiguity in doctrine: does the rule apply only to Copilot-authored commits, or unconditionally?

3. **✓ COMPLIANT — FR-134 has full doctrinal coverage.** CHANGELOG entry present with REQ-YG-131 tag. ARCHITECTURE.md requirement documented. All tests carry `@pytest.mark.req("REQ-YG-063")` or equivalent. Diary reflection written (`2026-03-08-reflection-fr-134.md`). CONF-206 confession documented for new noqa suppression.

4. **✓ COMPLIANT — noqa coverage is complete.** `noqa_coverage.py` reports 55 suppressions, 57 confessions, 0 undocumented. The surplus confessions are from the example patterns in `noqa_coverage.py` itself (CONF-200 through CONF-204).

5. **✓ COMPLIANT — Commit d346d2b is doctrinally exemplary.** `fix(diary): FR-134 lint fixes and CONF-206 confession` — correct type, scope, FR reference, multi-line body, and Co-authored-by trailer. This is the standard other commits should follow.

**Heuristic:** *Merge commits are doctrine's blind spot.* Conventional Commit enforcement gates PR titles (squash merge) and local commits (pre-commit hook), but merge commits created during conflict resolution bypass both. Either accept merge commits as exempt (document explicitly) or require `--no-commit` merges followed by a properly-formatted commit.

**Seed:** Should the pre-commit hook validate merge commit messages too, or should the project adopt a rebase-only workflow on feature branches to eliminate merge commits entirely?
