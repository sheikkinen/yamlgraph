# Feature Request: FR-437 FSM UI Activity Log Bridge

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 day
**Requested:** 2026-05-21

## Summary

Add a `yamlgraph.utils.fsm.ui_log` utility that lets yamlgraph graph nodes emit messages to the statemachine-engine UI activity log during execution, bridging the current black-box gap.

## Value Statement

Graph authors can emit progress, diagnostic, or user-facing messages to the FSM operator UI from within graph nodes, without coupling graph logic to application-specific logging infrastructure.

## Problem

When a yamlgraph graph runs inside an FSM action (`YamlgraphAsyncAction`), the graph execution is a black box to the FSM operator:

```
FSM action: "🚀 Launching graph X"    ← visible in UI activity log
  └─ graph node 1 executes             ← invisible
  └─ graph node 2 executes             ← invisible
  └─ graph node 3 executes             ← invisible
FSM action: "✓ Graph complete"         ← visible in UI activity log
```

The ninchat_voice project has `emit_ui_activity()` in `services/ui_activity.py`, but it's:
1. Application-specific (not reusable across FSM-integrated projects)
2. Inaccessible from within graph nodes (nodes are pure functions returning state dicts)
3. Uses subprocess invocation (`python -m statemachine_engine.database.cli send-event`) — correct but undocumented as a pattern

Graph authors currently have no way to emit structured progress messages during multi-step graph execution.

## Proposed Solution

### New module: `yamlgraph/utils/fsm/ui_log.py`

```python
"""Emit activity events to the statemachine-engine UI activity log.

Bridge for yamlgraph graph nodes to send structured progress messages
to the FSM operator during execution.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)


def emit_ui_activity(
    message: str,
    *,
    level: str = "INFO",
    source: str = "yamlgraph",
) -> None:
    """Emit a UI activity event to the statemachine-engine.

    Guarded by UI_EVENTS_ENABLED env var (default false).
    No-op when statemachine-engine is not installed or UI events are disabled.

    Args:
        message: Human-readable activity description.
        level: Log level (INFO, WARNING, ERROR).
        source: Source identifier (e.g. state name, node name).
    """
    if os.getenv("UI_EVENTS_ENABLED", "false").lower() != "true":
        return

    payload = json.dumps({"message": message, "level": level.upper()})
    cmd = [
        sys.executable,
        "-m",
        "statemachine_engine.database.cli",
        "send-event",
        "--target", "ui",
        "--type", "activity_log",
        "--source", source,
        "--payload", payload,
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=False, timeout=5)
    except FileNotFoundError:
        logger.debug("statemachine_engine not installed, skipping UI log")
    except subprocess.TimeoutExpired:
        logger.warning("UI activity log emission timed out")
```

### Usage from graph nodes

**Option A: Direct import in Python tool nodes**

```python
# nodes/my_tool.py
from yamlgraph.utils.fsm.ui_log import emit_ui_activity

def my_node(state):
    emit_ui_activity("Processing document...", source="document_processor")
    result = do_work(state["input"])
    emit_ui_activity(f"Document processed: {len(result)} items", source="document_processor")
    return {"output": result}
```

**Option B: Via state key convention (future)**

A graph-level `ui_log` state key that collects messages and the FSM action emits them post-node. This is a future extension, not part of this FR.

### What changes in ninchat_voice

The application-specific `services/ui_activity.py` can be replaced by importing from yamlgraph:

```python
# Before (application-specific)
from services.ui_activity import emit_ui_activity

# After (framework-provided)
from yamlgraph.utils.fsm.ui_log import emit_ui_activity
```

The ninchat_voice version can be deprecated and removed once all callers migrate.

### Export from fsm package

```python
# yamlgraph/utils/fsm/__init__.py
from yamlgraph.utils.fsm.ui_log import emit_ui_activity

__all__ = [
    ...,
    "emit_ui_activity",
]
```

## Acceptance Criteria

- [x] `yamlgraph/utils/fsm/ui_log.py` exists with `emit_ui_activity()` function
- [x] Guarded by `UI_EVENTS_ENABLED` env var (no-op when disabled)
- [x] Graceful degradation: no crash when statemachine-engine is not installed
- [x] Timeout protection on subprocess call (5s default)
- [x] Exported from `yamlgraph.utils.fsm` package
- [x] Unit tests with mocked subprocess
- [x] Documented in `yamlgraph/utils/fsm/` module docstring

## Design Decisions

### Why subprocess, not direct import?

The `statemachine_engine.database.cli send-event` subprocess approach is the established pattern in ninchat_voice. It:
- Writes to the FSM database (persistence)
- Emits via Unix socket to statemachine-ui WebSocket (real-time display)
- Works without importing statemachine_engine internals (looser coupling)

Direct Python import of `statemachine_engine.database` would be tighter coupling and would require the FSM dependency at import time rather than runtime.

### Why not a custom tool type?

A `ui_log` tool type would require graph YAML changes and node_factory extension. Direct Python import from tool nodes is simpler and doesn't require framework plumbing for what is essentially a side-effect utility.

## Related

- [yamlgraph/utils/fsm/](../yamlgraph/utils/fsm/): FSM bridge package (5 files, ~400 lines)
- [ninchat_voice/services/ui_activity.py](../projects/ninchat_voice/services/ui_activity.py): Application-specific version to be replaced
- [FR-431](FR-431-fsm-reinvention-hook.md): FSM reinvention detection hook
