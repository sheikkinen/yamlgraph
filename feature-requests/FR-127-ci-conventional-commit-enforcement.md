# Feature Request: CI Conventional Commit Enforcement

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-07

## Summary

Add a GitHub Actions workflow that enforces Conventional Commits on PR titles, closing the enforcement gap where server-side GitHub merge commits bypass local `commit-msg` hooks.

## Value Statement

All contributors get consistent conventional commit enforcement regardless of merge path, preventing violations like `eeb0aa7` from reaching the default branch.

## Problem

GitHub PR merge/squash commits are created server-side and never pass through local pre-commit hooks. The current enforcement relies entirely on `conventional-pre-commit` (compilerla) in the `commit-msg` hook stage, which only guards local commits. This creates a gap:

- **Local commits:** ✅ Enforced by `conventional-pre-commit`, `feat-requires-fr`, `changelog-required` hooks
- **PR merge commits:** ❌ No enforcement — server-side merge bypasses all local hooks
- **Revert commits:** ❌ Git's auto-generated `Revert "..."` format violates the convention

This was flagged by the Inquisitor in Audits VI and VII against commits `eeb0aa7` (`FR-114: Feature Request: Integrate enforce_worktree.sh...`) and `63db5d3` (`Revert "FR-114: ..."`). Both lack a conventional type prefix.

Scripture: *"audit without blocking mechanism = post-mortem before incident."*

## Proposed Solution

Add `.github/workflows/commitlint.yml` with two steps:

1. **Validate PR title** against Conventional Commits format using `action-semantic-pull-request@v5`
2. **Enforce `FR-XXX` reference** on `feat` PRs via inline script (parity with local `feat-requires-fr` hook)

```yaml
# .github/workflows/commitlint.yml
name: Conventional Commit Check

on:
  pull_request:
    types: [opened, edited, synchronize, reopened]

permissions:
  pull-requests: read

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - name: Validate PR title
        uses: amannn/action-semantic-pull-request@v5
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          types: |
            feat
            fix
            chore
            docs
            refactor
            test
            ci
            perf
            style
            build
            revert
          requireScope: false
          subjectPattern: ^.+$
          subjectPatternError: "PR title must have a subject after the type prefix"

      - name: feat requires FR-XXX
        if: startsWith(github.event.pull_request.title, 'feat')
        env:
          PR_TITLE: ${{ github.event.pull_request.title }}
        run: |
          if ! echo "$PR_TITLE" | grep -qE 'FR-[0-9]+'; then
            echo "::error::feat PRs must reference FR-XXX in the title"
            echo "Example: feat(streaming): FR-030 add subgraphs parameter"
            exit 1
          fi
```

### Design Decisions

**Why `action-semantic-pull-request` over `commitlint`?**
- No config file needed (no `commitlint.config.js` in this repo)
- Validates PR title directly (maps to squash-merge message)
- Well-maintained, purpose-built for this exact use case
- Type list stays consistent with `.pre-commit-config.yaml` line 142

**Revert type: explicitly allowed.**
Git's auto-generated `Revert "..."` messages are common during rollbacks. Rather than forcing contributors to rewrite revert messages as `fix:` or `chore:`, we add `revert` as an allowed type in both:
- The CI workflow type list (this FR)
- The local `conventional-pre-commit` args (update `.pre-commit-config.yaml` line 142 for parity)

This normalizes revert handling across both enforcement paths.

**Merge strategy: squash-only required.**
The PR title becomes the commit message only when "Squash and merge" is used. For this workflow to be a complete enforcement gate:
- Repository settings must restrict merge strategies to **squash merge only** on the default branch
- This is a manual GitHub settings step (Settings → General → Pull Requests → uncheck "Allow merge commits" and "Allow rebase merging")
- Document this requirement in `CLAUDE.md`

If non-squash merges are allowed, PR title validation has a remaining gap: regular merge commits use `Merge pull request #N...` and rebase merges use the original commit messages. This FR's scope is PR title enforcement; original commit messages are already enforced by the local `commit-msg` hook.

## Acceptance Criteria

- [ ] `.github/workflows/commitlint.yml` exists and runs on `pull_request` events (`opened`, `edited`, `synchronize`, `reopened`)
- [ ] Workflow validates PR title matches Conventional Commits format via `action-semantic-pull-request@v5`
- [ ] Allowed types match the local `conventional-pre-commit` hook types plus `revert`: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `perf`, `style`, `build`, `revert`
- [ ] `revert` added to local `conventional-pre-commit` args in `.pre-commit-config.yaml` for parity
- [ ] PRs with non-conforming titles show a failing check
- [ ] PRs with conforming titles pass the check
- [ ] `feat` PRs must include `FR-XXX` reference in title (second workflow step with inline script)
- [ ] `CLAUDE.md` updated: note that PR titles must follow Conventional Commits and that squash merge is the required merge strategy
- [ ] CHANGELOG.md updated

## Alternatives Considered

1. **Run `commitlint` CLI in CI against merge commit**: Requires installing `commitlint` + Node.js, adding a `commitlint.config.js`, and only works after the merge commit exists. More complex, slower, and detects violations after the fact rather than preventing them.

2. **GitHub Actions `commitlint` action**: Heavier dependency (Node.js, npm install). The `action-semantic-pull-request` action is purpose-built for PR title validation and needs no config file.

3. **Do nothing, rely on Inquisitor**: The Inquisitor detects violations post-commit but cannot prevent them. Detection without blocking is audit, not enforcement.

4. **Force reverts to use `fix:`/`chore:` prefix**: Rejected — adds friction to a time-sensitive operation (rollbacks). `revert` is a standard Conventional Commits type and should be allowed.

## Judgement

**Verdict:** APPROVED — 2026-03-07

**Security fix applied:** The original inline script used `TITLE="${{ github.event.pull_request.title }}"` which directly interpolates user-controlled input into bash — a known GitHub Actions script injection vector (see [GitHub docs on script injection](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#understanding-the-risk-of-script-injections)). Fixed to use `env:` block, passing the PR title as `$PR_TITLE` environment variable. No scope change.

**Notes:**
- Type "Bug" is defensible: the enforcement gap in `commit-msg` hooks IS the defect.
- Squash-merge-only requirement is correctly scoped as a manual settings step, not automated.
- The `revert` type addition to `.pre-commit-config.yaml` is a clean parity fix.
- Line references (e.g., "line 142") are approximate but intent is unambiguous.

**Scope frozen.** Authority granted to implement.

## Related

- **FR-038**: `feat-requires-fr` hook (local enforcement of FR-XXX in feat commits)
- **FR-076**: Chaplain Inquisitor (post-commit audit that detected these violations)
- **FR-077**: `changelog-required` hook (local enforcement of CHANGELOG.md)
- **Commits**: `eeb0aa7` (violation), `63db5d3` (compounding revert violation)
- **Inquisitor Audits**: VI, VII (where violations were flagged)
- `.pre-commit-config.yaml` lines 137–160 (existing local hook enforcement)
- `.github/workflows/` (existing CI: `workflow.yml` for PyPI release, `daily-digest.yml`)
