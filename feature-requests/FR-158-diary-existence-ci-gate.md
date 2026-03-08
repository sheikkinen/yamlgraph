# Feature Request: CI Gate for Diary Reflection Existence

**ID:** FR-158
**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Add a GitHub Actions job that blocks merge of `feat` and `fix` PRs unless a diary reflection file exists for the referenced FR number. Mirrors the FR-149 CHANGELOG gate pattern — file existence enforced in CI, content quality enforced by FR-144 pre-commit hook.

## Value Statement

The project maintains cognitive discipline by ensuring every meaningful feature or fix produces a diary reflection, closing the structural gap that five consecutive audits (XL–XLIV) identified but could not remediate through detection alone.

## Problem

FR-144 enforces diary reflection *content quality* (rejecting unfilled stubs) but no mechanism enforces *file existence*. The result: five consecutive Inquisitor audits (XL–XLIV) flagged missing diary reflections for FR-150, FR-154, FR-135, and FR-153 — all merged without reflections despite audit citations.

FR-152 retroactively created missing reflections for FR-137/FR-145, but recurrence was immediate. The fix-per-instance approach does not scale. This is the `audit_as_ritual` trap: "3+ audits without fix → ritual, not process." Detection without enforcement is observation without agency.

The FR-149 CHANGELOG gate proved that CI-level enforcement closes gaps that local hooks miss (server-side squash merges bypass pre-commit). The same pattern applied to diary reflections completes the enforcement chain.

## Proposed Solution

Add a `diary-gate` job to `.github/workflows/commitlint.yml` that:

1. Triggers on `feat` and `fix` PR types (detected via `startsWith` on PR title, matching FR-149 pattern).
2. Extracts the `FR-XXX` reference from the PR title.
3. Checks if any file matching `docs/diary/*reflection*fr-{number}*.md` exists in the PR's changed files.
4. Fails with an actionable error message if no matching diary file is found.
5. Skips (passes) for PRs without an FR reference — `fix` PRs without FR numbers are minor corrections that don't warrant reflection.

### Implementation

Add to `.github/workflows/commitlint.yml` after the existing `changelog-gate` job:

```yaml
  diary-gate:
    name: Diary reflection required for feat/fix
    runs-on: ubuntu-latest
    if: >-
      startsWith(github.event.pull_request.title, 'feat') ||
      startsWith(github.event.pull_request.title, 'fix')
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Verify diary reflection exists
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          PR_TITLE: ${{ github.event.pull_request.title }}
        run: |
          # Extract FR number from PR title
          FR_NUM=$(echo "$PR_TITLE" | grep -oE 'FR-[0-9]+' | head -1 | sed 's/FR-//')

          if [ -z "$FR_NUM" ]; then
            echo "⏭️ No FR-XXX reference in title — diary gate skipped"
            exit 0
          fi

          echo "🔍 Checking for diary reflection for FR-$FR_NUM..."

          if git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -qE "docs/diary/.*reflection.*fr-${FR_NUM}[^0-9]"; then
            echo "✅ Diary reflection found for FR-$FR_NUM"
          else
            echo "::error::feat/fix PRs referencing FR-$FR_NUM must include a diary reflection in docs/diary/"
            echo ""
            echo "Expected: docs/diary/YYYY-MM-DD-reflection-fr-${FR_NUM}.md"
            echo ""
            echo "The diary reflection should document:"
            echo "  - Cognitive traps encountered"
            echo "  - Heuristics learned"
            echo "  - A Seed question for future work"
            echo ""
            echo "See docs/diary/ for examples."
            exit 1
          fi
```

### Enforcement Composition

The two gates compose cleanly with no overlap:

| Gate | Layer | Enforces | Mechanism |
|------|-------|----------|-----------|
| FR-158 (this) | CI | File *existence* | GitHub Actions required check |
| FR-144 | Pre-commit | Content *quality* | Local hook rejects placeholders |

- FR-158 ensures a diary file is created and included in the PR.
- FR-144 ensures the file contains real reflection, not unfilled stubs.
- Neither gate duplicates the other's responsibility.

## Acceptance Criteria

- [x] New job `diary-gate` added to `.github/workflows/commitlint.yml`
- [x] `feat` PRs with `FR-XXX` reference and no `docs/diary/*reflection*fr-XXX*.md` in changed files → check fails
- [x] `feat` PRs with `FR-XXX` reference and matching diary file in changed files → check passes
- [x] `fix` PRs with `FR-XXX` reference follow same logic as `feat`
- [x] `fix` PRs without `FR-XXX` reference → check skips (passes)
- [x] `chore`, `docs`, `test`, `ci`, `refactor`, `perf`, `style`, `build`, `revert` PRs → job skipped entirely via `if` condition
- [ ] `diary-gate` added as required status check in branch protection (FR-150)
- [x] Error message includes expected file path pattern and content guidance
- [x] Documentation: `CLAUDE.md` Branch Protection table updated with new required check

## Alternatives Considered

1. **Pre-commit hook only (extend FR-144):** Pre-commit hooks are bypassed by server-side squash merges. FR-149 proved CI gates are the reliable enforcement layer; hooks remain the quality layer.

2. **Separate workflow file (`diary-gate.yml`):** Adds configuration surface. The commitlint workflow already owns PR-title-based enforcement; colocation keeps related gates discoverable.

3. **Require diary for ALL PR types:** Overly ceremonial. `chore`, `docs`, `refactor`, etc. carry lighter cognitive load; forcing reflection on a typo fix degrades the signal-to-noise ratio of diary entries.

4. **Check file existence in repository (not just diff):** Would allow retroactively added reflections to satisfy the gate for new PRs. Using `git diff` ensures the reflection is authored as part of the same PR, preserving temporal coupling between implementation and reflection.

## Related

- **FR-144:** Diary reflection content enforcement (pre-commit hook) — quality gate
- **FR-149:** CI CHANGELOG gate — architectural model for this gate
- **FR-150:** Branch protection rules — diary-gate becomes a required status check
- **FR-152:** Retroactive diary creation for FR-137/FR-145 — symptom fix this FR prevents
- **FR-134:** Diary folder refactor — established diary structure and stub mechanism
- **Audits XL–XLIV:** Five consecutive citations of missing diary reflections
- **Trap:** `audit_as_ritual` — "3+ audits without fix → ritual, not process"
- **Cure:** `audit_gate` — "Audit without blocking mechanism = post-mortem before incident"
