# FR-179: Asterisk ARI + AudioSocket Provider

**Priority:** MEDIUM
**Type:** Feature
**Status:** Amend
**Effort:** 5 days
**Requested:** 2026-03-11

## Summary

Add Asterisk PBX support to `projects/outcaller/` via the Asterisk REST Interface (ARI) for call lifecycle control and AudioSocket (TCP) for raw PCM media exchange. Introduce a `TelephonyProvider` protocol so Twilio and Asterisk implementations share a common boundary interface.

## Value Statement

YAMLGraph developers can deploy the outcaller/incaller voice agent on private PBX or carrier infrastructure with the same YAML-driven orchestration currently used for Twilio, without changing any graph YAML.

## Problem

`projects/outcaller/nodes/` is tightly coupled to Twilio's proprietary WebSocket Media Streams protocol (mulaw 8 kHz, JSON frames with `media.payload` base64 field, `mark` echo mechanism). There is no abstraction for the telephony boundary. Asterisk, the industry standard for enterprise PBX, uses a fundamentally different protocol:

- **Call control:** ARI REST API (not Twilio REST)
- **Media:** AudioSocket TCP with a 3-byte binary header `(type: uint8, length: uint16-BE)` — not WebSocket JSON frames
- **Audio format:** 16-bit signed PCM, 8 kHz or 16 kHz — not mulaw

Without a `TelephonyProvider` boundary, every new carrier requires forking the core `coordinator.py`, `tts.py`, and `stt.py` nodes.

## Proposed Solution

### 1. `TelephonyProvider` Protocol (boundary abstraction)

Introduce `projects/outcaller/providers/base.py` defining a minimal protocol:

```python
# projects/outcaller/providers/base.py
from typing import Protocol, runtime_checkable
import asyncio

@runtime_checkable
class TelephonyProvider(Protocol):
    """Boundary: normalises carrier-specific framing into queues of raw bytes."""

    async def originate(self, to: str, from_: str, **kwargs) -> str:
        """Start an outbound call. Returns call_sid / channel_id."""
        ...

    async def hangup(self, call_id: str) -> None:
        """Terminate the call."""
        ...

    async def read_audio(self) -> bytes | None:
        """Return next PCM frame (16-bit, 8 kHz mono) or None on hangup."""
        ...

    async def write_audio(self, pcm: bytes) -> None:
        """Send PCM frame to the remote party."""
        ...

    async def wait_connected(self, timeout: float = 30.0) -> None:
        """Block until the AudioSocket TCP connection is established."""
        ...
```

### 2. `AudioSocketServer` — boundary normalisation node

Reads from the TCP stream and writes framed audio back. Exposes `start()`/`stop()` for explicit lifecycle control. `handle()` runs a concurrent `_send_loop` task so the outbound queue is drained while the inbound reader is active. `_signal_hangup()` is the only write path to `_inbound` from external callers (e.g. `AsteriskProvider._ari_event_loop`), preventing boundary leakage.

```python
# projects/outcaller/providers/asterisk/audiosocket.py
import asyncio
import struct

MSG_HANGUP = 0x00
MSG_AUDIO  = 0x10
MSG_ID     = 0x01

class AudioSocketServer:
    """
    TCP server implementing the AudioSocket 3-byte framing protocol.
    Normalises raw PCM at the boundary; the rest of the pipeline is format-agnostic.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 9092):
        self._host = host
        self._port = port
        self._inbound: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._outbound: asyncio.Queue[bytes] = asyncio.Queue()
        self._connected = asyncio.Event()
        self._tcp_server: asyncio.Server | None = None

    async def start(self) -> None:
        """Start TCP listener. Must be called before originate()."""
        self._tcp_server = await asyncio.start_server(
            self.handle, self._host, self._port
        )

    async def stop(self) -> None:
        """Close TCP listener; release port."""
        if self._tcp_server:
            self._tcp_server.close()
            await self._tcp_server.wait_closed()
            self._tcp_server = None

    async def _signal_hangup(self) -> None:
        """Push None sentinel to inbound queue (normalised hangup signal)."""
        await self._inbound.put(None)

    async def _send_loop(self, writer: asyncio.StreamWriter) -> None:
        while True:
            pcm = await self._outbound.get()
            frame = struct.pack(">BH", MSG_AUDIO, len(pcm)) + pcm
            writer.write(frame)
            await writer.drain()

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._connected.set()
        send_task = asyncio.create_task(self._send_loop(writer))
        try:
            while True:
                header = await reader.readexactly(3)          # Normalize at the boundary
                kind, length = struct.unpack(">BH", header)
                payload = await reader.readexactly(length) if length else b""
                if kind == MSG_HANGUP:
                    await self._signal_hangup()               # sentinel → end of stream
                    break
                if kind == MSG_AUDIO:
                    await self._inbound.put(payload)
                # MSG_ID (0x01) carries channel UUID; log and ignore
        finally:
            send_task.cancel()
            writer.close()

    async def read_audio(self) -> bytes | None:
        return await self._inbound.get()

    async def write_audio(self, pcm: bytes) -> None:
        await self._outbound.put(pcm)
```

