# Judgement: FR-861 Shared-Repo Write Discipline

**Prior art:** dispositions inventoried in the parent FR, `feature-requests/FR-861-shared-repo-write-discipline.md` (with the FR-784 citation corrected per R-1 below).

**Verdict:** APPROVED WITH REVISIONS — the shared-repo hazard is real and the repo-local doctrine + guard direction is sound, but authority activates only after the FR replaces hidden-memory evidence with a committed incident taxonomy, freezes the hermetic adapter contract, and makes the primary-checkout commit guard mechanically unambiguous.

**Reviewed against:** `feature-requests/FR-861-shared-repo-write-discipline.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/judge-fr/SKILL.md`; `scripts/judge.sh`; `.github/skills/review-pr/doctrine.md`; `.github/skills/review-pr/SKILL.md`; `.github/skills/review-pr/adapters/README.md`; `scripts/review.sh`; `.github/skills/session-introspection/SKILL.md`; `.github/copilot-instructions.md`; `.github/hooks/scripts/pre-command-guard.sh`; `.pre-commit-config.yaml`; `scripts/worktree.sh`; `docs/diary/2026-08-23-the-worktree-is-the-airlock.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-767-graph-authoring-sole-route.judgement.md`; `feature-requests/FR-784-playwright-network-sniff-utility.md`; `feature-requests/FR-852-preserve-authoring-briefs.md`; `feature-requests/FR-852-preserve-authoring-briefs.judgement.md`; `feature-requests/FR-858-retire-committed-fr-board.md`; `feature-requests/FR-859-delete-orphaned-sim117-phantom-req-tag.md`; `feature-requests/FR-860-req-audit-run-scaffolding.md`; `feature-requests/FR-860-req-audit-run-scaffolding.judgement.md`.

## What is sound

The problem is real and repo-relevant. The FR names a concrete first consumer: a fresh agent or machine with zero local memory that must discover the write ritual from the repository itself (`feature-requests/FR-861-shared-repo-write-discipline.md:11-15`). Current committed doctrine only gives read-side situation awareness: `session-introspection` tells sessions to inspect live sessions, branch state, staged files, and FRs in motion before acting (`.github/skills/session-introspection/SKILL.md:8-23`), but it does not prescribe the write-side commit, stash, or generator airlock rituals.

The strategic classification is process/enforcement infrastructure, not a YAMLGraph framework primitive. It addresses the repo's existing `one_session_one_repo` operational hazard: shared index, working tree, and environment collisions are already named in Scripture, along with staged-check, pathspec, immediate-commit, post-commit audit, and interpreter-resolution rituals (`.github/copilot-instructions.md:163`). The diary evidence correctly identifies that repeated in-place counter-choreography is a symptom catalogue and that an immutable worktree snapshot is the better boundary normalization (`docs/diary/2026-08-23-the-worktree-is-the-airlock.md:14-29`, `docs/diary/2026-08-23-the-worktree-is-the-airlock.md:53-67`).

The chosen architectural pattern is aligned with local precedent. Judge and review both separate doctrine from thin wrappers, serialize route execution, use lineage sentinels, and verify draft artifacts rather than trusting exit codes (`.github/skills/judge-fr/SKILL.md:31-51`, `scripts/judge.sh:19-60`, `.github/skills/review-pr/SKILL.md:31-49`, `scripts/review.sh:21-62`). FR-767 is also valid precedent for moving a repeated instruction failure into a PreToolUse guard with a scoped sentinel and hook tests (`feature-requests/FR-767-graph-authoring-sole-route.md:119-156`, `feature-requests/FR-767-graph-authoring-sole-route.judgement.md:83-90`).

