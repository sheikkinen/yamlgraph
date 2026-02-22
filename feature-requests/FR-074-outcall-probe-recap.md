# Feature Request: Outcall Probe-Recap (Phase 1 — ElevenLabs Path)

**Priority:** HIGH
**Type:** Feature
**Status:** Approved
**Effort:** ~1 day
**FR:** FR-074
**Requested:** 2026-02-22
**Judged:** 2026-02-22

---

## Judgement

**APPROVED.** Scope frozen. Authority granted to implement.

### Verification Summary

All codebase references verified against `questionnaire-api/`:

| Claim | Verified |
|-------|----------|
| `scripts/voice_call.py` exists with `calls.create()` | ✅ |
| `POST /v1/questionnaire` with `session_id` + `template` | ✅ |
| `YamlGraphInterviewSession.process_message()` signature | ✅ |
| `graph.yaml` nodes: `detect_gaps → generate_probe → append_probe_response` | ✅ |
| `probe.yaml` uses `gaps`, `schema`, `messages` | ✅ |
| `ConversationalTemplate.from_yaml()` + `required_fields` | ✅ |
| `passthrough` node type supported in yamlgraph | ✅ |
| `is_outcall != true` condition handles missing state (→ `None != True` → `True`) | ✅ |
| State `total=False` TypedDict allows optional `is_outcall`/`target_vars` | ✅ |
| `.env.example` has `ELEVENLABS_API_KEY`, missing `ELEVENLABS_AGENT_ID` | ✅ |

### Condition Routing Correctness

Critical path verified through yamlgraph internals:

- **Inbound call** (no `is_outcall` in state): `is_outcall != true` → `None != True` → `True` → routes to `generate_probe` ✅
- **Outcall** (`is_outcall=True` in state): `is_outcall == true` → `True == True` → `True` → routes to `generate_outcall_probe` ✅

### Observations (non-blocking)

1. **`extracted` variable declared but unused in prompt**: `generate_outcall_probe` node declares `extracted: "{state.extracted}"` but `outcall_probe.yaml` doesn't reference `{{ extracted }}`. Acceptable — available for prompt evolution at no cost.
2. **Orphaned sessions**: If ElevenLabs call fails after bootstrap, the Redis key persists until TTL (24h). Acceptable — no state corruption, natural cleanup.
3. **No new yamlgraph framework changes required**: All node types (`passthrough`, `llm`, `interrupt`), condition operators (`!=`, `==`), and state mechanics (`total=False` TypedDict) already exist

---

## Summary

Enable outbound calls initiated by `scripts/voice_call.py` to conduct a structured probe-recap interview. `voice_call.py` first creates a questionnaire session via `POST /v1/voice/outcall`, then initiates the call through the **ElevenLabs outbound call API**, passing the `session_id` as a `dynamic_variables` entry. ElevenLabs owns all audio (STT/TTS) and calls `POST /v1/questionnaire` as a webhook — identical to the proven inbound architecture.

**Out of scope (deferred to Phase 2):** in-process STT/TTS, `OutcallSession` factory, and `voice.py` `customParameters` extraction. Those are only needed if ElevenLabs is replaced with a direct WebSocket audio loop.

---

## Problem

The probe-recap flow exists as a fully working text-based API (`POST /v1/questionnaire`), but outbound calls initiated by `voice_call.py` have no path into a questionnaire session. Three concrete gaps:

1. **No session bootstrap**: at call initiation nobody creates a session with `template` and `target_vars`, so ElevenLabs has no context about what fields to collect.
2. **No outcall prompt**: `probe.yaml` assumes prior conversation context and probes *gaps*. An outbound cold-call needs to introduce itself and work through *explicit target variables* from the first utterance.
3. **CLI carries no parameters**: `voice_call.py` currently dials with bare Twilio `calls.create()` TwiML — no questionnaire template or field list is passed anywhere.

| Context | Probe framing |
|---------|--------------|
| Inbound (existing) | Caller introduced the case; LLM probes for *gaps* |
| Outbound (new) | System calls cold; LLM introduces itself and works through `target_vars` explicitly |

