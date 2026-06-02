# Diary: The Self-Driving Car That Can't See

**Date:** 2026-05-31
**Context:** Evaluating three "next-level abstraction" proposals — Goal-Oriented Action Planning (HTN), Actor Model (Multi-Agent Swarms), Blackboard Architecture — as successors to DAGs and FSMs.
**Trap:** `framework_costume` + `growth_as_default`

## The Proposal

The argument: DAGs abstract data flow, FSMs abstract time flow, but both are "deterministic routing models" where the developer wires the boxes. The next level abstracts away the wiring itself. Three candidates: goal planners (declare intent, not process), actors (choreography, not orchestration), blackboards (data-triggered, not edge-triggered).

The metaphor: yamlgraph is a train track, statemachine-engine is the timetable, and the next framework is the self-driving car.

## The Inventory

Before evaluating the proposals, what does the codebase already contain?

| Primitive | What it does | Autonomy level |
|-----------|-------------|----------------|
| `type: agent` node | LLM decides which tools to call in a loop (`max_iterations: 10`) | **Tool selection is autonomous** |
| `type: router` node | LLM decides which edge to follow | **Routing is autonomous** |
| Reflexion loop | Draft → critique → refine until `score >= 0.8`, with loop limits | **Self-correction is autonomous** |
| Verification gate | LLM output verified, retry on failure (FR-164) | **Quality gate is autonomous** |
| Guard nodes | Deterministic pre/post-conditions on node execution | **Safety constraints are autonomous** |
| A2A server | Graph exposed as an A2A agent, callable by other agents | **Inter-agent communication exists** |
| A2A call node | Graph invokes external A2A agents | **Agent-to-agent is bidirectional** |
| Race node | Multiple providers execute in parallel, first wins | **Provider selection is autonomous** |
| FSM conductor | FSM dispatches graphs as actions, receives events back | **Lifecycle orchestration is autonomous** |

The system already has autonomous tool selection, autonomous routing, autonomous self-correction, autonomous inter-agent messaging, and autonomous lifecycle management. The wiring that remains is the *graph topology* — which nodes exist and their edges.

## Evaluating Each Proposal

### 1. Goal-Oriented Action Planning (HTN)

**Claim:** "Declare the goal, system builds the DAG at runtime."

**Reality check:** This is what `type: agent` already does at node level — the LLM decides which tools to call and in what order. The proposal wants this at *graph* level — the LLM decides which *nodes* to compose.

**The problem:** Who verifies the generated graph? YAMLGraph has a linter, a schema validator, loop limit enforcement, requirement traceability. A dynamically generated graph bypasses all of these. The Chaplain pipeline (Plan → Judge → Enforce → Inquisitor) exists precisely because graph authoring needs adversarial review. An HTN planner that generates graphs at runtime is an Enforce step with no Judge.

**The deeper problem:** Goal decomposition requires world knowledge that the LLM already has — it's called "reasoning." The graph is not the bottleneck; the *constraint specification* is. Moving from `edges:` to `goals:` doesn't eliminate the developer's work — it moves it from "what's the process?" to "what are the constraints?" The constraints are harder to specify than the process, because they're invisible until violated.

**Verdict:** The agent node is the right-sized version of this idea. Node-level autonomy (tool selection) works because the blast radius is one node. Graph-level autonomy (topology generation) fails because the blast radius is the entire pipeline, and there's no gate between generation and execution.

### 2. Actor Model (Multi-Agent Swarms)

**Claim:** "Decentralize control — autonomous actors with inboxes, self-organizing."

**Reality check:** The A2A server + A2A call node already implement agent-to-agent messaging. The FSM conductor already dispatches multiple graphs as independent actions. The missing piece is not the *mechanism* but the *coordination protocol*.

**The problem:** "Dancers responding to each other" sounds elegant until you need to debug why the system spent €47 on a loop of two agents politely asking each other to clarify. Choreography without observability is chaos. Orchestration (FSM conductor) exists because someone needs to own the timeout, the retry budget, and the cost ceiling.

**The deeper problem:** The proposal claims "a central FSM becomes too massive to maintain" at scale. But the FSM config for the Chaplain watcher pipeline — the most complex real system — is ~200 lines of YAML. The complexity is not in the FSM; it's in the *actions* (the graphs). Adding actors doesn't reduce that complexity; it distributes it across inboxes where it's harder to trace.

**The statemachine-engine already has:** named states with guard keys, event-driven transitions from any state (`from: "*"`), timeout-as-event, SQLite-backed persistence, WebSocket monitoring. What it doesn't have is *discovery* (agents finding each other dynamically). But discovery is an infrastructure concern (service registry), not a framework concern.