### 3. `AsteriskProvider` — call lifecycle via ARI REST + ARI WebSocket events

ARI call control uses REST. `StasisStart` / `StasisEnd` / `ChannelHangupRequest` events are delivered over an ARI WebSocket (`ws://<host>/ari/events?api_key=<>&app=<>`). `wait_connected()` gates on the AudioSocket TCP connection arriving (set by `AudioSocketServer.handle()`), which happens after the dialplan invokes the `AudioSocket()` channel application. Hangup pushes the None sentinel via `_server._signal_hangup()` — never by direct queue access.

The `_ari_event_loop` wraps the WebSocket body in `try/finally` so that an abrupt disconnect (network error, Asterisk restart) always calls `_signal_hangup()`, preventing `read_audio()` from blocking indefinitely. `hangup()` explicitly cancels `_ws_task` so the event loop task does not outlive the call object even if the ARI REST call raises.

```python
# projects/outcaller/providers/asterisk/ari.py
import asyncio
import contextlib
import json

import httpx
import websockets

from .audiosocket import AudioSocketServer

class AsteriskProvider:
    def __init__(self, ari_url: str, username: str, password: str,
                 app_name: str, audiosocket_port: int = 9092):
        self._ari_url = ari_url.rstrip("/")
        self._auth = (username, password)
        self._app = app_name
        self._server = AudioSocketServer(port=audiosocket_port)
        self._channel_id: str | None = None
        self._ws_task: asyncio.Task | None = None

    async def _ari_event_loop(self) -> None:
        """Subscribe to ARI WebSocket events; signal hangup on StasisEnd or disconnect."""
        user, pw = self._auth
        ws_url = (
            f"{self._ari_url.replace('http', 'ws')}/ari/events"
            f"?api_key={user}:{pw}&app={self._app}"
        )
        try:
            async with websockets.connect(ws_url) as ws:
                async for raw in ws:
                    event = json.loads(raw)
                    etype = event.get("type")
                    if etype in ("StasisEnd", "ChannelHangupRequest"):
                        await self._server._signal_hangup()
                        break
        finally:
            # Ensure hangup is always signalled even on abrupt WebSocket disconnect
            await self._server._signal_hangup()

    async def originate(self, to: str, from_: str, **kwargs) -> str:
        await self._server.start()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._ari_url}/ari/channels",
                auth=self._auth,
                params={
                    "endpoint": to,
                    "app": self._app,
                    "callerId": from_,
                },
            )
            resp.raise_for_status()
            self._channel_id = resp.json()["id"]
        self._ws_task = asyncio.create_task(self._ari_event_loop())
        return self._channel_id

    async def hangup(self, call_id: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.delete(
                f"{self._ari_url}/ari/channels/{call_id}", auth=self._auth
            )
        if self._ws_task:
            self._ws_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._ws_task
        await self._server.stop()

    async def read_audio(self) -> bytes | None:
        return await self._server.read_audio()

    async def write_audio(self, pcm: bytes) -> None:
        await self._server.write_audio(pcm)

    async def wait_connected(self, timeout: float = 30.0) -> None:
        """Unblocks when the AudioSocket TCP connection arrives (after dialplan AudioSocket())."""
        await asyncio.wait_for(self._server._connected.wait(), timeout=timeout)
```

### 4. YAML node configuration