---

## Prerequisites

**ElevenLabs agent configured**: The ElevenLabs agent's webhook tool schema must include `session_id` in the `POST /v1/questionnaire` request body. The agent reads `session_id` from its `dynamic_variables` context and passes it to the webhook. Verify by inspecting the ElevenLabs dashboard before integration testing.

---

## Proposed Solution

### Call flow

```
voice_call.py
  │
  ├─ 1. POST /v1/voice/outcall  →  { session_id }
  │
  └─ 2. POST https://api.elevenlabs.io/v1/convai/twilio/outbound_call
            {
              "agent_id": "<ELEVENLABS_AGENT_ID>",
              "to_number": "+358...",
              "from_number": "<TWILIO_PHONE_NUMBER>",
              "dynamic_variables": {
                "session_id": "<session_id>"
              }
            }

ElevenLabs places the Twilio call.
When the callee answers, ElevenLabs connects its voice agent and
calls POST /v1/questionnaire with { session_id, query }
— template and outcall context are resolved from the pre-bootstrapped session.
```

`session_id` travels via `dynamic_variables`. The ElevenLabs agent is configured with a tool/function that reads `session_id` from its dynamic variable context and includes it in the `POST /v1/questionnaire` webhook body.

The existing `voice.py` WebSocket (`/voice/stream`) and `calls.create()` path are **untouched** by this FR.

---

### Issue 1 Resolution — Template lookup from bootstrapped session (Option A)

ElevenLabs passes only `session_id` via `dynamic_variables` — it cannot derive `template` from `session_id`. The `POST /v1/questionnaire` endpoint currently requires `template` in every request body (default: `"navigator"`).

**Resolution: Option A — session-lookup fallback.**

`POST /v1/voice/outcall` stores outcall session metadata in Redis:

```
Key:   outcall:{session_id}
Value: {"template": "interrai-ca", "target_vars": ["memory", "distress"], "to": "+358..."}
TTL:   86400 (24h, same as checkpointer)
```

`POST /v1/questionnaire` is extended: before using `payload.template`, check if `outcall:{payload.session_id}` exists in Redis. If found, override `template` with the stored value and inject `is_outcall=true` and `target_vars` into the initial graph state.

```python
# In questionnaire_assessment(), before _get_graph_app():
outcall_meta = await lookup_outcall_session(request, payload.session_id)
if outcall_meta:
    template = outcall_meta["template"]
    target_vars = outcall_meta["target_vars"]
    is_outcall = True
else:
    template = payload.template
    target_vars = []
    is_outcall = False

app = await _get_graph_app(template)
```

When creating the `YamlGraphInterviewSession`, inject outcall state:

```python
if is_outcall and not is_resume:
    input_state["is_outcall"] = True
    input_state["target_vars"] = target_vars
```

**Tradeoffs**: Adds a Redis lookup per request. Acceptable because:
- Redis lookup is sub-ms; LLM call is seconds.
- Only outcall sessions have the key; inbound sessions hit a cache miss and proceed unchanged.
- Template is stored authoritatively at bootstrap time — no risk of drift between CLI and webhook.

**Store/lookup helpers** (`src/api/outcall_session.py`):

```python
import json
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

OUTCALL_PREFIX = "outcall:"
OUTCALL_TTL = 86400  # 24h

async def store_outcall_session(
    request: Request, session_id: str, template: str,
    target_vars: list[str], to: str,
) -> None:
    redis = request.app.state.redis
    key = f"{OUTCALL_PREFIX}{session_id}"
    value = json.dumps({"template": template, "target_vars": target_vars, "to": to})
    await redis.set(key, value, ex=OUTCALL_TTL)

async def lookup_outcall_session(
    request: Request, session_id: str,
) -> dict | None:
    redis = request.app.state.redis
    key = f"{OUTCALL_PREFIX}{session_id}"
    raw = await redis.get(key)
    if raw is None:
        return None
    return json.loads(raw)
```

---

### Issue 2 Resolution — Graph routing with intermediate node

