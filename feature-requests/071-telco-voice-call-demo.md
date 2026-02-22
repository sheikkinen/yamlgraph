# FR-071: Telco Voice Call Demo

**Priority:** MEDIUM
**Type:** Feature (Example — no core extensions required)
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-02-21
**Judged:** 2026-02-21

---

## Summary

Create a YAMLGraph example demo (`examples/demos/telco/`) that initiates an outbound Twilio phone call and conducts a multi-turn question-answer conversation using TTS (OpenAI `tts-1`) and STT (OpenAI `whisper-1`). The graph is the conversation brain; Python tool nodes handle all telephony I/O. This validates the "YAMLGraph as orchestrator, Python as I/O" pattern for real-time voice pipelines.

---

## Problem

YAMLGraph has no demonstration of real-time voice/telephony integration. The questionnaire-api project uses ElevenLabs as the voice layer and delegates conversation logic to an HTTP API — inverting ownership. A self-contained demo where YAMLGraph drives the conversation and delegates audio I/O to tool nodes is unproven, undocumented, and absent from the examples gallery.

---

## Context: What Exists in questionnaire-api

| File | Purpose |
|------|---------|
| `scripts/voice_call.py` | Twilio REST client; makes outbound calls with TwiML `<Connect><Stream>` |
| `src/api/routes/voice.py` | FastAPI WebSocket handler for Twilio Media Streams |
| `src/voice_test/vad.py` | `VADDetector`: webrtcvad-based silence detection on 8 kHz mulaw → PCM16 |
| `src/api/phone_session.py` | Redis-backed session resume (not needed for demo) |

Audio format throughout: **8 kHz mulaw** (Twilio Media Streams native).

---

## Proposed Solution

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│  YAMLGraph (examples/demos/telco/graph.yaml)             │
│                                                          │
│  [initiate_call] → [generate_response] → [route]         │
│                            ↑           /        \        │
│                      [accumulate]  [speak]    [end_call] │
│                            ↑          ↓                  │
│                      [transcribe] [listen]               │
└──────────────────────────────────────────────────────────┘
           │                             ▲
           │  Twilio REST (outbound)      │ Twilio Media Stream WS
           ▼                             │
        Twilio ──────────── callee phone ┘
```

**Flow:** `initiate_call → generate_response → route → speak → listen → transcribe → accumulate → generate_response → route → speak | end_call`

All I/O nodes use `type: python`. The conversation node uses `type: llm`.

---

### WebSocket Coordinator Design

`TelcoSession` is the single owner of all async/threading state:

- The asyncio event loop (created once, runs in a dedicated daemon thread)
- A uvicorn server bound in-process to `VOICE_SERVER_PORT` (default 8080)
- Two `asyncio.Queue` instances: `inbound` (Twilio audio → tool nodes) and `outbound` (tool nodes → Twilio audio)
- The Twilio `call_sid` and `stream_sid`

**`VOICE_STREAM_URL`** must be the public URL (e.g. ngrok) tunnelling to this internal server. If unset, `initiate_call` raises `MissingStreamUrlError` with the message: "Set VOICE_STREAM_URL to a public WebSocket URL pointing at VOICE_SERVER_PORT (use ngrok for local dev)."

**Lifecycle:**

```
Main thread (YAMLGraph graph run)
  │
  ├── TelcoSession.start()
  │     ├── start uvicorn in-process on VOICE_SERVER_PORT (daemon thread)
  │     ├── create asyncio event loop in same daemon thread
  │     └── store session in module-level registry keyed by call_sid placeholder
  │
  ├── initiate_call tool node
  │     ├── validates VOICE_STREAM_URL is set (raises MissingStreamUrlError if not)
  │     ├── calls Twilio REST API → call_sid returned
  │     ├── blocks (threading.Event, ≤30s timeout) until WebSocket connects
  │     │     └── raises CallNotAnsweredError if event not signalled in time
  │     └── stores call_sid + stream_sid in session registry
  │
  ├── speak tool node
  │     ├── generates TTS audio (sync OpenAI tts-1 call)
  │     ├── transcodes mp3 → pcm16 → mulaw 8kHz via ffmpeg subprocess
  │     ├── chunks audio into 640-byte mulaw frames
  │     └── puts frames on outbound Queue via run_coroutine_threadsafe()
  │
  ├── listen tool node
  │     ├── pulls frames from inbound Queue via run_coroutine_threadsafe()
  │     ├── feeds frames to VADDetector
  │     └── returns when VAD signals end-of-utterance
  │           └── raises CallHangupError if None sentinel received before VAD end
  │
  └── end_call tool node
        ├── hangs up via Twilio REST (call_sid)
        ├── signals WebSocket handler to close
        └── calls TelcoSession.shutdown() → joins event loop thread

