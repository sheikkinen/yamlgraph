# Judgement: FR-885 Deploy-Watch Outside the Session

**Prior art:** dispositioned in the FR (FR-743 watcher kill; FR-739/744 board surfaces; FR-888 coupling fenced by R-3).

**Verdict:** APPROVED WITH REVISIONS — the problem is real and the zero-LLM watcher is the right class of solution, but authority activates only after the FR resolves its contradictory launch model and fences the FR-888 teardown dependency.

**Reviewed against:** `feature-requests/FR-885-deploy-watch-outside-session.md`; `docs/FR-884-session-task-shapes.md`; `docs/FR-884-raw-read-log.md`; `feature-requests/FR-743-sessionstart-briefing-hook.md`; `feature-requests/FR-739-vscode-introspection-suite.md`; `feature-requests/FR-744-world-now-distill.md`; `feature-requests/FR-888-main-write-guard-worktree-route.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The pain is evidenced, not speculative. FR-884 measured deploy-watch as 6.3% of the classified token volume and identifies it as the top construction candidate because it is pure polling with no judgement (`docs/FR-884-session-task-shapes.md:21`); the raw-read log independently records poll/merge/check/status turns in mega-sessions paying 200K-700K prompt tokens for near-pure context resend (`docs/FR-884-raw-read-log.md:12`, `docs/FR-884-raw-read-log.md:25-30`). The FR names a first consumer and first event (`feature-requests/FR-885-deploy-watch-outside-session.md:8-9`), satisfying the `would_you_use_this` doctrine (`.github/copilot-instructions.md:125`).

The architecture choice is aligned: the proposed path is a stdlib script and status artifact, not a graph, because the task has no LLM judgement (`feature-requests/FR-885-deploy-watch-outside-session.md:51-58`). That matches the repo doctrine's `is_this_a_graph` question: graphs are for LLM/task-shape orchestration, while scripts are appropriate when no graph abstraction fits (`.github/copilot-instructions.md:133`). The FR also preserves FR-743's fail-open/visibility lesson rather than turning waiting into a blocking hook (`feature-requests/FR-743-sessionstart-briefing-hook.md:55-62`).

The acceptance criteria are mostly testable: synthetic endpoint and fake `gh` fixtures avoid live infrastructure in tests (`feature-requests/FR-885-deploy-watch-outside-session.md:89-90`), atomic status writes and explicit TIMEOUT are checkable (`feature-requests/FR-885-deploy-watch-outside-session.md:91-93`), and hook adoption is made mechanical rather than advisory (`feature-requests/FR-885-deploy-watch-outside-session.md:96-99`), consistent with the evidence that purely voluntary routes are not read at the moment of use (`feature-requests/FR-888-main-write-guard-worktree-route.md:49-58`).

## Required revisions

### R-1: Choose one launch owner and delete the contradictory lifecycle text

Fold the launch model to one authority: **PostToolUse observes `gh pr merge` and quickly spawns one detached watcher process, then returns within hook budget**. Remove or rewrite the conflicting claim that the watcher is "NOT hook-spawned" and that it is "born when the enforcing session ... launches it as its last act" (`feature-requests/FR-885-deploy-watch-outside-session.md:74-80`), because it contradicts the frozen auto-arm mechanism (`feature-requests/FR-885-deploy-watch-outside-session.md:60-72`). State explicitly that detached launch means no terminal-completion push notification; the durable interface is the status artifact plus the hook message.

### R-2: Specify the hook contract mechanically

Add a concrete hook contract: the observed command grammar, how the target SHA is resolved, how the status path is derived, how the version endpoint is configured, and what happens when required inputs are missing. Missing SHA or endpoint must produce an audit/message row and **not** silently claim a watcher was armed. The hook test must cover at least: merge command detected, non-merge `gh` command ignored, missing endpoint/sha reported, watcher spawn command formed, and hook runtime bounded. This makes the adoption claim mechanically checkable rather than merely asserted (`feature-requests/FR-885-deploy-watch-outside-session.md:96-99`).

### R-3: Fence the FR-888 teardown dependency

Do not let FR-885 independently authorize worktree teardown. Revise the FR to say: the watcher may execute merged-path teardown **only if FR-888 is separately judged/approved with that duty in scope**; otherwise FR-885 ends at writing deployment status. The current FR says the watcher performs FR-888 teardown (`feature-requests/FR-885-deploy-watch-outside-session.md:83-85`) and that the duty is "defined there, executed here" (`feature-requests/FR-885-deploy-watch-outside-session.md:113-117`), while FR-888 is still Proposed and owns the safety invariant that untracked trees are never auto-removed (`feature-requests/FR-888-main-write-guard-worktree-route.md:145-179`). This is one integration seam, not a license to implement FR-888's guard or board.

### R-4: Freeze the status artifact schema

Replace the prose-only artifact description with an exact schema in the FR before enforcement: format, required keys, allowed states, timestamp format, atomic-write behavior, and terminal-state semantics. The FR already names the intended one-line fields (`feature-requests/FR-885-deploy-watch-outside-session.md:44-47`) and says TIMEOUT must be explicit (`feature-requests/FR-885-deploy-watch-outside-session.md:91-93`); enforcement needs the exact contract so tests can assert it without interpreting prose.

### R-5: Add human-review gate for hook changes

Because this FR changes hook behavior, add an explicit enforcement condition that the hook diff receives human review before merge. Judge doctrine treats enforcement-infrastructure changes as adversarial input and requires human review as a gate (`.github/skills/judge-fr/doctrine.md:96-100`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/vscode/rollout_watch.py` stdlib watcher |
| D-2 | Synthetic fixture tests for watcher polling, atomic writes, terminal states, timeout, fake endpoint, and fake `gh` output |
| D-3 | PostToolUse hook wiring that detects `gh pr merge`, spawns one detached watcher, and reports `tmp/rollout-<sha>.status` |
| D-4 | Hook tests covering detection, ignored commands, missing inputs, bounded runtime, and artifact-path message |
| D-5 | FR update with one live rollout witness, changelog fragment, and diary reflection |
| D-6 | Conditional FR-888 merged-path teardown hook only if FR-888 grants that authority |

