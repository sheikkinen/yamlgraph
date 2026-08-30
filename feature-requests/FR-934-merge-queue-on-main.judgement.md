# Judgement: FR-934 Enable the GitHub merge queue on main

**Verdict:** APPROVED WITH REVISIONS — the merge queue is the smallest platform-native cure for the measured integration toll, but authority activates only after the FR resolves its docs-only cost contradiction, defines the exact required-context and settings contracts, and adds a test-first rollout with human review.

**Prior art:** the only filename-noun hit is the parent FR itself; its prior-art record is dispositioned in the FR body and confirmed here — FR-889 owns the worktree→PR substrate and §4d deadlock cure, FR-919 owns the doc-only skip this judgement's R-2 policy narrows, FR-902/FR-927 are the cautionary provisioning-automation precedent, and FR-935 is the sequenced companion kept out of this scope (C-6). No prior or REJECTED FR proposes governing the merge boundary.

**Reviewed against:** `feature-requests/FR-934-merge-queue-on-main.md`; `docs/plan-research-merge-queue.md`; `feature-requests/research-briefs/fr934-merge-integration-toll-brief.md`; `docs/diary/diary-2026-08-30-the-parallel-writers-and-the-serial-door.md`; `feature-requests/FR-889-os-enforced-main-write-lock.md`; `feature-requests/FR-889-os-enforced-main-write-lock.judgement.md`; `feature-requests/FR-919-ci-doc-only-skip.md`; `feature-requests/FR-919-ci-doc-only-skip.judgement.md`; `feature-requests/FR-902-session-worktree-lifecycle.judgement.md`; `feature-requests/FR-927-retire-fr902-lane-guard-hooks.md`; `feature-requests/FR-927-retire-fr902-lane-guard-hooks.judgement.md`; `feature-requests/FR-935-deny-admin-merge-outside-break-glass.md`; `.github/workflows/workflow.yml`; `.github/workflows/commitlint.yml`; `tests/unit/test_commitlint_workflow.py`; `tests/unit/test_branch_protection_docs.py`; `CLAUDE.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-893-diary-trap-census.judgement.md`; `feature-requests/FR-898-session-accountability-report.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The problem and consumer are concrete. FR-934 names the next two parallel-lane PRs as the first event and ties the proposal to a 78-commit, 20-worktree operating window (`feature-requests/FR-934-merge-queue-on-main.md:8-12`, `:54-58`). The diary independently identifies strict up-to-date protection as the serial integration boundary left after FR-889 made parallel writing safe (`docs/diary/diary-2026-08-30-the-parallel-writers-and-the-serial-door.md:24-42`). This is not speculative process gardening.

The selected mechanism is minimal and architecture-aligned. The committed research identifies GitHub's native queue as the platform feature that stacks, validates, and lands pull requests without author-driven rebases, while preserving squash merging (`docs/plan-research-merge-queue.md:23-37`). The current repository already has the required worktree-to-PR substrate and three named required contexts (`CLAUDE.md:390-410`). Adding the platform event to the workflows that own those contexts, changing the corresponding repository setting, and documenting the resulting ritual are one integration concern rather than an orthogonal bundle. FR-935 correctly keeps command-boundary enforcement of `--admin` in a separate, sequenced FR (`feature-requests/FR-934-merge-queue-on-main.md:111-114`, `:158-159`).

The main CI composition is feasible. `workflow.yml` already treats every non-`pull_request` event as code-bearing (`.github/workflows/workflow.yml:19-30`), and its matrix job always exists while only its expensive steps are conditionally gated (`.github/workflows/workflow.yml:61-103`). A `merge_group` trigger therefore reaches the existing `test (3.11)` and `test (3.13)` contexts without a second matrix implementation.

The alternatives are materially distinct: local rebasing automation, serialization, continued strict-plus-admin operation, manual batching, and the native queue are each dispositioned (`feature-requests/FR-934-merge-queue-on-main.md:142-150`). Strategically, this is **pattern documentation / repository integration policy**, not a YAMLGraph framework primitive: one repository consumes an existing GitHub abstraction, and no graph, runtime, provider, or public package capability is needed.

The proposal is directly testable once amended. Existing tests already parse `commitlint.yml` and pin its `commitlint` job and pull-request trigger (`tests/unit/test_commitlint_workflow.py:30-92`), while the branch-protection documentation tests already own the `CLAUDE.md` contract (`tests/unit/test_branch_protection_docs.py:44-83`). The missing witnesses can extend those patterns and fail specifically because `merge_group` handling and post-queue documentation are absent.

## Required revisions

### R-1: Add the missing Ideal Result and complete the research substance record

Insert `## Ideal Result` between Problem and Proposed Solution. State the observable end state: two independently ready PRs can be enqueued without head-branch updates, each required context reports on the queue candidate, the queue lands them in order by squash, and the repository returns to strict protection if queue validation cannot report.