FastAPI WebSocket handler (asyncio event loop thread, same process)
  ├── on connect: registers stream_sid, signals threading.Event
  ├── on message (audio): puts frame on inbound Queue
  ├── on message (outbound): reads outbound Queue, sends to Twilio
  └── on disconnect: puts sentinel (None) on inbound Queue → listen wakes up
```

---

### Graph YAML

```yaml
# examples/demos/telco/graph.yaml
version: "1.0"
name: telco-voice-demo
description: Outbound call with TTS/STT question-answer loop

tools:
  initiate_call:
    type: python
    module: examples.demos.telco.nodes.twilio_call
    function: initiate_call
    description: Make outbound Twilio call; block until WebSocket connects

  speak:
    type: python
    module: examples.demos.telco.nodes.twilio_call
    function: speak
    description: TTS → mulaw 8kHz → Twilio WebSocket

  listen:
    type: python
    module: examples.demos.telco.nodes.twilio_call
    function: listen
    description: Read Twilio audio via VAD, return utterance bytes

  transcribe:
    type: python
    module: examples.demos.telco.nodes.twilio_call
    function: transcribe
    description: mulaw → wav → OpenAI Whisper → text

  accumulate_answer:
    type: python
    module: examples.demos.telco.nodes.twilio_call
    function: accumulate_answer
    description: Append transcript to answers list in state

  end_call:
    type: python
    module: examples.demos.telco.nodes.twilio_call
    function: end_call
    description: Hang up via Twilio REST; close WebSocket

nodes:
  initiate_call:
    type: python
    tool: initiate_call
    state_key: call_info
    on_error: fail

  generate_response:
    type: llm
    prompt: telco/conversation
    state_key: next_utterance

  route:
    type: router
    condition: "next_utterance == '[DONE]'"
    routes:
      true: end_call
      false: speak

  speak:
    type: python
    tool: speak
    state_key: last_spoken
    loop_limit: 10
    on_error: fail

  listen:
    type: python
    tool: listen
    state_key: audio_raw
    on_error: fail

  transcribe:
    type: python
    tool: transcribe
    state_key: transcript
    on_error: fail

  accumulate_answer:
    type: python
    tool: accumulate_answer
    state_key: answers

  end_call:
    type: python
    tool: end_call
    state_key: call_result
    on_error: fail

edges:
  - from: START
    to: initiate_call
  - from: initiate_call
    to: generate_response
  - from: generate_response
    to: route
  - from: route
    to: speak
  - from: route
    to: end_call
  - from: speak
    to: listen
  - from: listen
    to: transcribe
  - from: transcribe
    to: accumulate_answer
  - from: accumulate_answer
    to: generate_response
