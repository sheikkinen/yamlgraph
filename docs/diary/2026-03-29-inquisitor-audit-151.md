## 2026-03-29: Inquisitor Audit — FR-208 A2A Server & Recent Commits

**Context:** Audited the 5 most recent commits on `main` covering FR-208 (A2A protocol server), FR-207 (Scripture template extraction), and supporting docs/chore commits. Checked compliance against the Scripture's Commandments, ADR-001, Sermon, and noqa Confessions.

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits**: All 5 commits follow the `type(scope): description` format. Both `feat` commits reference their FR number. Commit messages are precise and descriptive.

2. ✓ **COMPLIANT — FR-208 Full Doctrine Adherence**: Changelog fragment present (`FR-208-a2a-graph-support.md`), requirements added to ARCHITECTURE.md (REQ-YG-206..213), all 33 test functions carry `@pytest.mark.req` tags, diary reflection written, demo-output.log included, noqa suppression (CONF-004) documented in confessions.md. Module sizes within limits (330 + 241 lines). This is exemplary.

3. ✓ **COMPLIANT — FR-207 Doctrine Adherence**: Went through PR #72, changelog fragment present, diary reflection (`2026-03-28-reflection-fr-207.md`) written, requirements REQ-YG-201..205 covered.

4. ⚠ **DRIFT — Direct Pushes to Main**: Three commits (`d398e81`, `f0ba460`, `673c162`) have no associated PRs. These are `docs(FR)` and `chore` types — not feat/fix, so they don't trigger changelog-gate or diary-gate. However, branch protection rules state "No direct pushes to main." If admin bypass was used, no break-glass documentation was found in the commit trail. The spirit of the rule (auditability at merge boundary) is weakened when planning/chore commits bypass the PR gate.

5. ⚠ **DRIFT — Ephemeral Test Coverage**: FR-207 (c80894e) added `test_scripture_dev_template.py` (519 lines), then the very next commit (673c162) removed it during extraction to a separate repo. While the extraction is correct, the two commits create a window where tests exist then vanish on `main`. A single squash-merged PR containing both operations would have been cleaner — `mixed_commits_erode_auditability` applies.

**Heuristic:** *Extraction commits are refactors, not exemptions.* When code moves to another repo, the add-then-remove should be atomic (single PR) or the original feat PR should not land the code that's about to be extracted. Two sequential commits that add then delete 519 lines of tests is noise in the audit trail.

**Seed:** Could the Chaplain enforce a "net-zero test deletion" rule — any commit removing tests must either be paired with equivalent additions or carry an explicit `extraction:` trailer linking to the destination repository?
