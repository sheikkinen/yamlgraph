## 2026-04-20: Inquisitor Audit — Mixed-Concern Commit on fix/research-prompt-ecosystem-search

**Context:** Audited the 5 most recent commits from HEAD (`eb7fe111..82eb81e1`) spanning two merged features (FR-255, FR-256) and one in-progress branch (`fix/research-prompt-ecosystem-search`). Checked against Conventional Commits, changelog fragments, ADR-001 requirement traceability, diary reflections, noqa confessions, and the `mixed_commits_erode_auditability` process rule.

**Findings:**

1. ✗ **VIOLATION — Mixed-concern commit** (`eb7fe111`): Commit message is `fix(chaplain): add ecosystem search to research prompt`, but the diff contains 12 files / 499 insertions spanning three distinct concerns: (a) the actual fix to `research.yaml`, (b) the entire FR-257 feat implementation (CAP-113, ARCHITECTURE.md additions, 264-line test file, changelog fragment, capability YAML, FR update), and (c) unrelated diary/audit entries. The Scripture's `mixed_commits_erode_auditability` is explicit: "One concern per commit → clear blame, clear revert." A revert of this "fix" would also revert the FR-257 feature and audit records.

2. ⚠ **DRIFT — Commit type misrepresents content**: The commit is typed `fix` but delivers a `feat` (new capability CAP-113, new REQ-YG-260, new tests, new changelog fragment for FR-257). By omitting `FR-257` from the commit title, the `diary-gate` CI check is bypassed — yet the commit contains the diary reflection for FR-257. The gate's intent is satisfied in substance but circumvented in mechanism.

3. ✓ **COMPLIANT — Merged feats (FR-255, FR-256)**: Both follow Conventional Commits with FR references, have changelog fragments with valid `req:` front-matter, ARCHITECTURE.md updated with CAP/REQ entries, all test functions carry `@pytest.mark.req` tags, and diary reflections exist.

4. ✓ **COMPLIANT — docs commits**: `docs(FR)` commits (`c2f7905`, `325e434`) correctly typed for FR planning documents; no changelog or diary required.

5. ✓ **COMPLIANT — No unconfessed noqa**: No new `# noqa` suppressions across any of the 5 commits.

**Heuristic:** **Separate the fix from the feat it fixes.** When a follow-up fix is needed on a feature branch, commit the feat artifacts first (`feat(scope): FR-XXX ...`), then commit the fix separately (`fix(scope): ...`). This preserves atomicity, keeps CI gates honest, and ensures `git revert` targets a single concern. The trap is `quick_confidence` — "it's all related, one commit is fine" — but the commit message becomes the unit of auditability.

**Seed:** Should pre-commit gain a heuristic that warns when a `fix`-typed commit touches ARCHITECTURE.md or adds a new `capabilities/CAP-*.yaml` file? These artifacts are feat signals; their presence in a fix commit is a reliable indicator of mixed concerns.
