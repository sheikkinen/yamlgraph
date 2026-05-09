# Feature Request: FR-359 Pipecat FrameProcessor Integration

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved — authority granted 2026-05-09
**Effort:** 1–2 days (Phase 1 demo)
**Requested:** 2026-05-09

## Summary

Expose YAMLGraph graph execution as a pipecat `FrameProcessor`, enabling YAML-defined multi-step LLM reasoning inside pipecat voice/multimodal pipelines.

## Value Statement

Pipecat pipeline authors get structured multi-step LLM orchestration (routing, validation loops, Pydantic schemas) defined in YAML — without modifying pipeline code per business rule change — while pipecat handles transport, STT, TTS, and turn management. Graph logic changes are YAML-only; the `YAMLGraphProcessor` Python code stays frozen.

## Problem

Pipecat's LLM integration is single-turn: wire an `LLMService`, it receives context, returns text. Complex voice applications need multi-step reasoning *between* turns:

1. Classify intent (triage vs booking vs FAQ)
2. Route to appropriate sub-flow
3. Run structured questionnaire with validated answers
4. Generate summary, fact-check against responses
5. Produce typed JSON for downstream systems

Today, pipecat users implement this in Python — custom processors, manual state management, no schema validation. YAMLGraph already solves this with declarative YAML graphs, Pydantic schemas, and multi-provider LLM support.

## Proposed Solution

### `YAMLGraphProcessor(FrameProcessor)`

A pipecat processor that receives `TranscriptionFrame` (user speech), executes a YAMLGraph graph, and pushes `TTSSpeakFrame` (bot speech) plus a typed `YAMLGraphResultFrame` downstream.

```python
from pipecat.pipeline.pipeline import Pipeline

pipeline = Pipeline([
    transport.input(),
    stt,
    YAMLGraphProcessor(
        graph_path="graphs/triage.yaml",
        response_key="spoken_response",
        variables={"language": "fi"},
    ),
    tts,
    transport.output(),
])
```

### Frame Flow

```
TranscriptionFrame("I have chest pain")
        │
        ▼
YAMLGraphProcessor
  ├── 1. push TTSSpeakFrame("Kiitos, kirjaan tietoja.")  ← instant ack
  └── 2. asyncio.create_task(run_graph_async(...))       ← non-blocking
               │
               ▼  (2–5s later, background)
          graph complete
               │
          ├──► TTSSpeakFrame("Kuinka kauan oireet ovat kestäneet?")
          └──► YAMLGraphResultFrame(state={intent: "triage", severity: "high", ...})
```

### Custom Frame

```python
@dataclass
class YAMLGraphResultFrame(TextFrame):
    """Structured result from YAMLGraph execution.

    Carries the full graph state downstream so subsequent processors
    can read typed, Pydantic-validated fields — not just raw text.
    """
    graph_name: str = ""
    state: dict = field(default_factory=dict)
```

## Latency Design: The Ack Pattern

**Judgement Issue 2 resolved.** A YAMLGraph chain takes 2–10s. Silence of that length breaks voice UX. The solution is proven in production by ninchat_voice (NC-229).

### The pattern

```
TranscriptionFrame("I have chest pain")
        │
        ▼
YAMLGraphProcessor
  ├── 1. Push TTSSpeakFrame(ack_text)   ← instant, pre-baked phrase
  ├── 2. asyncio.create_task(run_graph) ← fire-and-forget, non-blocking
  │        │
  │        ▼  (2–5s later)
  │   graph result ready
  │        │
  └── 3. Push TTSSpeakFrame(result)     ← LLM response
       └──► YAMLGraphResultFrame(state) ← typed state
```

The processor never blocks the pipecat event loop. Step 1 happens in microseconds. Steps 2→3 happen in the background. Non-transcript frames continue to flow normally during graph execution.

### Ack phrase source

Pre-baked phrases stored as constants or optional audio file path — no TTS API call for the acknowledgment:

```python
YAMLGraphProcessor(
    graph_path="graphs/triage.yaml",
    ack_text="Kiitos, kirjaan tietoja.",   # spoken immediately on transcript receipt
    response_key="spoken_response",
)
```

### Stale result gating

The processor tracks a `task_generation` counter (same pattern as NC-205 in ninchat_voice). If a new `TranscriptionFrame` arrives while the graph is running, generation is bumped. The background task compares generation on completion — stale results are discarded without speaking.

```
Turn 1: TranscriptionFrame → gen=1, graph launches
Turn 2: TranscriptionFrame arrives during graph run → gen=2
Turn 1 graph completes: gen(1) ≠ current gen(2) → discard, don't speak
Turn 2 graph completes: gen(2) == current gen(2) → speak result
```

This prevents the classic double-answer problem in voice.

### Graph YAML (unchanged — standard YAMLGraph)

```yaml
# graphs/triage.yaml
metadata:
  provider: google

nodes:
  classify:
    type: llm
    prompt: classify_intent
    state_key: intent

  route:
    type: router
    field: intent.category
    routes:
      triage: ask_symptoms
      booking: check_calendar
      faq: answer_faq

  ask_symptoms:
    type: llm
    prompt: triage_questionnaire
    schema:
      name: TriageResult
      fields:
        severity: {type: str, description: "urgent/moderate/low"}
        symptoms: {type: list[str]}
        spoken_response: {type: str, description: "Next question to ask patient"}
    state_key: triage_result

edges:
  - [START, classify]
  - [classify, route]
  - [route, END]
  - [ask_symptoms, END]
```

