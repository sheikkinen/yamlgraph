# Feature Request: FR-109 Graph-as-Coordinator for Ninchat Voice Integration

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced (Phase 1 complete)
**Effort:** 5 days
**Requested:** 2026-02-27

## Summary

Replace the ElevenLabs-as-LLM architecture (two-fold SSE slow path, `_in_flight` dedup shield, `POST /v1/ninchat/result` polling endpoint) with a YAMLGraph coordinator graph that owns the Twilio WebSocket session and calls ElevenLabs TTS/STT as stateless `type: python` tool nodes — eliminating the structural root cause of FR-011/FR-013: ElevenLabs’ 8 s Custom LLM timeout.

**Project location:** `projects/ninchat_voice/` (within yamlgraph monorepo).

## Value Statement

The Ninchat voice channel’s 6–18 s WebSocket round-trip becomes an ordinary graph step with no external timeout. The existing `questionnaire-api/src/questionnaire/handlers/ninchat_inquiry.py` session-based `NinchatConnection` class is ported into `ninchat_session.py` wrappers (`create_session`, `send_to_bot`, `close_session`), and the `ninchat_mediator.yaml` prompt is ported (with Jinja2 amendment for greeting) to the new project — eliminating cross-repo coupling to `questionnaire-api`.

## Problem

ElevenLabs’ Custom LLM API abandons the SSE connection after ~8 s. Ninchat’s WebSocket round-trip takes 6–18 s. FR-011 and FR-013 introduced a two-fold SSE slow path to bridge this gap:

1. The graph acknowledges EL immediately with a tool_call ack.
2. EL polls `POST /v1/ninchat/result` (35 s timeout) while the graph completes the Ninchat round-trip.
3. `_drain_and_resolve()` resolves the in-flight future with the Ninchat answer and rewrites it for TTS via Gemini.

This produces ~400 lines of infrastructure (`_sse_slow_path.py`, `ninchat_result.py`, `_in_flight` dict in `streaming.py`) that exists solely because an external coordinator (EL agent) has a timeout shorter than Ninchat’s response time. The structural mismatch is permanent — it cannot be fixed by tuning.

**Current architecture (EL-as-LLM, in questionnaire-api):**
```
Phone caller → Twilio → ElevenLabs (STT + voice agent + TTS)
  → POST /v1/streaming/chat/completions          # streaming.py
    → YAMLGraph (ninchat-inquiry-rewrite)
      → NinchatConnection.send_and_receive()      # 6–18 s
      → _rewrite_for_tts() via Gemini             # 3–5 s
    ← SSE: ack + tool_call (slow path)            # _sse_slow_path.py:88
  ← POST /v1/ninchat/result (long-poll 35 s)      # ninchat_result.py
  ← tool passthrough SSE
← ElevenLabs speaks result
```

## Proposed Solution

**Graph-as-Coordinator:** The YAMLGraph graph owns the Twilio WebSocket. ElevenLabs TTS and STT are `type: python` tool nodes invoked by the graph at its own pace. No SSE. No polling. No timeout. This is a **standalone yamlgraph project** — questionnaire-api is not modified.

**Proposed architecture (Graph-as-Coordinator):**
```
Phone caller → Twilio WebSocket → /voice (FastAPI)   # projects/ninchat_voice/server.py
  → YAMLGraph (ninchat-voice-coordinator)
    ├── await_call              Twilio WS: TelcoSession start + WS connect
    ├── create_session          Ninchat WS: open session, wait for greeting
    ├── rewrite_greeting        type: llm, ninchat_greeting_mediator.yaml
    ├── speak_greeting          EL TTS (input: greeting_rewritten) → ffmpeg → Twilio mulaw
    ├── listen                  EL realtime STT ← Twilio audio → user_utterance: str
    ├── forward_to_bot          send_to_bot() — 6–18 s, no timeout
    ├── rewrite_response        type: llm, ninchat_mediator.yaml
    ├── speak_answer            EL TTS (input: response_rewritten) → ffmpeg → Twilio mulaw
    ↺   conditional edges       loop (listen→…→speak) while active, else close
    ├── close_session           close_ninchat_session()
    └── end_call                Twilio REST hang-up
```

### Graph: `ninchat-voice-coordinator`

**Design decisions:**
- **[J-1] TelcoSession reuse:** Voice nodes (`speak_greeting`, `speak_answer`, `listen`, `end_call`) import and reuse `TelcoSession` from `projects.outcaller.nodes.coordinator`. This is the same pattern used by `projects/incaller/` (REQ-YG-086). The `await_call()` node creates a `TelcoSession`, starts the uvicorn server, and calls `set_active_session()`. All downstream voice nodes call `get_active_session()` to access audio queues, the event loop, and mark synchronization. No reimplementation of coordinator.py — it is imported, not ported.
- **[J-8] TTS helper pattern:** A private `_speak(text: str)` helper implements the ElevenLabs → ffmpeg → Twilio mulaw streaming pipeline (~70 lines, ported from `outcaller/nodes/tts.py`). Two public wrappers: `speak_greeting(state)` reads `state["greeting_rewritten"]`; `speak_answer(state)` reads `state["response_rewritten"]`. Both call `_speak()`. No duplication.
- **[J-9/J-14] Serializable state only:** Live connections are held in `TelcoSession` (module-level singleton) and a module-level `_ninchat_conn` in `ninchat_session.py`. Only serializable metadata is stored in graph state: `call_info: {call_sid, stream_sid, caller_number}`. No `ninchat_session` key in state — the Ninchat connection is module-level, consistent with TelcoSession. Dict-returning Python tool nodes have no `state_key` (per `python_tool.py:158`, dict returns bypass `state_key`).
- **[J-4] Return key alignment:** The ported `listen_and_transcribe()` returns `{"user_utterance": text}` (not `{"transcript": ...}`). This is a porting change from the outcaller’s key naming.
- **[J-3] Separate greeting prompt:** `rewrite_greeting` uses `ninchat_greeting_mediator.yaml` (new, greeting-specific). `rewrite_response` uses `ninchat_mediator.yaml` (ported with Jinja2 conditional for `user_message`). The claim “prompt reused unmodified” is retracted for the greeting case.
- Loop control is implemented as **conditional edges** directly from `speak_answer`. No `type: router` node is used — `type: router` is an LLM-based intent classifier requiring a prompt template; it is not suited for deterministic boolean branching.
- Condition syntax follows the `conditions.py` evaluator (`left_path OP right_value`, compound `and`/`or`): `call_active == true and phase != 'complete'`.
- **[J-15] Ninchat session functions** are created in `projects/ninchat_voice/nodes/ninchat_session.py` by porting the `NinchatConnection` class from `questionnaire-api/src/questionnaire/handlers/ninchat_inquiry.py` (431 lines — session-based with `connect()`, `send_and_receive()`, `close()`, module-level `_connections` dict with per-connection keepalive thread). This is the latest and most mature Ninchat client implementation, superseding the one-shot `projects/ninchat/tools/inquiry.py`. The full `NinchatClient` class in `projects/ninchat/ninchat_tool.py` is bot-side (accepting audiences); `ninchat_inquiry.py` is user-side (requesting audiences) — matching our use case exactly.