Add an explicit `is_this_a_graph` answer and preserved disagreement to the cited research record or FR body. The correct classification is: "No; this is GitHub repository policy and CI event wiring, not an LLM pipeline." The existing research and alternatives provide genuine solution classes and precedent, but neither the FR nor its research record answers `is_this_a_graph`, and neither preserves the substantive disagreement over whether docs-only queue candidates should pay for the full matrix (`.github/skills/judge-fr/doctrine.md:118-128`; `feature-requests/TEMPLATE.md:11-20`, `:49-56`).

### R-2: Resolve the docs-only cost contradiction through an explicit human decision

The cited problem brief requires that docs-only PRs "must not start paying for the full test matrix" (`feature-requests/research-briefs/fr934-merge-integration-toll-brief.md:58-63`), while FR-934 deliberately makes every `merge_group` event run the full matrix and calls the resulting FR-919 saving preserved (`feature-requests/FR-934-merge-queue-on-main.md:81-86`, `:132-136`). Both cannot be true end to end.

**Question for the human cost/policy owner:** choose and record one option in FR-934 and align the cited brief, Problem, Proposed Solution, and AC-05 to it:

1. **PR-only saving (recommended):** docs-only pull-request validation remains cheap, but the combined queue candidate runs one full final matrix because it is the integration boundary. Narrow the preservation claim accordingly.
2. **End-to-end saving:** retain the brief's stronger constraint and specify a merge-group-safe changed-file classifier, including mixed queue groups, before authority. Add deterministic fixtures proving a docs-only group skips while any group containing code runs the matrix.

The Judge does not absorb this spend-versus-assurance decision. Authority remains inactive until the human choice is recorded in the FR.

### R-3: Define one exact `commitlint` required-context reporter

Replace "an always-success no-op job step" with the exact job/step shape. The existing required context is emitted by job id `commitlint`, but that job is currently excluded outside pull-request events (`.github/workflows/commitlint.yml:19-22`). The amendment must keep the same `commitlint` job id/context, remove its PR-only job-level exclusion, guard every step that reads `github.event.pull_request` with `github.event_name == 'pull_request'`, and add a merge-group-only no-op step in that same job. Do not introduce a differently named check and assume branch protection will treat it as `commitlint`.

Add RED-first YAML-shape tests, preferably in `tests/unit/test_commitlint_workflow.py` and a focused FR-934 workflow test, proving:

- both workflows trigger on `merge_group`;
- the `commitlint` job itself runs for `merge_group`;
- PR-title validation steps remain PR-only;
- the merge-group no-op exists in the same `commitlint` job;
- `workflow.yml` still emits the two existing matrix context names and follows the R-2 policy selected for merge groups.

The tests must carry existing requirement markers and fail for missing queue wiring, not for fixtures or imports (`.github/copilot-instructions.md:222`; `.github/skills/judge-fr/doctrine.md:58-61`).

### R-4: Pin the repository-setting mutation, readback, rollout, and rollback contracts

