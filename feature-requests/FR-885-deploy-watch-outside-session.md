# Feature Request: Deploy-Watch Outside the Session

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged (APPROVED WITH REVISIONS 2026-08-25, R-1..R-5 folded)
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
`now.py`): arguments = target sha, status path, hard deadline, poll
interval, version endpoint URL (+ optional `gh run` workflow name); polls
on an interval; writes the status artifact atomically after every poll;
exits when terminal. No graph needed — `is_this_a_graph` answered: no
judgement, no LLM, script is the right tool.

**Status artifact schema (frozen, R-4):** single line, atomic
(write-temp + rename), rewritten after every poll:

```
<state> target=<sha> deployed=<sha|-> started=<ISO8601Z> updated=<ISO8601Z> reason=<token|->
```

Allowed states: `BUILDING`, `BUMPED`, `SYNCING` (non-terminal);
`DEPLOYED`, `TIMEOUT` (terminal). TIMEOUT exits with a documented
non-zero code and a reason token; silence is never a terminal outcome.

**Launch model (R-1: ONE owner — the PostToolUse hook):** the hook
observes a `gh pr merge` command in the tool stream, quickly spawns ONE
detached watcher (nohup), and returns within hook budget; its system
message reports `watcher armed → tmp/rollout-<sha>.status` plus the
optional async-tail one-liner for sessions that want push. Detached
launch means NO terminal-completion push notification — the durable
interface is the status artifact plus the hook message. Manual launch of
the same script remains available but is secondary, not the contract.
Rationale: the merge command is the mechanically observable moment — a
trigger nobody has to remember. A deny-mode sole path (`scripts/merge.sh`)
was rejected: denial is for hazards (FR-888's shared index), not missed
conveniences; an advisory reminder is the adoption failure mode itself
(FR-884 evidence). GitHub-UI merges bypass the hook (board backstop).

**Hook contract (R-2, mechanical):**
- Grammar: fires on terminal commands matching `gh pr merge` (any flag
  order); ignores all other `gh` commands.
- Target sha: resolved from the merged branch head (`gh pr view --json`)
  or `git rev-parse HEAD` of the PR branch; if unresolvable → audit row +
  system message "watcher NOT armed: no target sha" — never a silent
  claim of armament.
- Status path: `tmp/rollout-<sha12>.status` derived from the resolved sha.
- Version endpoint: from env/config (documented key); missing → audit row
  + explicit not-armed message.
- Bounded: the hook only forms and spawns the command; polling happens in
  the detached process.

**Lifecycle:** one-shot process per merge arm — NOT a daemon (the
chaplain's death mode; July plan Q2 "no daemon dependency"). Born when
the PostToolUse hook observes the merge command; dies at
DEPLOYED/TIMEOUT; the status artifact is the interface. If the process
dies with the machine/window, no resurrection: the FR-888 board path
re-derives merge/deploy/prune state read-only at next refresh.

**FR-888 teardown fence (R-3):** the watcher executes merged-path
worktree teardown ONLY if FR-888 is separately judged and grants that
duty; absent that authority, FR-885 ends at writing deployment status.
This is one integration seam, not a license to implement FR-888's guard
or board under this FR.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `rollout_watch.py` accepts target SHA, status path, hard
      deadline, poll interval, version endpoint, optional workflow name;
      tests use fake endpoint and fake `gh` output only
- [ ] AC-02: Status artifact written atomically after every poll, single
      line matching the frozen schema; non-terminal progress states plus
      terminal DEPLOYED/TIMEOUT; silence is never a terminal outcome
- [ ] AC-03: TIMEOUT exits with a documented terminal code; final artifact
      carries target sha, last deployed sha, state, started/updated
      timestamps, reason
- [ ] AC-04: PostToolUse hook auto-arms on observed `gh pr merge`, returns
      within hook budget, message contains the artifact path
- [ ] AC-05: Hook tests cover merge detection, non-merge ignore, missing
      sha/endpoint reported (not silently claimed armed), detached spawn
      command formation, bounded runtime; no live merge or rollout in tests
- [ ] AC-06: One real rollout witness recorded in the FR with artifact
      transitions first poll → terminal state
      *(operator decision 2026-08-25: the witness runs in the fully armed
      environment — the NEXT FR arc after 888+885 land serves as the live
      acceptance test; its merge auto-arms the watcher)*
- [ ] AC-07: If FR-888 authority exists, merged-path teardown tested with
      safe-removal and untracked-never-auto-remove fixtures; absent that
      authority, no teardown code under this FR
- [ ] AC-08: Changelog fragment; diary reflection

**Enforcement gates (judgement):** hook diff requires human review before
merge (enforcement infrastructure, R-5); zero-LLM implementation; no live
infra in automated tests; teardown only under FR-888's authority.

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
- FR-888: defines the merged-FR worktree teardown duty; this watcher
  executes it ONLY under FR-888's separately granted authority (R-3 fence)
- Scripture: `is_this_a_graph`, `would_you_use_this`