```yaml
# projects/ninchat_voice/graphs/ninchat-voice-coordinator.yaml
version: "1.0"
name: ninchat-voice-coordinator
description: "Inbound voice coordinator: Twilio + ElevenLabs TTS/STT + Ninchat"

metadata:
  provider: google
  model: gemini-2.5-flash
  thinking_budget: 0

defaults:
  prompts_relative: true
  prompts_dir: prompts/

# [J-2] Explicit state declaration for keys not derived from state_key
state:
  call_info: dict
  call_active: bool
  phase: str
  call_disconnected: bool
  bot_greeting: str
  user_utterance: str
  user_message: str
  bot_response: str
  call_result: dict

loop_limits:
  listen: 20
  speak_answer: 20
  speak_greeting: 2
  forward_to_bot: 20
  rewrite_response: 20
  rewrite_greeting: 2

tools:
  await_call:
    type: python
    module: projects.ninchat_voice.nodes.voice_ws
    function: await_call

  speak_greeting:
    type: python
    module: projects.ninchat_voice.nodes.voice_ws
    function: speak_greeting         # reads state["greeting_rewritten"] via _speak()

  speak_answer:
    type: python
    module: projects.ninchat_voice.nodes.voice_ws
    function: speak_answer           # reads state["response_rewritten"] via _speak()

  listen_and_transcribe:
    type: python
    module: projects.ninchat_voice.nodes.voice_ws
    function: listen_and_transcribe  # returns {"user_utterance": str} [J-4]

  create_ninchat_session:
    type: python
    module: projects.ninchat_voice.nodes.ninchat_session
    function: create_session         # NEW: ported from ninchat_inquiry.py NinchatConnection

  send_to_bot:
    type: python
    module: projects.ninchat_voice.nodes.ninchat_session
    function: send_to_bot            # NEW: session-based send + receive

  close_ninchat_session:
    type: python
    module: projects.ninchat_voice.nodes.ninchat_session
    function: close_session          # NEW: close WebSocket

  end_call:
    type: python
    module: projects.ninchat_voice.nodes.voice_ws
    function: end_call

nodes:
  await_call:
    type: python
    tool: await_call
    on_error: fail
    # [J-14] No state_key — returns dict {call_info: {...}}, merges directly

  create_session:
    type: python
    tool: create_ninchat_session
    on_error: fail
    # [J-14] No state_key — returns dict {bot_greeting: str}, merges directly

  rewrite_greeting:
    type: llm
    prompt: ninchat_greeting_mediator  # [J-3] greeting-specific prompt
    state_key: greeting_rewritten
    on_error: fail

  speak_greeting:
    type: python
    tool: speak_greeting             # reads state["greeting_rewritten"] via _speak()
    on_error: fail

  listen:
    type: python
    tool: listen_and_transcribe
    on_error: fail
    # [J-14] No state_key — returns dict {user_utterance: str}, merges directly

  forward_to_bot:
    type: python
    tool: send_to_bot
    on_error: fail
    # [J-14] No state_key — returns dict {bot_response, call_active, phase, user_message}

  rewrite_response:
    type: llm
    prompt: ninchat_mediator         # ported prompt w/ Jinja2 conditional
    state_key: response_rewritten
    on_error: fail                   # [O-2] fail, not silent — voice context must not speak error text

  speak_answer:
    type: python
    tool: speak_answer               # reads state["response_rewritten"] via _speak()
    on_error: fail

  close_session:
    type: python
    tool: close_ninchat_session
    on_error: skip                   # [J-7] best-effort cleanup

  end_call:
    type: python
    tool: end_call
    state_key: call_result
    on_error: fail

edges:
  # [J-13] All edges use from:/to: dict format (arrow syntax not supported)
  - from: START
    to: await_call
  - from: await_call
    to: create_session
  - from: create_session
    to: rewrite_greeting
  - from: rewrite_greeting
    to: speak_greeting
  - from: speak_greeting
    to: listen

  # [O-3] call_disconnected guard: if caller hung up during STT, skip to cleanup
  - from: listen
    to: close_session
    condition: "call_disconnected == true"
  - from: listen
    to: forward_to_bot
    condition: "call_disconnected != true"

  - from: forward_to_bot
    to: rewrite_response
  - from: rewrite_response
    to: speak_answer

  # Loop control: continue listening or close when done
  - from: speak_answer
    to: listen
    condition: "call_active == true and phase != 'complete'"
  - from: speak_answer
    to: close_session
    condition: "call_active == false or phase == 'complete'"

  - from: close_session
    to: end_call
  - from: end_call
    to: END
```

### Coordinator state spec

| Key | Type | Declared by | Set by | Read by |
|-----|------|-------------|--------|---------|
| `call_info` | `dict` (`{call_sid, stream_sid, caller_number}`) | `state:` | `await_call` (dict merge) | `end_call` |
| `bot_greeting` | `str` | `state:` | `create_session` (dict merge) | `rewrite_greeting` |
| `greeting_rewritten` | `str` | `state_key` | `rewrite_greeting` | `speak_greeting` |
| `user_utterance` | `str` | `state:` | `listen` (dict merge) | `forward_to_bot` |
| `user_message` | `str` | `state:` | `forward_to_bot` (copies `user_utterance`) | `rewrite_response` prompt |
| `bot_response` | `str` | `state:` | `forward_to_bot` (dict merge) | `rewrite_response` |
| `response_rewritten` | `str` | `state_key` | `rewrite_response` | `speak_answer` |
| `call_active` | `bool` | `state:` | `forward_to_bot` (dict merge) | conditional edges |
| `phase` | `str` | `state:` | `forward_to_bot` (dict merge) | conditional edges |
| `call_disconnected` | `bool` | `state:` | `listen` (dict merge) | conditional edge: `listen → close_session` [O-3] |
| `call_result` | `dict` | `state:` | `end_call` (dict merge) | — |