Replace "small wait time," "timeout >= the slow path," and "applied via `gh api`" with exact values and commands. Record:

- the API endpoint or GraphQL mutation and complete payload used to enable the queue;
- squash merge method, minimum group size, grouping/wait value, non-failing-only policy, and numeric status-check timeout;
- the exact readback endpoint/query and response fields proving each queue property plus `strict: false`;
- the rollback operation that disables the queue and restores `strict: true`.

Do not assume `repos/:owner/:repo/branches/main/protection` exposes every merge-queue field merely because it exposes strict required-check state. The acceptance artifact must use the API surface that actually returns each asserted property.

**Question for the human reliability/spend owner:** select the numeric wait and timeout values after citing the current slowest successful required-test duration and the chosen safety margin. The FR may recommend values, but the human-owned tuning decision must be recorded before settings are changed.

Freeze the rollout order: first merge the tested workflow and documentation changes under the existing strict regime; then obtain human review; then enable the queue and disable strict in one controlled settings operation; then read the settings back; only then enqueue witness PRs. If any required context fails to report on the first merge group, stop the rollout and execute the recorded rollback before further merges.

### R-5: Make live witnesses mechanically auditable

Replace AC-02 through AC-05's narrative evidence with exact artifacts and assertions:

- record the merge-group check-suite URL and the three check-run names/conclusions for the first queue candidate;
- paste a minimal, non-secret settings readback containing all fields from R-4 into FR-934 implementation notes;
- for each of two parallel-lane witness PRs, record PR URL, head SHA at enqueue, queue-entry event, merge-group run URL, merged-at timestamp, and final squash commit; prove no synchronize/head-SHA change occurred after enqueue;
- prove no `--admin` use with a named audit source and bounded event/time query, not an unspecified "session audit log";
- make the docs-only witness assert the exact policy selected in R-2;
- record explicit human review of both workflow diffs and the repository-setting mutation.

