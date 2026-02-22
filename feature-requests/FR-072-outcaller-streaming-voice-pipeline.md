# Feature Request: FR-072 Outcaller Streaming Voice Pipeline

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-02-22

## Summary

Replace the batch TTS and batch STT REST calls in `projects/outcaller` with fully-streaming
pipelines: ElevenLabs TTS chunks piped through ffmpeg in realtime, and ElevenLabs
`scribe_v2_realtime` WebSocket for STT. Eliminates the two dominant latency sources that make
the current demo feel sluggish.

---

## Problem

The current `twilio_call.py` implementation has two batch bottlenecks that were explicitly
ruled out in FR-071's design but crept in during implementation:

### Delay 1 — TTS is fully buffered before playback

```python
# twilio_call.py:speak()
mp3_data = b"".join(audio_stream)          # blocks until ElevenLabs generates ALL audio
mulaw_data = _transcode_mp3_to_mulaw(mp3_data)  # then batch-transcodes the full blob
for i in range(0, len(mulaw_data), chunk_size):
    session.put_outbound_sync(chunk)        # only then starts sending to caller
```

**Impact:** Time-to-first-audio (TTFA) = full TTS generation time + full transcode time.
For a two-sentence response this is typically 1.5–3 seconds of silence before the caller
hears anything.

**Correct design (FR-071 §Audio Pipeline):** ElevenLabs streaming → ffmpeg subprocess
(persistent stdin/stdout pipe) → mulaw chunks → Twilio outbound queue, all concurrent.
TTFA drops to the ElevenLabs API time-to-first-byte (~200 ms).

### Delay 2 — STT uses batch REST API, not scribe_v2_realtime WebSocket

```python
# twilio_call.py:_transcribe_elevenlabs()
url = "https://api.elevenlabs.io/v1/speech-to-text"
response = httpx.post(url, files={"file": wav_data}, data={"model_id": "scribe_v1"})
```

This violates FR-071's accepted design (§Audio Pipeline, §Acceptance Criteria AC-8):
- Homemade `_is_silence()` energy detector adds a hardcoded 1.5-second post-speech pause
  (`max_silence = 75` frames) before declaring end-of-utterance.
- Full audio is buffered in memory before any transcription begins.
- A batch WAV upload adds round-trip overhead (upload + inference + response).

**Impact:** End-of-utterance latency = 1.5 s silence guard + upload time + inference time.
Total STT latency is 3–5 seconds per turn.

**Correct design (FR-071 §Audio Pipeline):** ElevenLabs `scribe_v2_realtime` WebSocket with
`commit_strategy=vad`. Frames are streamed as they arrive from Twilio; ElevenLabs' built-in
VAD fires `committed_transcript` within ~100–300 ms of the caller stopping speech.

### Combined effect

Each conversation turn costs ~5–8 seconds of dead time (batch TTS + batch STT). A
two-question survey takes 20–30 seconds of perceived silence. The demo is technically correct
but unusable in a realistic call scenario.

---

## Proposed Solution

### TTS: Streaming pipeline with persistent ffmpeg subprocess

Replace `speak()`:

```python
def speak(state: dict) -> dict:
    from elevenlabs import ElevenLabs
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    # Start ffmpeg once, pipe mp3 → mulaw 8kHz
    proc = subprocess.Popen(
        ["ffmpeg", "-i", "pipe:0", "-f", "mulaw", "-ar", "8000", "-ac", "1", "pipe:1"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )

    def _feed_mp3():
        for chunk in client.text_to_speech.stream(
            voice_id=ELEVENLABS_VOICE_ID,
            model_id=ELEVENLABS_MODEL,
            text=state["next_utterance"],
            output_format="mp3_22050_32",
        ):
            proc.stdin.write(chunk)
        proc.stdin.close()

    t = threading.Thread(target=_feed_mp3, daemon=True)
    t.start()

    # Stream mulaw chunks to Twilio as ffmpeg produces them
    while True:
        chunk = proc.stdout.read(640)
        if not chunk:
            break
        session.put_outbound_sync(chunk)

    t.join()
    proc.wait()
    return {"last_spoken": state["next_utterance"]}
```