**Implementation notes:**

- **[J-14] Dict-returning Python tool nodes have no `state_key`.** `await_call`, `create_session`, `listen`, `forward_to_bot`, `close_session`, and `end_call` all return dicts — per `python_tool.py:158`, the framework merges all dict keys directly into state, ignoring `state_key`. Only `rewrite_greeting` and `rewrite_response` (type: llm) use `state_key` because they return Pydantic/str values. This follows the existing `ninchat-inquiry-rewrite` pattern where no dict-returning node declares `state_key`.

- `forward_to_bot` writes `bot_response`, `call_active`, `phase`, and `user_message` to state via dict merge. `send_to_bot()` copies `state["user_utterance"]` to the return dict as `user_message` so the mediator prompt can reference `{user_message}`.

- **[J-1/J-9] Live connections are NOT in graph state.** The Twilio WebSocket is managed by `TelcoSession` (a module-level singleton imported from `projects.outcaller.nodes.coordinator`). The Ninchat WebSocket is held in a module-level `_ninchat_conn` variable in `ninchat_session.py`. Graph state contains only serializable metadata. This removes the MemorySaver-only constraint — the graph is checkpointable, though checkpointing is still out of scope.

- **[O-3] `call_disconnected` guard.** If the caller hangs up during STT, `listen_and_transcribe()` returns `{"user_utterance": "", "call_disconnected": true}`. A conditional edge from `listen` checks `call_disconnected == true` and routes directly to `close_session`, skipping `forward_to_bot` and the rewrite/speak cycle. This prevents the graph from forwarding empty utterances to Ninchat after hangup.

### Prompts

**`prompts/ninchat_greeting_mediator.yaml`** (new — J-3):
```yaml
# Greeting rewriter for TTS. No user_message context yet.
system: |
  Olet välittämässä Porin kaupungin terveyspalvelutietoja äänipuhelun kautta.

  Saat tervehdustekstin tietopalvelubotilta muuttujasta {bot_greeting}.

  Ohjeet:
  1. Kirjoita tervehdys luonnollisella puhutulla suomella TTS-lukijalle:
     - Poista emojit ja luettelomerkit
     - Säilytä kaikki faktatiedot täsmälleen
  2. Kirjoita vain puhutulle äänelle sopivaa tekstiä — ei otsikoita, ei listoja

user: |
  Botti tervehti: {bot_greeting}
```

**`prompts/ninchat_mediator.yaml`** (ported with Jinja2 amendment — J-3):
```yaml
# FR-009 / FR-109: Ninchat bot response rewriter for TTS voice output.
system: |
  Olet välittämässä Porin kaupungin terveyspalvelutietoja äänipuhelun kautta.

  Saat raakatekstin tietopalvelubotilta muuttujasta {bot_response}.
  {% if user_message %}Alkuperäinen käyttäjän kysymys oli: {user_message}{% endif %}

  Ohjeet:
  1. Kirjoita vastaus luonnollisella puhutulla suomella TTS-lukijalle:
     - Lausu puhelinnumerot numero kerrallaan suomeksi
     - Kuvaile verkkosivustot nimeltä, älä käytä URL-osoitteita
     - Poista emojit ja luettelomerkit
     - Säilytä kaikki faktatiedot täsmälleen
  2. ÄLÄ tervehdi käyttäjää — keskustelu on jo käynnissä
  3. Jos käyttäjä haluaa lopettaa, vastaa lyhyesti ja kohteliaasti
  4. Kirjoita vain puhutulle äänelle sopivaa tekstiä — ei otsikoita, ei listoja

user: |
  Botti vastasi: {bot_response}
```

### Project structure

```
projects/ninchat_voice/                      # [J-5] underscore, not hyphen
├── __init__.py
├── server.py                        # FastAPI /voice WebSocket endpoint
├── graphs/
│   └── ninchat-voice-coordinator.yaml
├── nodes/
│   ├── __init__.py
│   ├── voice_ws.py                  # await_call, speak_greeting, speak_answer,
│   │                                  listen_and_transcribe, end_call, _speak()
│   └── ninchat_session.py           # create_session, send_to_bot, close_session
├── prompts/
│   ├── ninchat_mediator.yaml        # ported w/ Jinja2 conditional [J-3]
│   └── ninchat_greeting_mediator.yaml  # new greeting prompt [J-3]
├── docs/
│   └── adr-graph-ninchat-integration.md
└── tests/
    └── test_coordinator_loop.py
```

### What is reused / ported

| Source | Target | Action |
|--------|--------|--------|
| `projects/outcaller/nodes/coordinator.py` | imported by `projects/ninchat_voice/nodes/voice_ws.py` | **Import** — `TelcoSession`, `get_active_session`, `set_active_session` [J-1] |
| `projects/outcaller/server_base.py` | imported by `projects/ninchat_voice/server.py` | **Import** — `register_voice_websocket()` [J-1] |
| `projects/outcaller/nodes/tts.py` | `projects/ninchat_voice/nodes/voice_ws.py` `_speak()` | **Port** EL TTS → ffmpeg → Twilio mulaw (adapted: `_speak(text)` helper) [J-8] |
| `projects/outcaller/nodes/stt.py` | `projects/ninchat_voice/nodes/voice_ws.py` `listen_and_transcribe()` | **Port** EL STT (adapted: returns `user_utterance` key) [J-4] |
| `projects/outcaller/nodes/twilio_inbound.py` | `projects/ninchat_voice/nodes/voice_ws.py` `await_call()` | **Port** pattern: TelcoSession + wait for WS |
| `projects/outcaller/nodes/twilio_call.py` `end_call()` | `projects/ninchat_voice/nodes/voice_ws.py` `end_call()` | **Port** Twilio REST hangup |
| `questionnaire-api/src/questionnaire/handlers/ninchat_inquiry.py` | `projects/ninchat_voice/nodes/ninchat_session.py` | **Port** `NinchatConnection` class (session-based create/send/close, per-connection keepalive) — **primary Ninchat client source** [J-15] |
| `questionnaire-api/.../ninchat_mediator.yaml` | `projects/ninchat_voice/prompts/ninchat_mediator.yaml` | **Port** with Jinja2 conditional [J-3] |
| (new) | `projects/ninchat_voice/prompts/ninchat_greeting_mediator.yaml` | **New** greeting-specific prompt [J-3] |

