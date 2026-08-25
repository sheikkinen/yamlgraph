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

## Acceptance Criteria

- [ ] Watcher script with synthetic-fixture tests (fake endpoint + fake
      `gh` output; never live infra in tests)
- [ ] Status artifact schema documented in the script docstring; atomic
      writes; TIMEOUT is an explicit terminal state, never silence
      (fail-open ≠ fail-silent — FR-884 diary lesson)
- [ ] One recorded live witness: a real rollout watched end-to-end with the
      artifact transitions captured in the FR
- [ ] Adoption trigger documented where enforce workflows are described:
      rollout waits are delegated to the watcher
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
- Scripture: `is_this_a_graph`, `would_you_use_this`