```yaml
# In outcaller.yaml / incaller.yaml:
nodes:
  telephony:
    type: tool
    tool: asterisk_provider
    config:
      ari_url: "http://localhost:8088"
      username: "asterisk"
      password: "asterisk"
      app_name: "yamlgraph_outcaller"
      audiosocket_port: 9092
```

### 5. `websockets` dependency

Add `websockets>=12.0` to the `telco` extras in `pyproject.toml`:

```toml
[project.optional-dependencies]
telco = [
    "twilio>=9.0.0",
    "elevenlabs>=1.0.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.27.0",
    "websockets>=12.0",
]
```

### 6. Scope boundary

This FR covers:
- `TelephonyProvider` protocol in `projects/outcaller/providers/base.py`
- `AudioSocketServer` TCP server with `start()`/`stop()` lifecycle, 3-byte header framing, concurrent `_send_loop`, and `_signal_hangup()` method
- `AsteriskProvider` wrapping ARI REST (originate/hangup) + ARI WebSocket event subscriber; calls `server.start()` in `originate()`, `server.stop()` in `hangup()`
- `StasisEnd` / `ChannelHangupRequest` event handling calls `_signal_hangup()` (not direct queue write)
- `_ari_event_loop` wraps WebSocket body in `try/finally`; `_signal_hangup()` always called on exit
- `hangup()` cancels `_ws_task` after the REST call (regardless of REST call success)
- `import json` at module top level (not inside loop body)
- `wait_connected()` gates on AudioSocket TCP connection, not on StasisStart
- Unit tests with mock ARI server and synthetic AudioSocket binary streams
- `reference/asterisk-setup.md` (Asterisk dialplan snippet, ARI config example)
- `websockets>=12.0` added to `telco` extras in `pyproject.toml`
- `REQ-YG-161` added to `ARCHITECTURE.md`

This FR does **not** cover:
- Refactoring `TelcoSession` or `coordinator.py` to use the protocol (separate FR)
- Transcoding between PCM rates inside YAMLGraph (delegated to ffmpeg tool)
- PSTN routing, SIP trunk configuration, or media encryption (deployment concerns)

## Acceptance Criteria

- [ ] `TelephonyProvider` protocol defined in `projects/outcaller/providers/base.py`; `AsteriskProvider` passes `isinstance(provider, TelephonyProvider)` check
- [ ] `AudioSocketServer.start()` binds the TCP listener; `stop()` closes it and releases the port — verified by unit test that `start()` → connection arrives → `stop()` with no port leak
- [ ] `AudioSocketServer.handle()` correctly unpacks 3-byte header (`type`, `uint16-BE length`) for `MSG_AUDIO (0x10)` and `MSG_HANGUP (0x00)` frame types
- [ ] `AudioSocketServer._send_loop` drains `_outbound` queue and writes framed audio bytes to the TCP writer; `handle()` starts `_send_loop` as a concurrent `asyncio.Task` and cancels it on hangup/disconnect
- [ ] `AudioSocketServer._signal_hangup()` is the sole write path for the None sentinel from external callers; `_ari_event_loop` calls `_signal_hangup()`, not `self._server._inbound.put(None)` directly
- [ ] Unit test: `write_audio(pcm)` → framed bytes (3-byte header + pcm) arrive at the mock TCP socket
- [ ] `AsteriskProvider.originate()` calls `server.start()` before `POST /ari/channels` and starts the ARI WebSocket event subscriber task; `hangup()` calls `DELETE /ari/channels/{id}` then cancels `_ws_task` then calls `server.stop()`
- [ ] `AsteriskProvider._ari_event_loop()` connects to `ws://<host>/ari/events?api_key=<user>:<pw>&app=<name>`; `StasisEnd` or `ChannelHangupRequest` event calls `_signal_hangup()`
- [ ] `AsteriskProvider._ari_event_loop()` wraps WebSocket body in `try/finally`; `_signal_hangup()` is called in the `finally` clause — guaranteeing `read_audio()` never blocks indefinitely on abrupt WebSocket disconnect
- [ ] Unit test: mock ARI WebSocket that closes connection abruptly (no hangup event); verify `_signal_hangup()` is still called and `read_audio()` returns `None`
- [ ] `hangup()` cancels `_ws_task` after REST call; unit test: mock REST client that raises on DELETE still results in `_ws_task` being cancelled
- [ ] `import json` is at module top level in `ari.py`, not inside the `async for` loop body
- [ ] `wait_connected()` blocks until the AudioSocket TCP connection is established (i.e., `AudioSocketServer._connected` event is set by `handle()`), not on StasisStart
- [ ] `read_audio()` returns `None` on hangup (sentinel-based termination, mirrors Twilio `None` sentinel in `TelcoSession.inbound`)
- [ ] Unit test: mock TCP server emits a sequence of `MSG_AUDIO` frames followed by `MSG_HANGUP`; `AudioSocketServer` yields all audio frames then `None`
- [ ] Unit test: mock `httpx` client verifies `originate()` REST call params and `hangup()` DELETE call
- [ ] Unit test: malformed frame (truncated header) raises `asyncio.IncompleteReadError` — not silently dropped
- [ ] Unit test: mock ARI WebSocket emits `StasisEnd`; `_ari_event_loop` calls `_signal_hangup()`, which pushes `None` sentinel to inbound queue
- [ ] `reference/asterisk-setup.md` documents: Asterisk `extensions.conf` snippet, `ari.conf` permissions, AudioSocket channel driver config, and port firewall note
- [ ] `websockets>=12.0` present in `telco` extras in `pyproject.toml`
- [ ] `ruff check` and `pytest tests/unit/` pass with no new failures
- [ ] Requirement `REQ-YG-161` added to `ARCHITECTURE.md`; test tagged `@pytest.mark.req("REQ-YG-161")`