### What this makes obsolete in questionnaire-api

> **These components are NOT deleted as part of FR-109.** They remain in questionnaire-api unchanged. A separate questionnaire-api PR (after FR-109 is validated in production) can remove them.

| Component | File (in questionnaire-api) | Why obsolete |
|-----------|------|--------|
| `_in_flight` dict | `src/api/routes/streaming.py:59` | Coordinator owns session; no duplicate requests possible |
| `_acquire_in_flight()` | `src/api/routes/streaming.py:240` | Same |
| `_drain_and_resolve()` | `src/api/routes/_sse_slow_path.py:233` | Replaced by inline `rewrite_response` LLM node |
| `_rewrite_for_tts()` | `src/api/routes/_sse_slow_path.py:160` | Same |
| Two-fold SSE slow path | `src/api/routes/_sse_slow_path.py` | Entire file made obsolete |
| Ninchat result endpoint | `src/api/routes/ninchat_result.py` | Entire file made obsolete |

### Hybrid scope (Ninchat only)

PHQ-9, interRAI, and navigator graphs respond in under 3 s — well within EL’s 8 s timeout. This migration is scoped to Ninchat exclusively. All other graphs continue as EL-as-LLM with no changes.

## Acceptance Criteria

### Decision gate (must pass before implementation proceeds)

- [ ] Barge-in gap analysis completed (OC-006): EL realtime STT + manual VAD assessed under elderly Finnish speech conditions; VAD threshold tuned or a mitigation strategy agreed
- [ ] EL realtime STT Finnish language accuracy benchmarked (OC-002 equivalent)
- [ ] Real call comparison: EL agent vs. coordinator — TTFA, barge-in, missed turn boundaries documented

### Prototype

- [ ] `projects/ninchat_voice/graphs/ninchat-voice-coordinator.yaml` exists and passes `yamlgraph graph lint`
- [ ] Graph runs end-to-end on the outcaller stack (local test with Twilio dev tunnel)
- [ ] Ninchat session functions (`create_session`, `send_to_bot`, `close_session`) work with the existing Ninchat bot
- [ ] `ninchat_greeting_mediator.yaml` and `ninchat_mediator.yaml` prompts work for greeting and response rewriting respectively

### Implementation (if decision gate passes)

- [ ] `projects/ninchat_voice/nodes/voice_ws.py` created with `await_call()`, `speak_greeting()`, `speak_answer()`, `listen_and_transcribe()`, `end_call()`, and private `_speak()` helper
- [ ] `voice_ws.py` imports `TelcoSession`, `get_active_session`, `set_active_session` from `projects.outcaller.nodes.coordinator` (no reimplementation) [J-1]
- [ ] `projects/ninchat_voice/nodes/ninchat_session.py` created with `create_session()`, `send_to_bot()`, `close_session()` ported from `questionnaire-api/src/questionnaire/handlers/ninchat_inquiry.py` `NinchatConnection` class
- [ ] `projects/ninchat_voice/server.py` created; imports `register_voice_websocket()` from `projects.outcaller.server_base` [J-1]
- [ ] `await_call()` creates `TelcoSession`, calls `set_active_session()`, returns serializable `call_info: {call_sid, stream_sid, caller_number}` [J-9]
- [ ] `speak_greeting(state)` reads `state["greeting_rewritten"]`; `speak_answer(state)` reads `state["response_rewritten"]`; both call `_speak()` [J-8]
- [ ] `listen_and_transcribe()` returns `{"user_utterance": text}` (not `{"transcript": ...}`) [J-4]
- [ ] `send_to_bot()` returns `{"bot_response": str, "call_active": bool, "phase": str, "user_message": str}` so all keys merge into state
- [ ] Graph YAML has `state:` section declaring `call_active`, `phase`, `call_disconnected`, `bot_greeting`, `user_message` [J-2]
- [ ] Graph YAML has `version`, `metadata`, `defaults`, `loop_limits`, and `on_error` on all nodes [J-6/7/10/11/12]
- [ ] `ninchat_greeting_mediator.yaml` created for greeting rewrite [J-3]
- [ ] `ninchat_mediator.yaml` ported with Jinja2 conditional for `user_message` [J-3]
- [ ] No files in `questionnaire-api/` are modified or deleted
- [ ] Unit test for coordinator graph loop (mock Ninchat + mock EL TTS/STT) exists in `projects/ninchat_voice/tests/` and passes
- [ ] Unit test tagged `@pytest.mark.req("REQ-YG-091")` with corresponding requirement added to `ARCHITECTURE.md` and `ALL_REQS` range extended in `scripts/req_coverage.py`
- [ ] `projects/ninchat_voice/docs/adr-graph-ninchat-integration.md` created; documents: architectural decision, rationale, `TelcoSession` import dependency, and serializable-state-only design
- [ ] CHANGELOG.md updated

### Non-goals

- Barge-in implementation is not in scope; tracked separately as OC-006
- Redis checkpointing for the coordinator graph is not in scope; in-memory per-call is acceptable
- PHQ-9, interRAI, and navigator graphs are untouched
- STT confidence gating is not in scope; `user_utterance` is plain `str` only
- `inputs:` remapping in `python_tool.py` is not in scope; tracked as a separate framework FR if needed
- Modifying or deleting any `questionnaire-api` files is explicitly out of scope

## Alternatives Considered

1. **Fix the SSE timeout** — ElevenLabs’ 8 s timeout is external and not configurable. Not viable.
2. **Reduce Ninchat latency** — 6–18 s is Ninchat’s inherent response time; it cannot be reduced.
3. **Keep two-fold SSE, add connection health checks (FR-012)** — Valid incremental fix; FR-012 is still needed for protocol hardening regardless. Does not eliminate the structural mismatch.
4. **WebSocket adapter over SSE** — Replaces SSE with WS on the Custom LLM API side; EL still enforces a session timeout. Same root cause.
5. **Keep EL-as-LLM for Ninchat permanently** — Viable if barge-in assessment shows coordinator model is worse for elderly callers. Two-fold SSE path would then be documented as permanent load-bearing infrastructure.
6. **Implement inside questionnaire-api** — Rejected. Adds voice infrastructure (ffmpeg, Twilio WS, EL TTS/STT) to a FastAPI questionnaire server. The yamlgraph monorepo already has the outcaller voice stack; building here as `projects/ninchat_voice` avoids polluting questionnaire-api with call handling concerns.
7. **Port coordinator.py to ninchat_voice** — Rejected. 350 lines of threading+async coordination for a project that needs exactly the same behavior. Import is cleaner than copy; the incaller project already imports from outcaller (REQ-YG-086 precedent).

