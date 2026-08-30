# The Queue That Reports, and the Context That Doesn't

**Date:** 2026-08-30
**Context:** FR-934 enforcement — merge_group wiring for the main merge queue.

## The observation

The entire technical content of this FR is one sentence: *a required
context that never reports is a deadlock, on every event type that can
carry it.* We had already paid for this lesson once — FR-889 §4d, where
docs-only PRs deadlocked because the path filter skipped the required
test matrix and skipped jobs never report (PR #501, admin merge
required). The queue is the same trap wearing a new event name:
`merge_group` candidates time out after 30 minutes if `commitlint` or
`test (3.11)`/`test (3.13)` never conclude.

The cure was also already in the tree. The `changes` job's
`github.event_name != 'pull_request'` short-circuit — written for tag
pushes (FR-919 C-3) — handles merge groups for free. The commitlint
no-op step is a copy of the §4d "required-context conclusion" pattern.
Enforcement was boring: five RED witnesses, two `on:` blocks, one job
condition, one no-op step. **Boring = the Judgement was good.**

## The trap avoided

`startsWith(github.event.pull_request.title, 'feat')` evaluates falsy
on merge_group events (null payload), so the feat-gate step was
*accidentally* safe. The judgement demanded the explicit
`github.event_name == 'pull_request'` guard anyway — correctness by
null-coercion is a `plausible_wrong_answer` waiting for the next person
to copy the step into a context where null semantics differ. Guard at
the boundary you mean, not the one that happens to hold.

## The sequencing insight

CLAUDE.md now documents the post-queue truth *before* the settings
flip exists. The frozen rollout order forces this: workflow + docs
merge under the old strict regime, the flip follows within minutes,
and the interval is owned by a named operator review (C-2). A doc that
briefly leads reality inside a supervised transaction is honest; a doc
that trails reality indefinitely is the actual lie. The alternative —
docs in a second PR after the flip — would leave a window where the
queue is live and undocumented, which is worse for the next agent.

**Seed:** The three required contexts now each carry a "report
success without doing work" branch (docs-only no-op, merge-group
no-op). That is a growing family of *conclusion-shaped* steps whose
only purpose is satisfying the reporting contract. Is there a point
where required contexts should be one thin always-reporting gate job
that `needs:` the real work, so the reporting contract lives in one
place instead of being re-derived per workflow per event type?