Add the repo-required diary reflection to the acceptance criteria. The current FR asks for a changelog fragment but omits the final reflection required by Scripture (`.github/copilot-instructions.md:24`, `:238`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-934-merge-queue-on-main.md` and its cited research/brief artifacts: fold R-1 through R-5, the two human decisions, implementation notes, settings readback, witness links, and any deviations. |
| D-2 | `tests/unit/test_commitlint_workflow.py` and one focused FR-934 workflow/settings-documentation test if needed: RED-first queue-trigger, exact-context, event-guard, and documentation assertions. |
| D-3 | `.github/workflows/workflow.yml`: add only the `merge_group` trigger and the merge-group behavior selected under R-2; preserve existing required matrix context names and release behavior. |
| D-4 | `.github/workflows/commitlint.yml`: add the `merge_group` trigger and make the existing `commitlint` job report safely on that event without executing PR-payload steps. |
| D-5 | GitHub protection for literal branch `main`: require the merge queue with the exact reviewed settings and set required-status strictness to false, with a recorded rollback to the current strict regime. |
| D-6 | `CLAUDE.md` and `tests/unit/test_branch_protection_docs.py`: document and pin the post-queue branch-protection truth and plain `gh pr merge --squash` enqueue ritual. |
| D-7 | `changelog/unreleased/*.md`: one `type: feat` fragment for FR-934. |
| D-8 | `docs/diary/*.md`: FR-934 implementation reflection with a Seed. |

Not authorized: any `.github/hooks/` or PreToolUse change; implementing FR-935's `--admin` denial; changing the required context set or job names; removing required checks; changing squash-only merge policy; modifying release/tag behavior; introducing a rebase bot, watcher, daemon, or local queue; changing YAMLGraph runtime, graphs, prompts, providers, capabilities, or package APIs; broad CI optimization beyond the R-2 merge-group policy; merging with `--admin` to satisfy a witness.

## Revised acceptance criteria

- [ ] AC-01: FR-934 contains `## Ideal Result`, an explicit `is_this_a_graph: No` classification, preserved disagreement, the R-2 human policy choice, the R-4 human tuning choice, and aligned cited evidence with no docs-only/full-matrix contradiction.
- [ ] AC-02: RED commits precede workflow implementation and contain requirement-marked tests that parse both workflow files and fail because `merge_group` handling is absent; the GREEN implementation makes those same tests pass.
- [ ] AC-03: `.github/workflows/workflow.yml` and `.github/workflows/commitlint.yml` both list `merge_group` in `"on"`; existing pull-request and tag triggers remain unchanged.
- [ ] AC-04: `.github/workflows/commitlint.yml` keeps job id `commitlint`; that job is not excluded on `merge_group`; all steps consuming `github.event.pull_request` are PR-only; a merge-group-only no-op step gives the same required `commitlint` context a successful conclusion.
- [ ] AC-05: On `merge_group`, `workflow.yml` reports exactly `test (3.11)` and `test (3.13)` and applies the docs/code execution policy selected in R-2; tests assert the relevant event expressions and job/step shape.
- [ ] AC-06: The first queue candidate records one merge-group run whose check suite contains concluded `commitlint`, `test (3.11)`, and `test (3.13)` checks; their names, conclusions, and URLs are cited in FR-934.
- [ ] AC-07: Human-reviewed settings are applied only after the workflow change is merged. A recorded API/GraphQL readback proves queue required on literal `main`, squash method, exact group/wait/non-failing/timeout values, unchanged required context names, and `strict: false`.
- [ ] AC-08: A tested rollback command/payload is recorded and can disable the queue while restoring `strict: true`; a missing required context on the first merge group triggers rollback before another merge attempt.
- [ ] AC-09: Two PRs from separate worktree lanes record PR URL, enqueue-time head SHA, queue event, merge-group run URL, merge time, and squash commit; neither has a synchronize/head-SHA change after enqueue, and neither is merged with `--admin`.
- [ ] AC-10: A docs-only PR enters and clears the queue without override and exhibits exactly the cost/safety behavior selected in R-2; its PR and merge-group run URLs are recorded.
- [ ] AC-11: `CLAUDE.md` states that `main` requires the merge queue, strict up-to-date is disabled because queue candidates are validated, squash remains the only merge method, and `gh pr merge --squash` enqueues normally; `tests/unit/test_branch_protection_docs.py` pins those claims.
- [ ] AC-12: The operator's review of `.github/workflows/workflow.yml`, `.github/workflows/commitlint.yml`, and the exact repository-setting mutation is recorded before the queue is treated as live.
- [ ] AC-13: A `type: feat` changelog fragment and FR-934 diary reflection are included, and `python scripts/req_coverage.py --strict` remains green.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-5 and both human decisions are folded into FR-934 and its cited evidence is internally consistent. | GATE |
| C-2 | Workflow and repository-protection changes are enforcement infrastructure; a human must review both workflow diffs and the exact settings payload before the queue is enabled. | GATE |
| C-3 | Do not enable the queue or disable strict up-to-date until the tested `merge_group` workflow handling has merged under the current protection regime. | GATE |
| C-4 | Preserve the exact required contexts `commitlint`, `test (3.11)`, and `test (3.13)`; no check removal, rename, or success-shaped fallback for a real test failure is authorized. | GATE |
| C-5 | If any required context does not report on the first merge group, stop, restore the recorded strict regime, and return to the FR; do not use `--admin` to complete the witness. | GATE |
| C-6 | FR-935 remains separate: no hook, guard, break-glass, or `--admin` enforcement change may enter FR-934. | GATE |
| C-7 | Do not broaden CI path classification or change docs-only merge-group cost beyond the explicit R-2 human choice. | GATE |

Authority granted: after the revisions and human decisions are folded, implement only the tested merge-group workflow wiring, reviewed `main` merge-queue settings, post-queue documentation, and recorded rollout witnesses within the frozen surfaces above.
