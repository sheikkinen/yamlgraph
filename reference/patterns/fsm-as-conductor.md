# FSM-as-Conductor Pattern

> statemachine-engine owns lifecycle; YAMLGraph owns cognition.

## The Pattern

An FSM orchestrates workflow states, guards, timeouts, and retries. YAMLGraph graphs handle LLM processing as fire-and-forget actions. The canonical bridge lives in `yamlgraph.utils.fsm` (`YamlgraphAsyncAction`) — it launches a graph as a background task and sends an AF_UNIX DGRAM event back when done.

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

`yamlgraph.utils.fsm` is the canonical bridge package. It:

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

1. **Interrupt path** — if graph paused at checkpoint, emit `event_map.continue`
2. **Completion phase map** — if graph finished and checkpoint state has `phase`, emit `event_map[phase]` when mapped
3. **Done fallback** — if graph finished and `event_map.done` is configured, emit it
4. **event_map** — match `event_key` field value against map keys
5. **_route / route** — use graph's built-in route field
6. **success** — fallback event

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
| **Chaplain** (automation) | 9+3 | 1–4 node graphs | subprocess¹ | minutes |

> ¹ The Chaplain's `yamlgraph_async_action` is a misnomer — it invokes `yamlgraph graph run` as a subprocess and `await`s completion, returning the event string directly. There is no `asyncio.create_task`, no guard key, and no socket dispatch. Event routing uses substring matching against stdout rather than structured state inspection. This works because the pipeline FSM's per-action timeouts (600–3600s) absorb the blocking call. The fsm-router and voicebot implementations are the true fire-and-forget variants.

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
  → micro_changelog → micro_title → sanity_check → validate_gate → done
                    ↘ (error) validate_fix ↗
```

- Graphs are multi-node pipelines (enforce-session: load map → plan context → assemble → enforce)
- Three-model separation: plan (gpt-5.3-codex), judge (claude-sonnet-4), enforce (gpt-5.3-codex)
- Validate loop with retry ceiling (max 5)
- Location: archived — `docs/archive/chaplain.md` (retired 2026-09)
- Context: `docs/archive/chaplain-system.md`

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

## Cross-Domain Clock Analysis

The pattern spans four orders of magnitude in clock speed across production deployments:

| System | FSM Clock | Typical Transition | External Events | Domain |
|--------|----------|-------------------|-----------------|--------|
| **Ninchat Voice** | ~100ms | Audio frame boundaries | incoming_call, hangup | Clinical telephony |
| **Game Engine** (proposed) | ~1s | Tick rate | player_action, timeout | Simulation |
| **Chaplain** | ~60s | CI operations | timeout, stop | CI/CD automation |
| **Kertomus** | ~120s | FHIR batch steps | new_job from DB queue | Medical data |

Same pattern, different clocks. The separation (lifecycle vs. reasoning vs. translation) is independent of the domain — just as MVC works for CLI tools and enterprise web apps because model/view/controller are independent of the application domain.

## Relationship to Established Patterns

| Pattern | Lifecycle | Step Execution | Durability | LLM-Aware |
|---------|----------|---------------|------------|-----------|
| **Saga** (microservices) | Orchestrator | Compensating transactions | Yes | No |
| **Actor Model** (Akka) | Mailbox | Actor message handler | Optional | No |
| **Temporal Workflow** | Workflow function | Activities | Yes (event sourcing) | No |
| **Prefect/Airflow** | DAG scheduler | Task functions | Yes (DB) | No |
| **FSM+Graph** | FSM config | YAMLGraph pipeline | Yes (SQLite queue) | **Yes** |

FSM+Graph is structurally closest to the **Saga pattern with non-deterministic steps**. The FSM is the saga orchestrator. Each graph is a saga step. The bridge handles compensation (error event → failure state → cleanup action). The key difference: saga steps are deterministic transactions with rollback; FSM+Graph steps are *non-deterministic LLM calls* with structured output validation. This makes the bridge harder — you can't simply "undo" an LLM call — but the lifecycle semantics (sequence, retry, timeout, compensate) are identical.

## See Also

- [examples/fsm-router/](../examples/fsm-router/) — Canonical example with README
- [docs/archive/chaplain-system.md](../docs/archive/chaplain-system.md) — Chaplain architecture (archived)
- [projects/ninchat_voice/docs/context/voice-projects.md](../projects/ninchat_voice/docs/context/voice-projects.md) — Voicebot architecture
- [Interrupt Nodes](interrupt-nodes.md) — YAMLGraph-native alternative for human-in-loop
- [Checkpointers](checkpointers.md) — State persistence for multi-turn graphs
