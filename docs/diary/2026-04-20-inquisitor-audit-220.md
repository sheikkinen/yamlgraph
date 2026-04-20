## 2026-04-20: Inquisitor Audit — Recent 5 Commits (FR-255 through FR-257 + docs)

**Context:** Routine Inquisitor audit of the 5 most recent commits on the current branch (`fix/research-prompt-ecosystem-search`). Covers two merged feat PRs (FR-255 #131, FR-256 #134), two docs commits (FR planning), and one in-progress fix commit (ecosystem search for FR-257 research prompt).

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow the format. `feat` commits reference FR-XXX. `docs` and `fix` commits use correct type/scope. Multi-line messages written properly (no dquote trap).

2. ✓ COMPLIANT — **Changelog fragments**: Both `feat` PRs (FR-255, FR-256) and the `fix` commit have corresponding fragments in `changelog/unreleased/`. `docs` commits correctly omit fragments (planning docs don't warrant changelog entries).

3. ✓ COMPLIANT — **Requirement traceability (ADR-001)**: FR-255 → REQ-YG-258, FR-256 → REQ-YG-259, FR-257 → REQ-YG-260 all registered in ARCHITECTURE.md. Tests tagged with matching `@pytest.mark.req()` markers.

4. ✓ COMPLIANT — **Diary reflections (Sermon: Distill)**: FR-255 has `2026-04-19-reflection-fr-255-extract-shared-invoke-graph.md`. FR-256 has `2026-04-20-reflection-fr-256-pipeline-timing-metrics.md`. FR-257 has `2026-04-20-reflection-fr-257-chaplain-research-step.md`. All three contain Heuristic and Seed sections.

5. ⚠ DRIFT — **Fix commit scope breadth**: `eb7fe111` (`fix(chaplain)`) carries 12 changed files including new tests, diary, capability registration, and changelog for both FR-257 and the fix itself. The fix is a follow-up to FR-257 but the commit bundles FR-257's implementation artifacts alongside. On the PR branch this is acceptable (squash merge will flatten), but if reviewed commit-by-commit, the mixed concerns reduce auditability. The Knowledge Graph trap `mixed_commits_erode_auditability` applies: "One concern per commit → clear blame, clear revert."

**Heuristic:** A follow-up fix on a feature branch should still isolate its own commit from the parent feature's artifacts. Even when squash merge will flatten everything, reviewers reading the branch history benefit from clear commit boundaries. The cost of an extra `git add -p` is lower than the cost of a reviewer asking "which change is the fix and which is the feature?"

**Seed:** Could the Chaplain's enforce pipeline automatically split commits that touch both `.chaplain/` infrastructure and `tests/` + `changelog/` into separate atomic commits? A pre-push hook that detects mixed-concern commits and warns (or auto-splits via `git add -p` heuristics) would enforce the `mixed_commits_erode_auditability` cure mechanically rather than by discipline alone.