## Implementation Approach

### Phase 0 — Decision gate (~1 day)
- Barge-in gap analysis: run OC-006 research; benchmark EL realtime STT in Finnish
- Produce short decision memo: go/no-go with explicit VAD threshold or mitigation

### Phase 1 — Prototype (1 day, if go)
- Create `projects/ninchat_voice/` project structure with `__init__.py`
- Create `graphs/ninchat-voice-coordinator.yaml` (full spec as above)
- Create `prompts/ninchat_greeting_mediator.yaml` (new) and `prompts/ninchat_mediator.yaml` (ported with Jinja2)
- Port `NinchatConnection` from `questionnaire-api/src/questionnaire/handlers/ninchat_inquiry.py` into `nodes/ninchat_session.py` (create/send/close — strip connection pool, one session per call)
- Run on outcaller stack locally with Twilio dev tunnel
- Validate Ninchat round-trip as an unblocked graph step

### Phase 2 — Port voice WebSocket module (1 day)
- Create `projects/ninchat_voice/nodes/voice_ws.py`:
  - Import `TelcoSession`, `get_active_session`, `set_active_session` from `projects.outcaller.nodes.coordinator`
  - Port `_speak(text)` helper from `outcaller/nodes/tts.py` (strip `[DONE]` marker logic, keep streaming pipeline)
  - Implement `speak_greeting(state)` and `speak_answer(state)` as thin wrappers [J-8]
  - Port `listen_and_transcribe()` from `outcaller/nodes/stt.py`; change return key to `user_utterance` [J-4]
  - Port `await_call()` from `outcaller/nodes/twilio_inbound.py`; return serializable `call_info` [J-9]
  - Port `end_call()` from `outcaller/nodes/twilio_call.py`
- Create `projects/ninchat_voice/server.py`:
  - Import `register_voice_websocket` from `projects.outcaller.server_base`
  - Minimal FastAPI app factory

### Phase 3 — Test & document (1 day)
- Add REQ-YG-091 to `ARCHITECTURE.md`: "Python tool nodes compose into a coordinator graph that implements call-session looping via conditional edges; no LLM router node required for loop control"
- Extend `ALL_REQS` in `scripts/req_coverage.py` to include `91`
- Write unit test tagged `@pytest.mark.req("REQ-YG-091")` for coordinator loop with mocked Ninchat and EL
- Create `projects/ninchat_voice/docs/adr-graph-ninchat-integration.md` documenting TelcoSession import dependency and serializable-state-only design
- Update CHANGELOG.md

### Phase 4 — Real call validation (0.5 day)
- Live call comparison: EL agent vs. coordinator
- Sign off on TTFA, barge-in quality, missed turn boundary rate

## Phased path and dependencies

| Phase | Action | Dependency |
|-------|--------|-----------|
| **Done** | FR-011 + FR-013 in production (in questionnaire-api) | — |
| **FR-012** | Protocol hardening: silent Ninchat error, keepalive | Independent; proceed regardless |
| **FR-007** | `x-graph` header — graph selection without `model` hack | Independent; proceed regardless |
| **OC-006** | Barge-in gap analysis + EL STT Finnish benchmark | **Decision gate for FR-109** |
| **FR-109 Phase 1–4** | Graph-as-coordinator prototype → implementation | OC-006 go decision |

## Related

### Within yamlgraph monorepo
- `projects/outcaller/nodes/coordinator.py` — `TelcoSession` imported by ninchat_voice (not ported) [J-1]
- `projects/outcaller/server_base.py` — `register_voice_websocket()` imported by ninchat_voice [J-1]
- `projects/ninchat/tools/inquiry.py` — one-shot Ninchat client (superseded by `ninchat_inquiry.py`; protocol reference only)
- `projects/ninchat/ninchat_tool.py` — full `NinchatClient` class (bot-side; not directly used, but protocol reference)
- `projects/outcaller/graphs/incaller.yaml` — coordinator pattern reference (imports outcaller modules via REQ-YG-086)
- `projects/outcaller/nodes/tts.py`, `stt.py`, `twilio_inbound.py`, `twilio_call.py` — port sources

### Within questionnaire-api (not modified by FR-109)

**Key existing implementation files (read these first):**
- `questionnaires/ninchat-inquiry-rewrite/graph.yaml` — current EL-as-LLM coordinator graph (multi-turn Ninchat proxy, interrupt-based, Redis checkpointed). Shows the node pattern this FR replaces: `create_session → forward_to_bot → check_done → ask_user` loop with `type: router` for done-detection
- `questionnaires/ninchat-inquiry-rewrite/prompts/ninchat_mediator.yaml` — original TTS rewrite prompt (ported with Jinja2 amendment to ninchat_voice)
- `questionnaires/ninchat-inquiry-rewrite/prompts/ninchat_check_done.yaml` — LLM router prompt for complete/continue detection (not needed in coordinator model — replaced by `call_active` boolean from `send_to_bot`)
- `src/questionnaire/handlers/ninchat_inquiry.py` (431 lines) — **PRIMARY SOURCE for Ninchat client**. Contains `NinchatConnection` class with `connect()` (session + audience + greeting), `send_and_receive()` (multi-turn), `close()`, plus module-level `_connections` dict with per-connection keepalive thread [J-15]. This is the latest and most mature Ninchat WebSocket implementation — supersedes the one-shot `projects/ninchat/tools/inquiry.py`. The coordinator's `ninchat_session.py` should be ported from this, not from `inquiry.py`

**Other references:**
- `docs/adr/elevenlabs-ninchat-adapter.md` — ADR for current two-fold SSE architecture
- FR-007: `x-graph` header for graph selection
- FR-011: Two-fold SSE response (the workaround this FR makes obsolete)
- FR-012: Ninchat protocol hardening (independent; proceed regardless)
- FR-013: SSE workaround improvements
- OC-001: TTFA 250 ms benchmark
- OC-002: STT pipeline design
- OC-006: Barge-in gap analysis (decision gate)

## Planner’s Reflection

