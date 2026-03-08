# Feature Request: CI Pre-Merge CHANGELOG Gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Add a GitHub Actions check that blocks merge of `feat` and `fix` PRs unless `CHANGELOG.md` is modified in the PR diff. This closes the structural gap where server-side squash merges bypass the local commit-msg hook (FR-077) and the post-merge script (FR-125) can be forgotten.

## Value Statement

Maintainers can no longer accidentally merge feature or fix PRs without a CHANGELOG entry, eliminating a recurring audit finding (Audits XXXIV, XXXV).

## Problem

Two existing enforcement mechanisms fail to guarantee CHANGELOG entries:

1. **FR-077 (commit-msg hook):** Blocks `feat:`/`fix:` commits locally unless `CHANGELOG.md` is staged. However, GitHub's server-side squash merge bypasses all local hooks — the commit is created on the server, not the developer's machine.

2. **FR-125 (finalize_merge.sh):** Post-merge script that adds CHANGELOG entries after merge. Being a manual step, it can be forgotten. Audits XXXIV and XXXV both flagged merged features (FR-137 DeepSeek provider, FR-145 phantom requirement detection) with missing CHANGELOG entries because the script was skipped.

Neither mechanism creates a **pre-merge gate**. The result: features merge without CHANGELOG entries, discovered only retroactively by the inquisitor.

## Proposed Solution

Extend `.github/workflows/commitlint.yml` with a job that checks whether `CHANGELOG.md` appears in the PR's changed files for `feat` and `fix` PRs.

```yaml
  changelog-gate:
    name: CHANGELOG required for feat/fix
    runs-on: ubuntu-latest
    if: >-
      startsWith(github.event.pull_request.title, 'feat') ||
      startsWith(github.event.pull_request.title, 'fix')
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Verify CHANGELOG.md modified
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          if git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -qE '^CHANGELOG\.md$'; then
            echo "✅ CHANGELOG.md is modified"
          else
            echo "::error::feat/fix PRs must include changes to CHANGELOG.md"
            exit 1
          fi
```

### Design Decisions

- **Extend commitlint.yml** rather than adding a new workflow — keeps PR-title enforcement co-located with CHANGELOG enforcement.
- **Title-based detection** (`startsWith`) matches the existing pattern in `commitlint.yml`'s `feat requires FR-XXX` step, and aligns with squash-merge convention where the PR title becomes the commit message.
- **`if` condition at job level** so the job is skipped (not failed) for non-feat/non-fix PRs, keeping CI green and fast.
- **git diff** against base/head SHAs to check actual file changes, not just the latest commit.

## Acceptance Criteria

- [ ] `feat` PRs targeting `main` without `CHANGELOG.md` in diff → check fails, merge blocked
- [ ] `fix` PRs targeting `main` without `CHANGELOG.md` in diff → check fails, merge blocked
- [ ] `feat`/`fix` PRs with `CHANGELOG.md` modified → check passes
- [ ] `chore`/`docs`/`refactor`/`test`/`ci`/`perf`/`style`/`build` PRs → check skipped (not failed)
- [ ] Job added to `.github/workflows/commitlint.yml` as a separate job (`changelog-gate`)
- [ ] Check configured as a required status check in branch protection rules for `main`

## Alternatives Considered

1. **Separate workflow file** — Rejected; co-locating with `commitlint.yml` keeps all PR-title-driven enforcement in one place.
2. **GitHub App / third-party action** — Rejected; a 10-line shell script is simpler and has no external dependencies.
3. **Probot / webhook** — Over-engineered for a diff check.
4. **Rely solely on FR-125 (post-merge script)** — Current state; fails because it's manual and can be forgotten, as proven by Audits XXXIV and XXXV.

## Related

- **FR-077** (`feature-requests/FR-077-changelog-commit-enforcement.md`) — Local commit-msg hook (bypassed by server-side squash merge)
- **FR-125** (`feature-requests/FR-125-enforce-pipeline-finalize.md`) — Post-merge finalization script (manual, can be skipped)
- **FR-127** (`feature-requests/FR-127-ci-conventional-commit-enforcement.md`) — CI conventional commit enforcement via `commitlint.yml`
- **Audit XXXIV** — Flagged FR-137 missing CHANGELOG entry
- **Audit XXXV** — Flagged FR-137 and FR-145 missing CHANGELOG entries
- `.github/workflows/commitlint.yml` — Target workflow for the new job