```

**Flow rationale:** The first `generate_response` call with empty `answers` produces a greeting + Q1. No standalone `greet` node is needed — the LLM prompt handles the greeting as part of Q1. `route` is placed after `generate_response` (not after `speak`) so `[DONE]` is detected before attempting TTS.

---

### Prompt YAML

Questions are passed as a comma-separated string and split inside the template (resolves ISSUE-2):

```yaml
# examples/demos/telco/prompts/conversation.yaml
system: |
  You are a phone assistant conducting a brief survey.
  {% set q_list = questions.split(",") %}
  Questions to ask (in order): {{ q_list | join("; ") }}
  Answers collected so far: {{ answers | join("; ") if answers else "none yet" }}

  Greet the caller on the first turn (when answers is empty).
  Ask the next unanswered question.
  When all questions have been answered, reply with exactly: [DONE]
  Keep responses short — this is a phone call.

user: "{% if transcript %}Caller said: {{ transcript }}{% else %}(call just connected){% endif %}"
```

**Run command:**
```bash
yamlgraph graph run examples/demos/telco/graph.yaml \
  --var phone="+3585..." \
  --var questions="What is your name?,How are you today?"
```

---

### Node Implementations

#### `nodes/coordinator.py` — TelcoSession and registry

Owns the event loop thread, two asyncio Queues, the in-process uvicorn server, and cleanup logic. See WebSocket Coordinator Design above.

```python
# Key interface
class TelcoSession:
    def start(self) -> None: ...       # starts uvicorn + event loop thread
    def shutdown(self) -> None: ...    # joins thread, cleans registry

_SESSIONS: dict[str, TelcoSession] = {}  # keyed by call_sid
```

#### `nodes/twilio_call.py`

```python
def initiate_call(state: dict) -> dict:
    """Validates VOICE_STREAM_URL; makes outbound Twilio call; blocks (≤30s) until WebSocket connects."""
    # Returns {"call_info": {"call_sid": "...", "stream_sid": "..."}}

def speak(state: dict) -> dict:
    """TTS → ffmpeg (mp3 → pcm16 → mulaw 8kHz) → 640-byte frames → outbound Queue."""
    # text = state["next_utterance"]
    # Returns {"last_spoken": text}

def listen(state: dict) -> dict:
    """Reads inbound Queue; feeds VADDetector; returns on end-of-utterance or hangup."""
    # Returns {"audio_raw": <bytes>}
    # Raises CallHangupError if sentinel received

def transcribe(state: dict) -> dict:
    """mulaw bytes → wav (ffmpeg subprocess) → OpenAI whisper-1 → text."""
    # Returns {"transcript": "..."}

def accumulate_answer(state: dict) -> dict:
    """Appends state['transcript'] to state['answers'] list."""
    # Returns {"answers": [...existing..., new_transcript]}

def end_call(state: dict) -> dict:
    """Hangs up via Twilio REST; shuts down TelcoSession."""
    # Returns {"call_result": {"status": "completed"}}
