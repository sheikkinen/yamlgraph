## 2026-04-21: Inquisitor Audit — Docs-Only Sprint with Duplicate Messages and Recurring Mixed Commit

**Context:** Audited the 5 most recent commits (7dc44faa..7a6209c2) covering FR-263 and FR-262 planning docs, accumulated diary landings, and a watcher timeout config change. Checked against Conventional Commits, CHANGELOG fragments (FR-179), ADR-001 req traceability, diary (Sermon: Distill), and noqa Confessions.

**Findings:**

1. ⚠ **DRIFT — Duplicate commit messages** (`7a6209c2` and `ee3d6e8e`): Both read `docs(FR): add FR-263-azure-openai-provider for enforce pipeline` but carry different content. The first adds the FR doc; the second updates usage evidence statistics. The word "add" is misleading on the second commit — it should read `docs(FR): update FR-263 usage evidence counts`. `git log --oneline` now shows two identical lines, making blame and revert ambiguous.

2. ✗ **VIOLATION — Mixed commit persists** (`a7a609c8` `chore: watcher timeout`): Bundles `.chaplain/graphs/copilot/graph.yaml` timeout tweak, 6 diary entries, a git report, and FR-259 planning doc — 9 files across 4 unrelated concerns. Previous audit (232) flagged the same commit. Knowledge Graph: `mixed_commits_erode_auditability: "One concern per commit → clear blame, clear revert"`. This commit cannot be cleanly reverted for any single concern without losing the others.

3. ✓ **COMPLIANT — Conventional Commits format**: All 5 commits use valid types and scopes (`docs(FR):`, `chore:`, `docs(diary):`). No bare messages or missing types.

4. ✓ **COMPLIANT — No changelog/test/req gaps**: All 5 commits are docs-only (FR planning, diary reflections, config). No production code, no new capabilities, no tests to tag. Changelog fragments not required for `docs:` or `chore:` types.

5. ✓ **COMPLIANT — noqa Confessions**: 86 suppressions, 99 documented confessions, 0 undocumented. Clean.

**Heuristic:** *Automated pipelines that commit on behalf of the author inherit the author's obligation to separate concerns.* The "enforce pipeline" produced two identical-message commits for FR-263 because the pipeline script uses a fixed message template. A pipeline should either amend the previous commit when updating the same artifact, or include a distinguishing qualifier (e.g., `add` vs `update`) in the message. The mixed commit (`a7a609c8`) is a recurring finding — two consecutive audits (232, 233) flag the same commit, suggesting the batch-commit pattern in the watcher needs a structural fix, not just advisory.

**Seed:** Should `watch.sh` enforce single-concern commits by grouping staged files by top-level directory and creating one commit per group, rather than committing everything staged in a single pass?