TTFA = ElevenLabs TTFB (~200 ms) + one ffmpeg buffer flush (~20 ms).

### STT: scribe_v2_realtime WebSocket (as FR-071 specified)

Replace `listen_and_transcribe()` and `_transcribe_elevenlabs()`:

```python
def listen_and_transcribe(state: dict) -> dict:
    """Twilio inbound frames → ffmpeg (mulaw 8kHz → pcm16 16kHz) → ElevenLabs scribe_v2_realtime."""
    import asyncio, websockets, json

    session = get_active_session()
    result_holder: list[str] = []

    async def _run():
        stt_url = (
            f"wss://api.elevenlabs.io/v1/speech-to-text/stream"
            f"?model_id=scribe_v2_realtime&commit_strategy=vad"
        )
        headers = {"xi-api-key": ELEVENLABS_API_KEY}

        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-f", "mulaw", "-ar", "8000", "-ac", "1", "-i", "pipe:0",
            "-f", "s16le", "-ar", "16000", "-ac", "1", "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )

        async with websockets.connect(stt_url, extra_headers=headers) as ws:
            async def feed_audio():
                while True:
                    frame = await session.inbound.get()
                    if frame is None:
                        proc.stdin.close()
                        return
                    proc.stdin.write(frame)
                    await proc.stdin.drain()

            async def forward_pcm():
                while True:
                    pcm = await proc.stdout.read(3200)  # 100ms of 16kHz pcm16
                    if not pcm:
                        break
                    await ws.send(pcm)

            async def receive_transcript():
                async for msg in ws:
                    event = json.loads(msg)
                    if event.get("type") == "committed_transcript":
                        result_holder.append(event["text"])
                        return

            await asyncio.gather(feed_audio(), forward_pcm(), receive_transcript())

    asyncio.run_coroutine_threadsafe(_run(), session.loop).result(timeout=60)
    return {"transcript": result_holder[0] if result_holder else ""}
```

Remove `_is_silence()`, `_pcm_to_wav()`, `_transcode_mulaw_to_pcm16()`, and
`_transcribe_elevenlabs()` — all obsolete.

### Summary of changes

| File | Change |
|------|--------|
| `nodes/twilio_call.py` | Rewrite `speak()` with streaming ffmpeg pipe; rewrite `listen_and_transcribe()` with `scribe_v2_realtime` WebSocket; delete 4 batch helper functions |
| `nodes/coordinator.py` | Expose `loop` property (the asyncio event loop) so `listen_and_transcribe` can submit coroutines without importing internals |
| `tests/unit/test_telco_nodes.py` | Update mocks: mock `subprocess.Popen` for streaming ffmpeg, mock `websockets.connect` for STT WebSocket |

No changes to `graph.yaml`, `server.py`, or `prompts/`.

---

## Acceptance Criteria

- [ ] `speak()` uses `client.text_to_speech.stream()` (or equivalent streaming method); no `b"".join()` buffering
- [ ] `speak()` uses a persistent ffmpeg subprocess (stdin/stdout pipe); no `subprocess.run()` batch call
- [ ] TTFA (logged) is ≤ 500 ms in unit test with mocked ElevenLabs streaming
- [ ] `listen_and_transcribe()` opens ElevenLabs `scribe_v2_realtime` WebSocket with `commit_strategy=vad`
- [ ] `listen_and_transcribe()` feeds frames to ElevenLabs as they arrive (no buffer-all-then-upload)
- [ ] `listen_and_transcribe()` returns on `committed_transcript` event; does not use `_is_silence()` or any energy-based detector
- [ ] `_is_silence()`, `_pcm_to_wav()`, `_transcode_mulaw_to_pcm16()`, `_transcribe_elevenlabs()` are deleted
- [ ] `coordinator.py` exposes `loop` property (read-only) for `listen_and_transcribe`
- [ ] No `audioop`; no `webrtcvad`; no batch REST calls to `/v1/speech-to-text`
- [ ] `tests/unit/test_telco_nodes.py` updated: mocks cover streaming ffmpeg + `scribe_v2_realtime` WS; all `@pytest.mark.req` tags retained (REQ-YG-078–082)
- [ ] `yamlgraph graph lint projects/outcaller/graph.yaml` passes unchanged
- [ ] `pytest tests/unit/test_telco_nodes.py` passes

