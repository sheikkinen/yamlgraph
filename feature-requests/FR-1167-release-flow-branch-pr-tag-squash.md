# Feature Request: Release flow documents the branch → PR → tag-the-squash-commit route

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Requested:** 2026-11-16
**First consumer / first event:** the next agent or operator asked to "release" — at the moment they open `reference/release-checklist.md` or load the `release-version` skill, and at the moment `scripts/release.sh` prints its next-step hint.
**Research:** in-body dispositioned alternatives table — [Alternatives Considered](#alternatives-considered) (FR-890 equivalent committed record)
**Prior art:** [FR-192-draconian-changelog-release-gate.md](FR-192-draconian-changelog-release-gate.md) — created `release.sh` and the checklist's "canonical" section under a direct-push-to-main model; this FR keeps its freeze/bump/aggregate/commit contract and changes only where the tag is made and what the operator is told to do next. [FR-728-session-safe-release-commit-hygiene.md](FR-728-session-safe-release-commit-hygiene.md) (Proposed) — release-commit atomicity against parallel sessions (shared index, `tmp/msg.txt`); orthogonal, untouched here. [FR-1107-changelog-release-sync-context-false-positive.md](FR-1107-changelog-release-sync-context-false-positive.md) (Proposed) — pre-commit version-bump detector false positive; orthogonal. [FR-906-release-tool-slots-to-pypi.md](FR-906-release-tool-slots-to-pypi.md) — publishes tool slots, not the release route; no overlap.

## Summary

The written release flow says "push to main, push tags". The real flow — the one every release since v0.6.1 used (PRs #727, #736, #749, #752, #755, #765, #781) — is: `scripts/release.sh X.Y.Z` on a `release/vX.Y.Z` branch, open a PR, squash-merge it, then tag **the squash commit on main** and push the tag; the tag push runs `workflow.yml`'s `build → publish → create-release` jobs. Update `reference/release-checklist.md`, the `release-version` skill, and `scripts/release.sh`'s tagging and next-step hint to the real flow.

## Value Statement

Whoever runs the next release gets a document and a script that lead to a published PyPI package instead of an unpublished, untagged version.

## Problem

Witnessed 2026-11-16:

1. **v0.6.6 was never published.** Its freeze PR #765 merged 2026-10-30 (`440c2507`), but no `v0.6.6` tag was ever pushed, so the tag-triggered `publish` job never ran. PyPI stayed at 0.6.5 for 17 days; the gap was only found when releasing 0.6.7. Nothing in the written flow names "tag the squash commit after merge" as a step — the checklist's tag step assumes the release commit itself lands on main.
2. **`release.sh` tags the wrong commit.** It runs `git tag vX.Y.Z` on the branch commit. Squash merge creates a different commit on main, so that local tag points at a commit main never contains. If pushed, `workflow.yml` would build from a branch-only commit; if not pushed, it blocks the correct `git tag vX.Y.Z <squash-sha>` later (`fatal: tag already exists`).
3. **The documented push is refused.** `release.sh` ends with `Run: git push && git push --tags`; the checklist and skill repeat it. Main is OS-locked (FR-889) and branch-protected (squash merge required, `CLAUDE.md` → Pull Request Conventions), so the direct push to main cannot be the route.
4. **The checklist's "Expected CI behavior on direct push to main" table** documents a scenario that no longer occurs.

## Ideal Result

An operator who only reads `reference/release-checklist.md` (or only the `release-version` skill, or only `release.sh`'s output) performs exactly the steps that publish: freeze on a release branch, PR, squash-merge, tag the squash commit on main, push the tag, verify PyPI. No document or script output instructs a step that is refused or that tags a commit main does not contain.

## Planned Operations

```yaml
probes:
  - "gh pr list --search 'chore(release)' — confirms every recent release used a release-branch PR (decides: PR flow is the de facto route, not a one-off)"
  - "grep -rn 'push --tags' reference/ .github/skills/ scripts/ — enumerates every place teaching the old route (decides edit set)"
  - "grep -n 'git tag' tests/unit/test_changelog_release_sync.py — finds the existing witness pinning the old tag-in-script contract"
branches:
  - "another file teaches direct push → add it to the edit set (partial_remediation)"
  - "removing the tag breaks a CI or hook consumer of release.sh → keep tag, print a warning instead; record deviation"
delegations:
  - "judge.sh: 1 run"
waits:
  - "judge"
commands:
  - scripts/judge.sh
  - pytest tests/unit/test_changelog_release_sync.py
  - python scripts/req_coverage.py --strict
  - python scripts/aggregate_capabilities.py
```

## Proposed Solution

1. **`scripts/release.sh`** — keep steps 1–5 (validate fragments, freeze, bump, aggregate, commit with `-F`). Remove step 6 (`git tag`). Replace the final hint with the remaining route, in order:
   ```
   ✓ Release vX.Y.Z committed on <branch>.
     Next: git push -u origin <branch>
           gh pr create --title "chore(release): vX.Y.Z changelog freeze" --fill
           gh pr merge <N> --squash --delete-branch   (after CI is green)
           git tag vX.Y.Z <squash-commit-on-main> && git push origin vX.Y.Z
   ```
   Refuse to run on `main` (exit non-zero with a message pointing at `release/vX.Y.Z`): the commit it makes must go through a PR.
2. **`reference/release-checklist.md`** — the canonical section becomes the branch → PR → squash-merge → tag-the-squash-commit route, including the post-merge verification (`gh run list --branch vX.Y.Z`, PyPI version check, `gh release view`). Delete the "Expected CI behavior on direct push to main" table and the manual flow's `git push` / `git push --tags` to main. Add one line on recovery: a merged freeze without a tag is unpublished — tag the squash commit, after confirming its CI is green.
3. **`.github/skills/release-version/SKILL.md`** — same route; it stays a discovery wrapper pointing at the checklist.
4. **`capabilities/CAP-71-release-changelog-sync.yaml` REQ-YG-190** — description says the script commits (no tag) and refuses `main`; regenerate `ARCHITECTURE.md`.
5. **Witnesses** in `tests/unit/test_changelog_release_sync.py` (REQ-YG-190):
   - `release.sh` does not run `git tag`; its output hint names `gh pr create` and tagging the squash commit.
   - `release.sh` refuses to run on `main` — executed in a throwaway git repo, asserted by exit code and message.
   - Neither the checklist nor the skill contains `git push --tags` or `git push && git push --tags`; both name `release/v`, `--squash` and the squash commit as the tag target.
   - The existing `test_release_script_commits_and_tags` is replaced: it pins the retired contract.

## Acceptance Criteria

- [ ] AC-01: `scripts/release.sh` contains no `git tag` invocation; its final output names push branch, `gh pr create`, squash merge, and tagging the squash commit on main, in that order.
- [ ] AC-02: `scripts/release.sh` exits non-zero on branch `main` before modifying any file; witnessed by executing it in a temp git repo.
- [ ] AC-03: `reference/release-checklist.md` and `.github/skills/release-version/SKILL.md` contain no `push --tags` and no instruction to push to main; both document release branch → PR → squash merge → tag the squash commit → push the tag → verify PyPI.
- [ ] AC-04: The checklist's "direct push to main" CI table is removed; a recovery line covers a merged-but-untagged freeze.
- [ ] AC-05: CAP-71 REQ-YG-190 text matches the new contract; `ARCHITECTURE.md` regenerated; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-06: `pytest tests/unit/test_changelog_release_sync.py` passes; RED and GREEN committed separately.
- [ ] AC-07: Changelog fragment (`type: fix`, `scope: release`) and diary entry.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Docs only — leave `release.sh` tagging | **Rejected.** The local tag points at a branch commit main never contains and blocks the correct tag (`tag already exists`). The defect is in the script, not only in prose. |
| A2 | `release.sh` keeps tagging; operator deletes and re-tags after merge | **Rejected.** Adds a destructive step to every release to undo a step the script should not take. |
| A3 | Automate tagging: a workflow on push to main that tags any `chore(release): vX.Y.Z` squash commit | **Deferred, not in scope.** It would have prevented the v0.6.6 gap, but it gives a workflow write access to tags, adding trusted CI surface; it needs its own FR and judge. Recorded as the follow-up. |
| A4 | `release.sh` does the whole route (push, PR, wait for CI, merge, tag) | **Rejected.** It merges without a human merge decision, which doctrine reserves for the human (Submit step). |
| A5 | Allow direct push to main for release commits | **Rejected.** Contradicts FR-889's OS lock and the squash-merge branch protection. |

## Out of Scope

- Workflow-driven auto-tagging (A3).
- FR-728 release-commit atomicity and FR-1107 version-bump detector.
- The stale editable install in the shared `.venv` after a worktree that ran `pip install -e .` is removed (witnessed 2026-11-16 during the v0.6.7 release); separate defect.
- The failing GitHub Pages build (`docs/investigations/fr1065-resumable-map.md` line 108).

## Related

- PR #765 (v0.6.6 freeze, merged, never tagged until 2026-11-16; tag then deleted because `440c2507` fails CI against the current anthropic SDK, fixed by FR-1156).
- PR #781 (v0.6.7 freeze), tag `v0.6.7` on `8f1fb874`, CI run 43861801565 (build, publish, create-release all green).
- `.github/workflows/workflow.yml` lines 10–12, 142–156 (tag trigger, tag/pyproject version check).
