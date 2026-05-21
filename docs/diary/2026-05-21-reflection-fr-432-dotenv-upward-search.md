# Reflection: FR-432 Upward .env Search with Git Boundary

**Date:** 2026-05-21
**FR:** FR-432 Upward `.env` Search with Git Boundary
**Author:** copilot enforce pass

## Trap

`plausible_wrong_answer` - missing API key errors looked like environment misconfiguration but the actual fault was boundary handling in `.env` discovery.

## What Happened

`yamlgraph.config` loaded `.env` only from exact CWD. When invoked from subdirectories or worktrees, key loading silently failed and later provider errors obscured the root cause. FR-432 moved dotenv discovery to upward search with explicit repository boundary semantics.

## Root Cause

Boundary detection conflated `.git` existence with repository root semantics. Worktrees store `.git` as a file, so `.exists()`-style boundary checks would stop too early and miss root-level `.env`.

## What Worked

- Boundary stop uses `.is_dir()` for `.git`, preserving worktree traversal.
- First-match upward search preserved local override precedence (`CWD/.env` wins).
- Tests encode both normal repo and worktree semantics, plus no-env and hard-boundary cases.

## Seed

Seed: Should environment discovery be centralized into a reusable boundary utility so config loading, hooks, and subprocess launchers all share identical root/stop semantics?
