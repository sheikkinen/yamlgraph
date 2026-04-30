# Feature Request: Watcher2 Pipeline Logging

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-04-29

## Summary

Add per-pipeline log files so that pipeline execution is observable. Currently
the pipeline subprocess output is captured by the engine's PIPE and discarded.

## Value Statement

Operators (human and agent) can diagnose stuck or failed pipelines by reading a
log file instead of guessing from SQLite state snapshots.

## Problem

The dispatcher launches the pipeline via `bash` action type. The engine's
`bash_action.py` captures subprocess stdout/stderr via `asyncio.subprocess.PIPE`
and only logs truncated 200-char snippets at DEBUG/WARNING level to the parent
process's logger — which itself is redirected to `logs/fsm-dispatcher.log`.

Result: pipeline state transitions, action output, and errors are invisible.

The only diagnostic available is:
```bash
sqlite3 data/pipeline.db "SELECT machine_name, current_state FROM machine_state;"
```

This tells *where* the pipeline is stuck, not *why*.

## Research: Existing Patterns

| Project | Pattern | Mechanism | Precedent |
|---------|---------|-----------|-----------|
| **ninchat_voice** (production) | File redirect | `statemachine ... --debug > logs/coordinator.log 2>&1` | Production-proven, used daily |
| **ninchat_voice** | `ui_log` action | Custom Python action writes to DB + Unix socket per state | Per-state YAML entries required |
| **image-generator-fsm** | `log_action.sh` | Shell sourced in each action script, appends to `troubleshoot.log` | Only covers bash actions |
| **old watcher2.sh** | Global exec redirect | `exec > >(tee -a "$LOG_FILE") 2>&1` | Mixes all output in one file |
| **validate-fsm-single.sh** | Tee | `2>&1 \| tee "$LOG_FILE"` | Test-only, captures everything |

## Approaches Evaluated

### A. File redirect in dispatcher YAML config (selected)

Add `2>&1 | tee` to the pipeline launch command in `watcher-dispatcher.yaml`.

```yaml
processing_topic:
    - type: bash
      command: |
        TOPIC="{topic_file}"
        BASENAME=$(basename "$TOPIC" .md)
        LOG="logs/fsm-pipeline-${BASENAME}-$(date +%Y%m%d-%H%M%S).log"
        ls -1t logs/fsm-pipeline-*.log 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null || true
        statemachine .chaplain/config/watcher-pipeline.yaml \
          --actions-dir .chaplain/actions \
          --initial-context "{\"topic_file\":\"$TOPIC\"}" \
          --debug \
          2>&1 | tee "$LOG"
      success: topic_done
      error: error
      timeout: 1800
```

- **Pro**: One config change. Matches ninchat_voice production pattern. Captures
  engine transitions + action output + errors. Accessible via `tail -f`, `grep`,
  `read_file`. Log rotation built in (keep 20).
- **Con**: Only captures what the engine logs to stderr. Nested bash action
  output still truncated to 200 chars by engine internals.

### B. `ui_log` custom action per state

Copy `ui_log_action.py` from ninchat_voice, add `- type: ui_log` entries to
each of the 25 pipeline states.

- **Pro**: Rich per-state messages visible in web UI.
- **Con**: 25 YAML entries to maintain. UI access requires browser tools. The
  agent primarily uses terminal for diagnostics.

### C. `log_action.sh` sourcing in bash scripts

Source `log_action.sh` in each `.chaplain/lib/watcher/*.sh` script, append to
`logs/troubleshoot.log`.

- **Pro**: Proven in image-generator-fsm. Per-action granularity.
- **Con**: Only covers bash-type actions, not `yamlgraph_async` or engine
  transitions. Requires modifying every script.

### D. LangSmith `@traceable` / `create_run()`

Create a custom FSM action that logs state transitions to LangSmith via
`run_type="tool"`.

- **Pro**: Rich dashboard, hierarchical traces, duration tracking.
- **Con**: No terminal access to LangSmith dashboard (agent cannot query it).
  Requires API key. Not used in any FSM project. Overkill for FSM state tracing.

### E. Global `exec > >(tee)` in start-system.sh

Like old `watcher2.sh`: capture all process output in one file.

- **Pro**: Zero config changes. Captures everything.
- **Con**: Mixes dispatcher and pipeline output. When running multiple topics,
  output interleaves. Per-pipeline files are cleaner.

## Decision

**Option A** — file redirect in dispatcher YAML config.

**Rationale**: The primary consumer of these logs is the agent operating via
terminal. File-based logging is optimal for `tail`, `grep`, and `read_file`.
The ninchat_voice production system uses exactly this pattern
(`statemachine ... --debug > logs/coordinator.log 2>&1`). One config change
provides full coverage of engine state transitions and action outcomes.

## Acceptance Criteria

- [ ] Pipeline subprocess output written to `logs/fsm-pipeline-<topic>-<timestamp>.log`
- [ ] `--debug` flag enables verbose engine logging
- [ ] Log rotation: keep last 20 pipeline logs
- [ ] Existing dispatcher log (`logs/fsm-dispatcher.log`) unchanged
- [ ] Log file path visible in dispatcher startup or identifiable by topic name
- [ ] Smoke test: drop topic, verify log file created and contains state transitions

## Related

- ninchat_voice `start-fsm.sh:159-162`: Production pattern (`> "$COORDINATOR_LOG" 2>&1`)
- image-generator-fsm `scripts/log_action.sh`: Action-level logging helper
- ninchat_voice `actions/real/ui_log_action.py`: UI activity log action
- FR-FSM-014: Pipeline Logging and Monitoring (engine-level FR, filed separately)
