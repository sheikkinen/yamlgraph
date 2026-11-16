# Judgement: FR-1167 Release flow documents the branch -> PR -> tag-the-squash-commit route

**Verdict:** APPROVED WITH REVISIONS — Correct the release handoff, but implementation authority activates only after R-1 through R-4 are folded into the committed FR; human approval remains required for merging enforcement changes and publishing releases.

**Reviewed against:** Committed `feature-requests/FR-1167-release-flow-branch-pr-tag-squash.md`; its cited `scripts/release.sh`, `reference/release-checklist.md`, `.github/skills/release-version/SKILL.md`, `tests/unit/test_changelog_release_sync.py`, `capabilities/CAP-71-release-changelog-sync.yaml`, and `.github/workflows/workflow.yml` (lines 1-210); prior-art `feature-requests/FR-192-draconian-changelog-release-gate.md`, `feature-requests/FR-728-session-safe-release-commit-hygiene.md`, `feature-requests/FR-1107-changelog-release-sync-context-false-positive.md`, and `feature-requests/FR-906-release-tool-slots-to-pypi.md`; doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md` (cited doctrine clauses), and `CLAUDE.md` (release and PR conventions, lines 98-109). Tracking and clean working-tree status were checked. No author narrative, working notes, live GitHub records, or PyPI responses were consumed. The historical PR/run claims are FR assertions, not independently verified publication evidence.

**Prior art:** FR-192, FR-728, FR-1107, FR-906 — dispositioned in R-2 and in the FR's Prior art line.

## What is sound

The strongest case against this proposal is that another manual handoff cannot guarantee publication: the incident in FR-1167:23 was a missed tag, and A3 would automate that boundary. Nevertheless, A3 adds trusted CI write behavior, whereas this proposal removes an objectively wrong local tag and a misleading next-step instruction without changing the publishing workflow (FR-1167:24,55-65,89). That smaller correction is worth shipping; it must not be described as automatic prevention of all unpublished releases.

The defect does not depend on accepting the incident narrative. The committed script tags its current commit and prints an unrestricted tag push (`scripts/release.sh:33-37`), while the repository requires squash merging (`CLAUDE.md:98-100`). The tag-triggered build checks the tagged source version, then publishes and creates a release (`.github/workflows/workflow.yml:142-156,179-200`). Keeping the freeze/bump/aggregate/commit sequence and changing the handoff is a coherent repair.

| Criterion | Finding and evidence |
|---|---|
| Scope | Minimal core correction with directly dependent documentation, requirement text, and witnesses (FR-1167:55-71). The open-ended edit-set branch and retain-tag fallback must be removed (FR-1167:40-41; R-1). |
| Consistency | The proposed printed `git tag` command is compatible with banning an executed tag command, but not a blanket substring ban (FR-1167:61,68,75). Retaining automatic tagging contradicts that contract (FR-1167:41; R-1). |
| Measurability | Most ACs name inspectable files or commands (FR-1167:75-81). Target acquisition, pre-tag CI evidence, and exact publication verification need executable detail, not an unexplained placeholder or generic green-CI assertion (FR-1167:60-64; R-3). |
| Feasibility | Existing Git, gh, Bash, and pytest suffice; no dependency or workflow change is needed. A newly created squash object must be fetched before local tagging. The workflow has PR, merge-group, and tag triggers, not an ordinary main-push trigger (`.github/workflows/workflow.yml:3-12`; R-3). |
| Architecture alignment | Reuse the existing release script and REQ-YG-190 rather than introduce a release framework (`scripts/release.sh:6-31`; `capabilities/CAP-71-release-changelog-sync.yaml:25-35`). A discovery wrapper should not retain a second, divergent manual release procedure (FR-1167:65; `.github/skills/release-version/SKILL.md:20-87`; R-3). |
| Single responsibility | One release-handoff concern. FR-728's shared-index/message race and FR-1107's diff detector remain separate, as FR-1167:95-97 states. No SPLIT is needed. |
| Strategic classification | **Pattern documentation**, with a necessary correction to existing process tooling; existing abstractions suffice. This is neither a framework primitive nor a new contrib graph. The alternatives are substantive, but the research record needs the explicit graph-fit answer and an accurate disposition of FR-906 (R-2). |
| Testability | Direct failing witnesses can replace the structural tag assertion (`tests/unit/test_changelog_release_sync.py:184-189`). The main-branch subprocess fixture must contain fragments and assert the specific refusal plus unchanged state, so a missing directory or BSD-sed failure cannot masquerade as the new guard (R-4). |

## Required revisions

### R-1: Make the no-automatic-tag contract unconditional and bounded

Delete the Planned Operations branch that retains tagging when a consumer breaks (FR-1167:41). Such a discovery must stop enforcement and return the dependency to planning; a warning does not cure the wrong tag target. Replace the open-ended "add it to the edit set" branch (FR-1167:40) with "record additional active instructional surfaces and amend the FR before editing them"; historical FRs are not active instructions to rewrite.

Define AC-01 as **no executed tag-creation command in release.sh**, while explicitly allowing the printed post-merge `git tag` instruction. Preserve steps 1-5 and both existing version bumps. Add the main refusal before the first filesystem mutation, with a named message pointing to `release/vX.Y.Z`; do not introduce an unrequested requirement that every other branch name match that pattern.

### R-2: Complete the research disposition without inventing another research project

Keep the five alternatives at FR-1167:87-91. Add the explicit answer: "`is_this_a_graph`: No. This is a deterministic Git release handoff with human merge authorization; the existing shell script, gh commands, and publishing workflow suffice. No new graph or LLM orchestration is proposed."

Correct the FR-906 disposition at FR-1167:9: it executed the old `release.sh -> tag -> push` contract, rather than having no release-route overlap (`feature-requests/FR-906-release-tool-slots-to-pypi.md:74-93`). State that this FR supersedes that route for future releases without rewriting FR-906's historical execution. Preserve the substantive disagreement with automation: A3 removes the missed-tag handoff but is deferred because it adds CI write authority. Keep FR-192's historical rejection of docs-only enforcement distinguished from this proposal's script correction.

This is a substantive existing alternatives record, not an absent or strawman research field; however, the required graph-fit and precedent details must be committed before authority activates (`.github/skills/judge-fr/doctrine.md:118-129`).

### R-3: Specify a usable, human-authorized post-merge route

Add a concrete checklist sequence that creates `release/vX.Y.Z` from an up-to-date fetched `origin/main` without requiring writes in the locked main checkout, runs the script, pushes only that branch, and opens the release PR. Put an explicit human merge decision between green required PR checks and the example squash-merge command; "CI is green" alone is not merge authorization (FR-1167:60,90; `.github/copilot-instructions.md:213`).

After merge, obtain the exact release PR's `mergeCommit.oid` with `gh pr view <N> --json state,mergeCommit`, require merged state, fetch `origin/main`, and check that the selected commit is an ancestor of fetched main. Do not tag the release branch or an arbitrary latest main commit. Verify `pyproject.toml` and `yamlgraph/__init__.py` at that exact commit agree with X.Y.Z and that its frozen changelog directory exists; then create `vX.Y.Z` at that SHA and push only `origin vX.Y.Z`. An existing tag must stop the sequence for inspection, not invite deletion or force replacement.

Identify pre-tag evidence as the release PR's successful required checks and any applicable merge-group checks. Do not instruct the reader to wait for an ordinary main-push CI run: the cited workflow does not trigger one. Tag publication remains separately gated by its own test/build chain (`.github/workflows/workflow.yml:3-12,142-144`).

Make post-tag verification select the tag workflow and confirm successful `build`, `publish`, and `create-release`, inspect `gh release view vX.Y.Z`, and query the version-specific PyPI record for `yamlgraph/X.Y.Z`, asserting that returned version. A run appearing in a list or some package version existing is insufficient. Apply the same exact-commit checks to merged-but-untagged recovery, and stop on failed CI; do not suggest changing the release target to bypass a failure.

Keep script output a concise ordered handoff with a checklist pointer, explicitly identifying the fetched release-PR squash SHA as its tag target. Reduce the skill to discovery metadata, the same concise route, and the canonical checklist link. Remove its duplicated manual procedure and unconditional `gh release create` instruction; remove the checklist's normal-path manual release-creation fallback as well (`.github/skills/release-version/SKILL.md:20-87`; `reference/release-checklist.md:123-126`). The existing workflow owns normal release creation.

### R-4: Make witnesses condemn the changed seam, not incidental failure

Specify the main-refusal fixture as an isolated Git repository explicitly initialized on `main`, with an initial commit, a real unreleased fragment, both version files, and before/after snapshots of files, HEAD, index, and tags. Invoke the real script with that repository as cwd. Assert nonzero exit, the main-specific message naming `release/vX.Y.Z`, and unchanged snapshots. Do not run the script against the working repository or depend on global Git identity or hooks.

Replace `test_release_script_commits_and_tags` with assertions that retain commit-with-`-F`, reject an executed tag command, permit the printed tag instruction, and check handoff order. Specify how quoted output is distinguished from executed shell commands; a global `assert "git tag" not in content` is expressly invalid. Retain the existing freeze, bump, aggregation, and empty-fragment witnesses and update obsolete test descriptions.

Use focused ordered documentation assertions for branch -> PR -> human-authorized squash merge -> exact fetched squash target -> single-tag push -> version-specific publication verification. A bag of unrelated occurrences of `release/v`, `--squash`, and "squash commit" does not witness that sequence (FR-1167:70). New witnesses retain REQ-YG-190 marking. Commit RED and GREEN separately as already required; no live merge, tag push, or publication is needed to validate this FR.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/release.sh`: early main refusal, removal of automatic tagging, replacement handoff output; existing steps 1-5 retained |
| D-2 | `reference/release-checklist.md`: canonical and manual route correction, exact squash-target acquisition, recovery and publication verification |
| D-3 | `.github/skills/release-version/SKILL.md`: concise discovery wrapper pointing at D-2 |
| D-4 | `capabilities/CAP-71-release-changelog-sync.yaml`: REQ-YG-190 contract and directly dependent descriptive wording; generated `ARCHITECTURE.md` |
| D-5 | `tests/unit/test_changelog_release_sync.py`: focused REQ-YG-190 witnesses and directly stale descriptions |
| D-6 | FR-1167 research/revision folds and implementation record; one `changelog/unreleased/` fix/release fragment and one `docs/diary/` reflection with **Seed:** |

