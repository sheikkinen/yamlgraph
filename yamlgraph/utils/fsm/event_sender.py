"""AF_UNIX datagram event sender for FSM control sockets."""

from __future__ import annotations

import json
import logging
import socket
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SOCKET_PREFIX = "/tmp/statemachine-control"  # noqa: S108 — CONF-302  # nosec B108
MAX_MESSAGE_BYTES = 4096


def send_event(
    machine_name: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Send a control event to the FSM engine socket."""
    socket_path = f"{SOCKET_PREFIX}-{machine_name}.sock"
    if not Path(socket_path).exists():
        raise FileNotFoundError(f"Control socket not found: {socket_path}")

    envelope = {"type": event_type, "payload": payload or {}}
    encoded = json.dumps(envelope).encode("utf-8")
    if len(encoded) > MAX_MESSAGE_BYTES:
        raise ValueError(
            f"Message ({len(encoded)} bytes) exceeds {MAX_MESSAGE_BYTES} byte limit"
        )

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        sock.sendto(encoded, socket_path)
        logger.debug(
            "Sent event %s to %s (%d bytes)", event_type, socket_path, len(encoded)
        )
    finally:
        sock.close()
