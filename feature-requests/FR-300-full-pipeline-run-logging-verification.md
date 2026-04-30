# Feature Request: FR-300 Full Pipeline Run Logging Verification

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-04-30

## Summary

Harden the existing FSM smoke-run script so a "full pipeline run" is only considered successful when logging is explicitly verified (dispatcher validation log + per-topic pipeline log).

## Value Statement

Watcher operators get a single deterministic command that proves both execution and observability, reducing false-positive "pipeline passed" outcomes where logging silently regressed.

## Problem

`.chaplain/scripts/validate-fsm-single.sh` already validates end-to-end flow, but its pass criteria focus on topic consumption, worktree cleanup, and error text scanning. It does not explicitly fail when expected pipeline log artifacts are missing or when debug logging output is absent.

This leaves a gap: a run can appear healthy while log visibility is degraded, making future failures harder to diagnose.

## Research: Existing Patterns

1. `.chaplain/scripts/validate-fsm-single.sh` runs dispatcher with `--debug` and captures output to `logs/fsm-validation/validate-*.log`.
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

Enhance `.chaplain/scripts/validate-fsm-single.sh` with explicit logging assertions:

1. After run completion, derive topic basename and assert a matching `logs/fsm-pipeline-<basename>-*.log` file exists and is non-empty.
2. Assert `logs/fsm-validation/validate-*.log` is non-empty and contains pipeline progression markers (for example `topic_done`, `cleaning_up`, or `completed`).
3. Emit both resolved log paths in final output for quick inspection.
4. Add focused tests for the script contract and update docs with the canonical command.

```bash
bash .chaplain/scripts/validate-fsm-single.sh .chaplain/inbox-fsm/test-pipeline-run.md
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

- `.chaplain/scripts/validate-fsm-single.sh`
- `.chaplain/config/watcher-dispatcher.yaml`
- `.chaplain/watcher2.sh`
- `feature-requests/FR-295-watcher-fsm-phase2-single-worker-validation.md`
- `feature-requests/FR-FSM-015-watcher2-pipeline-logging.md`