The `generate_probe` node currently connects to `append_probe_response`. To avoid executing the wrong prompt, an intermediate routing node splits the path:

```yaml
# New state field
state:
  is_outcall: bool
  target_vars: list

# New routing node (passthrough, no state changes)
route_probe:
  type: passthrough
  output: {}

# New outcall probe node
generate_outcall_probe:
  type: llm
  prompt: outcall_probe
  variables:
    schema: "{state.schema}"
    target_vars: "{state.target_vars}"
    messages: "{state.messages}"
    extracted: "{state.extracted}"
  state_key: response
```

**Edge topology** — replace the single `detect_gaps → generate_probe` edge:

```yaml
# Before (single path):
# - from: detect_gaps
#   to: generate_probe
#   condition: "has_gaps == true"

# After (two paths via router):
- from: detect_gaps
  to: route_probe
  condition: "has_gaps == true"
- from: detect_gaps
  to: set_recap_phase
  condition: "has_gaps == false"    # unchanged

- from: route_probe
  to: generate_probe
  condition: "is_outcall != true"   # inbound path
- from: route_probe
  to: generate_outcall_probe
  condition: "is_outcall == true"   # outcall path

- from: generate_probe
  to: append_probe_response         # unchanged
- from: generate_outcall_probe
  to: append_probe_response         # outcall rejoins same flow
```

`generate_outcall_probe` feeds into `append_probe_response` → `ask_probe` → the rest of the probing loop. The outcall-specific logic ends at probe generation; extraction, gap detection, recap, and scoring are shared.

---

### Issue 3 Resolution — `target_vars` default resolution

When `target_vars` is empty, the endpoint defaults to all `required: true` fields from the template schema:

```python
from questionnaire.config import QUESTIONNAIRES_DIR
from questionnaire.models.template import ConversationalTemplate

if not payload.target_vars:
    tmpl = ConversationalTemplate.from_yaml(
        QUESTIONNAIRES_DIR / payload.template / "schema.yaml"
    )
    target_vars = [f.id for f in tmpl.required_fields]
else:
    target_vars = payload.target_vars
```

This uses the existing `ConversationalTemplate.from_yaml()` loader and `required_fields` property (see `src/questionnaire/models/template.py`).

---

### Issue 4 Resolution — ElevenLabs agent configuration prerequisite

See **Prerequisites** section above. Additionally:

- The ElevenLabs agent's webhook tool schema must send `session_id` in the POST body.
- `template` is **not** passed by ElevenLabs — it is resolved via session lookup (Issue 1, Option A).
- Verification: inspect ElevenLabs dashboard agent tool definition before integration testing.
- Integration smoke test captures the webhook body to confirm `session_id` presence.

---

### 1. New `POST /v1/voice/outcall` endpoint

`voice_call.py` hits this endpoint **before** initiating the ElevenLabs call. It creates and stores the outcall session metadata, returning a `session_id`.

```python
# src/api/routes/voice.py  (new endpoint, same router as existing voice routes)

class OutcallRequest(BaseModel):
    template: str = "interrai-ca"
    target_vars: list[str] = Field(default_factory=list)
    to: str  # E.164 phone number; stored for audit log

class OutcallResponse(BaseModel):
    session_id: str

@router.post("/outcall", response_model=OutcallResponse)
async def create_outcall_session(
    request: Request,
    payload: OutcallRequest,
    _: str = Depends(verify_api_key),
) -> OutcallResponse:
    # Resolve target_vars default
    if not payload.target_vars:
        tmpl = ConversationalTemplate.from_yaml(
            QUESTIONNAIRES_DIR / payload.template / "schema.yaml"
        )
        target_vars = [f.id for f in tmpl.required_fields]
    else:
        target_vars = payload.target_vars

    session_id = str(uuid4())

    # Store outcall session metadata in Redis
    await store_outcall_session(
        request, session_id, payload.template, target_vars, payload.to,
    )

    logger.info(f"Outcall session {session_id} created: template={payload.template}, "
                f"target_vars={target_vars}, to={payload.to}")

    return OutcallResponse(session_id=session_id)
```

