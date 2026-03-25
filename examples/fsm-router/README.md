# FSM Router Example

> **Optional Integration Example** - This demonstrates YAMLGraph integration with an external framework.

Demonstrates running YAMLGraph pipelines as statemachine-engine actions.

**Compatibility:** statemachine-engine >= 1.0.70

## Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                      statemachine-engine FSM                          │
│                                                                       │
│                         ┌──► simple_response ──┐                      │
│                         │         (simple)     │                      │
│   waiting ──► classifying ──┬─────────────────►├──► waiting           │
│       ▲                     │                  │       │              │
│       │                     └──► complex_response ─────┘              │
│       │                          (complex|code)                       │
│       │                                                               │
│       │              ┌──► error ───────────────────────┘              │
│       │              │    (failed)                                    │
│       │              │                                                │
│       └──────────────┴────────────────► completed (stop from any)     │
│                                                                       │
│   classifying runs YAMLGraph classifier.yaml:                         │
│   ┌─────────────────────────────────────────────────────────────┐     │
│   │   LLM classifies query → returns route: simple|complex|code │     │
│   │   (code queries reuse complex_response for deep analysis)   │     │
│   └─────────────────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────────────────┘
```

## Key Concept

The FSM orchestrates the workflow. YAMLGraph handles the LLM processing.

1. **FSM** receives a `new_query` event → enters `classifying` state
2. **YAMLGraph** classifier runs → LLM decides route (simple/complex/code)
3. **FSM** transitions to appropriate response state based on route
4. **YAMLGraph** responder generates final response
5. **FSM** returns to `waiting` state

## Files

```
fsm-router/
├── config/
│   └── router.yaml           # FSM state machine config
├── actions/
│   └── yamlgraph_async_action.py  # Fire-and-forget action that runs YAMLGraph
├── graphs/
│   ├── classifier.yaml       # Query classification pipeline
│   ├── simple-responder.yaml # Fast response pipeline
│   ├── complex-responder.yaml# Deep analysis pipeline
│   └── prompts/
│       ├── classify.yaml
│       ├── simple-response.yaml
│       ├── complex-analysis.yaml
│       └── complex-response.yaml
├── docs/
│   └── fsm-diagrams/         # Generated Mermaid diagrams for UI
├── tests/
│   └── test_yamlgraph_async_action.py
├── run.sh                    # One-command startup script
└── README.md
```

## Installation

```bash
# From yamlgraph root
pip install -e ".[fsm]"

# Or install statemachine-engine separately
pip install statemachine-engine
```

## Running

### Quick Start

```bash
cd examples/fsm-router
./run.sh
```

The `run.sh` script handles everything:
- Loads `.env` from project root for API keys
- Activates the virtual environment if present
- Generates Mermaid diagrams for the UI
- Starts the Web UI on http://localhost:3001
- Starts the FSM state machine
- Cleans up all processes on Ctrl+C

### Manual Start (Alternative)

If you prefer to start components separately:

```bash
cd examples/fsm-router

# Generate diagrams for the UI
statemachine-diagrams config/router.yaml --output-dir docs/fsm-diagrams

# Terminal 1: Start the Web UI (includes WebSocket server)
statemachine-ui --port 3001 --project-root .

# Terminal 2: Start the FSM (with env vars for API keys)
source ../../.env  # Ensure MISTRAL_API_KEY is set
statemachine config/router.yaml \
  --machine-name query_router \
  --actions-dir ./actions
```

Open http://localhost:3001 to see the state machine diagram and real-time transitions.

### Start the FSM (Manual)

```bash
cd examples/fsm-router

# Make sure API keys are in environment
export MISTRAL_API_KEY="your-key"

# Start the state machine with custom actions
statemachine config/router.yaml \
  --machine-name query_router \
  --actions-dir ./actions
```

### Send a Query

In another terminal:

```bash
# Simple query → routes to simple_response
statemachine-db send-event \
  --target query_router \
  --type new_query \
  --payload '{"query": "Hello!"}'

# Complex query → routes to complex_response
statemachine-db send-event \
  --target query_router \
  --type new_query \
  --payload '{"query": "Explain the trade-offs between microservices and monoliths"}'

# Code query → routes to complex_response
statemachine-db send-event \
  --target query_router \
  --type new_query \
  --payload '{"query": "How do I implement a binary search tree in Python?"}'
```

### Interrupt/Resume Configuration

The async action also supports checkpoint-backed multi-turn graphs. To use it:

- configure the YAMLGraph with a checkpointer,
- pass a stable `thread_id` from the FSM context,
- map `continue` for paused-again turns and `done` for completed turns.

```yaml
actions:
  ask_question:
    - type: yamlgraph_async
      params:
        graph: graphs/questionnaire.yaml
        input_key: user_input
        output_key: assistant_response
        event_key: route
        thread_id: "{session_id}"
        event_map:
          continue: on_follow_up
          done: on_complete
          goodbye: on_goodbye
        success: on_follow_up
        failure: failed