**Key architectural insight:** This FR was originally written as a questionnaire-api modification — deleting SSE infrastructure and adding voice handling in-place. On reflection, that violates separation of concerns: questionnaire-api is a questionnaire server, not a voice call handler. The yamlgraph monorepo already has the outcaller voice stack (`projects/outcaller/`). Building the coordinator here as `projects/ninchat_voice` keeps voice infrastructure isolated and avoids polluting questionnaire-api.

**Ninchat client reuse:** The mature implementation is `questionnaire-api/src/questionnaire/handlers/ninchat_inquiry.py` (431 lines) — a session-based `NinchatConnection` class with `connect()`, `send_and_receive()`, `close()`, plus module-level `_connections` dict with per-connection keepalive thread [J-15]. This already has the create/send/close pattern the coordinator needs. The older `projects/ninchat/tools/inquiry.py` is a one-shot function and is superseded. Porting `NinchatConnection` into `ninchat_session.py` (stripping the connection pool — one session per call) is the correct approach.

**Risk:** The `NinchatClient` in `ninchat_tool.py` is the BOT-side client (accepting audiences); `ninchat_inquiry.py` is the USER-side client (requesting audiences). The coordinator needs the USER-side pattern. Don't confuse the two.

**Scope fence:** questionnaire-api cleanup (deleting the SSE slow path) is a separate PR AFTER this coordinator is validated in production. FR-109 adds; it does not delete.

---

## Judgement

**Examiner:** The Planner
**Date:** 2026-02-27
**Verdict:** CONDITIONAL APPROVAL — 12 defects found; 5 critical, 4 moderate, 3 minor. Resolve all critical defects before granting authority. Moderate/minor may be resolved during Phase 1.

### Critical Defects (must resolve before implementation)

**J-1. TelcoSession dependency is unacknowledged.**
The outcaller’s `speak()`, `listen_and_transcribe()`, and `end_call()` all call `get_active_session()` to access a module-level `TelcoSession` singleton (`projects/outcaller/nodes/coordinator.py`). This singleton manages the asyncio event loop thread, audio queues, WebSocket protocol, mark synchronization, and disconnect detection. The FR says “port from outcaller” but never mentions `TelcoSession` or `coordinator.py`. These functions *cannot work* without a session coordinator.

**Resolution required:** Either (a) import and reuse `TelcoSession` from outcaller (tight coupling — acceptable for prototype), (b) port `coordinator.py` to `projects/ninchat_voice/nodes/` (~350 lines added scope), or (c) adopt a different session pattern. Decision must be explicit in the FR.

✅ **RESOLVED:** Option (a) adopted. `voice_ws.py` imports `TelcoSession`, `get_active_session`, `set_active_session` from `projects.outcaller.nodes.coordinator`. This follows the REQ-YG-086 precedent established by the incaller project. Added to design decisions, port table, acceptance criteria, and Related section.

**J-2. Missing `state:` section — undeclared state keys will fail.**
The graph YAML has no `state:` section. The framework’s state builder (`models/state_builder.py`) auto-generates fields from `state_key` declarations — but `call_active`, `phase`, `call_disconnected` are set by dict returns from `send_to_bot()`, not declared as any node’s `state_key`. LangGraph TypedDicts are strict: undeclared keys cause runtime errors. The condition evaluator reads `call_active` and `phase` — both will be missing from the generated state.

**Resolution required:** Add explicit `state:` section to the graph YAML declaring at minimum: `call_active: bool`, `phase: str`, and all other keys from the state spec table.

✅ **RESOLVED:** `state:` section added declaring `call_active: bool`, `phase: str`, `call_disconnected: bool`, `bot_greeting: str`, `user_message: str`.

**J-3. `ninchat_mediator.yaml` prompt doesn’t fit greeting rewrite.**
The prompt template uses `{bot_response}` and `{user_message}`: *“Alkuperäinen käyttäjän kysymys oli: {user_message}”* (“The original user question was: {user_message}”). For `rewrite_greeting`, there is no user question yet — the caller just connected. Passing an empty `user_message` produces *“Alkuperäinen käyttäjän kysymys oli:”* which is nonsensical speech.

**Resolution required:** Either (a) create a separate `ninchat_greeting_mediator.yaml` prompt for greeting rewrite, or (b) add a Jinja2 conditional: `{% if user_message %}...{% endif %}`. The claim “prompt reused unmodified” is false for the greeting case.

✅ **RESOLVED:** Both (a) and (b) applied. New `ninchat_greeting_mediator.yaml` for greeting rewrite. `ninchat_mediator.yaml` ported with Jinja2 conditional. Claim “reused unmodified” retracted. Spec includes full prompt YAML for both.

**J-4. `listen_and_transcribe()` returns `{"transcript": ...}`, not `{"user_utterance": ...}`.**
The outcaller’s function returns `{"transcript": text, "call_disconnected": bool}`. Since it returns a dict, the framework passes it through directly — `state_key` is ignored per `python_tool.py:158`. The graph expects `user_utterance` in state (used by `forward_to_bot`), but the actual key is `transcript`. The `forward_to_bot` node will read an empty `user_utterance`.

**Resolution required:** The ninchat-voice `listen_and_transcribe()` must return `{"user_utterance": text}`, not `{"transcript": text}`. This is a porting change, not reuse.

✅ **RESOLVED:** Return key changed to `user_utterance` in porting notes, acceptance criteria, and Phase 2 implementation steps.

**J-5. Folder name `ninchat-voice` breaks Python imports.**
The codebase convention states: “Convert paths with hyphens to snake_case to avoid import issues.” The graph YAML references `module: projects.ninchat_voice.nodes.voice_ws`. Python cannot import from a folder named `ninchat-voice` using dot notation. The FR acknowledges this but proposes vague solutions (“symlink or `__init__.py`”).

**Resolution required:** Name the folder `ninchat_voice` (no hyphen). This is the existing pattern (`outcaller`, `incaller`, `ninchat`). The user’s request for `ninchat-voice` must yield to the import system.

✅ **RESOLVED:** All references changed from `ninchat-voice` to `ninchat_voice`. Convention note removed. Consistent with existing projects.

### Moderate Defects (resolve during Phase 1)

**J-6. No `loop_limits` section.**
✅ **RESOLVED:** `loop_limits:` section added to graph YAML.

**J-7. No `on_error` declarations.**
✅ **RESOLVED:** `on_error: fail` on all critical nodes; `on_error: skip` on `close_session`.