**Verdict:** The FSM+Graph+A2A stack is already an actor system in practice — the FSM is the supervisor actor, graphs are worker actors, A2A is the message protocol. The missing piece is observability (FR-467), not architecture.

### 3. Blackboard Architecture

**Claim:** "Shared memory space, agents wake up when data they understand appears."

**Reality check:** This is event-driven architecture — and the FSM's `event_map` + `context_map` already does this. When a graph completes, it posts an event; the FSM's transition table decides which state (and therefore which next action) fires. Adding a new "agent" means adding a state and a transition — one line of YAML.

**The problem:** "No edges, no transitions, no predefined graph — agents react to data" is the Pub/Sub pattern. It has a 40-year track record. The reason enterprise systems moved *away* from pure pub/sub toward explicit orchestration (Temporal, Prefect, Airflow) is debuggability. When the Fraud_Detection_Agent doesn't wake up, is it because the data shape changed, the subscription filter is wrong, the agent crashed, or the data was consumed by another subscriber first? In a graph, you trace the edge. In a blackboard, you grep logs.

**The deeper problem:** The proposal assumes adding a new agent should require zero changes to existing config. But the *reason* you'd add a Fraud_Detection_Agent is that fraud detection is a new *business requirement*. That requirement needs a test, a capability (CAP), a req (REQ-YG-XXX), and traceability. Adding it without touching existing config means adding it without updating the system's claim of what it does — which violates requirement traceability (ADR-001).

**Verdict:** The FSM transition table is a blackboard with explicit subscriptions. It's less magical and more debuggable. The proposal's appeal is *zero-config extensibility*, but that's a trap — extensibility without traceability is technical debt with a delayed fuse.

## The Metaphor Problem

"Train track → self-driving car" is seductive but misleading. A self-driving car needs:

1. **Perception** — what's the current state of the world? (The FSM has this: named states + context)
2. **Planning** — what sequence of actions reaches the goal? (The agent node has this: tool-call loop)
3. **Control** — execute the plan with feedback correction (The reflexion loop has this: critique → refine)
4. **Safety** — don't crash (Guards, verification gates, loop limits)

The pieces exist. What doesn't exist — and what the proposals don't address — is **perception**. The self-driving car can't see. It doesn't know what tools are available in the environment, what their current state is, or what other agents are doing. The A2A agent card is a step toward this (it advertises capabilities), but there's no runtime discovery or capability negotiation.

## The Real Gap

The proposals diagnose the wrong constraint. The bottleneck is not "wiring the graph" — the graph is 30-60 lines of YAML. The bottleneck is:

1. **Constraint specification** — knowing what the system should NOT do is harder than specifying what it should do
2. **Observability** — seeing what happened across FSM + Graph + A2A boundaries (FR-467)
3. **Discovery** — agents knowing what other agents can do at runtime (A2A agent cards are static)

None of these are solved by abstracting away the graph topology. They're solved by better tooling around the existing topology.

## Trap

`growth_as_default` — the assumption that the next commit should add something. The proposals add HTN planners, actor frameworks, blackboard engines. But the existing stack (FSM + Graph + A2A + guards + reflexion + verification gates) already has more autonomy than most systems know what to do with. The constraint is not "more autonomy" — it's "more visibility into the autonomy we already have."

Also `framework_costume` — goal planners, actor models, and blackboards are computational paradigms. Implementing them as YAML config creates a DSL for distributed systems. That's Temporal. That's Akka. That's already a multi-billion-dollar industry. The question isn't "can yamlgraph do this?" — it's "should yamlgraph become a distributed systems framework?" The answer from the three-layer architecture is no: the framework owns cognition (LLM reasoning), the FSM owns lifecycle, and infrastructure owns distribution.

## Heuristic

**Autonomy without observability is chaos.** Every proposal adds agent autonomy (self-wiring, self-organizing, self-triggering) without adding a corresponding observability mechanism. The ratio matters: for every degree of freedom you give an agent, you need a corresponding instrument to see what it chose and why. The existing stack has this ratio roughly balanced — agent nodes have iteration logging, routers have trace events, the FSM has WebSocket monitoring. Breaking the ratio by adding graph-level autonomy without graph-level observability creates systems that work in demos and fail in production.

## Seed

The three proposals are wrong about the *mechanism* but right about the *direction*. The next abstraction isn't removing the graph — it's making the graph **smaller**. Not "declare the goal and let the system build the graph" but "declare the goal and let the system select from a *library* of pre-validated graphs." That's the Chaplain pattern: a catalog of judged FRs (validated plans) that the enforcer selects from based on the current state. The graph isn't generated — it's *retrieved*. RAG for graphs, not RAG for documents. And that brings us full circle to the three-node pattern that already exists.