```

Behavior with this configuration:

1. First turn starts the graph with `{user_input: ...}` plus `{"configurable": {"thread_id": ...}}`.
2. If the graph is paused at an interrupt, the next FSM turn resumes with `Command(resume=user_input)`.
3. If the graph pauses again, the action emits `continue`.
4. If the graph finishes and `event_map.done` is configured, the action emits `done`.
5. If no interrupt path is active, the existing `event_map` / `_route` / `success` behavior stays unchanged.

The `thread_id` must stay stable across turns for the same conversation, and the graph itself must be compiled with checkpointing enabled for resume to work.

### Stop the FSM

```bash
statemachine-db send-event \
  --target query_router \
  --type stop
```

## How It Works

### 1. YamlgraphAsyncAction

See [actions/yamlgraph_async_action.py](actions/yamlgraph_async_action.py) - a fire-and-forget statemachine-engine action that:
- Launches a YAMLGraph pipeline as a background asyncio task
- Returns `None` immediately so the engine event loop stays responsive
- Dispatches the result event via the engine's control socket when complete
- Returns the `_route` field or `event_map` match as the FSM transition event
- Resumes interrupted graphs with `Command(resume=...)` when `thread_id` points to a paused checkpoint

### 2. Router Integration

| File | Purpose |
|------|--------|
| [graphs/classifier.yaml](graphs/classifier.yaml) | LLM node references prompt, stores result in `classification` |
| [graphs/prompts/classify.yaml](graphs/prompts/classify.yaml) | Defines `output_schema` with `route` enum: `simple`, `complex`, `code` |

The action reads `classification.route` and returns it as the FSM event.

### 3. FSM Transitions

See [config/router.yaml](config/router.yaml) for full transition definitions:

| Event | From | To | Notes |
|-------|------|----|---------|
| `simple` | classifying | simple_response | Fast path |
| `complex` | classifying | complex_response | Deep analysis |
| `code` | classifying | complex_response | Reuses complex path |
| `failed` | classifying | error | Error recovery |

## Testing

```bash
cd examples/fsm-router
pytest tests/ -v --no-cov
```

## Why This Pattern?

| Benefit | Description |
|---------|-------------|
| **Separation of concerns** | FSM handles orchestration, YAMLGraph handles LLM |
| **Job queue** | FSM provides SQLite persistence, retries |
| **Multi-machine** | FSM can coordinate multiple workers |
| **Audit trail** | FSM logs all state transitions |
| **LLM flexibility** | YAMLGraph provides multi-provider LLM support |

## When to Use

✅ **Use this when you need:**
- Persistent job queues
- Multi-machine coordination
- Audit trails
- Long-running workflows with LLM steps

❌ **Don't use when:**
- Simple request → LLM → response (just use YAMLGraph alone)
- Already have Celery/Airflow/Temporal

## Use Cases

### High Value (Clear FSM+LLM Fit)

| Use Case | FSM Provides | YAMLGraph Provides |
|----------|--------------|-------------------|
| **Support Ticket Triage** | Queue, SLA timers, escalation paths, audit trail | Intent classification, priority detection, auto-response |
| **Document Processing** | Job queue, retry on failure, approval workflow | OCR cleanup, entity extraction, summarization |
| **Multi-Step Approval** | State persistence, human gates, timeout handling | Draft generation, compliance check, summaries |
| **Chatbot with Handoff** | Session state, agent routing, escalation | Intent detection, response generation, sentiment |
| **Code Review Automation** | PR queue, reviewer assignment, merge gates | Code analysis, security scanning, review comments |

### Integration Patterns

| Pattern | Description |
|---------|-------------|
| **LLM-as-Router** | FSM transitions driven by LLM classification (this example) |
| **Human-in-Loop** | FSM manages approval gates, YAMLGraph prepares content |
| **Multi-Agent** | FSM coordinates multiple YAMLGraph agents |
| **Retry with Refinement** | FSM retries failed calls, YAMLGraph self-corrects |

## See Also

- [statemachine-engine docs](https://github.com/sheikkinen/statemachine-engine)
- [YAMLGraph examples](../README.md)
- [FSM + YAMLGraph brainstorming](../../docs-planning/brainstorming-fsm-yamlgraph.md)

## State Groups (for Kanban View)

The FSM config ([config/router.yaml](config/router.yaml)) uses state group comments (`# === GROUP ===`) for the UI's Kanban view. Run `statemachine-diagrams` to generate Mermaid diagrams.