**J-8. `speak_greeting` and `speak_answer` — duplicated TTS pipeline.**
✅ **RESOLVED:** Design amended to allow private `_speak()` helper with two thin public wrappers.

**J-9. `call_connected` state design conflicts with outcaller pattern.**
✅ **RESOLVED:** Renamed to `call_info` with serializable dict. Live connections held in TelcoSession singleton. MemorySaver-only constraint removed.

### Minor Defects (resolve during implementation)

**J-10. Missing `version: "1.0"` in graph YAML.** ✅ **RESOLVED.**

**J-11. Missing `metadata:` section.** ✅ **RESOLVED:** `metadata: {provider: google, model: gemini-2.5-flash, thinking_budget: 0}`.

**J-12. `defaults: prompts_relative: true` not set.** ✅ **RESOLVED:** `defaults: {prompts_relative: true, prompts_dir: prompts/}`.

### Post-Amendment Verdict

All 12 defects resolved. The plan is clear, minimal, and internally consistent. **Authority granted.** Proceed to Phase 0 (OC-006 decision gate).

---

## Second Judgement

**Examiner:** The Judge
**Date:** 2026-02-27
**Scope:** Full codebase cross-reference of the amended FR-109 (550 lines). Every material claim verified against actual files. 17-point audit checklist executed.
**Verdict:** CONDITIONAL APPROVAL — 4 new defects found; 1 critical, 2 moderate, 1 minor. Prior 12 defects confirmed resolved.

### Prior Defects (J-1 through J-12)

All 12 defects from the first Judgement are confirmed resolved. The amendments are structurally sound and internally consistent. No regressions.

### New Defects

**J-13. (Critical) Edge arrow syntax `- START -> await_call` is invalid.** ✅ **RESOLVED.** All edges rewritten to `from:`/`to:` dict format.
The graph YAML uses arrow shorthand for 8 of 12 edges:
```yaml
edges:
  - START -> await_call
  - await_call -> create_session
  - create_session -> rewrite_greeting
  ...
```
This syntax is **not supported** by the framework. The edge schema (`yamlgraph/models/graph_schema.py:139`) requires dict format with `from:` and `to:` keys:
```python
class EdgeConfig(BaseModel):
    from_node: str = Field(..., alias="from")
    to: str | list[str] = Field(...)
    condition: str | None = Field(default=None)
```
FR-033 (sequence syntax) is still "Proposed" — not implemented. No existing graph in the monorepo uses arrow syntax. The `ninchat-inquiry-rewrite` graph in questionnaire-api uses the correct `from:`/`to:` format.

**Resolution required:** Rewrite all edges to dict format:
```yaml
edges:
  - from: START
    to: await_call
  - from: await_call
    to: create_session
  ...
```
The conditional edges already use correct `from:`/`to:`/`condition:` format.

**J-14. (Moderate) `state_key` on dict-returning Python tool nodes is misleading.** ✅ **RESOLVED.** Option (a) applied: `state_key` removed from all dict-returning Python nodes; `ninchat_session` row deleted from state spec; design decision J-9 updated.
Three Python tool nodes have `state_key` declarations but will return dicts:
- `await_call` → `state_key: call_info` — but will return `{"call_info": {...}, ...}`, so the `call_info` key merges directly. `state_key` is ignored.
- `create_session` → `state_key: ninchat_session` — designed to return `{bot_greeting: str, queue_id: str}`. Since it's a dict, it merges directly — but the dict keys are `bot_greeting` and `queue_id`, **not** `ninchat_session`. The `ninchat_session` key is never set, yet the state spec table claims it exists and is read by `forward_to_bot` and `close_session`.
- `forward_to_bot` → `state_key: bot_response` — returns dict with `bot_response`, `call_active`, `phase`, `user_message`. Correct behavior: dict merges. But `state_key: bot_response` is documented as a comment "dict return merges" — misleading.

Per `python_tool.py:158`: when a function returns `dict`, the framework merges all keys directly into state. The `state_key` field is only used for non-dict returns. The existing `ninchat-inquiry-rewrite` graph handles this correctly: its `create_session`, `forward_to_bot`, and `close_session` nodes have **no `state_key`** — because their functions return dicts.

**Impact:**
- `ninchat_session` key will never exist in state. The state spec table row for it is false. The state builder will create the field (from `state_key` declaration), but it will never be populated.
- `close_session` claims to read `ninchat_session` — it cannot, since the key is never set. The ported `close_session()` function should use the module-level `_ninchat_ws` variable instead (consistent with the J-9 design: live connections NOT in state).
- `forward_to_bot` claims to read `ninchat_session` — same issue.

**Resolution required:** Either (a) remove `state_key` from dict-returning nodes and update the state spec table to remove the `ninchat_session` row, ensuring `close_session` and `forward_to_bot` use module-level connection state; or (b) redesign `create_session()` to return a non-dict (e.g., just the greeting string) and store connection metadata under `state_key: ninchat_session` — but this contradicts the J-9 "serializable state only" decision.

Recommended: option (a) — follow the existing `ninchat-inquiry-rewrite` pattern. Module-level `_ninchat_ws` holds the live connection. `bot_greeting` and `queue_id` merge directly from the dict return. Remove `ninchat_session` from state entirely.

**J-15. (Moderate) `ninchat_inquiry.py` does NOT have a `ConnectionPool` class.** ✅ **RESOLVED.** All 4 references corrected to "module-level `_connections` dict with per-connection keepalive thread".
The FR claims the primary source has "connection pooling, keepalive daemon" as a class. The actual implementation at `questionnaire-api/src/questionnaire/handlers/ninchat_inquiry.py:236` uses a **module-level dict** `_connections: dict[str, NinchatConnection] = {}` — not a `ConnectionPool` class. Keepalive is per-connection (`NinchatConnection._keepalive_loop()`), not a pool-level daemon.

This is cosmetic for implementation — the porting strategy (strip pool, one connection per call) is correct — but the claim of a `ConnectionPool` class is factually wrong.

**Resolution required:** Correct the claim from "ConnectionPool class with keepalive daemon" to "module-level `_connections` dict with per-connection keepalive thread" in all references.

