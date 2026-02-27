# Feature Request: FR-101 Graph-as-Coordinator for Ninchat Voice Integration

**Priority:** HIGH
**Type:** Feature
**Status:** Approved
**Effort:** 5 days
**Requested:** 2026-02-27

## Summary

Replace the ElevenLabs-as-LLM architecture (two-fold SSE slow path, `_in_flight` dedup shield, `POST /v1/ninchat/result` polling endpoint) with a YAMLGraph coordinator graph that owns the Twilio WebSocket session and calls ElevenLabs TTS/STT as stateless `type: python` tool nodes — eliminating the structural root cause of FR-011/FR-013: ElevenLabs' 8 s Custom LLM timeout.

## Value Statement

The Ninchat voice channel's 6–18 s WebSocket round-trip becomes an ordinary graph step with no external timeout, allowing `ninchat_inquiry.py` tools and `ninchat_mediator.yaml` prompt to be reused unchanged while deleting ~400 lines of workaround code from `questionnaire-api`.

## Problem

ElevenLabs' Custom LLM API abandons the SSE connection after ~8 s. Ninchat's WebSocket round-trip takes 6–18 s. FR-011 and FR-013 introduced a two-fold SSE slow path to bridge this gap:

1. The graph acknowledges EL immediately with a tool_call ack.
2. EL polls `POST /v1/ninchat/result` (35 s timeout) while the graph completes the Ninchat round-trip.
3. `_drain_and_resolve()` resolves the in-flight future with the Ninchat answer and rewrites it for TTS via Gemini.

This produces ~400 lines of infrastructure (`_sse_slow_path.py`, `ninchat_result.py`, `_in_flight` dict in `streaming.py`) that exists solely because an external coordinator (EL agent) has a timeout shorter than Ninchat's response time. The structural mismatch is permanent — it cannot be fixed by tuning.

**Current architecture (EL-as-LLM):**
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

**Graph-as-Coordinator:** The YAMLGraph graph owns the Twilio WebSocket. ElevenLabs TTS and STT are `type: python` tool nodes invoked by the graph at its own pace. No SSE. No polling. No timeout.

**Proposed architecture (Graph-as-Coordinator):**
```
Phone caller → Twilio WebSocket → /voice (FastAPI)   # voice_ws.py
  → YAMLGraph (ninchat-voice-coordinator)
    ├── await_call              Twilio WS: extract call_sid from first 'connected' frame
    ├── create_session          NinchatConnection: open WS, wait for greeting
    ├── rewrite_greeting        type: llm, ninchat_mediator.yaml (REUSED)
    ├── speak_greeting          EL TTS (input: greeting_rewritten) → ffmpeg → Twilio mulaw
    ├── listen                  EL realtime STT ← Twilio audio → user_utterance: str
    ├── forward_to_bot          send_to_bot() — 6–18 s, no timeout
    ├── rewrite_response        type: llm, ninchat_mediator.yaml (REUSED)
    ├── speak_answer            EL TTS (input: response_rewritten) → ffmpeg → Twilio mulaw
    ↺   conditional edges       loop (listen→…→speak) while active, else close
    ├── close_session           close_bot_session()
    └── end_call                Twilio REST hang-up
```

### Graph: `ninchat-voice-coordinator`

**Design decisions:**
- `type: python` tool nodes receive the full state dict (framework does not support `inputs:` remapping). `speak_greeting(state)` reads `state["greeting_rewritten"]` directly; `speak_answer(state)` reads `state["response_rewritten"]` directly. Two separate functions; no shared helper.
- Loop control is implemented as **conditional edges** directly from `speak_answer`. No `type: router` node is used — `type: router` is an LLM-based intent classifier requiring a prompt template; it is not suited for deterministic boolean branching.
- Condition syntax follows the `conditions.py` evaluator (`left_path OP right_value`, compound `and`/`or`): `call_active == true and phase != 'complete'`.

