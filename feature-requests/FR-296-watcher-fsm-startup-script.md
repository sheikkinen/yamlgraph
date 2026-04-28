# Feature Request: Watcher FSM System Startup Script

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-04-28

## Summary

Create `.chaplain/scripts/start-system.sh` — a single script that starts the full watcher FSM system (UI, diagrams, dispatcher, pipeline) following the proven multi-process startup pattern from `image-generator-fsm/scripts/start-system.sh`.

## Value Statement

Operators get a single command to start the entire watcher FSM system with proper sequencing, health checks, and signal-based teardown, replacing ad-hoc manual process launches.

## Problem

The watcher FSM is a multi-process system requiring specific startup order:

1. **UI** must start first — it creates the event socket at `/tmp/statemachine-events.sock`
2. **Diagrams** must be generated before or during startup — the UI can't display FSM visualizations without them
3. **Dispatcher** depends on the event socket — without it, events fall back to database-only
4. **Pipeline** is spawned by the dispatcher — but the dispatcher config must use `--initial-context` (not `--context`)

Currently these are started manually with separate terminal commands. Errors in startup order cause silent degradation (no real-time events, no diagrams in UI).

## Proposed Solution

Create `.chaplain/scripts/start-system.sh` following the image-generator-fsm pattern:

```bash
#!/usr/bin/env bash
# .chaplain/scripts/start-system.sh
# Usage: .chaplain/scripts/start-system.sh [--inbox DIR]
```

### Phases

#### Phase 0: Prerequisites
- Check `$VIRTUAL_ENV`; if unset, activate `.venv/bin/activate` or exit with instructions
- Verify commands: `statemachine`, `statemachine-ui`, `statemachine-validate`, `statemachine-diagrams`
- Verify config files exist: `watcher-dispatcher.yaml`, `watcher-pipeline.yaml`
- Verify actions dir exists: `.chaplain/actions/`
- Create `logs/` and `data/` dirs

#### Phase 1: Cleanup
- Kill by saved PID files first (`kill $(cat logs/fsm-*.pid) 2>/dev/null`), then fallback `pkill -f "statemachine .chaplain"`
- Remove stale event socket (`rm -f /tmp/statemachine-events.sock`)
- Remove stale PID files (`rm -f logs/fsm-*.pid`)
- Reset database state (`rm -f data/pipeline.db` — auto-recreated by engine)

#### Phase 2: Validate & Generate Diagrams
- `statemachine-validate .chaplain/config/watcher-dispatcher.yaml`
- `statemachine-validate .chaplain/config/watcher-pipeline.yaml`
- `statemachine-diagrams .chaplain/config/watcher-dispatcher.yaml --output-dir docs/fsm-diagrams`
- `statemachine-diagrams .chaplain/config/watcher-pipeline.yaml --output-dir docs/fsm-diagrams`

#### Phase 3: Start UI
- `statemachine-ui --port 3001 --project-root . > logs/fsm-ui.log 2>&1 &`
- Wait for event socket: poll `/tmp/statemachine-events.sock` (max 10s)
- Wait for HTTP: poll `localhost:3001` (max 10s)

#### Phase 4: Start Dispatcher
- `statemachine .chaplain/config/watcher-dispatcher.yaml --actions-dir .chaplain/actions --initial-context '{"inbox_dir":".chaplain/inbox"}' > logs/fsm-dispatcher.log 2>&1 &`
- Verify PID alive after 2s
- Print status summary (PIDs, ports, log paths)

#### Phase 5: Keep-Alive
- `while true; do sleep 1; done` — keeps the script alive so the `trap` fires on Ctrl+C
- Without this, backgrounded children survive but cleanup never runs

#### Signal Handling
- `trap cleanup INT TERM` — kills all child PIDs on Ctrl+C
- cleanup function kills UI and dispatcher by saved PID, then `pkill -f "statemachine .chaplain"` as fallback for spawned pipelines
- Write PID files (`logs/fsm-ui.pid`, `logs/fsm-dispatcher.pid`) for clean shutdown

### Key Differences from image-generator-fsm

| Aspect | image-generator-fsm | watcher |
|--------|---------------------|---------|
| Machines | 4 independent FSMs | 1 dispatcher spawning pipeline |
| UI | npm-based dev server | `statemachine-ui` CLI |
| Sample job | Creates test job on startup | Uses inbox directory |
| Log capture | Per-machine log files | Dispatcher captures pipeline via bash action |

### Config

The script uses `.chaplain/config/` for YAML configs and `.chaplain/actions/` for custom actions. The inbox directory defaults to `.chaplain/inbox` (production) but can be overridden:

```bash
# Production
.chaplain/scripts/start-system.sh

# Test with isolated inbox
.chaplain/scripts/start-system.sh --inbox .chaplain/inbox-fsm
```

## Acceptance Criteria

- [ ] `.chaplain/scripts/start-system.sh` exists and is executable
- [ ] Checks virtual environment, activates `.venv/` or exits with instructions
- [ ] Validates both config files before starting any process
- [ ] Generates diagrams for both configs
- [ ] Starts UI first, waits for event socket
- [ ] Starts dispatcher with correct `--initial-context` JSON
- [ ] Keep-alive loop keeps script running so `trap` fires on Ctrl+C
- [ ] `Ctrl+C` cleanly shuts down all processes (UI, dispatcher, spawned pipelines)
- [ ] `--inbox DIR` flag overrides inbox directory
- [ ] Status summary printed after successful startup (PIDs, ports, log paths)
- [ ] Script is idempotent (safe to run after unclean shutdown)

## Alternatives Considered

1. **systemd/launchd service files** — Too heavyweight for development workflow
2. **Docker Compose** — Adds container overhead; the FSM is a local dev tool
3. **Makefile targets** — Doesn't handle process lifecycle (cleanup, signals)

## Related

- `image-generator-fsm/scripts/start-system.sh` — Reference implementation
- `fsm/scripts/start-system.sh` — Simpler reference from statemachine-engine
- FR-295: Watcher FSM Phase 2 (single-worker validation)
- FR-292: Pipeline path alignment
- `.chaplain/config/watcher-dispatcher.yaml` — Dispatcher config
- `.chaplain/config/watcher-pipeline.yaml` — Pipeline config