The proposed surfaces are feasible. `scripts/worktree.sh` already provisions and tears down linked worktrees and symlinks the main `.venv` when present (`scripts/worktree.sh:146-157`, `scripts/worktree.sh:252-281`). The current pre-command guard already denies dangerous terminal patterns, audit-logs decisions, and implements the FR-767 authoring guard before terminal-only checks (`.github/hooks/scripts/pre-command-guard.sh:19-50`, `.github/hooks/scripts/pre-command-guard.sh:169-298`). The existing pre-commit configuration confirms the concrete generator problem: `fr-board-check` runs `scripts/fr_board.py --check`, and `cap-architecture-sync` runs `scripts/aggregate_capabilities.py` (`.pre-commit-config.yaml:88-96`, `.pre-commit-config.yaml:289-297`).

The scope can remain one FR because the doctrine, hermetic generator route, and commit/stash guard all serve one responsibility: safe writes in a shared repo. The FR must not, however, leave implementation-defining details to the enforcer.

## Required revisions

### R-1: Replace hidden-memory evidence with a committed six-shape taxonomy

The FR's core evidence says six interleave shapes were diagnosed across prior work, but it also says the full cure currently lives in `/memories/repo/hook-lessons.md`, which is local agent memory (`feature-requests/FR-861-shared-repo-write-discipline.md:19-27`). Judge input closure permits only committed artifacts; hidden memory cannot be the source for repo doctrine (`.github/skills/judge-fr/doctrine.md:16-24`).

Fold a taxonomy table into FR-861 before enforcement. Each row must name the shape, committed evidence source, failure mode, cure, and enforcing surface. Correct the prior-art inventory at the same time: the cited `FR-784` file is a Playwright network-sniff utility (`feature-requests/FR-784-playwright-network-sniff-utility.md:14-24`), not an interleave-shape cure. If a shape has only local-memory evidence, state that explicitly and include enough incident detail in FR-861 to make the doctrine judgeable without reading local memory.

### R-2: Freeze `scripts/hermetic.sh` as an explicit artifact-copy contract

The proposed adapter is underspecified. The FR says `scripts/hermetic.sh <cmd...>` overlays "currently-staged + explicitly listed files" and copies "declared output artifacts" back (`feature-requests/FR-861-shared-repo-write-discipline.md:51-57`), but the CLI has no syntax for explicitly listed inputs or declared outputs. AC-2 then calls `scripts/hermetic.sh 'python scripts/fr_board.py'` with no output declaration (`feature-requests/FR-861-shared-repo-write-discipline.md:113-115`). An implementation could either fail to copy anything back or copy every dirty file from the airlock, which would recreate the shared-tree hazard in another form.

Revise the FR to define the exact interface. At minimum, it must specify how callers declare input overlays and output paths, how staged files are discovered, how paths are constrained to the repo, how the main repo's Python/venv is resolved, what happens on command failure, and that undeclared dirty files in the airlock are never copied back. Because FR-858 may delete `docs/fr-board.md` and its hook (`feature-requests/FR-858-retire-committed-fr-board.md:47-58`), the acceptance witness must not depend solely on `docs/fr-board.md`; either name the FR-858 successor path or include a surviving generator such as `scripts/aggregate_capabilities.py`, whose pre-commit hook exists today (`.pre-commit-config.yaml:88-96`).

### R-3: Make primary-checkout commit denial target resolution fail closed

The guard rule is directionally right: deny agent commits in the primary checkout and allow linked worktrees (`feature-requests/FR-861-shared-repo-write-discipline.md:58-68`). But the mechanical predicate is not fully specified. The active guard parses only the raw terminal command string and currently exits early for non-terminal tools after the FR-767 check (`.github/hooks/scripts/pre-command-guard.sh:300-305`). A reliable commit guard must decide which working tree the command targets, including `git commit`, `git -C <path> commit`, and `cd <path> && git commit` forms.

Fold a fail-closed target-resolution rule into the FR. The hook must resolve the intended worktree root before deciding primary versus linked. It may distinguish primary checkouts by the resolved worktree root containing a `.git` directory and linked worktrees by a `.git` file, as FR-861 proposes (`feature-requests/FR-861-shared-repo-write-discipline.md:61-64`), but if the command shape makes the target ambiguous, the guard must deny and route to `scripts/worktree.sh` rather than approve. Tests must cover plain `git commit`, `git -C`, `cd ... && git commit`, linked-worktree allow, primary-checkout deny, and ambiguous-target deny.