```yaml
# questionnaires/ninchat-voice-coordinator/graph.yaml
name: ninchat-voice-coordinator
description: "Inbound voice coordinator: Twilio + ElevenLabs TTS/STT + Ninchat"

tools:
  await_call:
    type: python
    module: api.routes.voice_ws
    function: await_call

  speak_greeting:
    type: python
    module: api.routes.voice_ws
    function: speak_greeting         # reads state["greeting_rewritten"]

  speak_answer:
    type: python
    module: api.routes.voice_ws
    function: speak_answer           # reads state["response_rewritten"]

  listen_and_transcribe:
    type: python
    module: api.routes.voice_ws
    function: listen_and_transcribe

  create_ninchat_session:
    type: python
    module: questionnaire.handlers.ninchat_inquiry
    function: create_bot_session     # REUSED, no change

  send_to_bot:
    type: python
    module: questionnaire.handlers.ninchat_inquiry
    function: send_to_bot            # REUSED, no change; returns {bot_response, call_active, phase}

  close_ninchat_session:
    type: python
    module: questionnaire.handlers.ninchat_inquiry
    function: close_bot_session      # REUSED, no change

  end_call:
    type: python
    module: api.routes.voice_ws
    function: end_call

nodes:
  await_call:
    type: python
    tool: await_call
    state_key: call_connected        # {call_sid: str, ws: WebSocket}

  create_session:
    type: python
    tool: create_ninchat_session
    state_key: ninchat_session

  rewrite_greeting:
    type: llm
    prompt: ninchat_mediator         # REUSED prompt
    state_key: greeting_rewritten

  speak_greeting:
    type: python
    tool: speak_greeting             # reads state["greeting_rewritten"] directly

  listen:
    type: python
    tool: listen_and_transcribe
    state_key: user_utterance        # str (plain transcript; is_final consumed internally)

  forward_to_bot:
    type: python
    tool: send_to_bot
    state_key: bot_response          # dict return merges bot_response + call_active + phase into state

  rewrite_response:
    type: llm
    prompt: ninchat_mediator         # REUSED prompt
    state_key: response_rewritten

  speak_answer:
    type: python
    tool: speak_answer               # reads state["response_rewritten"] directly

  close_session:
    type: python
    tool: close_ninchat_session

  end_call:
    type: python
    tool: end_call

edges:
  - START -> await_call
  - await_call -> create_session
  - create_session -> rewrite_greeting
  - rewrite_greeting -> speak_greeting
  - speak_greeting -> listen
  - listen -> forward_to_bot
  - forward_to_bot -> rewrite_response
  - rewrite_response -> speak_answer
  - from: speak_answer
    to: listen
    condition: "call_active == true and phase != 'complete'"
  - from: speak_answer
    to: close_session
    condition: "call_active == false or phase == 'complete'"
  - close_session -> end_call
  - end_call -> END
```

### Coordinator state spec

| Key | Type | Set by | Read by |
|-----|------|--------|---------|
| `call_connected` | `dict` (`{call_sid: str, ws: WebSocket}`) | `await_call` | `speak_greeting`, `listen`, `speak_answer`, `end_call` |
| `ninchat_session` | `dict` | `create_session` | `forward_to_bot`, `close_session` |
| `greeting_rewritten` | `str` | `rewrite_greeting` | `speak_greeting` |
| `user_utterance` | `str` | `listen` | `forward_to_bot` |
| `bot_response` | `str` | `forward_to_bot` | `rewrite_response` |
| `response_rewritten` | `str` | `rewrite_response` | `speak_answer` |
| `call_active` | `bool` | `forward_to_bot` (hangup detection) | conditional edges |
| `phase` | `str` | `forward_to_bot` (Ninchat session state) | conditional edges |

**Implementation notes:**

- `forward_to_bot` writes `bot_response`, `call_active`, and `phase` to state. When `send_to_bot()` returns a dict, all keys merge into state regardless of `state_key`. `state_key: bot_response` only governs single non-dict returns. Ensure `send_to_bot()` returns `{"bot_response": ..., "call_active": ..., "phase": ...}`.

- `call_connected` holds a live `WebSocket`; `ninchat_session` holds a live `NinchatConnection`. These objects are not serializable. **This graph must use `MemorySaver` only.** Document this constraint explicitly in `docs/adr/graph-ninchat-integration.md`. SQLite/Redis checkpointing for this graph is out of scope (see Non-goals).

### What is reused unchanged

| Current component | New role |
|------------------|---------|
| `ninchat_inquiry.py:244` `create_bot_session()` | `create_ninchat_session` tool node |
| `ninchat_inquiry.py:276` `send_to_bot()` | `send_to_bot` tool node |
| `ninchat_inquiry.py:311` `close_bot_session()` | `close_ninchat_session` tool node |
| `ninchat_mediator.yaml` prompt | `rewrite_greeting` and `rewrite_response` LLM nodes |

### What is deleted from questionnaire-api