## Delivery: Demo, Not Core Integration

**Decision (2026-05-09):** Do not add `yamlgraph/integrations/` or optional deps to the yamlgraph core package.

### Why optional deps were rejected

| Problem | Impact |
|---------|--------|
| Pipecat is a heavy framework (60+ services, audio, WebRTC) | Pulls in `daily-python`, `av`, `pyaudio`, GStreamer into any CI that installs `yamlgraph[pipecat]` |
| Version coupling | Any pipecat breaking change requires a yamlgraph release to fix |
| Wrong discovery direction | Pipecat users search pipecat's community integrations, not yamlgraph's optional extras |
| Import guards (`try: from pipecat import`) | This is the "shim/adapter" pattern the Scripture forbids |

### The correct model: inverse dependency

YAMLGraph's `run_graph_async()` API is stable. A pipecat user imports from yamlgraph; yamlgraph does not know pipecat exists. This is the same model as `langchain-anthropic` — integration packages own the coupling.

**Phase 1 (this FR):** Reference demo in `examples/demos/pipecat-voice/` — proves the pattern, copy-paste ready.

**Phase 2 (future FR if adoption justifies):** Separate `yamlgraph-pipecat` package, published independently, listed in pipecat's `COMMUNITY_INTEGRATIONS.md`.

```
examples/demos/pipecat-voice/
  processor.py          # YAMLGraphProcessor (~100 lines, copy-paste ready)
  pipeline.py           # wiring example with daily.co transport
  graphs/triage.yaml    # the YAMLGraph graph
  prompts/              # prompt yamls
  demo-output.log       # proof demo ran (required by demo-gate)
  README.md             # how to use it
```

No files added to `yamlgraph/` itself.

## Acceptance Criteria — Phase 1 (this FR)

- [ ] `YAMLGraphProcessor` in `examples/demos/pipecat-voice/processor.py`
- [ ] On `TranscriptionFrame`: push `ack_text` as `TTSSpeakFrame` immediately, then fire graph as background task
- [ ] On graph completion: push `TTSSpeakFrame(result[response_key])` + `YAMLGraphResultFrame(state)`
- [ ] Non-transcript frames pass through unmodified
- [ ] Stale result gating: `task_generation` counter; discard if new transcript arrived during graph run
- [ ] `YAMLGraphResultFrame` dataclass with `graph_name: str`, `state: dict`
- [ ] **Zero changes to `yamlgraph/` core or `pyproject.toml`**
- [ ] `demo-output.log` — captured stdout of mock-transport smoke test (text file, satisfies demo-gate)
- [ ] Tests with mock pipeline (no real audio/LLM) in `examples/demos/pipecat-voice/tests/`
- [ ] `reference/pipecat-integration.md` — pattern doc including ack pattern, stale gating, Phase 2 path

**Explicitly deferred to Phase 2:**
- Multi-turn state via checkpointer + `thread_id` (requires transport-specific metadata extraction)
- Interrupt/resume (`Command(resume=...)`) — depends on checkpointer being in place

## Scope Boundaries

**In scope (Phase 1):**
- Single processor: transcript in → ack speak → graph (async) → result speak
- Stale result gating via task_generation
- Custom result frame with typed state
- Mock-transport runnable smoke test

**Out of scope (future FRs):**
- Checkpointer + thread_id for multi-turn state (Phase 2)
- Interrupt/resume (`interrupt_before` + `Command(resume=...)`) (Phase 2)
- FSM coordinator equivalent in pipecat (NC-280 supervisor pattern)
- Streaming graph output as incremental TTS frames
- Pipecat Observer that writes graph execution to LangSmith
- `YAMLGraphServiceSwitcher` that swaps graphs mid-conversation

## Alternatives Considered

| Approach | Rejected because |
|----------|-----------------|
| `yamlgraph[pipecat]` optional dep | Version coupling, wrong discovery direction, import guards are shims the Scripture forbids |
| Pipecat function calling → YAMLGraph | Function calls are LLM-initiated, not pipeline-controlled; can't guarantee graph execution |
| Custom LLMService subclass | LLMService assumes single provider; YAMLGraph orchestrates multi-step across providers |
| Pipecat Flows library | Flows handles conversation structure but not multi-step LLM chains with schemas and routing |
| Plain Python processor | Works but defeats the purpose — every logic change requires code deployment |

## Related

- `yamlgraph/executor_async.py` — `run_graph_async()` API used by the processor
- `yamlgraph/graph_loader.py` — `load_graph_config()`, `compile_graph()`
- `projects/pipecat/` — local pipecat checkout for development
- `projects/ninchat_voice/` — production FSM + YAMLGraph voice system (validates the pattern)
- `projects/voice_runtime/` — current voice abstraction layer
- `reference/mcp-server.md` — precedent for YAMLGraph integration with external tool (CAP-19)
- `docs/diary/2026-05-09-nc281-event-bus-seed.md` — cross-reference reflection