## Alternatives Considered

- **AEAP (Asterisk External App Protocol):** More feature-rich but adds a JSON RPC layer that duplicates framing already present in AudioSocket. Rejected: over-engineered for raw audio streaming.
- **SIP/RTP via pjsip or aiortc:** Requires jitter buffer, SSRC tracking, and DTLS-SRTP — high entropy (Commandment 8). Rejected.
- **Full `TelcoSession` refactor:** Replacing the Twilio `TelcoSession` coordinator with a provider-agnostic version is valuable but out of scope here (would risk regressing OC-006 mark tracking). Separate FR warranted after this lands.

## Judge Review — AMEND (2026-03-11)

Three issues from initial review are resolved in this amended version:

1. **WebSocket disconnect leaves `read_audio()` blocked (critical):** Fixed. `_ari_event_loop` now wraps the WebSocket body in `try/finally` and calls `_signal_hangup()` in `finally`, guaranteeing the None sentinel is pushed even on abrupt disconnect. New acceptance criterion added.

2. **`import json` inside loop body:** Fixed. `import json` moved to module top level in `ari.py`.

3. **`hangup()` never cancels `_ws_task`:** Fixed. `hangup()` now cancels `_ws_task` (with `contextlib.suppress(asyncio.CancelledError)`) after the REST call, before `server.stop()`. New acceptance criterion added.

## Related

- **FR-071:** Outbound Twilio voice call (baseline telephony implementation)
- **OC-008:** Consolidated incaller/outcaller — defines the shared `projects/outcaller/` structure this FR extends
- **REQ-YG-161:** Asterisk Transport Support (to be added to `ARCHITECTURE.md`)
- **`projects/outcaller/nodes/coordinator.py`:** `TelcoSession` — the sync/async bridge this provider will eventually replace
- **`projects/outcaller/nodes/tts.py`:** `speak()` — consumes `write_audio()` output
- **`projects/outcaller/nodes/stt.py`:** `listen_and_transcribe()` — consumes `read_audio()` frames

## Judge Verdict — APPROVE (2026-03-11)

**Status:** Approved — scope frozen, authority to implement granted.

**Notes for implementer:**

1. **`hangup()` resilience gap** (AC-10): The proposed code sketch has no `try/finally` around the REST DELETE call. The acceptance criterion explicitly requires `_ws_task` to be cancelled even if REST raises. TDD will surface this at RED phase — add a `try/finally` (or `try/except`) around the `httpx` call so `_ws_task.cancel()` and `server.stop()` always execute.

2. **Double `None` sentinel in `_ari_event_loop`**: The `break`-path calls `_signal_hangup()` before exiting, and `finally` calls it again → two `None`s in the inbound queue. Harmless within this FR's scope (single-use provider instance, consumer breaks on first `None`), but document it in a code comment so future `TelcoSession` refactor authors know.

Begin with the failing tests (Commandment 7). Red first.
