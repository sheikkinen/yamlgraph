"""Emit UI activity log events for FSM-integrated graph execution.

This helper bridges yamlgraph nodes to the statemachine-engine activity log
without importing engine internals at module import time.
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
    timeout_seconds: float = 5,
) -> None:
    """Emit an activity event to statemachine-engine UI activity log.

    Guarded by `UI_EVENTS_ENABLED=true` to avoid subprocess overhead in
    deployments without a local statemachine UI/event bridge.
    """
    if os.getenv("UI_EVENTS_ENABLED", "false").lower() != "true":
        return

    payload = json.dumps({"message": message, "level": level.upper()})
    cmd = [
        sys.executable,
        "-m",
        "statemachine_engine.database.cli",
        "send-event",
        "--target",
        "ui",
        "--type",
        "activity_log",
        "--source",
        source,
        "--payload",
        payload,
    ]

    try:
        subprocess.run(  # noqa: S603 — CONF-255
            cmd,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        logger.debug("statemachine_engine CLI is unavailable; skipping UI activity")
    except subprocess.TimeoutExpired:
        logger.warning("UI activity log emission timed out after %ss", timeout_seconds)
