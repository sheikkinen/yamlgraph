## 2026-04-19: Inquisitor Audit — FR-244/FR-248 A2A work & housekeeping

**Context:** Audited the 5 most recent commits spanning FR-244 (A2A SDK v1.0 compat), FR-248 (Agent Card/skill/streaming), and related housekeeping. Checked Conventional Commits, changelog fragments, requirement traceability, test markers, diary entries, and noqa confessions.

**Findings:**

1. ✓ COMPLIANT — **FR-244 & FR-248 changelog fragments exist** in `changelog/unreleased/` with correct type, scope, and REQ references. Requirements REQ-YG-245 and REQ-YG-250–253 are registered in ARCHITECTURE.md with capability entries. All tests carry `@pytest.mark.req` markers.

2. ✓ COMPLIANT — **Diary entries written for both features.** FR-244 diary names the "version bump iceberg" trap and extracts a reusable heuristic. FR-248 diary identifies the cache-scope and framework-costume traps. Both plant Seeds.

3. ⚠ DRIFT — **`chore:` commit on main omits scope.** Commit `0a1c6af3` uses `chore: fix CAP-103→104...` without a scope parenthetical. Valid per Conventional Commits spec, but project convention shows `type(scope): description` as the expected format. No CI enforcement gap (commitlint allows optional scope), but inconsistent with project examples.

4. ⚠ DRIFT — **Misleading fix commit message on feature branch.** Commit `9527a29a` says "restore REQ-YG-246 markers" but the diff shows markers changing FROM REQ-YG-246 TO REQ-YG-250. The message describes the opposite of what the code does. Low impact since squash merge will discard it, but the commit log is temporarily misleading.

5. ✓ COMPLIANT — **No new noqa suppressions.** Changed files (`a2a_nodes.py`, `a2a.py`, `graph_schema.py`) contain no `# noqa` directives. No confession debt introduced.

**Heuristic:** **Squash-merge amnesty is not commit-message amnesty.** Feature branch commits that will be squash-merged still appear in `git log --all` and `git bisect`. A misleading message ("restore X" when the diff does the opposite) can misdirect future debugging. Write accurate messages even on throwaway branches.

**Seed:** Should the commitlint CI check be extended to validate that `chore`/`docs` commits also include a scope, matching the project's documented convention? Currently only `feat` PRs are checked for FR-XXX; the scope requirement is advisory for other types.
