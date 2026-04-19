## 2026-04-19: Inquisitor Audit — REQ traceability & noqa hygiene

**Context:** Audited the 5 most recent commits on `feat/fr-243-github-issues-remote-inbox` (11156737–48c4d2ee). Focus: requirement traceability integrity and noqa confession cross-referencing — areas not fully covered by audits 201–202.

**Findings:**

1. ✗ VIOLATION — **FR-248 commit message cites wrong REQ IDs.** Squash-merged commit `6f3d8294` on `main` references REQ-YG-246–249 in its body, but ARCHITECTURE.md and tests correctly use REQ-YG-250–253. REQ-YG-246 belongs to FR-246 (A2A Server docs), REQ-YG-247 to FR-243 (GitHub Issues inbox). The commit message is immutable — `git log --grep REQ-YG-246` will return a false match. Root cause: REQ IDs were assigned in the commit message before the renumbering fixup landed.

2. ⚠ DRIFT — **Inline noqa comments lack CONF-XXX cross-references.** 20 of 21 `# noqa` lines omit their confession ID (e.g., `# noqa: S602` instead of `# noqa: S602 (CONF-007)`). Only `a2a_server.py` follows the expected pattern. All suppressions are documented in `docs/confessions.md`, but discoverability suffers — a developer reading `shell.py:129` cannot find the justification without searching confessions.md.

3. ✓ COMPLIANT — **All feat commits have changelog fragments, diary entries, and test markers.** FR-248 (REQ-YG-250–253, 20+ tests), FR-243 (REQ-YG-247, 25 tests across 6 classes with class-level markers). No gaps.

4. ✓ COMPLIANT — **Conventional Commits format correct on all 5 commits.** Types (`chore`, `docs`, `feat`) with scopes. `feat` commits reference FR-XXX.

5. ⚠ DRIFT — **Audit frequency vs remediation ratio.** Audits 200–202 flagged CAP/REQ collision churn and audit saturation. Neither has spawned a corrective FR. The Knowledge Graph trap `audit_as_ritual` remains active: detection without enforcement is advisory.

**Heuristic:** **Immutable messages demand final-state IDs.** Squash-merge commit messages become permanent history. Any ID referenced in the message body must reflect the post-renumbering state, not the pre-collision draft. Review the commit message body at merge time, not at branch creation time.

**Seed:** Should the PR merge workflow include a CI check that validates REQ-YG-XXX references in the PR body against ARCHITECTURE.md, rejecting merges where cited REQ IDs don't match the capability table?