- `target_vars` empty → defaults to all `required: true` fields from the template schema.
- Outcall metadata is stored in Redis under `outcall:{session_id}` (see Issue 1 resolution).
- `to` is stored for audit logging; it is not used to look up the session at webhook time.
- No graph app is loaded or checkpointer session created — that happens lazily on the first `POST /v1/questionnaire` call from ElevenLabs.

---

### 2. CLI `outcall` command in `voice_call.py`

```python
@cli.command()
@click.option("--to", "-t", required=True, help="Phone number to call (E.164)")
@click.option("--template", default="interrai-ca", help="Questionnaire template")
@click.option("--target-vars", default="", help="Comma-separated field IDs to collect")
@click.option("--api-url", default="https://questionnaire-agent.fly.dev", help="Server base URL")
def outcall(to: str, template: str, target_vars: str, api_url: str):
    """Initiate an outbound probe-recap call via ElevenLabs."""
    # 1. Bootstrap session
    resp = requests.post(
        f"{api_url}/v1/voice/outcall",
        json={
            "template": template,
            "target_vars": target_vars.split(",") if target_vars else [],
            "to": to,
        },
        headers={"Authorization": f"Bearer {os.environ['API_KEY']}"},
    )
    resp.raise_for_status()
    session_id = resp.json()["session_id"]
    click.echo(f"Session: {session_id}")

    # 2. Initiate call via ElevenLabs outbound API
    el_resp = requests.post(
        "https://api.elevenlabs.io/v1/convai/twilio/outbound_call",
        json={
            "agent_id": os.environ["ELEVENLABS_AGENT_ID"],
            "to_number": to,
            "from_number": os.environ["TWILIO_PHONE_NUMBER"],
            "dynamic_variables": {"session_id": session_id},
        },
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
    )
    el_resp.raise_for_status()
    click.echo(f"Call initiated: {el_resp.json()}")
```

`target_vars` empty → `[]` → endpoint defaults to all required schema fields.

---

### 3. `outcall_probe.yaml` prompt

```yaml
# questionnaires/interrai-ca/prompts/outcall_probe.yaml
system: |
  Olet empaattinen terveydenhuollon ammattilainen, joka soittaa omaishoitajalle.
  Sinulla on lista kerättävistä tiedoista.

  Ohjeita:
  - Esittele itsesi ja soiton tarkoitus lyhyesti (vain ensimmäisellä kierroksella)
  - Kysy kohdemuuttujat luontevasti – ei kyselylomakemaisesti
  - Yhdistä samaan ryhmään kuuluvia aiheita
  - Ole lämmin ja kiinnostunut
  - Kysy ensin tärkeimmät (required) kentät

user: |
  {% if not messages %}
  Tämä on ensimmäinen puheenvuoro. Esittele itsesi ja soiton tarkoitus lyhyesti ennen kysymyksiä.
  {% endif %}

  Kerättävät tiedot (kohdemuuttujat):
  {% for field_id in target_vars %}{% for field in schema.fields %}{% if field.id == field_id %}
  - {{ field.label }}: {{ field.description }}{% if field.required %} (tärkeä){% endif %}
  {% endif %}{% endfor %}{% endfor %}

  {% if messages %}
  Viimeaikainen keskustelu:
  {% for msg in messages[-4:] %}
  {{ msg.role }}: {{ msg.content }}
  {% endfor %}
  {% endif %}

  Luo tiivis, empaattinen kysymys tai aloituspuheenvuoro joka kartoittaa kohdemuuttujia luontevasti.
  Vastaa vain puheenvuorolla.
```

Key differences from `probe.yaml`:
- Takes `target_vars` (explicit field IDs) instead of `gaps` (dynamically derived).
- Generates an introduction on the first turn (`not messages`); omits it on subsequent turns.
- Falls back gracefully when `messages` is empty (no `messages[-4:]` assumption).

---

### 4. `POST /v1/questionnaire` modification

Extend to resolve outcall session metadata before processing:

