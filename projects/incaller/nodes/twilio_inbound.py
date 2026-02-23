"""Twilio inbound call tool nodes for YAMLGraph Incaller.

IC-000 / REQ-YG-084: await_call node starts HTTP+WS server and blocks
until an inbound Twilio call connects via webhook + Media Streams.

Unlike outcaller's initiate_call (which dials outbound), await_call:
1. Starts server with /incoming webhook + /voice WebSocket
2. Waits for Twilio to POST to /incoming (call arrives)
3. Returns TwiML instructing Twilio to connect Media Stream
4. Blocks until WebSocket connects
5. Returns call info with caller_number from webhook
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

# Load .env from incaller directory (projects/incaller/.env)
try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass  # dotenv optional

logger = logging.getLogger(__name__)

# Environment variables
VOICE_STREAM_URL = os.getenv("VOICE_STREAM_URL", "") or os.getenv("NGROK_URL", "")
INCALLER_TIMEOUT = int(os.getenv("INCALLER_TIMEOUT", "300"))

# Re-import coordinator from outcaller (REQ-YG-086: reuse without duplication)
from projects.outcaller.nodes.coordinator import (  # noqa: E402
    CallNotAnsweredError,
    MissingStreamUrlError,
    TelcoSession,
    set_active_session,
)

__all__ = ["await_call", "INCALLER_TIMEOUT", "VOICE_STREAM_URL"]


def await_call(state: dict[str, Any]) -> dict[str, Any]:
    """Start server and wait for inbound Twilio call.

    1. Creates TelcoSession with incaller server (HTTP webhook + WebSocket)
    2. Starts uvicorn on VOICE_SERVER_PORT
    3. Blocks until Twilio POSTs to /incoming AND WebSocket connects
    4. Returns call_info with call_sid, stream_sid, and caller_number

    Args:
        state: Graph state (not used for inbound; caller dials in)

    Returns:
        {"call_info": {"call_sid": "...", "stream_sid": "...", "caller_number": "..."}}

    Raises:
        MissingStreamUrlError: If VOICE_STREAM_URL not set
        CallNotAnsweredError: If no call arrives within timeout
    """
    # Validate VOICE_STREAM_URL is set
    if not VOICE_STREAM_URL:
        raise MissingStreamUrlError()

    # Create session and start server
    session = TelcoSession()
    session.start_with_app(create_incaller_app)  # Use incaller's server.py
    set_active_session(session)

    # Wait for uvicorn to be ready
    time.sleep(1.0)

    logger.info(
        "Incaller server running. Waiting for inbound call (timeout: %ds)...",
        INCALLER_TIMEOUT,
    )

    # Wait for WebSocket to connect (Twilio calls after webhook returns TwiML)
    if not session._ws_connected.wait(timeout=INCALLER_TIMEOUT):
        session.stop()
        raise CallNotAnsweredError(INCALLER_TIMEOUT)

    logger.info(
        "Call connected: call_sid=%s, stream_sid=%s, from=%s",
        session.call_sid,
        session.stream_sid,
        getattr(session, "caller_number", "unknown"),
    )

    return {
        "call_info": {
            "call_sid": session.call_sid,
            "stream_sid": session.stream_sid,
            "caller_number": getattr(session, "caller_number", ""),
        }
    }


def create_incaller_app(session: TelcoSession):
    """Factory function to create incaller FastAPI app."""
    from projects.incaller.server import create_app

    return create_app(session)
