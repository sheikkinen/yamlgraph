# Feature Request: Watcher2 Pipeline

**Priority:** HIGH
**Type:** Enhancement
**Status:** Draft
**Effort:** 5–7 days (phased)
**Requested:** 2026-04-22

## Summary

Replace monolithic `watch.sh` + separate `enforce_worktree.sh` / `bugfix_worktree.sh` with a single `watcher2.sh` orchestrator that isolates all work in a git worktree, runs shell scripts and yamlgraph copilot nodes in sequence, and manages the full PR lifecycle (create → CI → merge → cleanup).

## Value Statement

The current watcher has 20+ silent `2>/dev/null || true` patterns, duplicated logic across enforce/bugfix scripts, and mixes planning with enforcement in a single monolithic loop. Watcher2 provides a clean separation: shell libs for git operations, yamlgraph graphs for LLM work, and a thin orchestrator that owns control flow.

## Problem

1. `watch.sh` suppresses failures silently — operational issues go unnoticed.
2. `enforce_worktree.sh` and `bugfix_worktree.sh` duplicate logging, cleanup, and preflight logic.
3. Planning (FR draft, judge) runs on main; only enforcement runs in a worktree — creating split-brain commits.
4. No CI gate before merge — worktree is torn down before validating the PR.

## Implementation Phases

### Phase 1: Git skeleton (no LLM)

Shell-only loop proving the worktree lifecycle end-to-end.

- `lib/inbox_sync.sh` — import GH issues labeled `chaplain`
- `lib/preflight.sh` — prune stale worktrees/branches
- `lib/worktree_setup.sh` — create worktree + branch from main
- Simulate work (touch placeholder), run pre-commit, commit, push
- `lib/create_pr.sh` — `gh pr create`
- `lib/wait_ci.sh` — poll CI status with timeout
- `lib/merge_pr.sh` — `gh pr merge --squash`
- `lib/worktree_teardown.sh` — remove worktree, prune branch, pull main
- `lib/post_merge.sh` — close GH issue
- `lib/metrics.sh` — emit pipeline timing JSON

**Exit criteria:** inbox item → worktree → PR → CI green → merge → cleanup, fully automated.

### Phase 2: Diary copilot node

Add a single yamlgraph copilot invocation inside the worktree.

- One copilot graph: read inbox topic, write diary entry to `docs/diary/`
- Uses `--export-state` to prove state chaining works
- Commit diary, push, PR, merge as in phase 1

**Exit criteria:** copilot writes diary in worktree, merges to main.

### Phase 3: Planning + judging

Add plan session (copilot session 1):

- plan → research → write_acceptance → judge (resume chain)
- Shell: `pytest` after write_acceptance to verify RED
- Shell: check judge verdict, abort if rejected
- Commit FR + tests after each step

**Exit criteria:** FR drafted, tests written, verdict rendered — all in worktree branch.

### Phase 4: Enforcement

Add enforce session (copilot session 2):

- implement → test_and_demo → critique_and_distill (resume chain)
- Shell: finalize (pre-commit, commit, push)
- Copilot: fix finalize if pre-commit fails (resume)
- Inquisitor audit (copilot session 3)

**Exit criteria:** full pipeline — inbox → plan → enforce → PR → CI → merge → cleanup.

### Phase 5: Retire old pipeline

- Remove `watch.sh`, `scripts/enforce_worktree.sh`, `scripts/bugfix_worktree.sh`
- Update CLAUDE.md and reference docs
- Run watcher2 as primary for N cycles, monitor

## Key Design Decisions

- **Everything in the worktree.** All yamlgraph operations (plan, enforce, inquisitor) run inside the worktree. Main stays clean until merge.
- **Diary after every yamlgraph step.** Small copilot node resumes session, appends diary entry while context is warm.
- **Orchestrator owns control flow.** Shell decides whether to continue, abort, or retry — not the graph.
- **No silent suppression.** Failures are logged visibly; non-blocking failures warn but don't halt.
- **CI-gated merge.** Worktree removal only after CI passes and PR merges. CI failure preserves worktree for inspection.

## Dependencies

- FR-269: `--import-state` / `--export-state` (merged, v0.4.71)

## Deliverables

- `watcher2.sh` (new orchestrator)
- `.chaplain/lib/`: `inbox_sync.sh`, `preflight.sh`, `worktree_setup.sh`, `worktree_teardown.sh`, `create_pr.sh`, `wait_ci.sh`, `merge_pr.sh`, `post_merge.sh`, `metrics.sh`
- Per-phase copilot graphs
- Retired: `watch.sh`, `scripts/enforce_worktree.sh`, `scripts/bugfix_worktree.sh`

## Context

Full design: `docs/refactoring-watcher-pipeline-v3.md`