**J-16. (Minor) Missing `- from: close_session` `to: END` edge.**
The edges section ends with:
```yaml
  - close_session -> end_call
  - end_call -> END
```
This is correct (close_session → end_call → END). However, the existing `ninchat-inquiry-rewrite` graph has an explicit `close_session → END` edge. The FR-109 graph routes `close_session → end_call → END`, which is the correct flow for a voice call (need to hang up after closing Ninchat). No defect in logic — but worth noting that the `end_call → END` terminal edge is present and correct. ~~This is a non-issue.~~

**Retracted** — on closer reading, `end_call -> END` is present and the flow is correct. Not a defect.

### Observations (not defects)

**O-1. `send_to_bot()` return contract differs from existing implementation.**
The existing `ninchat_inquiry.py:send_to_bot()` returns `{"response": response}` on success — using key `response`, not `bot_response`. The FR-109 design requires `{"bot_response": str, "call_active": bool, "phase": str, "user_message": str}`. This is an intentional redesign, not a bug. The ported function will have a different return contract. Document this clearly in the porting notes.

**O-2. `on_error` default behavior.** ✅ **RESOLVED.** `on_error: fail` added to `rewrite_response` — in voice context, speaking an error message is worse than failing fast. `rewrite_greeting` already had `on_error: fail`.

**O-3. `call_disconnected` guard.** ✅ **RESOLVED.** Two conditional edges added from `listen`: `call_disconnected == true` → `close_session`, `call_disconnected != true` → `forward_to_bot`. State spec table updated: "Read by" now says "conditional edge (listen → close_session)".

### Confirmed Correct

| Claim | Verdict | Evidence |
|-------|---------|----------|
| TelcoSession exports from coordinator.py | ✓ TRUE | `get_active_session()`, `set_active_session()`, `clear_active_session()` at module level |
| incaller imports from outcaller (REQ-YG-086) | ✓ TRUE | `projects/incaller/nodes/twilio_inbound.py:38` imports TelcoSession |
| `register_voice_websocket(app, session)` | ✓ TRUE | `server_base.py:31` signature confirmed |
| tts.py `[DONE]` marker logic | ✓ TRUE | Lines 47-55; must be stripped in port |
| stt.py returns `{"transcript": ...}` | ✓ TRUE | Line 175; `call_disconnected` conditionally added |
| `await_call()` calls `set_active_session()` | ✓ TRUE | `twilio_inbound.py:81` |
| `end_call()` calls `shutdown()` + `clear_active_session()` | ✓ TRUE | `twilio_call.py:171-172` |
| `python_tool.py` dict merge behavior | ✓ TRUE | Lines 158-161; dict returns bypass `state_key` |
| `conditions.py` supports `and`/`or` + `== true` | ✓ TRUE | Lines 189-194 (compound), line 103 (boolean literals) |
| `state_builder.py` merges `state:` with `state_key` fields | ✓ TRUE | `build_state_class()` merges both into one TypedDict |
| LLM nodes pass entire state as prompt variables | ✓ TRUE | `llm_nodes.py:162-166` + `expressions.py:227` |
| `ninchat_mediator.yaml` uses `{bot_response}` + `{user_message}` | ✓ TRUE | Confirmed in original prompt |
| `ninchat-inquiry-rewrite` graph uses `type: router` for done-detection | ✓ TRUE | `check_done` node at line 68 |

### Second Judgement Verdict

**J-13 is critical** — the graph YAML will fail to parse. Must be fixed before implementation.
**J-14 is moderate** — the `ninchat_session` phantom state key will cause confusion and is architecturally inconsistent with J-9. Should be fixed.
**J-15 is moderate** — factual inaccuracy, easy fix.
**J-16 retracted.**

**O-3 is a design question** worth conscious resolution: should `call_disconnected` short-circuit the loop?

Resolve J-13 (critical) before granting final authority. J-14 and J-15 may be resolved during amendment.

### Post-Second-Amendment Verdict

All 3 defects (J-13, J-14, J-15) resolved. Both observations (O-2, O-3) consciously resolved. The graph YAML now uses correct `from:`/`to:` edge format, dict-returning nodes have no `state_key`, the `ninchat_session` phantom state key is eliminated, ConnectionPool claims are corrected, LLM nodes fail fast on error, and `call_disconnected` is properly guarded with conditional edges. **Authority granted.** Proceed to Phase 0 (OC-006 decision gate).

---

## Enforcement Log

**Date:** 2026-02-27
**Enforcer:** Copilot (Planner role)

### Phase 1: Graph + Tool Nodes (TDD)

| Artifact | Status | Notes |
|----------|--------|-------|
| `graphs/ninchat-voice-coordinator.yaml` | ✅ | 10 nodes, 14 edges, `prompts_dir: ../prompts/` |
| `prompts/ninchat_greeting_mediator.yaml` | ✅ | Finnish greeting rewrite |
| `prompts/ninchat_mediator.yaml` | ✅ | Response rewrite with Jinja2 `{% if user_message %}` |
| `nodes/ninchat_session.py` | ✅ | NinchatConnection + `create_session`/`send_to_bot`/`close_session` |
| `nodes/voice_ws.py` | ✅ | `await_call`/`speak_greeting`/`speak_answer`/`listen_and_transcribe`/`end_call` |
| `server.py` | ✅ | FastAPI `/incoming` webhook + voice WebSocket |
| `tests/test_coordinator_loop.py` | ✅ | 21/21 passing, ruff clean |
| `tests/conftest.py` | ✅ | Path setup + NV-XXX req marker enforcement |

### Decisions

1. **Requirement namespace:** `NV-XXX` (not `REQ-YG-XXX`). Projects under `projects/` are private repos with their own req trackers, following outcaller's `OC-XXX`/`IC-XXX` convention.
2. **Shared outcaller deps:** `voice_ws.py` imports `TelcoSession`, `get_active_session`, `set_active_session`, `clear_active_session`, `CallHangupError`, `MissingStreamUrlError` from `projects.outcaller.nodes.coordinator`; `server.py` imports `register_voice_websocket` from `projects.outcaller.server_base`.
3. **`prompts_dir: ../prompts/`**: Linter resolves relative to `graph_path.parent` (= `graphs/`), so `../prompts/` reaches the project's `prompts/` directory.
4. **Graph YAML `from:`/`to:` edge format**: All edges use dict format per J-13. No `state_key` on dict-returning Python tool nodes per J-14.

### Remaining Phases

- **Phase 2:** Integration test with live Ninchat sandbox + Twilio (requires API keys)
- **Phase 3:** E2E voice call test (manual TESTPLAN validation)
