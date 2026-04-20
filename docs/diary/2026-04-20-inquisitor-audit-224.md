## 2026-04-20: Inquisitor Audit — Mixed Feat/Fix in Ecosystem Search Branch

**Context:** Audited the 5 most recent commits on `fix/research-prompt-ecosystem-search` branch against Scripture. Focused on Conventional Commits, changelog fragments, req traceability, diary entries, and noqa confessions.

**Findings:**

- ✓ COMPLIANT — **FR-256 (`ae8a7026`) fully doctrine-compliant.** Conventional Commit with FR reference, changelog fragment with `req: REQ-YG-259`, 6 tests with `@pytest.mark.req("REQ-YG-259")`, ARCHITECTURE.md updated, diary reflection written. Exemplary.

- ✓ COMPLIANT — **noqa confessions complete.** `noqa_coverage.py` reports 86 suppressions, 0 undocumented. No new suppressions in audited commits.

- ✓ COMPLIANT — **All 5 commits follow Conventional Commits format.** Types (`feat`, `fix`, `chore`, `docs`) used correctly. FR-256 includes FR reference in title.

- ⚠ DRIFT — **FR-257 implementation delivered via `fix` branch.** Commit `eb7fe111` (`fix(chaplain)`) bundles FR-257 feat implementation (research step, judge update, capabilities, ARCHITECTURE.md, feat changelog fragment) alongside the ecosystem search fix. When squash-merged under a `fix(...)` title, the feat delivery bypasses `diary-gate` (which triggers on `FR-XXX` in PR title) and the commit type misrepresents scope. The `mixed_commits_erode_auditability` trap from the Knowledge Graph.

- ⚠ DRIFT — **No diary entry for ecosystem search fix.** FR-257 has a reflection (`2026-04-20-reflection-fr-257-chaplain-research-step.md`), but the ecosystem search follow-up fix lacks its own reflection. The insight — that research looking only inward missed competitive landscape evidence — is valuable enough to warrant capture. Currently buried in the commit message.

**Heuristic:** **Feat deliveries must travel in feat branches.** When a fix branch accumulates feat-level changes (new capabilities, ARCHITECTURE.md updates, feat changelog fragments), the branch has mutated scope. Split the feat into its own branch before merge, or rename the branch/PR to `feat`. The CI gates (`diary-gate`, `commitlint` FR-XXX check) are calibrated to commit type — smuggling a feat through a fix bypasses the gates without triggering them.

**Seed:** Could a pre-commit hook detect changelog fragment types that conflict with branch prefix? A `fix/` branch containing a `type: feat` changelog fragment is a mechanical signal of scope mutation — catchable before the PR is even opened.
