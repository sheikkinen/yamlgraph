# Diary: 09 Revision — Multi-FSM Architecture

**Date:** 2026-03-13
**Document:** `docs-planning/voicebot-analysis/09-full-scale-architecture.md`
**Action:** Revised all 7 structural defects from initial judgement

## Cognitive Process

The initial 09 blueprint was a clean top-down design: three FSMs, clean
separation of concerns, conditional transitions. The judgement revealed it
was a wish, not a fact — the FSM engine has no conditions, no cross-machine
dispatch, and the Conversation FSM added forwarding complexity without
proportional benefit.

## Trap: Framework Costume

The three-FSM model was an FSM wearing a microservice costume. The Conversation
FSM had no autonomous behavior — it was a relay station that received commands
from the Coordinator, ran graphs, and forwarded results back. Every graph
result needed a chain of intermediate forwarding states because the engine
can't branch on event payload.

**Cure: Working system inertia inverted.** Instead of defending the 3-FSM
design because "it's clean separation," I asked: does the Conversation FSM
earn its existence? The answer was no — its entire job could be absorbed by
the Coordinator with zero loss of separation, because graph execution is
already fire-and-forget via `yamlgraph_async`.

## Trap: Downstream Fix (Almost)

The initial instinct for Defect 2 (no conditions) was to add intermediate
states or separate events at each transition point — a 6-location fix. The
deeper fix was to push the branching logic INTO the YAMLGraphs (where it
belongs) using `event_map`. The intent-router graph classifies intent AND
checks auth need, then dispatches the right event. The FSM engine stays
dumb on purpose.

**The One Law applied:** Normalize at the boundary where external data enters
(the graph output → event_map), not downstream where it manifests (6
transitions needing conditions).

## Key Insight: 2-FSM > 3-FSM

The engine's proven pattern is monolithic: ninchat_voice uses a single 15-state
FSM. The new Call Orchestrator has 12 states — less than ninchat_voice! — and
handles more functionality (intent routing, auth gating, topic switching,
session save). The Telephony FSM stays separate because audio I/O is genuinely
different (bridge listener, TTS/STT, Twilio WebSocket) and its events
(`voice_speak`, `voice_listen`) are hardware-coupled.

The `send_event_to` action (~20 lines) bridges between the two FSMs using the
existing Unix DGRAM socket mechanism. No new infrastructure.

## New Pattern: Guard Reset via Intermediate States

The `heard` and `silence_forwarding` states in the Telephony FSM exist solely
to clear the J-1 guard key when returning to `listening`. The FSM engine clears
guards on entry to a *different* state, so self-loops don't restart actions.
Transitioning through an intermediate state (heard → forwarded → listening)
achieves guard reset as a side effect of the state change.

## Seed

If `send_event_to` proves reliable, could the FSM engine grow a native
cross-machine event bus? A `forward:` field on transitions that dispatches
events to other machines on transition — like a built-in relay. This would
eliminate explicit forwarding states entirely.