### R-4: Reconcile the commit-message ritual with existing repo doctrine

FR-861 proposes unique message files under `/tmp/msg-<topic>.txt` and says never to use shared `./tmp/msg.txt` (`feature-requests/FR-861-shared-repo-write-discipline.md:36-39`). Current repo doctrine says the opposite for multiline commits: always write to `./tmp/msg.txt` and use `git commit -F ./tmp/msg.txt` (`.github/copilot-instructions.md:28`). Enforcers cannot obey both.

Revise the FR to make the doctrine transition explicit. Either update `.github/copilot-instructions.md` within this FR to point at the new session-introspection write doctrine and unique message-file rule, or alter the proposed doctrine to preserve the current `./tmp/msg.txt` rule. If unique message files remain, make them repo-local under `tmp/` or explicitly justify `/tmp/`; and state that pathspec commits are a worktree/private-index ritual only, because the primary checkout commit guard denies agent commits there.

### R-5: Add the mandatory human-review and rollout gate for hook/doctrine changes

This FR changes enforcement infrastructure and agent operating doctrine. Judge discipline treats such changes as adversarial input and requires a human-review gate (`.github/skills/judge-fr/doctrine.md:94-103`). FR-861 mentions an audit-log dry run only as risk mitigation for chaplain/watcher automation (`feature-requests/FR-861-shared-repo-write-discipline.md:134-137`), not as a binding acceptance criterion or condition.

