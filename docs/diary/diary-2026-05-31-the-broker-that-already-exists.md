# Diary: The Broker That Already Exists

**Date:** 2026-05-31
**Context:** Strategic analysis session — evaluating a "Declarative Event Broker" proposal for connecting yamlgraph and statemachine-engine

## The Proposal

"A YAML-configured event router that listens for events emitted by a yamlgraph agent and automatically spins up a statemachine-engine worker, or vice versa — the central nervous system for multi-agent enterprise deployments."

## The Discovery

The proposal describes something that already exists. The FSM action config *is* the declarative event broker:

```yaml
actions:
  graph_processing:
    - type: yamlgraph_async
      params:
        event_map:
          continue: graph_continue
          done: graph_done
          crisis: crisis_detected
```

`event_map` is the routing table. `context_map` is the payload transformer. FSM transitions are the downstream dispatch. The "custom Python script" (`yamlgraph_async_action.py`) is the runtime, not the configuration — analogous to `StateGraph.compile()`. You don't rewrite the compiler for each graph.

The connectivity is already YAML-declared across six concerns: which graph to run, input mapping, output routing, payload extraction, event-to-state mapping, and state-to-action dispatch. All in the FSM config file.

## The Trap

`architecture_as_diagram` — drawing a box labeled "Event Broker" between two existing boxes makes the diagram look cleaner, but the implementation would duplicate what `event_map` + `context_map` + FSM transitions already do.

This is a variant of `framework_costume`: the proposal looks like a new system because it uses enterprise vocabulary ("event broker", "central nervous system", "multi-agent deployment"). Strip the vocabulary and the requirement is: "when graph A finishes, start process B with A's output." That's a state transition with a context map. It exists.

## What's Actually Missing

Not connectivity — **visibility**. The events flow, the results arrive, the state transitions happen. You just can't see them from a single pane. FR-467 (Mission Control) addresses this.

The one scenario where a separate broker would add value: **multi-FSM coordination across machines**. Today this uses SQLite job queue (`check_database_queue_action` → `start_fsm_action`) — already declarative, already decoupled, already durable. An external broker (Redis Streams, NATS) would add fan-out and cross-machine distribution, but that's infrastructure, not framework.

## Heuristic

**Before proposing connective tissue, inventory the existing joints.** The FSM config's `event_map` + `context_map` + transitions already form a declarative event router — it just doesn't call itself one. Naming a pattern doesn't create a need to reimplement it.

Corollary: when an architecture diagram has a box you can't point to in the codebase, check whether its function is already distributed across existing components before building it. The absence of a named component ≠ the absence of the capability.

## Seed

When does the distributed case (multi-FSM, multi-machine) actually arise? The current systems are single-machine with prefork workers sharing a SQLite queue. If the game engine initiative materializes, would it need cross-machine FSM coordination, or would each game instance be self-contained? The answer determines whether Redis/NATS infrastructure is a real need or a premature abstraction.
