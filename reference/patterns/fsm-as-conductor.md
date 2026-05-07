# FSM-as-Conductor Pattern

> statemachine-engine owns lifecycle; YAMLGraph owns cognition.

## The Pattern

An FSM orchestrates workflow states, guards, timeouts, and retries. YAMLGraph graphs handle LLM processing as fire-and-forget actions. The bridge between them is `yamlgraph_async_action` — it launches a graph as a background task and sends an AF_UNIX DGRAM event back when done.

```
┌──────────────────────────────────────────────┐
│            statemachine-engine               │
│                                              │
│   states ─── transitions ─── guards          │
│      │           │              │            │
│   timeouts    events        retries          │
│                  │                            │
│          "when" + "which"                    │
└──────────────────┬───────────────────────────┘
                   │
       yamlgraph_async_action
       (fire-and-forget bridge)
                   │
      ┌────────────┼────────────┐
      │            │            │
      ▼            ▼            ▼
 ┌─────────┐ ┌──────────┐ ┌──────────┐
 │ graph A │ │ graph B  │ │ graph C  │
 │  (LLM)  │ │  (LLM)  │ │  (LLM)  │
 └────┬────┘ └────┬─────┘ └────┬─────┘
      │           │            │
      └─────┬─────┘────────────┘
            │
 AF_UNIX DGRAM event → FSM
 (event_map / _route / success)
```

**The FSM never does cognitive work.** It sequences, guards, retries, and routes. **YAMLGraph never owns lifecycle.** It processes, returns, and lets the FSM decide what's next.

## Boundary Contract

Both sides normalize at the boundary where external data enters — the One Law applied twice:

```yaml
# FSM side: event payload → durable context key
events:
  incoming_call:
    context_map:
      call_sid: payload.call_sid

# YAMLGraph side: LLM output → state field
nodes:
  classify:
    state_key: classification
```

## The Bridge Action

`yamlgraph_async_action.py` is the canonical bridge. It:

1. Sets a guard key to prevent duplicate launches (FSM polls at 50ms)
2. Launches the graph via `asyncio.create_task`
3. Returns `None` immediately (FSM stays in current state)
4. On completion, sends an event back via AF_UNIX DGRAM socket
5. Clears the guard key

### YAML Configuration

```yaml
actions:
  classifying:
    - type: yamlgraph_async
      params:
        graph: graphs/classifier.yaml
        input_key: query              # context key → graph input
        output_key: classification    # graph output → context key
        event_key: classification     # field to match against event_map
        event_map:
          simple: simple              # graph output → FSM event
          complex: complex
          code: code
        success: simple               # fallback if no route matched
        failure: failed
```

### Event Resolution Order

1. **Interrupt path** — if graph paused at checkpoint, emit `event_map.continue`; if finished, emit `event_map.done`
2. **event_map** — match `event_key` field value against map keys
3. **_route / route** — use graph's built-in route field
4. **success** — fallback event

### Interrupt/Resume (Checkpoint-Backed)

For multi-turn graphs with checkpointing:

```yaml
actions:
  ask_question:
    - type: yamlgraph_async
      params:
        graph: graphs/questionnaire.yaml
        input_key: user_input
        output_key: assistant_response
        thread_id: "{session_id}"       # stable across turns
        event_map:
          continue: on_follow_up        # graph paused again
          done: on_complete             # graph finished
        success: on_follow_up
        failure: failed
```

First turn starts the graph. Subsequent turns resume with `Command(resume=user_input)` if the graph is paused at an interrupt.

## Three Production Instances

| System | FSM States | Graph Complexity | IPC | Latency |
|--------|-----------|------------------|-----|---------|
| **fsm-router** (example) | 5 | 1-node graphs | in-process task | seconds |
| **voicebot** (production) | 15+ | 1-node subgraphs | two-process DGRAM | milliseconds |
| **Chaplain** (automation) | 9+3 | 1–4 node graphs | subprocess + task | minutes |

