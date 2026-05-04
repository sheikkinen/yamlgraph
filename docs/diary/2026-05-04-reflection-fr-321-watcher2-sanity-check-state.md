# Reflection: FR-321 watcher2 sanity-check state

**Date:** 2026-05-04
**FR:** FR-321 — Replace `YamlgraphAsyncAction` shell execution with `create_subprocess_exec(*argv)`
**Reviewer:** watcher2 post-validate sanity reviewer

## Trap

`downstream_fix` — FR-319 added `shlex.quote()` at the point where shell-significant characters were being assembled, but the shell boundary itself remained. Quoting at the join site is the classic symptom-patch: the right location is the process creation boundary, not the string assembly.

## What Happened

FR-319 reduced the blast radius by quoting `--var` payloads before joining them into a shell string. FR-321 completed the intent by eliminating the shell entirely: `create_subprocess_shell(command)` → `create_subprocess_exec(*cmd_parts)`. The `shlex` import was deleted, the joined `command` string was deleted, and each token is now passed directly as an argv element.

## Root Cause

The original implementation assembled argv tokens but then joined them into a string and re-parsed through a shell. This introduced a second parse pass that could re-interpret literal characters as shell syntax. The boundary where untrusted text enters (var substitution) was separated from the process creation call by a shell re-parser—precisely the scenario the `normalize_at_boundary` law forbids.

## What Worked

- Scope was tightly constrained: one action file, one new test file, no FSM topology changes.
- The existing `git_commit_action.py` pattern provided prior art for `create_subprocess_exec`, making the fix low-risk.
- All 5 acceptance tests (AC-01 through AC-05) pass and assert behavioral contracts: exec used, shell not called, literal argv tokens, routing and timeout unchanged.
- Diff is proportional: 14 lines changed in the action module, 146-line focused test file. No collateral changes.

## Seed

When a boundary fix is deferred with "out of scope for this FR" (as FR-319 did), does the project need an automatic tracking mechanism — a `deferred_boundary_debt` entry in the FR — that triggers a follow-up FR creation so the debt does not require a fresh issue to resurface it?
