# 2026-04-22 — FR-273 Watcher2 Phase 1: Git Skeleton

## What happened

Built watcher2.sh — a new pipeline orchestrator replacing watch.sh + enforce_worktree.sh + bugfix_worktree.sh. Phase 1 is shell-only: no LLM, just the worktree lifecycle end-to-end.

9 sourced shell libs in `.chaplain/lib/watcher/` handle: inbox sync, preflight, worktree setup/teardown, PR create/merge, CI polling, post-merge cleanup, and metrics.

## Trap encountered

**"Run from anywhere" assumption.** First test run was from the worktree itself, which can't checkout main (main is locked by the parent repo). The preflight silently tried to switch branches and failed. Fix: hard error if not on main — watcher2 must run from the main repo.

**CI status shape mismatch.** `gh pr checks --json` returns states like `SKIPPED,SUCCESS` — the original code checked for exact `== "SUCCESS"` which never matched. Fix: check for failures first, then pending states, treat everything else as done.

## Heuristic

*Test infrastructure from its deployment context.* A worktree orchestrator must be tested from the main repo, not from a worktree — the environment constraints are different.

## Seed

How should watcher2 handle re-entry? If it crashes mid-cycle, should it resume the worktree or start fresh? The processing dir move prevents re-pick, but the worktree may be left behind.
