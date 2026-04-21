## 2026-04-20: Inquisitor Audit — Chaplain Pipeline FR-257/258/260

**Context:** Audited the 5 most recent commits on `main` (a2816f5e..21d6ff07) covering FR-257 (research step), FR-258 (post-merge finalization), FR-260 (acceptance tests FR), and a follow-up fix adding ecosystem search to the research prompt.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits and changelog fragments.** All 5 commits follow `type(scope): description` format. Both `feat` commits reference FR-XXX. All feat/fix commits have corresponding changelog fragments in `changelog/unreleased/` with correct front-matter (type, scope, req).

2. ✓ COMPLIANT — **ADR-001 requirement traceability.** FR-257 registered CAP-113/REQ-YG-260 in ARCHITECTURE.md with 6 tagged tests. FR-258 registered CAP-114/REQ-YG-261 with 10+ tagged tests. Both link back through changelog `req:` fields.

3. ✓ COMPLIANT — **Diary reflections.** Both feat commits have dedicated diary entries (FR-257: cognitive trap analysis of `unchallenged_premise`; FR-258: `downstream_fix` trap with shared library extraction). Both include heuristics and seeds per the Sermon.

4. ⚠ DRIFT — **Mixed concerns in fix commit.** `fix(chaplain)` (#136) bundles 6 inquisitor audit diary entries alongside the prompt fix. The sub-commit "chore: add inquisitor audit entries to trigger CI" is a separate concern. Per Knowledge Graph `mixed_commits_erode_auditability`: one concern per commit for clear blame and clear revert. The audit entries should have been a separate PR or commit.

5. ✓ COMPLIANT — **No unconfessed noqa.** No `# noqa` suppressions found in any of the 5 commits' diffs.

**Heuristic:** CI-trigger commits reveal a process gap. When unrelated files are bundled into a PR solely to trigger or satisfy CI gates, the gate is working (it forced an action) but the response is wrong (mixing concerns instead of addressing the root cause). The fix: ensure diary-gate and other gates are satisfied by artifacts *related* to the PR's primary purpose, not by hitchhiking unrelated work.

**Seed:** Could a CI check detect mixed-concern PRs? A heuristic: if a PR modifies files in 3+ unrelated directories (e.g., `.chaplain/prompts/` + `docs/diary/inquisitor-*` + `changelog/`) and the diary files don't reference the PR's FR, flag it as a potential mixed-concern commit.
