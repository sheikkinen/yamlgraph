"""FastAPI app for Incaller with Twilio inbound webhook + Media Streams WebSocket.

IC-000 / REQ-YG-085: Incaller server has:
- POST /incoming: Twilio voice webhook for inbound calls
- WS /voice: Twilio Media Streams WebSocket (same as outcaller)
- GET /health: Health check

The /incoming webhook receives the call, responds with TwiML instructing
Twilio to connect a Media Stream WebSocket back to /voice.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import os
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from projects.outcaller.nodes.coordinator import TelcoSession

logger = logging.getLogger(__name__)

# Environment variables
VOICE_STREAM_URL = os.getenv("VOICE_STREAM_URL", "") or os.getenv("NGROK_URL", "")


def create_app(session: TelcoSession) -> FastAPI:
    """Create FastAPI app with inbound webhook and WebSocket handler.

    Args:
        session: TelcoSession to use for audio queues and call state

    Returns:
        FastAPI app instance
    """
    app = FastAPI(title="Incaller Voice Server")

    @app.post("/incoming")
    async def incoming_call(request: Request) -> Response:
        """Handle Twilio inbound voice webhook.

        Twilio POSTs form data with CallSid, From, To, etc.
        Responds with TwiML instructing Twilio to connect a Media Stream.

        REQ-YG-085: POST /incoming responds with TwiML <Connect><Stream>.
        """
        form = await request.form()
        call_sid = str(form.get("CallSid", ""))
        caller = str(form.get("From", ""))

        # Store call info in session
        session.call_sid = call_sid
        session.caller_number = caller

        logger.info("Incoming call: call_sid=%s, from=%s", call_sid, caller)

        # Convert https:// to wss:// for Twilio WebSocket
        ws_url = VOICE_STREAM_URL.replace("https://", "wss://").replace(
            "http://", "ws://"
        )

        # VOICE_STREAM_URL is trusted config, not user input — f-string is safe
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}/voice" />
    </Connect>
</Response>"""

        return Response(content=twiml.strip(), media_type="application/xml")

    @app.websocket("/voice")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """Handle Twilio Media Streams WebSocket connection.

        Identical to outcaller's WebSocket handler — reused logic.
        """
        await websocket.accept()
        logger.info("WebSocket connection accepted")

        # Task to send outbound audio
        async def send_audio() -> None:
            while True:
                try:
                    audio_data = await session.get_outbound()
                    payload = {
                        "event": "media",
                        "streamSid": session.stream_sid,
                        "media": {"payload": base64.b64encode(audio_data).decode()},
                    }
                    await websocket.send_text(json.dumps(payload))
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Error sending audio: %s", e)
                    break

        # Task to send marks after outbound audio queued
        async def send_marks() -> None:
            while True:
                try:
                    mark_name = await session.get_pending_mark()
                    mark_payload = {
                        "event": "mark",
                        "streamSid": session.stream_sid,
                        "mark": {"name": mark_name},
                    }
                    await websocket.send_text(json.dumps(mark_payload))
                    logger.info("Sent mark: %s", mark_name)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Error sending mark: %s", e)
                    break

        send_task: asyncio.Task | None = None
        mark_task: asyncio.Task | None = None

        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)
                event = data.get("event")

                if event == "connected":
                    logger.info("Twilio connected")

                elif event == "start":
                    stream_sid = data.get("streamSid")
                    call_sid = data.get("start", {}).get("callSid")
                    logger.info(
                        "Stream started: stream_sid=%s, call_sid=%s",
                        stream_sid,
                        call_sid,
                    )
                    session.call_sid = call_sid
                    session.signal_ws_connected(stream_sid)

                    # Start sending outbound audio and marks
                    send_task = asyncio.create_task(send_audio())
                    mark_task = asyncio.create_task(send_marks())

                elif event == "media":
                    payload = data.get("media", {}).get("payload", "")
                    if payload:
                        audio_bytes = base64.b64decode(payload)
                        session.put_inbound(audio_bytes)

                elif event == "mark":
                    mark_name = data.get("mark", {}).get("name", "")
                    logger.info("Received mark: %s", mark_name)
                    session.signal_mark_received(mark_name)

                elif event == "stop":
                    logger.info("Stream stopped - user disconnected")
                    session.signal_disconnected()
                    break

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
            session.signal_disconnected()
        except Exception as e:
            logger.error("WebSocket error: %s", e)
            session.signal_disconnected()
        finally:
            if send_task is not None:
                send_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await send_task
            if mark_task is not None:
                mark_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await mark_task

    @app.get("/health")
    async def health() -> dict:
        """Health check endpoint."""
        return {"status": "ok"}

    return app
