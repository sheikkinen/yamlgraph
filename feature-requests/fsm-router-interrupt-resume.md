# Feature Request: FR-204 Interrupt Resume Support for the FSM Router Example

**Priority:** MEDIUM
**FR:** FR-204
**Type:** Enhancement
**Status:** In Progress
**Effort:** 1 day
**Requested:** 2026-03-25

## Summary

**Judge Verdict:** APPROVE


Bring the interrupt/resume behavior from the production FSM integration into
`examples/fsm-router/actions/yamlgraph_async_action.py` so the example can drive
checkpointed multi-turn graphs, while staying self-contained and simpler than
`projects/ninchat_voice`.

## Value Statement

FSM example authors get a working reference for interrupt-based YAMLGraph flows,
so they can build multi-turn routers without reverse-engineering production-only
code.

## Problem

The canonical example action in `examples/fsm-router` has drifted behind the
production implementation in
`projects/ninchat_voice/actions/real/yamlgraph_async_action.py`.

Today the example only supports fresh graph execution. It does not:

- accept a `thread_id` for checkpoint-backed continuity,
- inspect graph state to detect whether execution should resume,
- call `Command(resume=...)` for interrupted graphs,
- distinguish between a graph that paused at an interrupt and one that fully
  completed,
- expose `event_map.continue` and `event_map.done` routing for multi-turn FSM
  flows.

This makes the example unusable for the repository’s documented interrupt
pattern, which requires a checkpointer plus `thread_id` and resumes with
`Command(resume=...)` as described in `reference/interrupt-nodes.md` and
`ARCHITECTURE.md`.

## Proposed Solution

Update `examples/fsm-router/actions/yamlgraph_async_action.py` to mirror the
minimal interrupt logic already proven in the production action, without porting
ninchat-specific services.

The change is intentionally narrow:

1. Add `thread_id` parameter support in `YamlgraphAsyncAction.execute()`.
2. Pass `input_key` through to `_run_and_dispatch()`.
3. Build `run_config = {"configurable": {"thread_id": thread_id}}` when
   `thread_id` is set.
4. Before `run_graph_async()`, call `app.aget_state(run_config)` and, when
   `state.next` is present, resume with `Command(resume=user_input)` instead of
   starting from a fresh `initial_state`.
5. After `run_graph_async()`, call `app.aget_state(run_config)` again:
   - if `state.next` is present, dispatch
     `event_map.get("continue", success_event)`,
   - if `state.next` is empty and `event_map.done` exists, dispatch that event,
   - otherwise fall through to the current legacy event resolution path.
6. Preserve the example’s existing `_send_event()` socket helper and current
   fire-and-forget execution model.
7. Extend example tests and `examples/fsm-router/README.md` usage to cover interrupt-based configuration.

The example should follow the repository’s interrupt contract:

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

Behavior:

- first turn: graph runs with `initial_state` and checkpoint config,
- interrupted turn: action detects prior `state.next` and resumes with
  `Command(resume=user_input)`,
- paused-again turn: action emits `continue`,
- finished turn: action emits `done` when configured,
- legacy single-turn routing remains unchanged when no interrupt path is active.

## Scope Freeze

Implementation is limited to `examples/fsm-router/actions/yamlgraph_async_action.py`, `examples/fsm-router/tests/test_yamlgraph_async_action.py`, and `examples/fsm-router/README.md`. Do not port `projects/ninchat_voice` infrastructure or broaden the change beyond the example action's interrupt/resume behavior.

## Acceptance Criteria

- [x] `YamlgraphAsyncAction.execute()` accepts `params.thread_id` and passes it
      into `_run_and_dispatch()`.
- [x] `_run_and_dispatch()` accepts `input_key` and uses it to populate
      `Command(resume=...)` when resuming an interrupted graph.
- [x] When `thread_id` is set, the example builds
      `{"configurable": {"thread_id": thread_id}}` and passes it to both
      `app.aget_state()` and `run_graph_async()`.
- [x] If `app.aget_state(run_config)` reports `state.next` before execution, the
      action resumes with `Command(resume=user_input)` instead of a fresh state
      dict.
- [x] If `app.aget_state(run_config)` reports `state.next` after execution, the
      action dispatches `event_map.get("continue", success_event)` and includes
      the resolved `output_key` payload when available.
- [x] If `app.aget_state(run_config)` reports no pending `next` after execution
      and `event_map.done` exists, the action dispatches that event.
- [x] When no interrupt path is active, existing event behavior remains
      unchanged: `event_map` lookup, `_route` fallback, `success_event`
      fallback, failure dispatch, and guard cleanup still work.
- [x] The example keeps `_send_event()` and does not add
      `FsmEventSender`, `emit_ui_activity()`, `_llm_phase()`, or other
      ninchat-specific infrastructure.
- [x] Tests are added or updated in
      `examples/fsm-router/tests/test_yamlgraph_async_action.py` to cover:
      interrupt resume detection, `continue` dispatch, `done` dispatch, and the
      unchanged legacy path.
- [ ] `pytest examples/fsm-router/tests/ -v` passes.
- [x] `examples/fsm-router/README.md` includes an interrupt-based FSM example showing `thread_id`,
      checkpointer usage expectations, and `continue`/`done` event mapping.

## Alternatives Considered

### 1. Copy the production action verbatim

Rejected because it would pull ninchat-specific concerns into the example:
`FsmEventSender`, `emit_ui_activity()`, phase labeling, and voice-specific path
assumptions. The example should stay self-contained.

### 2. Document interrupts without changing the example

Rejected because the repository already documents interrupt nodes as a first
class pattern. Leaving the example non-functional for that pattern forces users
to infer missing glue from production code.

### 3. Add a brand-new action type for interrupt graphs

Rejected because the existing `yamlgraph_async` action already owns the async
FSM integration point. Interrupt support is a focused extension, not a separate
capability.

## Related

- `feature-requests/TEMPLATE.md`
- `examples/fsm-router/actions/yamlgraph_async_action.py`
- `examples/fsm-router/tests/test_yamlgraph_async_action.py`
- `projects/ninchat_voice/actions/real/yamlgraph_async_action.py`
- `reference/interrupt-nodes.md`
- `ARCHITECTURE.md`
