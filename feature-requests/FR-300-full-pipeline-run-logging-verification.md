# Feature Request: FR-300 Full Pipeline Run Logging Verification

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Superseded
**Effort:** 0.5 days
**Requested:** 2026-04-30

## Summary

Historical proposal to harden a single-worker FSM smoke-run harness so a "full pipeline run" is only considered successful when logging is explicitly verified (dispatcher validation log + per-topic pipeline log). Superseded by FR-320 harness retirement.

## Value Statement

Watcher operators get a single deterministic command that proves both execution and observability, reducing false-positive "pipeline passed" outcomes where logging silently regressed.

## Problem

The legacy single-worker validation harness validated end-to-end flow, but its pass criteria focused on topic consumption, worktree cleanup, and error text scanning. It did not explicitly fail when expected pipeline log artifacts were missing or when debug logging output was absent.

This leaves a gap: a run can appear healthy while log visibility is degraded, making future failures harder to diagnose.

## Research: Existing Patterns

1. The legacy single-worker harness ran the dispatcher with `--debug` and captured output to `logs/fsm-validation/validate-*.log`.
2. `.chaplain/config/watcher-dispatcher.yaml` `processing_topic` action already writes per-topic logs to `logs/fsm-pipeline-<topic>-<timestamp>.log` using `tee` and `--debug`.
3. `.chaplain/watcher2.sh` uses global `tee` logging (`logs/watcher2-run-*.log`) and log rotation, showing the same "log first, debug by file" operating pattern.

## Objectives

1. Make log verification a first-class part of full pipeline validation.
2. Keep scope limited to the validation harness (no production workflow redesign).

## Constraints

1. No new dependencies; shell + existing CLI tools only.
2. Preserve production behavior in `watcher2.sh` and FSM configs.
3. Use isolated FSM test inbox (`.chaplain/inbox-fsm`) for validation runs.
4. Fail loudly on missing/empty logs (no silent fallback).

## Proposed Solution

Enhance the legacy single-worker harness with explicit logging assertions:

1. After run completion, derive topic basename and assert a matching `logs/fsm-pipeline-<basename>-*.log` file exists and is non-empty.
2. Assert `logs/fsm-validation/validate-*.log` is non-empty and contains pipeline progression markers (for example `topic_done`, `cleaning_up`, or `completed`).
3. Emit both resolved log paths in final output for quick inspection.
4. Add focused tests for the script contract and update docs with the canonical command.

```bash
# Superseded in FR-320 (retirement cleanup): no active command retained here.
```

## Acceptance Criteria

- [ ] Validation script exits 0 only when full pipeline execution succeeds
- [ ] Validation script fails if `logs/fsm-validation/validate-*.log` is missing or empty
- [ ] Validation script fails if matching `logs/fsm-pipeline-<topic>-*.log` is missing or empty
- [ ] Validation script verifies completion/progression markers in log output
- [ ] Script output reports resolved dispatcher and pipeline log file paths
- [ ] Tests added
- [ ] Documentation updated

## Alternatives Considered

1. Keep current script behavior and rely on manual log inspection (rejected: non-deterministic and easy to skip).
2. Validate only dispatcher log and ignore per-topic pipeline log artifacts (rejected: misses the worker-level logging contract).
3. Add external observability tooling for this check (rejected: unnecessary complexity for a local smoke-run requirement).

## Related

- `feature-requests/FR-320-retire-validate-fsm-single-harness.md`
- `.chaplain/config/watcher-dispatcher.yaml`
- `.chaplain/watcher2.sh`
- `feature-requests/FR-295-watcher-fsm-phase2-single-worker-validation.md`
- `feature-requests/FR-FSM-015-watcher2-pipeline-logging.md`
