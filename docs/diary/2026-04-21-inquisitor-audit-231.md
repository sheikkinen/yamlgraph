## 2026-04-21: Inquisitor Audit — Changelog Fragment Hygiene and Author Identity

**Context:** Audited the 5 most recent commits on `main` (a7a609c8..20e9eb9c) against the Scripture. The window spans docs/FR additions, diary landings, a CI fix, and a chaplain config tweak.

**Findings:**

1. ✗ **VIOLATION — Changelog fragment missing YAML front matter.** `changelog/unreleased/fix-a2a-sdk-optional-skip.md` lacks the required `---` / `type:` / `scope:` front matter (FR-179). Every other fragment in `unreleased/` follows the canonical format. This fragment would fail `changelog-req-gate` if CI enforced front-matter parsing on `fix` types.

2. ⚠ **DRIFT — Phantom author on local commit.** Commit `a7a609c8` (`chore: watcher timeout`) is authored by `Test <test@test.com>` rather than the project owner. The Chaplain watcher daemon appears to commit with a generic identity, eroding auditability. The knowledge graph trap `mixed_commits_erode_auditability` applies: unclear authorship makes blame forensics unreliable.

3. ✓ **COMPLIANT — Conventional Commits.** All 5 commits follow `type(scope): description` format correctly. The `docs(FR):` prefix for feature request documents is consistent and clear.

4. ✓ **COMPLIANT — Diary discipline.** Commit `7dc44faa` lands 9 diary/reflection files covering NC-220, NC-232, NV-latency, and philosopher entries. The Sermon's Distill step is well-exercised.

5. ✓ **COMPLIANT — noqa confessions.** 171 CONF entries vs 21 active `# noqa` suppressions across `yamlgraph/`. No new suppressions introduced in the audited window.

**Heuristic:** Automation that creates commits must inherit the operator's git identity, not a placeholder — `automation_inherits_doctrine` extends to authorship, not just `--no-verify`. A daemon commit with `Test <test@test.com>` passes format checks but fails forensic traceability.

**Seed:** Should the Chaplain watcher configure `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` from a `.chaplain/identity` file, making daemon authorship explicit and auditable rather than accidentally generic?
