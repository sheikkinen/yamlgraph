# Reflection: FR-316 Watcher2 Validate Split (validate_fix + validate_gate)

**Date:** 2026-05-03
**FR:** FR-316

## Trap

**downstream_fix** — CI failures (diary-gate, commitlint, branch-behind) were surfacing at the `done` step where they could not be repaired, only reported.

## What Happened

Every pipeline run through the old `validate → precommit_check → done` flow leaked fixable issues to CI. Diary files were created but not committed. PR titles used wrong types. Branches fell behind main during enforce.

## Root Cause

The validate boundary did not own the full CI-parity contract. It ran lint/test remediation but not commit-title, branch-freshness, or diary-in-diff checks.

## What Worked

Split validate into two explicit states: `validate_fix` (LLM repair) and `validate_gate` (deterministic CI-parity gate with bounded retry). The gate checks all four CI contracts locally before `done` ever runs.

## Seed

Can the validate_gate diagnostics be used to auto-classify failure patterns and skip LLM repair for purely mechanical fixes (e.g., `git rebase` for branch-behind)?
