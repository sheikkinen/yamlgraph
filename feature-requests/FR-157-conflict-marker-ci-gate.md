# Feature Request: FR-157 Conflict Marker CI Gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Add a `conflict-check` CI job that fails when unresolved merge conflict markers are present in tracked files, and enable "require branches to be up-to-date before merging" in branch protection to prevent the race condition that creates them.

## Value Statement

All contributors are protected from broken files reaching `main`, because the server-side merge path — which bypasses the local `check-merge-conflict` pre-commit hook — is now gated by CI.

## Problem

Merge conflict markers reached `main` and persisted across two consecutive Inquisitor audits (XXXVII and XXXVIII). Root cause: concurrent PR squash-merges targeting the same file (`CHANGELOG.md`) without a rebase requirement.

The existing `check-merge-conflict` hook in `.pre-commit-config.yaml` (line 21) only runs locally. GitHub server-side squash merges bypass it entirely. This is a structural gap — local hooks cannot guard the server-side merge path.

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

**Pattern details:**
- `^<{7} ` — conflict start marker (7 `<` followed by space)
- `^={7}$` — conflict separator (exactly 7 `=`)
- `^>{7} ` — conflict end marker (7 `>` followed by space)
- `:!.github` — excludes workflow files (which may legitimately document these patterns)
- `:!*.md.bak` — excludes backup files (defensive; should be gitignored)

### 2. Require branch up-to-date (preventive)

In GitHub Settings → Branches → `main` branch protection rule (FR-150):

Enable **"Require branches to be up to date before merging"** on the existing required status checks. This forces the second of two concurrent PRs to rebase after the first merges, eliminating the condition that creates conflicts.

**Trade-off:** Adds friction — PRs touching overlapping files must rebase before merge. Acceptable because:
- Prevents the exact class of bugs that reached `main` twice.
- Surfaces conflicts at PR time rather than in `main`.
- Most PRs unaffected (only concurrent edits to the same file).

## Implementation Scope

| File | Change | Est. Lines |
|------|--------|-----------|
| `.github/workflows/commitlint.yml` | Add `conflict-check` job | +15 |
| `CLAUDE.md` | Update branch protection table with new status check and up-to-date requirement | +5 |
| GitHub Settings (manual) | Add `conflict-check` as required status check; enable "Require branches to be up to date" | N/A |

## Acceptance Criteria

- [ ] `.github/workflows/commitlint.yml` contains a `conflict-check` job that greps tracked files (excluding workflow definitions) for conflict marker patterns (`<<<<<<<`, `=======`, `>>>>>>>`)
- [ ] The `conflict-check` job fails with a non-zero exit code when conflict markers are present
- [ ] The `conflict-check` job passes (exit 0) when no conflict markers are present
- [ ] `conflict-check` is added as a required status check in GitHub branch protection for `main`
- [ ] "Require branches to be up to date before merging" is enabled on `main` branch protection
- [ ] `CLAUDE.md` branch protection table updated: new `conflict-check` row and "up-to-date" requirement noted
- [ ] Tests: manual verification that a PR branch containing conflict markers triggers CI failure (no unit test — this is a CI-only gate)

## Alternatives Considered

1. **Post-merge scan only (Inquisitor):** Already exists and caught the violation, but is reactive — damage reaches `main` before detection. Rejected: prevention is cheaper than remediation.

2. **GitHub Actions marketplace action (e.g., `check-merge-conflicts`):** Adds an external dependency for a one-line `git grep`. Rejected: the inline script is simpler, auditable, and has no supply-chain risk.

3. **Server-side pre-receive hook:** Not available on GitHub.com (only GitHub Enterprise Server). Not applicable.

4. **CI gate only, without "require up-to-date":** Catches markers in existing PR branches but does not prevent the race condition that creates them. The CI gate is necessary but insufficient alone — the up-to-date requirement is the structural prevention.

## Related

- **FR-150** (`feature-requests/FR-150-branch-protection-main.md`): Branch protection for `main` — this FR extends its rules with a third required status check and the up-to-date requirement
- **Inquisitor Audits XXXVII & XXXVIII**: Identified the violation that motivates this FR
- `.pre-commit-config.yaml` line 21: Existing local `check-merge-conflict` hook (bypassed by server-side merges)
- `.github/workflows/commitlint.yml`: Target file for the new CI job

## Judgement

**Verdict:** APPROVE — Scope frozen, authority granted.

**Reviewed:** 2026-03-08

**Assessment:**
- Scope is clear and minimal: one CI job + one branch protection toggle, both addressing the same root cause.
- Root cause is well-documented with specific audit citations (XXXVII, XXXVIII) and concrete file evidence.
- Acceptance criteria are measurable and verifiable (CI job behavior, GitHub settings, documentation).
- Implementation is feasible — ~15 lines of workflow YAML + a settings toggle. 0.5 day estimate is accurate.
- Aligns with existing architecture: extends `commitlint.yml` (already PR-triggered) and FR-150 branch protection.
- Single responsibility: both changes solve "conflict markers reaching main" — the CI gate catches existing markers, the up-to-date requirement prevents the race condition. Alternative #4 explicitly argues they are interdependent.

**Editorial fixes applied:**
1. AC #1: "all tracked files" → "tracked files (excluding workflow definitions)" to match the `:!.github` exclusion in the implementation.
2. Added clarifying note that `*.md.bak` exclusion is defensive (these files should be gitignored).

**No SPLIT warranted:** The CI gate and up-to-date requirement are two halves of one fix. The FR's own Alternative #4 demonstrates the CI gate alone is insufficient — it catches symptoms but not the race condition. Splitting would produce an incomplete FR.
