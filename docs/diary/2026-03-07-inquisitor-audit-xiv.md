## 2026-03-07: Inquisitor Audit XIV — mixed commit, standing findings frozen

**Context:** Fourteenth audit covering commits `6c737d9`..`b58eaa7` (5 commits: `chore(enforce)` ×1, `docs(chaplain)` ×2, `docs(diary)` ×1, `chore(graph)` ×1). One new commit since Audit XIII: `b58eaa7 chore(graph): move provider/model to defaults block`. Zero `feat:` or `fix:` commits in window. Audit XIII recused itself until a qualifying condition was met — none have been met, but the user explicitly invoked this audit.

**Findings:**

1. **⚠ DRIFT — Mixed commit bundles unrelated changes.** `b58eaa7` message says "move provider/model to defaults block" but the diff also adds 62 lines to `docs/diary.md` (Audit X, Audit XI, two chaplain entries). The commit message describes only the 4-line `graph.yaml` change. This makes `git log --oneline` misleading and complicates bisect. These should have been two commits.

2. **✓ COMPLIANT — Conventional Commits.** All 5 commits use valid prefixes. `b58eaa7` lacks a Co-authored-by trailer but the change appears manual (human-authored config restructuring).

3. **✓ COMPLIANT — noqa confessions.** Single framework suppression (`ARG002` in `token_tracker.py`) confessed as CONF-002. No new suppressions added.

4. **✓ COMPLIANT — ADR-001, CHANGELOG.** No new capabilities, tests, or `feat:`/`fix:` commits. No CHANGELOG entry required. Standing FR-116 CHANGELOG gap remains a release-blocker (classified Audit XI, not re-flagged).

5. **⚠ DRIFT — Three standing findings persist (7th consecutive audit).** ARCHITECTURE.md line 1125: "7 providers" (should be 8). FR-112 status: "Draft" (should be "Done"). FR-116 CHANGELOG: absent. These are frozen findings — documented since Audit VIII, each fixable in <1 minute. This audit will not re-classify them. They are release-blockers per Audit XI's ruling.

**Heuristic:** *A commit message that describes one change while the diff contains two is a lie to future-self.* Mixed commits erode the value of `git log` and `git bisect`. The fix is trivial: commit diary entries separately from code changes, even when both are ready at the same time.

**Seed:** Should pre-commit enforce that commits touching both `docs/diary.md` and non-docs files require an explicit `--mixed` flag or separate commits? This would catch the pattern at the gate rather than at audit.
