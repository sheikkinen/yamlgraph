# Reflection: FR-697 Watcher2 Sanity Check

**Date:** 2026-07-07
**FR:** FR-697 — Executor-Neutral Worktree Tooling (`wt`)
**Reviewer:** watcher2 post-validate sanity pass

## Trap

`working_system_inertia` — three independent lifecycle implementations existed and worked in
isolation, which masked the drift and the missing operator lane. The FR-662 guard correctly
blocked bare `checkout -b` but silently omitted the third option it already permitted.

## What Happened

The enforce agent correctly followed the RED-first mandate: test modules were written and
committed before production code, then the canonical `scripts/worktree.sh` and wrappers were
implemented. Watcher setup/teardown collapsed from ~130 lines of duplicated lifecycle logic to
thin 3-line `exec` wrappers. `copilot_instrument.sh` removed its private `worktree add/remove`
calls and now delegates to the shared command. CAP-189..192 were created and ARCHITECTURE.md
was updated.

## Root Cause

Lifecycle logic drifted across three call sites because no shared abstraction existed.
Each path paid independently for incident knowledge (FR-139 bare corruption, FR-174 stale .pth,
FR-241 editable-install self-heal). The operator lane was technically allowed by the hook but
not surfaced in denial guidance, resulting in an 83% direct-to-main commit pattern.

## What Worked

- Proportionality is good: 1003 insertions / 133 deletions for a feature replacing ~130 lines
  of duplicated shell logic with a 315-line canonical command and 4 thin test modules.
- All 10 acceptance tests pass GREEN after implementation.
- Tests check behavior (script text contracts, subprocess exit codes, spike note log
  creation) rather than implementation trivia.
- FR acceptance criteria checklist is fully satisfied and verifiable against the diff.
- REQ markers on all new tests; CAP YAML files match REQ IDs; changelog fragment present.
- One minor concern: `test_worktree_spike_rm_requires_note_and_blocks_without_it` and
  `test_worktree_spike_rm_appends_spike_note_log_line` test with real `git init` + real bash
  subprocess invocations — this is correct E2E for shell behavior, not a mock escape.

## Seed:

When a guard (hook, gate, CI check) correctly blocks a path but the denial message omits a
viable alternative that the guard itself already allows, what is the minimum detectable signal
that the message has drifted from actual policy — and can that signal be automated as a
requirement test so silence in the deny text is a failing assertion, not a documentation debt?
