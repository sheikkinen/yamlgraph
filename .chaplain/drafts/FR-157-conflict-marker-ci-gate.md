# Feature Request: FR-157 Conflict Marker CI Gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Add a CI job that fails the PR status check when unresolved merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) are present in any tracked file, and enable "require branches to be up-to-date before merging" in branch protection to prevent the root cause.

## Value Statement

All contributors are protected from broken files reaching `main`, because the server-side merge path — which bypasses the local `check-merge-conflict` pre-commit hook — is now gated by CI.

## Problem

Merge conflict markers reached `main` and persisted across two consecutive Inquisitor audits (XXXVII and XXXVIII). The root cause: concurrent PR squash-merges targeting the same file (CHANGELOG.md) without a rebase requirement.

The existing `check-merge-conflict` hook in `.pre-commit-config.yaml` only runs locally. GitHub server-side squash merges bypass it entirely. This is a structural gap — local hooks cannot guard the server-side merge path.

**Audit trail:**
- Audit XXXVII: `CHANGELOG.md` lines 13–18 contained `<<<<<<<`/`=======`/`>>>>>>>` markers between FR-145 and FR-149 entries.
- Audit XXXVIII: Same violation still present (`UU CHANGELOG.md`).

## Proposed Solution

Two complementary changes — one reactive (CI gate), one preventive (branch protection):

### 1. CI conflict marker check (reactive gate)

Add a `conflict-check` job to `.github/workflows/commitlint.yml`, which already triggers on `pull_request` events:

```yaml
  conflict-check:
    name: No conflict markers
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for conflict markers
        run: |
          if git grep -n -E '^<{7} |^={7}$|^>{7} ' -- ':!.github' ':!*.md.bak'; then
            echo "::error::Unresolved merge conflict markers found in tracked files"
            exit 1
          else
            echo "✅ No conflict markers found"
          fi
```

Then add `conflict-check` as a required status check in GitHub branch protection settings for `main` (alongside existing `commitlint` and `test` checks).

### 2. Require branch up-to-date (preventive)

In GitHub Settings → Branches → `main` branch protection rule (FR-150):

Enable **"Require branches to be up to date before merging"** on the existing required status checks. This forces the second of two concurrent PRs to rebase after the first merges, eliminating the condition that creates conflicts.

**Trade-off:** This adds friction — PRs touching overlapping files must rebase before merge. This is acceptable because:
- It prevents the exact class of bugs that reached `main` twice.
- The rebase step surfaces conflicts at PR time rather than in `main`.
- Most PRs won't be affected (only concurrent edits to the same file).

## Acceptance Criteria

- [ ] `.github/workflows/commitlint.yml` contains a `conflict-check` job that greps all tracked files for conflict marker patterns (`<<<<<<<`, `=======`, `>>>>>>>`)
- [ ] The `conflict-check` job fails with a non-zero exit code when conflict markers are present
- [ ] The `conflict-check` job passes when no conflict markers are present
- [ ] `conflict-check` is added as a required status check in GitHub branch protection for `main`
- [ ] "Require branches to be up to date before merging" is enabled on `main` branch protection
- [ ] Tests added: integration test or manual verification that a PR branch containing conflict markers triggers CI failure
- [ ] Documentation updated: `CLAUDE.md` branch protection table updated with new `conflict-check` status check and "up-to-date" requirement

## Alternatives Considered

1. **Post-merge scan only (Inquisitor):** Already exists and caught the violation, but is reactive — damage reaches `main` before detection. Rejected because prevention is cheaper than remediation.

2. **GitHub Actions marketplace action (e.g., `check-merge-conflicts`):** Adds an external dependency for a one-line `git grep`. Rejected — the inline script is simpler, auditable, and has no supply-chain risk.

3. **Server-side pre-receive hook:** Not available on GitHub.com (only GitHub Enterprise Server). Not applicable.

4. **CI gate only, without "require up-to-date":** Catches markers in existing PR branches but doesn't prevent the race condition that creates them. Implemented as the primary gate, but the up-to-date requirement is the structural prevention.

## Related

- **FR-150** (`feature-requests/FR-150-branch-protection-main.md`): Branch protection for `main` — this FR extends its rules
- **Inquisitor Audits XXXVII & XXXVIII**: Identified the violation
- `.pre-commit-config.yaml` line 21: Existing local `check-merge-conflict` hook (bypassed by server-side merges)
- `.github/workflows/commitlint.yml`: Target file for the new CI job
