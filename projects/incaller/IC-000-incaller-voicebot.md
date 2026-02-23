# Feature Request: IC-000 Incaller — Inbound Twilio Voice Call

**Priority:** MEDIUM
**Type:** Feature (Project — reuses outcaller telephony infrastructure)
**Status:** Implemented ✅
**Effort:** 2 days (actual: 0.5 days)
**Requested:** 2026-02-23
**Approved:** 2026-02-23

---

## Summary

Create a YAMLGraph project (`projects/incaller/`) that receives inbound Twilio phone calls and conducts a voicebot conversation using the same ElevenLabs TTS/STT pipeline proven in the outcaller. The key architectural difference: instead of initiating a call via Twilio REST API, the incaller starts an HTTP+WebSocket server and waits for Twilio to route an incoming call to it via webhook.

---

## Problem

The outcaller (`projects/outcaller/`) initiates outbound calls — the bot calls the user. There is no mechanism for the reverse: a user calling a Twilio phone number and being routed to the YAMLGraph voicebot. Inbound call handling requires:

1. An HTTP endpoint that Twilio can POST to when a call arrives (voice webhook)
2. TwiML response instructing Twilio to connect a Media Stream WebSocket
3. A graph node that blocks until the call connects, then proceeds with conversation

The outcaller's `initiate_call` node calls the Twilio REST API and then waits for the WebSocket; the incaller reverses this — it listens for the webhook first, then the WebSocket follows automatically.

---

## Prior Art