### fsm-router — Query Routing

Canonical example. FSM classifies incoming queries and routes to simple/complex response paths.

```
waiting → classifying → simple_response → waiting
                      → complex_response → waiting
```

- Graphs: `classifier.yaml`, `simple-responder.yaml`, `complex-responder.yaml`
- Each graph is a single LLM call
- Location: `examples/fsm-router/`

### voicebot — Telephony Call Coordinator

Production inbound call system. FSM owns real-time call lifecycle (15 states, audio transport, turn-taking). YAMLGraph handles offline LLM tasks (intent classification, response rewriting).

```
idle → warming_up → connecting → speaking_greeting
  → listening → waiting_for_all_events → rewriting_response
  → speaking_response → listening (loop, max 20 turns)
  → speaking_goodbye → goodbye_wait → closing → cleanup → idle
```

- Two-process architecture: uvicorn (audio) + statemachine-engine (FSM)
- IPC: AF_UNIX DGRAM sockets (JSON envelopes)
- 5 coordinator modes: simple, bargein, questionnaire, triage, navigator
- Location: `projects/ninchat_voice/`
- Context: `projects/ninchat_voice/docs/context/voice-projects.md`

### Chaplain — Development Lifecycle Automation

Two FSMs: dispatcher (poll inbox) + pipeline worker (plan → judge → enforce → merge). YAMLGraph does all cognitive work — planning, judging, implementing, validating.

```
setup → plan → capture_fr → judge → enforce_session
  → validate_fix → sanity_check → validate_gate → done
```

- Graphs are multi-node pipelines (enforce-session: load map → plan context → assemble → enforce)
- Three-model separation: plan (gpt-5.3-codex), judge (claude-sonnet-4), enforce (gpt-5.3-codex)
- Validate loop with retry ceiling (max 5)
- Location: `.chaplain/`
- Context: `docs/context/chaplain-system.md`

## Scaling Dimensions

Complexity scales along two axes independently:

| Axis | What grows | Examples |
|------|-----------|----------|
| **Vertical** (FSM states) | More lifecycle states, guards, error paths | voicebot: 5 → 15 states as modes added |
| **Horizontal** (graph nodes) | More LLM steps per invocation | Chaplain enforce: 1 → 4 nodes with context planning |

The bridge contract stays identical regardless of scale.

## When to Use This Pattern

**Use FSM-as-conductor when:**
- Workflow has explicit states with different behaviors (not just sequential LLM calls)
- You need timeouts, retries, or guards that are hard to express in a DAG
- External events drive transitions (user input, webhooks, timers)
- Real-time constraints require non-blocking LLM calls

**Use plain YAMLGraph when:**
- Processing is a DAG without external event triggers
- No need for persistent state across turns (or checkpointing suffices)
- All nodes are LLM calls with no I/O-bound waits between them

## Relationship to `framework_costume` Trap

Scripture defines the trap: *"FSM wearing DAG costume → if <50% nodes use core features, wrong tool."* This pattern is the cure. Don't force either paradigm alone — use both at their natural boundary. The FSM doesn't wear a DAG costume; the DAG doesn't pretend to be an FSM. The bridge contract is the seam.

## Requirements

```bash
pip install statemachine-engine   # >= 1.0.70
pip install yamlgraph
```

## See Also

- [examples/fsm-router/](../examples/fsm-router/) — Canonical example with README
- [docs/context/chaplain-system.md](../docs/context/chaplain-system.md) — Chaplain architecture
- [projects/ninchat_voice/docs/context/voice-projects.md](../projects/ninchat_voice/docs/context/voice-projects.md) — Voicebot architecture
- [Interrupt Nodes](interrupt-nodes.md) — YAMLGraph-native alternative for human-in-loop
- [Checkpointers](checkpointers.md) — State persistence for multi-turn graphs
