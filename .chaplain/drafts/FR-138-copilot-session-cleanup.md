# Feature Request: Copilot Session Cleanup Script

**ID:** FR-138
**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-03-08

## Summary

Add a script to prune stale Copilot CLI sessions from `~/.copilot/session-state/`. Today 664 sessions accumulate indefinitely (12 MB, growing ~300/week) with no automated or documented cleanup path. A simple age-based pruning script restores control without modifying the Copilot CLI itself.

## Value Statement

Developers running copilot nodes (FR-081) and the chaplain watch pipeline get automatic reclamation of stale session state, preventing unbounded disk growth and removing the mental burden of manual cleanup.

## Problem

Each `copilot -p` invocation creates a persistent session directory under `~/.copilot/session-state/<uuid>/` containing `workspace.yaml`, `checkpoints/`, and `files/`. These sessions:

1. **Accumulate indefinitely** — no TTL, no auto-expiry, no `copilot gc` command exists.
2. **Grow fast** — the chaplain watch pipeline (`watch.sh` → `enforce_worktree.sh`) creates 10-20 sessions/day via parallel copilot nodes; current count is 664 sessions spanning 4 weeks.
3. **Require manual cleanup** — the only option today is `rm -rf ~/.copilot/session-state/<uuid>` per session, with no guidance on which are safe to delete.
4. **Silently degrade** — large session directories slow `--resume` picker startup and waste disk.

The Copilot CLI offers `--resume <id>` and `--continue` for session reuse but provides no list, delete, or prune commands.

## Proposed Solution

### 1. Cleanup script: `scripts/copilot_session_gc.sh`

A shell script that prunes sessions older than a configurable age threshold:

```bash
#!/usr/bin/env bash
# scripts/copilot_session_gc.sh — Prune old Copilot CLI sessions
#
# Usage:
#   scripts/copilot_session_gc.sh [--max-age DAYS] [--dry-run]
#
# Defaults: --max-age 7

set -euo pipefail

MAX_AGE_DAYS=7
DRY_RUN=false
SESSION_DIR="${COPILOT_SESSION_DIR:-$HOME/.copilot/session-state}"

# Parse args...
# For each session dir older than MAX_AGE_DAYS (by mtime):
#   - Skip the currently active session (from $COPILOT_SESSION_ID if set)
#   - Log the session UUID, age, and summary (from workspace.yaml)
#   - Remove unless --dry-run
```

Key design decisions:
- **Shell script, not Python** — cleanup runs outside Python venv; no yamlgraph dependency.
- **Age-based, not count-based** — simple, predictable, no need to parse session content.
- **`--dry-run` default for first run** — show what would be deleted before deleting.
- **Skip active session** — never delete the session that invoked the script.
- **Environment override** — `COPILOT_SESSION_DIR` for testing and non-standard installs.

### 2. Integration with watch.sh

Add a periodic cleanup call to the chaplain watch loop:

```bash
# In .chaplain/watch.sh, at the top of each poll cycle:
if (( loop_count % 10 == 0 )); then
    scripts/copilot_session_gc.sh --max-age 3 >> tmp/session-gc.log 2>&1
fi
```

### 3. Standalone CLI usage

```bash
# Preview what would be removed
scripts/copilot_session_gc.sh --dry-run

# Remove sessions older than 7 days (default)
scripts/copilot_session_gc.sh

# Aggressive cleanup: remove sessions older than 1 day
scripts/copilot_session_gc.sh --max-age 1
```

## Acceptance Criteria

- [ ] `scripts/copilot_session_gc.sh` exists and is executable
- [ ] `--max-age DAYS` controls the age threshold (default: 7)
- [ ] `--dry-run` lists sessions that would be deleted without removing them
- [ ] Active session (matching `$COPILOT_SESSION_ID` env var) is never deleted
- [ ] Each deleted session is logged with UUID and age
- [ ] Script exits cleanly when `~/.copilot/session-state/` does not exist
- [ ] Script is idempotent (running twice has no side effects)
- [ ] Tests: unit test validates age filtering logic (mock filesystem or temp dir)
- [ ] Documentation: add cleanup section to `reference/getting-started.md` or README

## Alternatives Considered

1. **Python script in yamlgraph CLI** (`yamlgraph session gc`) — Would add a dependency on yamlgraph being installed just to clean up host-level state. The Copilot session directory is a CLI concern, not a framework concern. A standalone shell script is more appropriate. Rejected.

2. **Automatic cleanup in `copilot_node.py` after graph completion** — Fragile: would break `--resume` for downstream graphs or manual continuation. Session lifetime is a user/operator decision, not a framework decision. Rejected.

3. **Count-based pruning (keep N most recent)** — Less predictable than age-based. A user with 50 sessions from today shouldn't have them all deleted just because there are more than N. Rejected.

4. **Wait for Copilot CLI to add `copilot session gc`** — No indication this is planned. The session directory structure is stable and well-understood. A local script solves the immediate problem. Can be deprecated if the CLI adds native support later.

## Related

- `yamlgraph/node_factory/copilot_node.py` — Creates sessions via subprocess
- `feature-requests/105-copilot-session-continuations.md` — Session resumption (FR-105)
- `feature-requests/FR-081-copilot-node.md` — Copilot node type
- `.chaplain/watch.sh` — Primary session accumulation source
- `~/.copilot/session-state/` — Host-level session storage (664 sessions, 12 MB)