```python
# In questionnaire_assessment(), at the top of the try block:

# Check for outcall session metadata
outcall_meta = await lookup_outcall_session(request, payload.session_id)
if outcall_meta:
    template = outcall_meta["template"]
    logger.info(f"Outcall session detected: {payload.session_id}, "
                f"template={template}")
else:
    template = payload.template

app = await _get_graph_app(template)

# ... existing session resume logic ...

# When creating new session, inject outcall state:
if session is None:
    session = YamlGraphInterviewSession(
        app=app, thread_id=session_id, template_name=template,
    )

# In process_message for new sessions, pass outcall state:
if outcall_meta and not is_resume:
    result = await session.process_message(
        payload.query,
        skip_opening=payload.skip_opening,
        is_outcall=True,
        target_vars=outcall_meta["target_vars"],
    )
else:
    result = await session.process_message(
        payload.query, skip_opening=payload.skip_opening,
    )
```

`YamlGraphInterviewSession.process_message()` gains optional `is_outcall` and `target_vars` kwargs, injected into `input_state` for new sessions:

```python
async def process_message(
    self, message: str, skip_opening: bool = False,
    is_outcall: bool = False, target_vars: list[str] | None = None,
) -> InterviewResponse:
    # ... existing logic ...
    if not is_resume:
        input_state = {"user_message": message, "template_name": self._template_name}
        if skip_opening:
            input_state["skip_opening"] = True
        if is_outcall:
            input_state["is_outcall"] = True
            input_state["target_vars"] = target_vars or []
        result = await run_graph_async(self._app, input_state, config)
```

Once injected into graph state, `is_outcall` and `target_vars` persist through the checkpointer. Subsequent `POST /v1/questionnaire` calls (resumed sessions) use the checkpointed state — no repeated injection needed.

---

## Acceptance Criteria

### Endpoint & CLI
- [ ] `POST /v1/voice/outcall` creates a questionnaire session, stores metadata in Redis under `outcall:{session_id}`, and returns `{ "session_id": "..." }`
- [ ] `POST /v1/voice/outcall` with `target_vars=[]` and `template="interrai-ca"` stores `target_vars` matching the `required: true` field IDs from `questionnaires/interrai-ca/schema.yaml`
- [ ] `voice_call.py outcall` command accepts `--to`, `--template`, `--target-vars`, and `--api-url` options
- [ ] `voice_call.py outcall` calls `POST /v1/voice/outcall` then ElevenLabs outbound API in sequence

### Template resolution (Issue 1)
- [ ] `POST /v1/questionnaire` with a `session_id` that has outcall metadata in Redis uses the stored `template` instead of the request body default
- [ ] `POST /v1/questionnaire` with a `session_id` that has NO outcall metadata uses `payload.template` as before (no regression)

### Graph routing (Issue 2)
- [ ] `graph.yaml` state includes `is_outcall: bool` and `target_vars: list`
- [ ] `route_probe` passthrough node routes to `generate_outcall_probe` when `is_outcall == true` and `generate_probe` when `is_outcall != true`
- [ ] `generate_outcall_probe` connects to `append_probe_response` (rejoins inbound flow)

### Prompt (Issue 4 minor note)
- [ ] `outcall_probe.yaml` exists at `questionnaires/interrai-ca/prompts/outcall_probe.yaml`
- [ ] `outcall_probe.yaml` variable contract: accepts `target_vars: list[str]`, `schema`, `messages`, `extracted`; output shape identical to `probe.yaml` (single utterance string)
- [ ] Template rendering test (Jinja2 only, no LLM): first-turn render (empty `messages`) includes introduction phrasing
- [ ] Template rendering test (Jinja2 only, no LLM): subsequent-turn render (non-empty `messages`) omits introduction phrasing

### Outcall state injection
- [ ] `POST /v1/voice/outcall` sets `is_outcall: true` and `target_vars` in initial graph state (via outcall metadata → session process_message)
- [ ] `is_outcall` and `target_vars` persist through checkpointer on session resume