---

## Constraints

- ElevenLabs Python SDK must expose a streaming TTS method (verify: `client.text_to_speech.stream()` or `convert()` with `stream=True`); pin to SDK version that provides it
- `scribe_v2_realtime` WebSocket URL and frame protocol must be confirmed from ElevenLabs docs before implementation
- ffmpeg must be available (already documented in README)
- `asyncio.run_coroutine_threadsafe` pattern already established in `coordinator.py`; STT node must submit to `session._loop` (expose via `loop` property)
- No changes to graph YAML, edges, or state schema — only the Python implementation changes
- Loop limit (`loop_limit: 10` on `speak`) remains; YAMLGraph mechanism unchanged

---

## Alternatives Considered

1. **Keep batch TTS, only fix STT** — Partial improvement. TTS is the longer delay for short
   utterances (greetings). Fixing both removes all perceivable pauses.

2. **Replace ElevenLabs with Twilio `<Say>` for TTS** — Zero latency (Twilio handles audio),
   but loses voice quality and ElevenLabs parity. Contradicts FR-071 design.

3. **Twilio AI Assistants / ConversationRelay** — Managed real-time pipeline, no ffmpeg
   needed. Would remove YAMLGraph as orchestrator; defeats demo purpose.

4. **WebRTC (Agora, Daily) instead of Twilio Media Streams** — Eliminates the mulaw codec
   constraint, enables native PCM. Too large a scope change for this FR; consider as
   separate FR.

5. **ElevenLabs Conversational AI API** — Fully managed conversation including TTS/STT/LLM.
   YAMLGraph becomes irrelevant; defeats demo purpose.

---

## Implementation Approach

1. **Confirm ElevenLabs SDK streaming TTS method** — check `elevenlabs` package for
   `text_to_speech.stream()` vs. `convert(stream=True)` vs. async generator
2. **Confirm `scribe_v2_realtime` WS protocol** — message schema for `committed_transcript`,
   correct URL pattern, auth header
3. **Expose `loop` on `TelcoSession`** — add `@property loop` returning `self._loop`
4. **Rewrite `speak()`** — streaming ffmpeg pipe, concurrent MP3 feed + mulaw read
5. **Rewrite `listen_and_transcribe()`** — `scribe_v2_realtime` WS coroutine, submitted via
   `run_coroutine_threadsafe`
6. **Delete dead helpers** — `_is_silence`, `_pcm_to_wav`, `_transcode_mulaw_to_pcm16`,
   `_transcribe_elevenlabs`
7. **Update unit tests** — mock `subprocess.Popen`, `websockets.connect`, streaming generator
8. **Verify:** `pytest tests/unit/test_telco_nodes.py`, `yamlgraph graph lint`

> **Implementation note (Judge):** The STT pseudo-code's `asyncio.gather(feed_audio(), forward_pcm(), receive_transcript())` will deadlock — `gather` waits for all three, but `feed_audio` / `forward_pcm` have no exit signal after `receive_transcript` returns a transcript. Use `asyncio.wait(return_when=FIRST_COMPLETED)` or signal termination via a shared `asyncio.Event` so all three coroutines exit cleanly.

---

## Related

- `projects/outcaller/071-telco-voice-call-demo.md` — original FR; this fixes the two
  batch-pipeline deviations from that spec
- `projects/outcaller/nodes/twilio_call.py` — implementation to replace
- `projects/outcaller/nodes/coordinator.py` — minor `loop` property addition
- `sosiaalitoimi-palveluohjaus/src/voice/speaker.py` — streaming TTS reference (prior art)
- `sosiaalitoimi-palveluohjaus/src/voice/stt_client.py` — `scribe_v2_realtime` WS reference (prior art)
- `feature-requests/FR-071-thinking-budget-graph-level.md` — unrelated FR-071 (different domain)