| Component | File | Reason |
|-----------|------|--------|
| `_in_flight` dict | `src/api/routes/streaming.py:59` | Coordinator owns session; no duplicate requests possible |
| `_acquire_in_flight()` | `src/api/routes/streaming.py:240` | Same |
| `_drain_and_resolve()` | `src/api/routes/_sse_slow_path.py:233` | Replaced by inline `rewrite_response` LLM node |
| `_rewrite_for_tts()` | `src/api/routes/_sse_slow_path.py:160` | Same |
| Two-fold SSE slow path | `src/api/routes/_sse_slow_path.py` | Entire file deleted |
| Ninchat result endpoint | `src/api/routes/ninchat_result.py` | Entire file deleted |

### What is added to questionnaire-api

| Component | Source reference |
|----------|-----------------|
| `/voice` WebSocket server | Port `../yamlgraph/projects/outcaller/server_base.py` → `src/api/routes/voice_ws.py` |
| `await_call()`, `speak_greeting()`, `speak_answer()`, `listen_and_transcribe()`, `end_call()` | Port from `outcaller/nodes/twilio_inbound.py`, `tts.py`, `stt.py`, `twilio_call.py` |
| `questionnaires/ninchat-voice-coordinator/graph.yaml` | New coordinator graph |
| `ffmpeg` | Add to `Dockerfile` (one-line) |

### Hybrid scope (Ninchat only)

PHQ-9, interRAI, and navigator graphs respond in under 3 s — well within EL's 8 s timeout. This migration is scoped to Ninchat exclusively. All other graphs continue as EL-as-LLM with no changes.

## Acceptance Criteria

### Decision gate (must pass before implementation proceeds)

- [ ] Barge-in gap analysis completed (OC-006): EL realtime STT + manual VAD assessed under elderly Finnish speech conditions; VAD threshold tuned or a mitigation strategy agreed
- [ ] EL realtime STT Finnish language accuracy benchmarked (OC-002 equivalent)
- [ ] Real call comparison: EL agent vs. coordinator — TTFA, barge-in, missed turn boundaries documented

### Prototype

- [ ] `questionnaires/ninchat-voice-coordinator/graph.yaml` exists and passes `yamlgraph graph lint`
- [ ] Graph runs end-to-end on the outcaller stack (local test with Twilio dev tunnel)
- [ ] `ninchat_inquiry.py` functions imported unmodified as tool nodes
- [ ] `ninchat_mediator.yaml` prompt reused unmodified as LLM nodes

### Implementation (if decision gate passes)

- [ ] `src/api/routes/voice_ws.py` created with `await_call()`, `speak_greeting()`, `speak_answer()`, `listen_and_transcribe()`, `end_call()` ported from outcaller
- [ ] `await_call()` docstring states: awaits first Twilio `connected` frame, extracts `call_sid`, injects `call_connected: {call_sid: str, ws: WebSocket}` into state
- [ ] `speak_greeting(state)` reads `state["greeting_rewritten"]`; `speak_answer(state)` reads `state["response_rewritten"]` — no `inputs:` stanza in YAML (framework does not support it)
- [ ] `listen_and_transcribe()` returns plain `str`; `is_final` EL flag consumed internally, not surfaced to state
- [ ] `send_to_bot()` returns `{"bot_response": str, "call_active": bool, "phase": str}` so all three keys merge into state
- [ ] `ffmpeg` added to `Dockerfile`
- [ ] `src/api/routes/_sse_slow_path.py` deleted
- [ ] `src/api/routes/ninchat_result.py` deleted
- [ ] `_in_flight` dict and `_acquire_in_flight()` removed from `src/api/routes/streaming.py`
- [ ] All existing PHQ-9, interRAI, navigator graph tests pass without modification
- [ ] Unit test for coordinator graph loop (mock Ninchat + mock EL TTS/STT) exists in `tests/unit/` and passes
- [ ] Unit test tagged `@pytest.mark.req("REQ-YG-091")` with corresponding requirement added to `ARCHITECTURE.md` and `ALL_REQS` range extended in `scripts/req_coverage.py`
- [ ] `docs/adr/graph-ninchat-integration.md` updated; documents: architectural decision, rationale, and **MemorySaver-only constraint** (non-serializable `WebSocket`/`NinchatConnection` objects in state prevent disk-based checkpointing)
- [ ] CHANGELOG.md updated

### Non-goals

- Barge-in implementation is not in scope; tracked separately as OC-006
- Redis checkpointing for the coordinator graph is not in scope; in-memory per-call is acceptable
- PHQ-9, interRAI, and navigator graphs are untouched
- STT confidence gating is not in scope; `user_utterance` is plain `str` only
- `inputs:` remapping in `python_tool.py` is not in scope; tracked as a separate framework FR if needed

## Alternatives Considered

