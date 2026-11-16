---
name: release-version
description: "Release a new YAMLGraph version. Use when: bumping version, creating a release, tagging, pushing a release, freezing changelog, or handling pre-commit hook cascades during release."
argument-hint: "version number like '0.4.62'"
---

# Release Version

Discovery wrapper. The canonical procedure, including checks, recovery and verification, is [`reference/release-checklist.md`](../../../reference/release-checklist.md); follow it, not this summary.

## Route (FR-1167)

1. `git fetch origin`, then `scripts/worktree.sh new vX.Y.Z --prefix release/`. This branches `release/vX.Y.Z` from origin/main; main stays locked.
2. `scripts/release.sh X.Y.Z`: freezes, bumps and commits. It refuses to run on main and does not tag.
3. `git push -u origin release/vX.Y.Z` and `gh pr create`.
4. Required PR checks green, then **the human merge decision**, then `gh pr merge <N> --squash --delete-branch`.
5. Get `mergeCommit` from `gh pr view <N> --json state,mergeCommit` and `git fetch origin`. Confirm that `git merge-base --is-ancestor <sha> origin/main` succeeds and that the version files read X.Y.Z at `<sha>`.
6. `git tag vX.Y.Z <sha>`, then `git push origin vX.Y.Z`. If the tag already exists, stop.
7. Verify the tag CI run (`build`, `publish`, `create-release`), `gh release view vX.Y.Z`, and the exact version on PyPI.

The tag push publishes. A merged release PR without a tag publishes nothing; see the checklist's Recovery section.

Hook failures during step 2, phantom requirements and multi-line commit messages: see the checklist.
