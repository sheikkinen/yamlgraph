# Diary: FR-236 Worktree Teardown Editable Install Guard

**Date:** 2026-04-18
**FR:** FR-236 (worktree teardown)

## Cognitive Process

A subtle failure mode surfaced post-teardown: pip trusts `direct_url.json` in `.dist-info/` without verifying the referenced path still exists. After removing a worktree, the stale file causes `ModuleNotFoundError` on subsequent installs, a symptom far removed from its root cause.

## Trap: Downstream Symptom Fix

The immediate symptom is `ModuleNotFoundError`. The naive fix would be to re-run `pip install -e .` unconditionally on each worktree use. The correct fix is to remove the stale `direct_url.json` at teardown — normalizing at the boundary where the invariant is violated.

## Insight

**File system state left by teardown is a boundary condition.** When a worktree is removed, any metadata files referencing it must also be cleaned up. Package managers (pip) trust their own metadata absolutely; stale metadata is worse than missing metadata.

## Heuristic

Treat post-teardown filesystem state as an external input boundary. Any file that encodes a path to a removed resource is stale by definition and must be cleaned at teardown, not lazily discovered at next use.

## Seed

Should the worktree helper expose a `verify_install()` function that checks `direct_url.json` references are still valid, usable as a pre-flight check before any command that depends on the installed package?