1. **Fix the SSE timeout** — ElevenLabs' 8 s timeout is external and not configurable. Not viable.
2. **Reduce Ninchat latency** — 6–18 s is Ninchat's inherent response time; it cannot be reduced in `questionnaire-api`.
3. **Keep two-fold SSE, add connection health checks (FR-012)** — Valid incremental fix; FR-012 is still needed for protocol hardening regardless. Does not eliminate the structural mismatch.
4. **WebSocket adapter over SSE** — Replaces SSE with WS on the Custom LLM API side; EL still enforces a session timeout. Same root cause.
5. **Keep EL-as-LLM for Ninchat permanently** — Viable if barge-in assessment shows coordinator model is worse for elderly callers. Two-fold SSE path would then be documented as permanent load-bearing infrastructure in `docs/adr/elevenlabs-ninchat-adapter.md`.

## Implementation Approach

### Phase 0 — Decision gate (~1 day)
- Barge-in gap analysis: run OC-006 research; benchmark EL realtime STT in Finnish
- Produce short decision memo: go/no-go with explicit VAD threshold or mitigation

### Phase 1 — Prototype (1 day, if go)
- Create `questionnaires/ninchat-voice-coordinator/` with `graph.yaml`
- Run on outcaller stack locally with Twilio dev tunnel
- Validate Ninchat round-trip as an unblocked graph step

### Phase 2 — Port voice WebSocket module (1 day)
- Create `src/api/routes/voice_ws.py` with ported functions from outcaller
- Implement `await_call()` awaiting first Twilio `connected` frame
- Implement `speak_greeting(state)` and `speak_answer(state)` as separate functions (no `inputs:` stanza)
- Implement `listen_and_transcribe()` returning plain `str`
- Add `ffmpeg` to `Dockerfile`
- Register `/voice` WebSocket endpoint in FastAPI app

### Phase 3 — Delete slow path (0.5 day)
- Remove `_sse_slow_path.py`, `ninchat_result.py`
- Remove `_in_flight` infrastructure from `streaming.py`
- Verify all non-Ninchat graphs pass existing tests

### Phase 4 — Test & document (1 day)
- Add REQ-YG-091 to `ARCHITECTURE.md`: "Python tool nodes compose into a coordinator graph that implements call-session looping via conditional edges (`state_key == true and other_key != value`); no LLM router node required for loop control"
- Extend `ALL_REQS` in `scripts/req_coverage.py` to include `91`
- Write unit test tagged `@pytest.mark.req("REQ-YG-091")` for coordinator loop with mocked Ninchat and EL
- Update `docs/adr/graph-ninchat-integration.md` including MemorySaver-only constraint
- Update CHANGELOG.md

### Phase 5 — Real call validation (0.5 day)
- Live call comparison: EL agent vs. coordinator
- Sign off on TTFA, barge-in quality, missed turn boundary rate

## Phased path and dependencies

| Phase | Action | Dependency |
|-------|--------|-----------|
| **Done** | FR-011 + FR-013 in production | — |
| **FR-012** | Protocol hardening: silent Ninchat error, keepalive | Independent; proceed regardless |
| **FR-007** | `x-graph` header — graph selection without `model` hack | Independent; proceed regardless |
| **OC-006** | Barge-in gap analysis + EL STT Finnish benchmark | **Decision gate for FR-101** |
| **FR-101 Phase 1–5** | Graph-as-coordinator prototype → implementation | OC-006 go decision |

## Related / in questionnaire-api

- `src/questionnaire/handlers/ninchat_inquiry.py` — reused unchanged
- `questionnaires/ninchat-inquiry-rewrite/prompts/ninchat_mediator.yaml` — reused unchanged
- `../yamlgraph/projects/outcaller/graphs/incaller.yaml` — coordinator pattern reference
- `../yamlgraph/projects/outcaller/nodes/tts.py`, `stt.py`, `twilio_inbound.py` — port sources
- `../yamlgraph/projects/outcaller/server_base.py` — WebSocket server port source
- `docs/adr/elevenlabs-ninchat-adapter.md` — ADR for current two-fold SSE architecture
- `docs/adr/graph-ninchat-integration.md` — ADR to update
- FR-007: `x-graph` header for graph selection
- FR-011: Two-fold SSE response (the workaround this FR eliminates)
- FR-012: Ninchat protocol hardening (independent; proceed regardless)
- FR-013: SSE workaround improvements
- OC-001: TTFA 250 ms benchmark
- OC-002: STT pipeline design
- OC-006: Barge-in gap analysis (decision gate)