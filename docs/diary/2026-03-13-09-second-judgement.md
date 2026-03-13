# Diary: Second Judgement of 09 — Mechanical Simulation

**Date:** 2026-03-13
**Document:** `docs-planning/voicebot-analysis/09-full-scale-architecture.md`
**Action:** Judged revised architecture against FSM engine source code

## Cognitive Process

Three research passes: (1) engine internals (transition matching, action
execution, socket architecture), (2) ninchat_voice action patterns
(yamlgraph_async event_map, voice_speak guards, bridge dispatch), (3)
tick-by-tick mechanical simulation of turn loop and auth flow.

## Trap Avoided: Quick Confidence

The revision looked clean. Defects 2-7 were addressed structurally. The
temptation was to rubber-stamp it. Instead: "When I feel certain, let that
be the sign to Judge."

Mechanical simulation revealed the `process_event()` return-value trap —
any action returning a truthy string triggers an immediate state transition
mid-action-list. This is a subtle engine behavior that makes the built-in
`send_event` dangerous for multi-action states, validating the need for a
fire-and-forget variant.

## Trap Identified: Plausible Wrong Answer

The `send_event_to` proposal looked like unnecessary complexity given the
engine's built-in `send_event`. The plausible wrong answer was "just use
the built-in." The built-in's `return "event_sent"` behavior would silently
break multi-action states — a bug that only manifests when a transition
on `event_sent` exists (which none do currently, but which someone might
add later).

## Key Insight: The Engine's Main Loop is the Contract

The engine's loop order — `_check_control_socket` → `_execute_state_actions`
→ sleep — is THE critical invariant. Self-events via DGRAM arrive between
ticks. Context promotion via `_apply_context_map` happens before
`process_event()`. Guard cleanup happens per-action, not per-engine.
Understanding this loop is understanding the engine.

## Insight: J-1 Guard is Convention, Not Engine Feature

The engine has NO built-in guard mechanism. Every fire-and-forget action
implements its own guard manually (keyed on `_bridge_sent_{state}` or
`_graph_running_{state}`). A new `send_event_to` action MUST follow this
convention — it's not optional, it's not obvious, and it's not enforced
by the engine.

## Seed

Could the engine formalize the J-1 guard as a first-class concept? An
`on_entry: true` flag on actions that the engine enforces (run once per
state entry, not every tick) would eliminate an entire class of bugs.