Not authorized: any LLM or YAMLGraph implementation; daemon/service lifecycle; live infrastructure in automated tests; a deny-mode merge wrapper or sole-route merge command; GitHub UI merge interception; implementing FR-888's main-write guard or board orphan detection here; deleting worktrees with untracked files; new third-party dependencies; broad refactors of the hook system.

## Revised acceptance criteria

- [ ] AC-01: `scripts/vscode/rollout_watch.py` accepts target SHA, status path, hard deadline, poll interval, version endpoint, and optional workflow name; tests use fake endpoint and fake `gh` output only.
- [ ] AC-02: The status artifact is written atomically after every poll as a single line matching the frozen schema; allowed states include non-terminal progress states plus terminal `DEPLOYED` and `TIMEOUT`; silence is never a terminal outcome.
- [ ] AC-03: TIMEOUT exits non-zero or with an explicitly documented terminal code, and the final artifact contains target SHA, last observed deployed SHA, state, started timestamp, updated timestamp, and reason.
- [ ] AC-04: PostToolUse hook auto-arms the watcher on an observed `gh pr merge` command, returns within hook budget, and its message contains the artifact path.
- [ ] AC-05: Hook tests cover merge detection, non-merge ignore, missing target SHA/endpoint reporting, detached spawn command formation, and bounded runtime; no test performs a live merge or live rollout.
- [ ] AC-06: One real rollout witness is recorded in the FR with captured artifact transitions from first poll to terminal state.
- [ ] AC-07: If FR-888 authority exists, merged-path teardown is tested with both safe removal and untracked-files-never-auto-remove fixtures; if FR-888 authority does not exist, no teardown code is implemented under this FR.
- [ ] AC-08: Changelog fragment and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-5 must be folded into the FR before implementation authority activates. | GATE |
| C-2 | Hook changes require human review before merge because they modify enforcement infrastructure. | GATE |
| C-3 | The implementation must remain zero-LLM and must not invoke YAMLGraph for rollout polling. | GATE |
| C-4 | Automated tests must not call live GitHub merge, live CI/CD, or a production version endpoint. | GATE |
| C-5 | Worktree teardown is permitted only under the separately approved FR-888 contract; untracked files must never be auto-removed. | GATE |

Authority granted: after the required revisions are folded, build the zero-LLM rollout watcher, its PostToolUse auto-arm, the status artifact contract, and only the FR-888 teardown integration explicitly authorized by FR-888.