| Source | What it provides |
|--------|-----------------|
| `projects/outcaller/server.py` | FastAPI WebSocket handler for Twilio Media Streams |
| `projects/outcaller/nodes/coordinator.py` | TelcoSession: async/sync bridge, event loop thread, Queue pair |
| `projects/outcaller/nodes/tts.py` | ElevenLabs TTS streaming pipeline (reusable as-is) |
| `projects/outcaller/nodes/stt.py` | ElevenLabs STT streaming pipeline (reusable as-is) |
| `projects/outcaller/nodes/twilio_call.py` | `accumulate_answer`, `end_call` (reusable as-is) |
| `projects/outcaller/nodes/probe_recap.py` | Probe-recap tools (reusable as-is) |
| Twilio docs: [Receive and Reply](https://www.twilio.com/docs/voice/tutorials) | Inbound webhook + TwiML `<Connect><Stream>` pattern |

---

## Proposed Solution

### Architecture

```
Caller dials Twilio number
        │
        ▼
   Twilio routes to webhook
        │
        │  HTTP POST /incoming
        ▼
┌──────────────────────────────────────────────────────────┐
│  Incaller Server (projects/incaller/server.py)            │
│                                                          │
│  POST /incoming  → returns TwiML <Connect><Stream>       │
│  WS   /voice     → Twilio Media Streams (reused)         │
└──────────────────────────────────────────────────────────┘
        │                              ▲
        │  WebSocket connected          │ Audio frames (mulaw 8kHz)
        ▼                              │
┌──────────────────────────────────────────────────────────┐
│  YAMLGraph (projects/incaller/graph.yaml)                 │
│                                                          │
│  [await_call] → [generate_probe/response] → [speak] →    │
│                          ↑                      │        │
│                          └── [accumulate] ← [listen] ←───┘
└──────────────────────────────────────────────────────────┘
```

### Call Flow (vs. Outcaller)

| Step | Outcaller (`initiate_call`) | Incaller (`await_call`) |
|------|-----------------------------|-------------------------|
| 1 | Start TelcoSession + server | Start TelcoSession + server |
| 2 | Call Twilio REST API (outbound dial) | **Wait for Twilio webhook POST** |
| 3 | Wait for WebSocket connect | **Respond with TwiML; wait for WebSocket connect** |
| 4 | Proceed with conversation | Proceed with conversation (identical) |

After step 3, both projects are functionally identical: TTS, STT, probe-recap, and end-call all work the same way.

---

### New: `await_call` Node

The only new node. Replaces `initiate_call` in the graph.

```python
# projects/incaller/nodes/twilio_inbound.py

def await_call(state: dict[str, Any]) -> dict[str, Any]:
    """Start server and wait for inbound Twilio call.

    1. Loads .env from projects/incaller/.env (own env, not outcaller's)
    2. Creates TelcoSession with incaller server (HTTP webhook + WebSocket)
    3. Starts uvicorn on VOICE_SERVER_PORT
    4. Blocks until Twilio POSTs to /incoming AND WebSocket connects
    5. Returns call_info with call_sid, stream_sid, and caller_number

    Raises:
        MissingStreamUrlError: If VOICE_STREAM_URL not set
        CallNotAnsweredError: If no call arrives within timeout
    """
```

**Note:** The outcaller's `twilio_call.py` loads `.env` from `Path(__file__).parent.parent / ".env"` (hard-coded to outcaller dir). The incaller's `await_call` must load its own `.env` from `projects/incaller/.env` before importing outcaller modules that read env vars at module level. Alternatively, the incaller `.env` can be loaded by a top-level `__init__.py` or the graph runner.

The timeout for `await_call` should be configurable via `INCALLER_TIMEOUT` env var (default: 300s / 5 minutes) since the bot must wait for a human to dial in. This is longer than the outcaller's 30s timeout (where the call is already being placed).

---

### New: `server.py` with Webhook Endpoint

Extends the outcaller's `server.py` pattern with an HTTP POST endpoint:

```python
# projects/incaller/server.py

def create_app(session: TelcoSession) -> FastAPI:
    app = FastAPI(title="Incaller Voice Server")

    @app.post("/incoming")
    async def incoming_call(request: Request) -> Response:
        """Handle Twilio inbound voice webhook.

        Twilio POSTs form data with CallSid, From, To, etc.
        Responds with TwiML instructing Twilio to connect a Media Stream.
        """
        form = await request.form()
        call_sid = form.get("CallSid", "")
        caller = form.get("From", "")
        session.call_sid = call_sid
        logger.info("Incoming call: call_sid=%s, from=%s", call_sid, caller)

        # Store caller info for greeting
        session.caller_number = caller

        ws_url = os.getenv("VOICE_STREAM_URL", "").replace("https://", "wss://")
        # VOICE_STREAM_URL is trusted config, not user input — f-string is safe here
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Connect>
                <Stream url="{ws_url}/voice" />
            </Connect>
        </Response>"""
        return Response(content=twiml.strip(), media_type="application/xml")

    @app.websocket("/voice")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        # ... identical to outcaller's server.py WebSocket handler
```

The WebSocket handler is identical to the outcaller's. The only addition is the `/incoming` POST endpoint.

---

### Reused from Outcaller (Import Directly)

| Module | Functions | Notes |
|--------|-----------|-------|
| `projects.outcaller.nodes.twilio_call` | `speak`, `listen_and_transcribe`, `accumulate_answer`, `end_call` | Re-exports TTS/STT; state management, call teardown |
| `projects.outcaller.nodes.probe_recap` | `parse_targets`, `extract_answers`, `check_missing`, `apply_corrections` | Identical — probe-recap logic |
| `projects.outcaller.nodes.coordinator` | `TelcoSession`, `get_active_session`, `set_active_session` | Identical — async/sync bridge |

The incaller graph's `tools:` section references outcaller modules directly:

```yaml
tools:
  speak:
    type: python
    module: projects.outcaller.nodes.tts
    function: speak
  listen_and_transcribe:
    type: python
    module: projects.outcaller.nodes.stt
    function: listen_and_transcribe
  # ... etc.
```

---

### Graph YAML

```yaml
# projects/incaller/graph.yaml
version: "1.0"
name: incaller-voice-demo
description: Inbound call voicebot with ElevenLabs TTS/STT

metadata:
  provider: google
  model: gemini-2.5-flash
  thinking_budget: 0

defaults:
  prompts_relative: true
  prompts_dir: prompts

state:
  # Call info (set by await_call)
  call_info: dict
  # Caller info (set by await_call from Twilio webhook)
  caller_number: str
  # Conversation mode
  questions: str
  answers: list
  transcript: str
  next_utterance: str
  last_spoken: str
  call_disconnected: bool
  call_done: bool
  call_result: dict
  # Probe-recap (OC-005 compatible)
  targets: str
  target_fields: list
  extracted: dict
  missing_fields: list
  phase: str
  probe_count: int
  recap_analysis: dict
  recap_count: int
  user_refused: bool

loop_limits:
  speak: 10
  listen_and_transcribe: 10
  accumulate_answer: 10
  generate_probe: 6
  generate_recap: 4
  generate_goodbye: 2
  generate_response: 10
  extract_answers: 6
  check_missing: 6
  analyze_recap_response: 4
  apply_corrections: 4

tools:
  await_call:
    type: python
    module: projects.incaller.nodes.twilio_inbound
    function: await_call
    description: Start server and wait for inbound Twilio call

  speak:
    type: python
    module: projects.outcaller.nodes.twilio_call
    function: speak
    description: ElevenLabs TTS → mulaw 8kHz → Twilio WebSocket

  listen_and_transcribe:
    type: python
    module: projects.outcaller.nodes.twilio_call
    function: listen_and_transcribe
    description: Read Twilio audio → ElevenLabs realtime STT → transcript

  accumulate_answer:
    type: python
    module: projects.outcaller.nodes.twilio_call
    function: accumulate_answer
    description: Append transcript to answers list in state

  end_call:
    type: python
    module: projects.outcaller.nodes.twilio_call
    function: end_call
    description: Hang up via Twilio REST; close WebSocket

  parse_targets:
    type: python
    module: projects.outcaller.nodes.probe_recap
    function: parse_targets
    description: Parse 'key:desc|key:desc' into structured target fields

  extract_answers:
    type: python
    module: projects.outcaller.nodes.probe_recap
    function: extract_answers
    description: Call LLM for extraction, merge into existing extracted dict

  check_missing:
    type: python
    module: projects.outcaller.nodes.probe_recap
    function: check_missing
    description: Compute missing fields and set phase for routing

  apply_corrections:
    type: python
    module: projects.outcaller.nodes.probe_recap
    function: apply_corrections
    description: Apply caller corrections to extracted answers

nodes:
  await_call:
    type: python
    tool: await_call
    state_key: call_info
    on_error: fail

  # Legacy questions path
  generate_response:
    type: llm
    prompt: conversation
    state_key: next_utterance

  speak:
    type: python
    tool: speak
    state_key: last_spoken
    loop_limit: 10
    on_error: fail

  listen_and_transcribe:
    type: python
    tool: listen_and_transcribe
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

  # Probe-recap nodes (OC-005)
  parse_targets:
    type: python
    tool: parse_targets
    state_key: target_fields
    on_error: fail

  extract_answers:
    type: python
    tool: extract_answers
    state_key: extracted
    on_error: fail

  check_missing:
    type: python
    tool: check_missing
    state_key: missing_fields
    on_error: fail

  generate_probe:
    type: llm
    prompt: generate_probe
    state_key: next_utterance
    skip_if_exists: false

  generate_recap:
    type: llm
    prompt: generate_recap
    state_key: next_utterance

  analyze_recap_response:
    type: llm
    prompt: analyze_recap_response
    state_key: recap_analysis

  apply_corrections:
    type: python
    tool: apply_corrections
    state_key: extracted
    on_error: fail

  generate_goodbye:
    type: llm
    prompt: goodbye
    state_key: next_utterance
    skip_if_exists: false

  generate_goodbye_refused:
    type: llm
    prompt: goodbye_refused
    state_key: next_utterance
    skip_if_exists: false

edges:
  - from: START
    to: await_call

  # === Branching at await_call ===
  - from: await_call
    to: parse_targets
    condition: "targets != None"
  - from: await_call
    to: generate_response
    condition: "targets == None"

  # === Targets path: parse → check → probe/recap ===
  - from: parse_targets
    to: check_missing

  - from: check_missing
    to: generate_recap
    condition: "phase == \"recap\""
  - from: check_missing
    to: generate_probe
    condition: "phase == \"probe\""

  # === All LLM response nodes → speak ===
  - from: generate_probe
    to: speak
  - from: generate_recap
    to: speak
  - from: generate_goodbye
    to: speak
  - from: generate_goodbye_refused
    to: speak
  - from: generate_response
    to: speak

  # === After speaking, check if we're done ===
  - from: speak
    to: end_call
    condition: "call_done == True"
  - from: speak
    to: end_call
    condition: "call_disconnected == True"
  - from: speak
    to: listen_and_transcribe
    condition: "call_done != True"

  # === Handle disconnection during listen ===
  - from: listen_and_transcribe
    to: end_call
    condition: "call_disconnected == True"
  - from: listen_and_transcribe
    to: accumulate_answer
    condition: "call_disconnected != True"

  # === Routing after accumulate_answer (mode-dependent) ===
  - from: accumulate_answer
    to: generate_response
    condition: "targets == None"
  - from: accumulate_answer
    to: extract_answers
    condition: "phase == \"probe\""
  - from: accumulate_answer
    to: analyze_recap_response
    condition: "phase == \"recap\""

  # === Extraction → check or exit on refusal ===
  - from: extract_answers
    to: generate_goodbye_refused
    condition: "user_refused == True"
  - from: extract_answers
    to: check_missing
    condition: "user_refused != True"

  # === Recap response routing ===
  - from: analyze_recap_response
    to: generate_goodbye_refused
    condition: "recap_analysis.user_refused == True"
  - from: analyze_recap_response
    to: generate_goodbye
    condition: "recap_analysis.is_confirmed == True"
  - from: analyze_recap_response
    to: generate_goodbye
    condition: "recap_count >= 3"
  - from: analyze_recap_response
    to: apply_corrections
    condition: "recap_analysis.is_confirmed != True"

  # === Correction loop ===
  - from: apply_corrections
    to: generate_recap

  # === Terminal ===
  - from: end_call
    to: END
```

---

### Prompts

The incaller needs its own prompts because the tone differs — the caller initiated the call, so the bot should welcome them rather than introduce an outbound purpose.

| File | Derives from | Change |
|------|-------------|--------|
| `prompts/conversation.yaml` | `outcaller/prompts/conversation.yaml` | "Thank you for calling" instead of "I'm calling to..." |
| `prompts/generate_probe.yaml` | `outcaller/prompts/generate_probe.yaml` | Welcome greeting for first turn adapted for inbound |
| `prompts/generate_recap.yaml` | `outcaller/prompts/generate_recap.yaml` | Minimal changes (same recap logic) |
| `prompts/analyze_recap_response.yaml` | `outcaller/prompts/analyze_recap_response.yaml` | Identical (LLM analysis is context-independent) |
| `prompts/extract_answers.yaml` | `outcaller/prompts/extract_answers.yaml` | Identical |
| `prompts/goodbye.yaml` | `outcaller/prompts/goodbye.yaml` | "Thank you for calling" vs "Thank you for your time" |
| `prompts/goodbye_refused.yaml` | `outcaller/prompts/goodbye_refused.yaml` | Adapted for inbound context |

---

### Twilio Phone Number Configuration

For inbound calls, the Twilio phone number must have its **Voice webhook** configured:

1. Go to Twilio Console → Phone Numbers → Active Numbers → select number
2. Set **A CALL COMES IN** to: `Webhook` → `https://<VOICE_STREAM_URL>/incoming` → `HTTP POST`
3. Save

This is a one-time manual configuration. The `/incoming` endpoint on our server handles the rest.

Alternatively, configure via Twilio CLI or REST API:

```bash
twilio phone-numbers:update +358454918222 \
  --voice-url="https://capacitive-bernetta-transitorily.ngrok-free.dev/incoming"
```

---

### Run Command

```bash
# Targets mode (structured data collection)
yamlgraph graph run projects/incaller/graph.yaml \
  --var 'targets=caller_name:Your full name|issue:What is your issue' \
  --full

# Questions mode (free-form conversation)
yamlgraph graph run projects/incaller/graph.yaml \
  --var 'questions=What is your name?,How can we help you today?' \
  --full

# No --var phone needed (caller dials in; phone not needed)
```

The graph starts, the server begins listening, and the bot waits for an inbound call. Once a caller dials the Twilio number, the conversation begins.

---

### File Layout

```
projects/incaller/
├── __init__.py                       # Package marker
├── .env                              # API keys (shared with outcaller or separate)
├── graph.yaml                        # Incaller graph (await_call + shared nodes)
├── server.py                         # FastAPI: POST /incoming + WS /voice
├── README.md                         # Setup, Twilio config, run command
├── nodes/
│   ├── __init__.py
│   └── twilio_inbound.py             # await_call() — only new node
├── prompts/
│   ├── conversation.yaml             # Inbound-adapted conversation prompt
│   ├── generate_probe.yaml           # Welcome + probe (inbound tone)
│   ├── generate_recap.yaml           # Recap (minimal changes)
│   ├── analyze_recap_response.yaml   # Identical to outcaller
│   ├── extract_answers.yaml          # Identical to outcaller
│   ├── goodbye.yaml                  # "Thank you for calling"
│   └── goodbye_refused.yaml          # Inbound refusal goodbye
└── README.md                         # Setup, Twilio config, run command
```

The FR itself lives at `feature-requests/IC-000-incaller-voicebot.md` (not inside the project).

New code: ~100 lines (`twilio_inbound.py` ~50 lines, `server.py` ~50 lines delta from outcaller).

---

## Acceptance Criteria

- [x] `projects/incaller/` contains `graph.yaml`, `server.py`, `nodes/twilio_inbound.py`, `prompts/`, `README.md`
- [x] `await_call` node starts TelcoSession + uvicorn server, then blocks until Twilio webhook + WebSocket connect
- [x] `POST /incoming` endpoint receives Twilio webhook, responds with TwiML `<Connect><Stream url="wss://.../voice" />`
- [x] `caller_number` extracted from Twilio webhook `From` field and stored in state
- [x] `await_call` timeout configurable (default 300s); raises `CallNotAnsweredError` if no call arrives
- [x] `await_call` raises `MissingStreamUrlError` if `VOICE_STREAM_URL` is not set
- [x] Targets mode works: `--var 'targets=...'` triggers probe-recap flow (reused from outcaller)
- [x] Questions mode works: `--var 'questions=...'` triggers legacy conversation flow
- [x] TTS, STT, accumulate, end_call reused from outcaller via direct module import
- [x] Probe-recap nodes reused from outcaller via direct module import
- [x] All prompts adapted for inbound call context ("Thank you for calling" tone)
- [x] Graph lint passes: `yamlgraph graph lint projects/incaller/graph.yaml`
- [x] README documents: Twilio phone number webhook configuration, ngrok setup, env vars, run command
- [x] Tests in `tests/unit/test_incaller.py` with `@pytest.mark.req` tags
- [x] REQ-YG-084–086 added to `ARCHITECTURE.md` and `scripts/req_coverage.py`

---

## Constraints

- **Reuse over reimplementation**: TTS, STT, coordinator, probe-recap imported from outcaller — no duplication of working code
- **Single new node**: Only `await_call` is new Python code; everything else is graph wiring + prompts
- **Same audio codec**: 8 kHz mulaw throughout (Twilio Media Streams requirement)
- **Same dependencies**: No new Python packages beyond outcaller's (`twilio`, `elevenlabs`, `fastapi`, `uvicorn`)
- **ffmpeg required**: Same system dependency as outcaller
- **VOICE_STREAM_URL required**: Must be publicly reachable (ngrok for local dev)
- **Twilio phone number must be pre-configured**: Voice webhook URL must point to `/incoming` endpoint
- **No `phone` var required**: Unlike outcaller, the caller dials in — no outbound number needed
- **Longer timeout**: `await_call` defaults to 300s (vs outcaller's 30s) since we wait for a human to call

---

## Alternatives Considered

1. **Integrate into outcaller as a mode** — Add `--var mode=inbound` to outcaller graph and branch at start. Rejected: muddies the outcaller's purpose, complicates the graph with more conditional edges, and the greeting tone differs fundamentally (inbound vs outbound).

2. **Extract shared telephony into `projects/shared/telco/`** — Create a shared module. Rejected for now: premature abstraction. Direct import from outcaller is simpler and equally functional. If a third voice project appears, refactor then.

3. **Use Twilio's `<Say>` verb for greeting before `<Stream>`** — Have Twilio speak a short greeting ("Please hold") before connecting the WebSocket. Considered: could reduce perceived latency. Deferred: the bot's first `generate_probe` already includes a greeting, and adding `<Say>` introduces a voice mismatch (Twilio TTS voice ≠ ElevenLabs voice).

4. **Twilio Programmable Voice (serverless Functions)** — Use Twilio Functions to host the webhook. Rejected: adds external deployment complexity and moves logic outside YAMLGraph's orchestration.

5. **Copy all outcaller nodes** — Fork all Python files into incaller. Rejected: violates DRY; any bug fix or enhancement in outcaller nodes would need to be applied twice.

---

## Implementation Approach

### Phase 1: Server + await_call (Day 1)

1. Create `projects/incaller/` directory structure
2. Implement `server.py` — copy outcaller's `server.py`, add `POST /incoming` endpoint
3. Implement `nodes/twilio_inbound.py` — `await_call()` function
4. Write `graph.yaml` — reference outcaller tools, use `await_call` as entry node
5. Write unit tests for `await_call` and `/incoming` endpoint (mock Twilio, mock WebSocket)
6. Add requirements REQ-YG-084–086 to `ARCHITECTURE.md`

### Phase 2: Prompts + Integration (Day 2)

7. Write inbound-adapted prompts (7 files)
8. Write `README.md` with Twilio webhook configuration instructions
9. Integration test (manual): configure Twilio number, start ngrok, run graph, call in
10. Graph lint validation
11. Backward compatibility check: verify outcaller still works unchanged
12. Reflect in `docs/diary.md`

---

## Requirements

Add to `ARCHITECTURE.md`:

| Requirement | Description |
|-------------|-------------|
| REQ-YG-084 | Incaller: `await_call` node starts HTTP+WS server and blocks until inbound Twilio call connects |
| REQ-YG-085 | Incaller: `POST /incoming` webhook responds with TwiML `<Connect><Stream>` for Twilio Media Streams |
| REQ-YG-086 | Incaller: reuses outcaller TTS, STT, probe-recap, and coordinator without code duplication |

---

## Related

- `projects/outcaller/` — Outcaller project (source of reusable telephony code)
- `projects/outcaller/OC-000-telco-voice-call-demo.md` — FR-071 outcaller feature request
- `projects/outcaller/OC-005-outcaller-probe-recap.md` — Probe-recap pattern
- `projects/outcaller/nodes/coordinator.py` — TelcoSession (reused)
- `projects/outcaller/nodes/tts.py` — ElevenLabs TTS (reused)
- `projects/outcaller/nodes/stt.py` — ElevenLabs STT (reused)
- [Twilio Media Streams](https://www.twilio.com/docs/voice/media-streams) — Twilio WebSocket protocol
- [Twilio Incoming Call Webhook](https://www.twilio.com/docs/voice/make-calls#handle-incoming-calls) — Webhook configuration

---

## Judgement

**Verdict: APPROVED** ✅ — Scope frozen. Authority granted. Proceed to Enforce.

**Date:** 2026-02-23

### Issues Found & Resolved

| # | Issue | Resolution |
|---|-------|------------|
| 1 | Requirement numbering gap: FR used REQ-YG-087–089, skipping 084–086 | Fixed to REQ-YG-084–086 (contiguous with last existing REQ-YG-083) |
| 2 | `call_info` used as `state_key` but not declared in `state:` section | Added `call_info: dict` to state |
| 3 | `last_spoken` and `call_result` used as `state_key` in nodes but not in `state:` | Added both to state section |
| 4 | Graph nodes/edges used `# ...` placeholders instead of full specification | Expanded to complete 15-node, 21-edge graph matching outcaller topology |
| 5 | Tools referenced `projects.outcaller.nodes.tts` and `.stt` directly | Changed to `projects.outcaller.nodes.twilio_call` (re-export module), matching outcaller's own graph.yaml pattern |
| 6 | Reused-modules table listed TTS/STT as separate imports | Consolidated under `twilio_call` module for consistency |
| 7 | `.env` loading concern: outcaller's `twilio_call.py` hard-codes path to outcaller `.env` | Documented that `await_call` must load incaller's own `.env` before outcaller module imports |
| 8 | TwiML f-string XML injection concern | Added comment: `VOICE_STREAM_URL` is trusted config, not user input |
| 9 | Missing `__init__.py` in file layout for incaller package root | Added `__init__.py` to file layout |
| 10 | FR file location listed as inside project dir | Corrected: FR lives at `feature-requests/IC-000-incaller-voicebot.md` |

### Assessment

- **Architecture**: Sound. The single-node-delta approach (swap `initiate_call` for `await_call`) is minimal and correct. The call flow table clearly shows the divergence point (step 2–3) and convergence (step 4+).
- **Reuse strategy**: Verified — all 9 claimed outcaller functions exist at the referenced paths. Cross-project imports work via `python_tool.py`'s `sys.path.insert(0, cwd)` mechanism. The `projects/` package hierarchy has `__init__.py` at all levels.
- **Scope**: Tight — ~100 lines new Python, 7 prompt files, 1 graph YAML. No framework changes. No new dependencies.
- **Effort estimate**: 2 days is realistic given the reuse leverage.
- **Alternatives**: Well-reasoned. The "premature abstraction" rejection of shared telco module is correct — wait for the third use case.
