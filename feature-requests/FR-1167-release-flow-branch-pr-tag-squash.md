# Feature Request: Release flow documents the branch → PR → tag-the-squash-commit route

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS, R-1..R-4 folded ([judgement](FR-1167-release-flow-branch-pr-tag-squash.judgement.md))
**Requested:** 2026-11-16
**First consumer / first event:** the next agent or operator asked to "release" — at the moment they open `reference/release-checklist.md` or load the `release-version` skill, and at the moment `scripts/release.sh` prints its next-step hint.
**Research:** in-body dispositioned alternatives table — [Alternatives Considered](#alternatives-considered) (FR-890 equivalent committed record)
**Prior art:** [FR-192-draconian-changelog-release-gate.md](FR-192-draconian-changelog-release-gate.md) — created `release.sh` and the checklist's "canonical" section under a direct-push-to-main model; this FR keeps its freeze/bump/aggregate/commit contract and changes only where the tag is made and what the operator is told to do next. [FR-728-session-safe-release-commit-hygiene.md](FR-728-session-safe-release-commit-hygiene.md) (Proposed) — release-commit atomicity against parallel sessions (shared index, `tmp/msg.txt`); orthogonal, untouched here. [FR-1107-changelog-release-sync-context-false-positive.md](FR-1107-changelog-release-sync-context-false-positive.md) (Proposed) — pre-commit version-bump detector false positive; orthogonal. [FR-906-release-tool-slots-to-pypi.md](FR-906-release-tool-slots-to-pypi.md) — executed the old `release.sh → tag → push` route (its lines 74–93); this FR supersedes that route for future releases without rewriting FR-906's historical record. FR-192 rejected docs-only enforcement; this FR is a script correction with docs following, not docs-only.

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
  - "another active instructional surface teaches direct push → record it and amend this FR before editing it; historical FRs are not rewritten"
  - "removing the tag breaks a CI or hook consumer of release.sh → stop enforcement and return to planning; automatic tagging is never retained as a fallback"
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

Folded from judgement R-1..R-4.

1. **`scripts/release.sh`** (D-1)
   - Keep steps 1–5 unchanged: validate fragments, freeze, bump `pyproject.toml` and `yamlgraph/__init__.py`, aggregate, commit with `-F`.
   - **Refuse `main`** before the first filesystem mutation: exit non-zero with a message naming `release/vX.Y.Z`. No other branch-name restriction.
   - **Execute no tag creation** (R-1). The printed handoff may contain a `git tag` *instruction*; tests distinguish `echo`ed text from executed lines.
   - Final output is a concise ordered handoff with a pointer to `reference/release-checklist.md`:
     1. push the branch;
     2. `gh pr create`;
     3. human-authorized squash merge after green PR checks;
     4. get the PR's `mergeCommit.oid` and fetch `origin/main`;
     5. `git tag vX.Y.Z <squash-sha>`;
     6. `git push origin vX.Y.Z`.
2. **`reference/release-checklist.md`** (D-2): the ordered route.
   1. `git fetch origin` and create `release/vX.Y.Z` from `origin/main` in a worktree (`scripts/worktree.sh new vX.Y.Z --prefix release/`); main stays locked.
   2. Run `scripts/release.sh X.Y.Z`, push only the branch, then `gh pr create`.
   3. Wait for the required PR checks (and merge-group checks if any), then the **human merge decision**, then `gh pr merge <N> --squash`.
   4. `gh pr view <N> --json state,mergeCommit`: require `MERGED`, take `mergeCommit.oid`, `git fetch origin`, and check `git merge-base --is-ancestor <sha> origin/main`.
   5. At `<sha>`, check that `pyproject.toml` and `yamlgraph/__init__.py` both read X.Y.Z and that `changelog/X.Y.Z/` exists.
   6. If the tag `vX.Y.Z` already exists, **stop and inspect**; never delete or force it.
   7. `git tag vX.Y.Z <sha>`, then `git push origin vX.Y.Z` (only that tag).
   8. Verify:
      - the tag workflow run (`gh run list --branch vX.Y.Z --workflow CI`) shows `build`, `publish` and `create-release` successful;
      - `gh release view vX.Y.Z`;
      - `https://pypi.org/pypi/yamlgraph/X.Y.Z/json` returns version X.Y.Z.

   No ordinary push-to-main CI run is claimed, because `workflow.yml` triggers on PRs, merge groups and tags. **Recovery** for a merged but untagged freeze uses the same steps 4–8 on that PR's squash SHA, and stops on failed checks. Also remove:
   - the direct-push CI table;
   - every `push --tags`;
   - the normal-path manual `gh release create` (the workflow creates the release).
3. **`.github/skills/release-version/SKILL.md`** (D-3): discovery metadata, the same concise route, and the checklist link. Delete the duplicated manual procedure and the unconditional `gh release create`.
4. **CAP-71 REQ-YG-190** (D-4): text says commit-only preparation plus main refusal; regenerate `ARCHITECTURE.md` with `python scripts/aggregate_capabilities.py`.
5. **Witnesses** (D-5, REQ-YG-190, in `tests/unit/test_changelog_release_sync.py`):
   - **Executed-line parse of `release.sh`.** Comment lines and `echo`/`printf` lines are excluded:
     - no executed `git tag`;
     - `commit -F` is retained;
     - the printed handoff appears in the order branch push → `gh pr create` → `--squash` → `mergeCommit` → `git tag` → `git push origin v`.
   - **Isolated `main` fixture.** A temp git repo:
     - initialised on `main`, with local identity and no hooks;
     - has an initial commit, a real unreleased fragment, and both version files.

     The real script runs there with that cwd. Assert:
     - a non-zero exit;
     - the message names `release/v`;
     - files, HEAD, index and tags are unchanged.
   - **Ordered documentation assertions** for the checklist and the skill, plus absence of `push --tags`.
   - **`test_release_script_commits_and_tags` is replaced**; the other existing witnesses are kept.

**`is_this_a_graph`: No.** This is a deterministic git release handoff with a human merge authorization. The existing shell script, `gh` commands and publishing workflow suffice; no graph or LLM orchestration is proposed.

## Acceptance Criteria

- [ ] AC-01: `release.sh` retains fragment validation, freeze, both version bumps, aggregation and commit-with-`-F`. It executes no tag creation, and prints:
  - branch push → PR creation → human-authorized squash merge → tag the fetched release-PR squash SHA → single-tag push;
  - a checklist pointer.
- [ ] AC-02: The populated isolated `main` fixture exits non-zero with a main-specific refusal naming `release/vX.Y.Z`. Files, HEAD, index and tags are unchanged, and no broader branch-name restriction is added.
- [ ] AC-03: The checklist and skill contain no `push --tags` and no direct-main-push instruction. The ordered route:
  - identifies the exact merged PR and obtains its squash SHA;
  - fetches main, checks ancestry and release metadata;
  - pushes only the intended tag.

  The skill is a concise wrapper.
- [ ] AC-04: The direct-main-push CI table and normal-path manual `gh release create` are removed. Recovery uses the merged PR's exact squash SHA with the same checks, stops on failed checks or an existing tag, and never force-replaces a tag.
- [ ] AC-05: Verification distinguishes PR/merge-group checks from tag CI. It:
  - selects the tag workflow and its successful `build`, `publish` and `create-release` jobs;
  - uses `gh release view` and an exact-version PyPI assertion;
  - claims no ordinary main-push CI run.
- [ ] AC-06: CAP-71 REQ-YG-190 matches the commit-only/main-refusal contract; `ARCHITECTURE.md` is regenerated; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-07: The changed-contract witnesses fail before implementation and `pytest tests/unit/test_changelog_release_sync.py` passes after. RED and GREEN are committed separately, and new tests carry REQ-YG-190.
- [ ] AC-08: A `fix`/`release` changelog fragment and a diary reflection with **Seed:** exist. The FR records implementation status and decisions.
- [ ] AC-09: The FR contains R-1..R-4, the graph-fit answer, the corrected FR-906 disposition and the bounded edit set. No new dependencies, no workflow changes and no live publication.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Docs only — leave `release.sh` tagging | **Rejected.** The local tag points at a branch commit main never contains and blocks the correct tag (`tag already exists`). The defect is in the script, not only in prose. |
| A2 | `release.sh` keeps tagging; operator deletes and re-tags after merge | **Rejected.** Adds a destructive step to every release to undo a step the script should not take. |
| A3 | Automate tagging: a workflow on push to main that tags any `chore(release): vX.Y.Z` squash commit | **Deferred, not in scope.** It would have prevented the v0.6.6 gap, but it gives a workflow write access to tags, adding trusted CI surface; it needs its own FR and judge. Recorded as the follow-up. |
| A4 | `release.sh` does the whole route (push, PR, wait for CI, merge, tag) | **Rejected.** It merges without a human merge decision, which doctrine reserves for the human (Submit step). |
| A5 | Allow direct push to main for release commits | **Rejected.** Contradicts FR-889's OS lock and the squash-merge branch protection. |

## Judgement fold (2026-11-16)

- **R-1:** the no-automatic-tag rule is unconditional, and the edit set is bounded. See the Planned Operations branches and AC-01.
- **R-2:** added the graph-fit answer, corrected the FR-906 disposition and distinguished this FR from FR-192.
- **R-3:** the post-merge route now has the exact squash SHA, an ancestry check, a metadata check, a stop on an existing tag, tag CI distinguished from PR checks, and an exact-version PyPI check. It keeps the human merge decision.
- **R-4:** the witnesses parse executed lines rather than searching for substrings, use the isolated `main` fixture with before/after snapshots, and assert documentation order.
- **Conditions C-2 and C-3** are human gates. C-2 needs the operator to approve the main refusal and moving tagging to the post-merge step before merge. C-3 requires each real release to keep its own merge decision.

## Out of Scope

- Workflow-driven auto-tagging (A3).
- FR-728 release-commit atomicity and FR-1107 version-bump detector.
- The stale editable install in the shared `.venv` after a worktree that ran `pip install -e .` is removed (witnessed 2026-11-16 during the v0.6.7 release); separate defect.
- The failing GitHub Pages build (`docs/investigations/fr1065-resumable-map.md` line 108).

## Related

- PR #765 (v0.6.6 freeze, merged, never tagged until 2026-11-16; tag then deleted because `440c2507` fails CI against the current anthropic SDK, fixed by FR-1156).
- PR #781 (v0.6.7 freeze), tag `v0.6.7` on `8f1fb874`, CI run 43861801565 (build, publish, create-release all green).
- `.github/workflows/workflow.yml` lines 10–12, 142–156 (tag trigger, tag/pyproject version check).