### No regression
- [ ] Inbound probe-recap flow is **unaffected** — no regression in existing `POST /v1/questionnaire` or `probe.yaml`
- [ ] Existing `voice.py` WebSocket (`/voice/stream`) is untouched

### Integration
- [ ] Integration test: `POST /v1/voice/outcall` with `template="interrai-ca"` and `target_vars=["memory", "distress"]` returns a valid `session_id`; a subsequent `POST /v1/questionnaire` with that `session_id` resolves template from outcall metadata and succeeds
- [ ] Integration smoke test confirms ElevenLabs agent tool definition passes `session_id` in the webhook body (inspect via ElevenLabs conversation logs or mock webhook capture)

### Documentation
- [ ] New environment variables documented in `.env.example`: `ELEVENLABS_AGENT_ID`, `ELEVENLABS_API_KEY`

---

## Alternatives Considered

**Issue 1 — Option B (pass `template` via `dynamic_variables`)**: ElevenLabs would receive `{"session_id": "...", "template": "interrai-ca"}` and pass both to the webhook. Rejected: doubles the ElevenLabs agent configuration surface; template might drift if CLI and webhook disagree; Redis lookup is sub-ms and authoritative.

**Mechanism 1 (call-metadata store keyed by CallSid)**: `voice_call.py` stores `template` + `target_vars` in a side-store; ElevenLabs webhook passes `CallSid`; `/v1/questionnaire` looks them up. Rejected: introduces a runtime lookup dependency on `CallSid` being available when ElevenLabs first connects, with no clear transaction boundary.

**Mechanism 2 (ElevenLabs conversation config injection only)**: Parameters injected into ElevenLabs prompt context at call initiation without creating a session object. Rejected: `/v1/questionnaire` would still need session bootstrapping on first message, coupling it to outcall detection logic.

**`{% if target_vars %}` branch in `probe.yaml`**: Rejected — entangles inbound/outbound concerns; harder to tune independently.

---

## Deferred to Phase 2

- **`voice.py` `customParameters` extraction**: not needed when ElevenLabs connects via `session_id` in `dynamic_variables` rather than reading parameters from the Twilio WebSocket `start` event.
- **`OutcallSession` factory and in-process STT/TTS loop**: only relevant if the WebSocket handles audio directly. ElevenLabs owns the audio pipeline on the Phase 1 path.

Phase 2 FR will be written if the ElevenLabs path is replaced with a direct WebSocket audio loop.

---

## Files Changed

| File | Change |
|------|--------|
| `src/api/routes/voice.py` | Add `POST /v1/voice/outcall` endpoint |
| `src/api/outcall_session.py` | New: Redis store/lookup helpers for outcall metadata |
| `src/api/routes/questionnaire.py` | Extend to resolve template from outcall metadata |
| `src/questionnaire/yamlgraph_session.py` | Add `is_outcall` and `target_vars` kwargs to `process_message()` |
| `questionnaires/interrai-ca/graph.yaml` | Add `is_outcall`, `target_vars` state; `route_probe` node; `generate_outcall_probe` node; updated edges |
| `questionnaires/interrai-ca/prompts/outcall_probe.yaml` | New: outcall-specific probe prompt |
| `scripts/voice_call.py` | Add `outcall` CLI command |
| `.env.example` | Add `ELEVENLABS_AGENT_ID`, `ELEVENLABS_API_KEY` |

---

## Related

- `scripts/voice_call.py` — outbound call CLI (extended with `outcall` command)
- `src/api/routes/voice.py` — voice router (new `POST /outcall` endpoint added here)
- `src/api/routes/questionnaire.py` — questionnaire endpoint (extended with outcall session lookup)
- `questionnaires/interrai-ca/prompts/probe.yaml` — existing inbound probe prompt (unchanged)
- `questionnaires/interrai-ca/prompts/recap.yaml` — recap prompt (unchanged)
- `docs/overall-architecture.md` — voice pipeline architecture
- ElevenLabs outbound call API: `POST https://api.elevenlabs.io/v1/convai/twilio/outbound_call`