Add a GATE condition requiring human review before the denial is considered active doctrine. The FR must also require a dry-run or warn-mode audit over current chaplain/watcher commit paths before enabling primary-checkout commit denial, with any legitimate primary-checkout automation either moved to worktrees or explicitly recorded as out of scope. This is necessary because a false positive in `git commit` denial blocks enforcement sessions at the commit boundary.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/session-introspection/doctrine.md`: committed write-side doctrine, including the six-shape taxonomy and cures after R-1 is folded. |
| D-2 | `.github/skills/session-introspection/SKILL.md`: trigger/description update advertising write rituals as well as read-side situation awareness. |
| D-3 | `scripts/hermetic.sh`: one hermetic generator runner with the frozen input/output contract from R-2. |
| D-4 | Tests for `scripts/hermetic.sh` under the existing script-test pattern: worktree creation, explicit overlay, declared-output copyback, failure isolation, cleanup, and surviving-generator witness. |
| D-5 | `.github/hooks/scripts/pre-command-guard.sh`: primary-checkout commit denial and explicit-stash-ref rules only, with audit logging and denial messages naming `scripts/worktree.sh` and the doctrine path. |
| D-6 | Hook tests under the existing hook test harness for primary vs linked worktree commits, target-resolution ambiguity, and bare vs explicit stash operations. |
| D-7 | `.github/copilot-instructions.md`: only the minimal pointer/message-file reconciliation required by R-4. |
| D-8 | `feature-requests/FR-861-shared-repo-write-discipline.md`: folded revisions, implementation status, decisions, validation record, and local-memory disposition note. |
| D-9 | `changelog/unreleased/` and `docs/diary/` only as required by existing repository gates for the final commit type. |

Not authorized: invoking or changing judge/review routes; changing graph-authoring route semantics; adding required CI checks; adding session locks or preventing parallel sessions; guarding `git push`/`git fetch`; mechanically blocking file edits in the primary checkout; changing YAMLGraph runtime primitives; deleting `docs/fr-board.md` or its hook under this FR; committing local `/memories/` content; copying undeclared airlock outputs; adding global hook bypasses or silent fallbacks.

## Revised acceptance criteria

- [ ] AC-01: FR-861 contains a six-shape taxonomy table with committed evidence source, failure mode, cure, and enforcing surface for each shape; the `FR-784` prior-art citation is corrected or explicitly marked as non-evidence.
- [ ] AC-02: `.github/skills/session-introspection/doctrine.md` contains the folded write-side contract: worktree-first rule, commit ritual, explicit-stash-ref rule, hermetic-generator rule, and six-shape appendix.
- [ ] AC-03: `.github/skills/session-introspection/SKILL.md` description and body advertise write rituals, not only read-side session introspection.
- [ ] AC-04: `scripts/hermetic.sh --help` documents the frozen interface for command, input overlay, declared outputs, output-copy policy, failure behavior, cleanup behavior, and main-repo Python/venv resolution.
- [ ] AC-05: Hermetic-runner tests prove a HEAD worktree is created, staged and explicitly listed inputs are overlaid, declared outputs are copied back, undeclared dirty airlock files are not copied, failure leaves main-tree non-output files unchanged, and the temporary worktree is removed.
- [ ] AC-06: The hermetic-runner witness uses a current generator target: `docs/fr-board.md` only if FR-858 has not retired it, otherwise the FR-858 successor or a surviving generator such as `scripts/aggregate_capabilities.py`.
- [ ] AC-07: In the primary checkout, an agent `git commit` tool call is denied with a message naming `scripts/worktree.sh` and `.github/skills/session-introspection/doctrine.md`; the identical command inside a linked worktree is allowed.
- [ ] AC-08: Guard tests cover target resolution for plain `git commit`, `git -C <path> commit`, `cd <path> && git commit`, linked-worktree allow, primary-checkout deny, and ambiguous-target deny.
- [ ] AC-09: Guard tests cover `git stash pop` and `git stash apply`: bare forms denied; explicit `stash@{n}` refs allowed.
- [ ] AC-10: Guard denial and approval decisions are audit-logged with stable reason codes for primary-checkout commit denial, ambiguous commit target, bare stash pop/apply denial, and allowed linked-worktree commit.
- [ ] AC-11: The commit-message-file rule is reconciled with `.github/copilot-instructions.md`; no committed doctrine simultaneously requires both shared `./tmp/msg.txt` and unique message files.
- [ ] AC-12: No new required CI checks are added, and no judge/review route, graph-authoring route, graph artifact, prompt artifact, push/fetch guard, session lock, or primary-checkout edit guard is changed.
- [ ] AC-13: Tests added or changed by this FR carry valid `@pytest.mark.req("REQ-YG-XXX")` coverage, with any required capability registry update included.
- [ ] AC-14: Implementation status records the human-review gate result, dry-run/warn-mode findings for chaplain/watcher commit paths, validations run, and the local-memory disposition without committing private memory content.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-5 must be folded into FR-861 before implementation authority activates. | GATE |
| C-2 | A human must review the hook and doctrine changes before the primary-checkout commit denial is considered active doctrine. | GATE |
| C-3 | The guard must fail closed on ambiguous commit targets and stash commands; do not approve a command merely because the parser could not resolve it. | GATE |
| C-4 | `scripts/hermetic.sh` may copy back only declared output paths; any undeclared dirty file in the airlock must fail the run or be ignored with an explicit diagnostic, never copied silently. | GATE |
| C-5 | The hermetic runner must leave the main working tree untouched on command failure except for already-declared output paths whose copyback occurs only after successful command completion. | GATE |
| C-6 | Do not use local `/memories/` content as enforcement input unless its relevant facts are copied into committed FR/doctrine text first. | GATE |
| C-7 | If FR-858 lands first and removes `docs/fr-board.md` or `fr-board-check`, update only FR-861's hermetic-runner witness target; do not resurrect the committed board under this FR. | GATE |
| C-8 | Keep this FR local-only: no new required CI checks, no push/fetch guard, no session lock, and no primary-checkout edit-blocking guard. | GATE |

Authority granted after revisions: implement the shared-repo write doctrine, one hermetic generator runner, and local PreToolUse write-discipline guard within the frozen surfaces above.