```

All mulaw↔wav transcoding uses `ffmpeg` subprocess. `audioop` is not used (removed in Python 3.13).

#### `lib/vad.py` — VAD copy strategy

Copy `questionnaire-api/src/voice_test/vad.py` to `examples/demos/telco/lib/vad.py`. Document source URL and commit SHA in the file header. No `sys.path` manipulation.

#### `server.py` — FastAPI app for in-process uvicorn

```python
# examples/demos/telco/server.py
# FastAPI app with /voice WebSocket endpoint
# TelcoSession.start() imports and serves this app
```

---

### Loop Protection

`loop_limit: 10` on the `speak` node in `graph.yaml`. YAMLGraph's existing `check_loop_limit()` mechanism enforces this. No hard-coding needed.

---

### Requirements

Add to `ARCHITECTURE.md`:

```
| REQ-YG-078 | Telco demo: YAMLGraph orchestrates outbound Twilio voice call via type:python tool nodes | `examples/demos/telco` |
| REQ-YG-079 | Telco demo: speak node performs TTS via OpenAI tts-1 and transcodes to mulaw 8kHz via ffmpeg | `examples/demos/telco/nodes` |
| REQ-YG-080 | Telco demo: listen node reads Twilio Media Stream audio via VADDetector | `examples/demos/telco/nodes` |
| REQ-YG-081 | Telco demo: transcribe node converts mulaw utterance to text via OpenAI whisper-1 | `examples/demos/telco/nodes` |
| REQ-YG-082 | Telco demo: WebSocket coordinator bridges asyncio event loop and synchronous tool nodes via thread-safe Queue | `examples/demos/telco/nodes/coordinator` |
```

Update `ALL_REQS` range and `CAPABILITIES` dict in `scripts/req_coverage.py` to include REQ-YG-078 through REQ-YG-082.

---

## Acceptance Criteria

- [ ] `examples/demos/telco/` contains `graph.yaml`, `prompts/conversation.yaml`, `nodes/twilio_call.py`, `nodes/coordinator.py`, `server.py`, `lib/vad.py`, `README.md`
- [ ] All tool nodes use `type: python` (not `type: tool`); no `input_map` key used
- [ ] `accumulate_answer` node populates `answers` state key (appends each transcript)
- [ ] First graph turn produces a greeting + Q1 via LLM (no standalone greet node)
- [ ] `TelcoSession.start()` binds uvicorn in-process on `VOICE_SERVER_PORT` (default 8080); `VOICE_STREAM_URL` is the public URL tunnelling to that port
- [ ] `initiate_call` raises `MissingStreamUrlError` with clear message if `VOICE_STREAM_URL` is unset
- [ ] `initiate_call` raises `CallNotAnsweredError` after 30s if WebSocket never connects
- [ ] TTS: OpenAI `tts-1` → ffmpeg → mulaw 8kHz (no `audioop`)
- [ ] STT: ffmpeg mulaw → wav → OpenAI `whisper-1`
- [ ] VAD: `lib/vad.py` copied from questionnaire-api with source attribution; no `sys.path` manipulation
- [ ] `loop_limit: 10` on `speak` node in graph YAML (YAMLGraph loop protection)
- [ ] `TelcoSession` in `coordinator.py` owns event loop thread, two asyncio Queues, in-process uvicorn server
- [ ] WebSocket disconnect during `listen` raises `CallHangupError`, graph terminates cleanly via `on_error: fail`
- [ ] `end_call` hangs up via Twilio REST and calls `TelcoSession.shutdown()`
- [ ] Questions passed as comma-separated string: `--var questions="Q1?,Q2?"`; prompt splits with `questions.split(",")`
- [ ] Demo runs: `yamlgraph graph run examples/demos/telco/graph.yaml --var phone="+3585..." --var questions="Q1?,Q2?"`
- [ ] Required env vars documented in README: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `OPENAI_API_KEY`, `VOICE_STREAM_URL`, `VOICE_SERVER_PORT` (default 8080)
- [ ] README documents ngrok setup: start ngrok → set `VOICE_STREAM_URL` → run graph
- [ ] `tests/unit/test_telco_nodes.py` with mocked Twilio + OpenAI + VAD, tagged `@pytest.mark.req("REQ-YG-078")` through `REQ-YG-082`
- [ ] REQ-YG-078–082 added to `ARCHITECTURE.md` and `scripts/req_coverage.py`
- [ ] `yamlgraph graph lint examples/demos/telco/graph.yaml` passes with no errors

---

## Alternatives Considered

1. **ElevenLabs as TTS** — Already used in questionnaire-api. Requires separate API key; OpenAI TTS simpler since `OPENAI_API_KEY` is already required.
2. **Twilio `<Say>` verb** — Built-in TTS, no external API. Polling-based, no real-time streaming control.
3. **ElevenLabs as entire voice layer** (current questionnaire-api topology) — YAMLGraph becomes a tool, not the orchestrator. Inverts the ownership model; valid for production but defeats the demo purpose.
4. **Direct WebRTC** — Eliminates Twilio dependency but far more complex. Not appropriate for a demo.
5. **Auto-start uvicorn as subprocess / `--local` flag** — Dropped in favour of in-process uvicorn inside `TelcoSession`. In-process keeps in-memory Queues viable and is self-contained.
6. **Redis pub/sub as Queue bridge** (ISSUE-1 Option B) — Would allow external WebSocket server but adds broker dependency and contradicts "demo scope" constraint. Rejected.
7. **JSON list for `--var questions`** (ISSUE-2 Option C) — Requires `parse_vars` change with broader framework scope. Rejected; comma-separated string is simpler and sufficient for a demo.
8. **`--var-file vars.yaml` for questions** (ISSUE-2 Option B) — Valid workaround but less ergonomic. Rejected in favour of comma-split in template.

---

## Constraints

- Audio codec throughout: **8 kHz mulaw** (Twilio Media Streams requirement)
- `ffmpeg` must be available in the runtime environment (all transcoding routes through it)
- `VOICE_STREAM_URL` must be publicly reachable by Twilio (ngrok for local dev); points at in-process uvicorn server
- `audioop` must not be used (removed in Python 3.13; project targets Python 3.11+)
- Loop protection via `loop_limit: 10` on `speak` node (existing YAMLGraph mechanism)
- Call auto-terminates after 5 minutes (inherits from Twilio circuit breaker in `voice.py`)
- No `sys.path` manipulation; VAD copied to `lib/vad.py`
- Questions passed as comma-separated `--var` string; no `parse_vars` framework change

---

## Implementation Approach

1. **Add requirements** REQ-YG-078–082 to `ARCHITECTURE.md` and `scripts/req_coverage.py`
2. **Copy VAD** from `questionnaire-api/src/voice_test/vad.py` to `examples/demos/telco/lib/vad.py`
3. **Implement `server.py`** — FastAPI app with `/voice` WebSocket endpoint
4. **Implement `coordinator.py`** — `TelcoSession`, module-level registry, event loop thread, in-process uvicorn, two asyncio Queues
5. **Implement `twilio_call.py`** — six tool functions; uses `coordinator.py` for all async bridging
6. **Write `graph.yaml` and `prompts/conversation.yaml`** (comma-split questions in template)
7. **Write `README.md`** — env vars, ngrok setup, run command
8. **Write `tests/unit/test_telco_nodes.py`** — TDD red-green-refactor; mock Twilio, OpenAI, VAD; tag `@pytest.mark.req`
9. **Verify:** `yamlgraph graph lint`, `pytest tests/unit/test_telco_nodes.py`, `python scripts/req_coverage.py`

---

## Judge Resolutions

### ISSUE-1 (Critical — resolved): WebSocket server ownership contradiction

**Resolution: Option A adopted.** `TelcoSession.start()` binds uvicorn in-process on `VOICE_SERVER_PORT` (default 8080). The asyncio event loop thread runs both the FastAPI WebSocket handler and the Queue bridge. `VOICE_STREAM_URL` is the _public_ URL (e.g. ngrok) tunnelling to this internal server. In-memory Queues remain viable because handler and tool nodes share the same process. The "No auto-start" statement and `MissingStreamUrlError` for missing URL are retained but now the URL must point at the internal server. `server.py` added to the demo file list.

### ISSUE-2 (Minor — resolved): `--var questions` passed as string, not list

**Resolution: Option A adopted.** Questions are passed as a comma-separated string (`--var questions="Q1?,Q2?"`). The prompt template splits with `{% set q_list = questions.split(",") %}`. No `parse_vars` framework change. Demo command and prompt template updated throughout.

---

## Related

- `questionnaire-api/src/api/routes/voice.py` — Twilio WebSocket handler (reference)
- `questionnaire-api/src/voice_test/vad.py` — VAD detector to copy
- `questionnaire-api/scripts/voice_call.py` — Twilio outbound call pattern
- `questionnaire-api/docs/plan-e2e-call-test-harness.md` — E2E test harness design
- `examples/demos/python-map/` — canonical `type: python` tool node pattern
- `examples/npc/` — production application pattern (session, human-in-loop)
- `ARCHITECTURE.md` — three-layer pattern, tool nodes
