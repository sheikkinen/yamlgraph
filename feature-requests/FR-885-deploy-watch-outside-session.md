# Feature Request: Deploy-Watch Outside the Session

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-25
**First consumer / first event:** any enforce session awaiting a CD rollout —
the next "poll" turn it would otherwise burn 200K–700K prompt tokens on.

**Prior art:** FR-743 (Enforced) built and then *killed* a generic
push-notification watcher at the `would_you_use_this` gate — that kill was of
consumer-less git-event subscriptions; this FR differs by naming a measured
consumer and cost (FR-884 census: deploy-watch ≈41M tokens/6.3% primary,
plus ~10 poll + ~30 merge/check micro-turns witnessed inside one mega-session,
each a full-context resend). FR-743's verified async-terminal notification
seam and fail-open briefing pattern are reused, not re-derived. FR-739/744
(now.py situation board) are the display surface, not the watcher. No
graveyard hit proposes a rollout-specific watcher.

## Summary

A zero-LLM rollout watcher that polls CI/CD state (workflow run, deployed
version endpoint, GitOps sync) outside the premium session and writes a
one-line verdict artifact the agent can check for pennies.

## Value Statement

The operator stops paying frontier-model context-resend prices for "is it
deployed yet"; the agent gets a deterministic answer file instead of a
polling loop.

## Problem

FR-884 (docs/FR-884-session-task-shapes.md) measured the micro-turn tax:
single-word poll/merge/check turns late in long sessions each pay full
context (200K–700K prompt tokens witnessed, docs/FR-884-raw-read-log.md
S-H1). Deploy-watch has *no LLM judgement in it at all* — it is pure
polling — yet it consumed ~6.3% of window tokens as a primary shape and an
unmeasured further share embedded in enforce sessions.

## Ideal Result

An enforce session that merges a PR starts the watcher in one command and
moves on; when the agent (or human) next cares, `cat tmp/rollout-<sha>.status`
answers in one line — target sha, deployed sha, state (building / bumped /
syncing / DEPLOYED / TIMEOUT), timestamps. Zero LLM tokens spent waiting.

## Proposed Solution

`scripts/vscode/rollout_watch.py` (stdlib-only, same spike conventions as
`now.py`): arguments = target sha + version endpoint URL (+ optional
`gh run` workflow name); polls on an interval with a hard deadline; writes
the status artifact atomically after every poll; exits when terminal.
Started via the async-terminal seam (`mode=async`) so completion notifies
the session that launched it (FR-743 witnessed channel). Optional
`--notify` hook appends to the session-briefing surface. No graph needed —
`is_this_a_graph` answered: no judgement, no LLM, script is the right tool.

**Launch mechanism (frozen 2026-08-25 — "no one remembers the script"):**
the watcher is **auto-armed by a PostToolUse hook** that observes a
`gh pr merge` command in the tool stream: the hook launches
`rollout_watch.py` detached (nohup) and reports in its system message
`watcher armed → tmp/rollout-<sha>.status` plus the optional async-tail
one-liner for sessions that want push notification. Rationale: the merge
command is the mechanically observable moment — a trigger nobody has to
remember. A deny-mode sole path (`scripts/merge.sh`) was rejected: denial
is for hazards (FR-888's shared index), not missed conveniences; and an
advisory reminder is the adoption failure mode itself (FR-884 evidence).
Manual launch remains available. Auto-arm degradations accepted: detached
means no terminal-completion push (artifact + hook message compensate);
GitHub-UI merges bypass the hook entirely (board backstop catches both).

**Lifecycle (frozen):** a one-shot process per merge arm — NOT a daemon
(the chaplain's death mode; July plan Q2 "no daemon dependency") and NOT
hook-spawned (5s hook budget, and the async-notification seam belongs only
to terminals the agent itself started — FR-743 finding). Born when the
enforcing session runs `gh pr merge --auto` and launches it as its last
act; dies at DEPLOYED/TIMEOUT; the status artifact is the interface —
the launcher gets the terminal notification, everyone else reads the
file. If the watcher dies with its VS Code window, no resurrection: the
FR-888 AC-10/AC-11 board path re-derives merge/deploy/prune state
read-only at next refresh. On DEPLOYED with the PR merged, its terminal
step performs the FR-888 merged-path teardown (verify zero untracked →
`worktree.sh remove`, else flag).

## Acceptance Criteria

- [ ] Watcher script with synthetic-fixture tests (fake endpoint + fake
      `gh` output; never live infra in tests)
- [ ] Status artifact schema documented in the script docstring; atomic
      writes; TIMEOUT is an explicit terminal state, never silence
      (fail-open ≠ fail-silent — FR-884 diary lesson)
- [ ] One recorded live witness: a real rollout watched end-to-end with the
      artifact transitions captured in the FR
- [ ] Adoption is mechanical, not documented: PostToolUse hook auto-arms
      the watcher on an observed `gh pr merge` — witnessed by a hook test
      (fixture command stream, no live merge); hook message contains the
      artifact path
- [ ] Changelog fragment; diary reflection

## Alternatives Considered

- **PreToolUse nudge on poll-shaped turns** — enforcement without an
  alternative to offer; build the alternative first, nudge later if the
  next census shows no shift.
- **Graph with LLM summary of rollout state** — framework costume; there is
  no judgement here.
- **Do nothing** — the 2026-08 invoice prices this at real money monthly.

## Related

- FR-884 census + raw-read log (evidence)
- FR-743 (notification seam, fail-open pattern), FR-739 (tap/altimeter)
- FR-888: the watcher's terminal step owns merged-FR worktree teardown
  (verify merged + zero untracked → remove) — duty defined there, executed
  here; scope both FRs together at judgement
- Scripture: `is_this_a_graph`, `would_you_use_this`
