# Reflection: FR-265 create_worktree Drafts Ignore Fix

**Date:** 2026-04-21
**FR:** FR-265
**Branch:** feat/fr-265-create-worktree-drafts-ignore-fix

## What Was Done

Fixed a Chaplain pipeline failure where `create_worktree()` called `git add` on a draft FR file under `.chaplain/drafts/`, a directory excluded by `.gitignore`. This caused exit code 1 and halted the pipeline before acceptance tests or judge could run. Fix: use `git add --force` to override `.gitignore` for the draft file, and treat "nothing to commit" (already staged, idempotent run) as success.

## Cognitive Trap: Normalize at the Boundary

The root cause is a **boundary mismatch**: the function assumed `git add` would always succeed for any path, but the filesystem boundary (`.gitignore`) silently converts success into failure. The fix normalizes at the exact boundary where the external tool (git) meets our code — not downstream with a generic error handler.

This is the `downstream_fix` trap in reverse: the symptom was a pipeline halt in the worktree step, but the root cause was an unguarded assumption at the `git add` callsite.

## Heuristic

**Test the tool contract, not just the return value**: When shelling out to `git`, `subprocess`, or any external tool, map every meaningful exit code to an explicit intent. Exit 1 from `git add` can mean "file not found", "permission denied", or "nothing new to stage" — each requires different handling. A blanket `check=True` hides this. Enumerate the cases explicitly.

## Seed

Could the Chaplain's worktree creation be made fully `.gitignore`-aware by scanning `.gitignore` patterns before calling `git add`, and proactively using `--force` only when needed? This would make the behavior self-documenting without requiring callers to know about the ignore rules.