Not authorized: workflow changes or automatic tagging; automated human merge decisions; a real release/version bump/tag push as part of this fix; tag deletion or force movement; branch-protection or lock changes; FR-728 message/index atomicity; FR-1107 detector changes; BSD/GNU-sed portability refactoring; new graphs, dependencies, capability IDs, or generic release orchestration; editable-install or Pages repairs; rewriting historical FRs; additional instructional surfaces without a scope amendment.

## Revised acceptance criteria

- [ ] AC-01: `release.sh` retains its existing fragment validation, freeze, both version bumps, aggregation, and commit-with-`-F`; it executes no tag creation and prints branch push -> PR creation -> human-authorized squash merge -> tagging the fetched release-PR squash SHA on main -> single-tag push, with a canonical checklist pointer.
- [ ] AC-02: The populated isolated `main` fixture exits nonzero with a main-specific refusal naming `release/vX.Y.Z`; files, HEAD, index, and tags are unchanged. No broader branch-name restriction is introduced.
- [ ] AC-03: The checklist and skill contain no `push --tags` or direct-main-push instructions. Their ordered route identifies the exact merged PR, obtains its squash SHA, fetches main, checks ancestry and release metadata, and pushes only the intended tag. The skill is a concise wrapper, not a duplicated manual procedure.
- [ ] AC-04: The direct-main-push CI table and normal-path manual GitHub release creation are removed. Recovery uses the merged release PR's exact squash SHA and the same checks, stops on failed checks or an existing tag, and never force-replaces a tag.
- [ ] AC-05: Documented verification distinguishes pre-merge/merge-group checks from tag CI; selects the tag workflow and successful publishing jobs; uses `gh release view` and an exact-version PyPI assertion. It does not claim that an ordinary main-push CI run exists.
- [ ] AC-06: CAP-71 REQ-YG-190 and directly dependent descriptions match the commit-only preparation/main-refusal contract; `ARCHITECTURE.md` is regenerated; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-07: Focused changed-contract witnesses fail before implementation for the intended assertions, then `pytest tests/unit/test_changelog_release_sync.py` passes. RED and GREEN are separately committed; new tests carry REQ-YG-190 through the repository's existing marking pattern.
- [ ] AC-08: A fix/release changelog fragment and a diary reflection with **Seed:** exist; FR-1167 records implementation status and decisions, including any stopped dependency discovery rather than silently retaining automatic tagging.
- [ ] AC-09: The committed FR contains all four revisions, the explicit graph-fit answer, corrected FR-906 disposition, and the bounded edit set. No new dependencies, workflow modifications, or live publication operations are introduced.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 must be folded into the committed FR before implementation begins; this draft does not independently promote itself to the canonical judgement. | GATE |
| C-2 | Human reviewer question: **Do you approve the early main-refusal guard and the transfer of tag creation from the release script to a human-authorized post-merge handoff?** Obtain an explicit affirmative review before merging this enforcement-infrastructure change (`.github/skills/judge-fr/doctrine.md:98-101`). | GATE |
| C-3 | Human release question: **Do you authorize merging this particular release PR and publishing its version?** The documented flow must preserve this decision; this judgement grants neither release merge nor publishing authority. | GATE |
| C-4 | Preserve the publishing workflow, existing hooks, main lock, and squash requirement. If a dependency requires automatic tagging, stop and amend scope instead of using the proposed fallback. | GATE |
| C-5 | Tests may mutate only isolated fixtures. No real release, remote push, tag deletion/retargeting, or merge is authorized to demonstrate the documentation fix. | GATE |
| C-6 | Separate RED/GREEN evidence, targeted tests, requirement coverage, and applicable existing formatting/lint hooks must be green before submission; FR implementation status, fragment, and diary are required. | GATE |

Authority granted: Conditional authority to implement only D-1 through D-6 after the committed FR incorporates R-1 through R-4; human review gates merging the enforcement change, and each real release requires its own human authorization.
