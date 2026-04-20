## 2026-04-20: Inquisitor Audit — FR-256 & FR-257 Compliance Review

**Context:** Audited the 5 most recent commits (c2f79058..c1a4695b) spanning two feature branches: FR-256 (pipeline timing metrics, merged to main) and FR-257 (chaplain research step, in progress). Checked against Conventional Commits, changelog fragments, ADR-001 requirement traceability, diary reflections, and noqa confessions.

**Findings:**

1. ✓ **COMPLIANT — Conventional Commits**: All 5 commits follow the format. Both `feat` commits reference their FR ID in the title. The 3 `chore`/`docs` commits are correctly typed for administrative and planning work.

2. ✓ **COMPLIANT — Changelog & Requirement Traceability**: Both feat branches have changelog fragments with valid YAML front matter (`req: REQ-YG-259`, `req: REQ-YG-260`). Both REQs appear in ARCHITECTURE.md. All test functions carry `@pytest.mark.req` tags (6 each in `test_pipeline_timing.py` and `test_chaplain_research_step.py`).

3. ✓ **COMPLIANT — Diary Reflections**: Both features have diary entries with Heuristic and Seed sections. FR-256 identifies the `infrastructure_self_exempt` trap; FR-257 connects to the `unchallenged_premise` trap from the Knowledge Graph. Both Seeds propose concrete next steps (remote metrics visibility, PR/Issue-aware research).

4. ⚠ **DRIFT — Stale IDs in FR-257 commit body**: Commit 78261c7e body says "New: CAP-112, REQ-YG-259" but these were renamed to CAP-113/REQ-YG-260 in follow-up commit 10f7fc96. The commit message is immutable so this is cosmetic, but the stale reference could mislead future `git log` archaeology. The ARCHITECTURE.md and changelog fragment are correct.

5. ✓ **COMPLIANT — No unconfessed noqa**: No new `# noqa` suppressions were introduced in the diff across all 5 commits.

**Heuristic:** **Assign CAP/REQ IDs after collision check, not before commit.** The FR-257 branch had to rename its capability IDs after discovering a collision with FR-256's IDs that were merged to main. If the rename had happened before the feat commit, the stale reference in the immutable commit body would not exist. When multiple branches are in flight, defer final ID assignment until rebase against main.

**Seed:** Could the `req_coverage.py` script gain a `--check-collisions` mode that scans all branches (or at least the changelog/unreleased directory) for duplicate CAP/REQ IDs before commit? This would catch collisions at lint time rather than requiring a post-hoc rename commit.
