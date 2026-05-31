# Feature Request: Mission Control — Unified FSM + YAMLGraph Observability

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 5 days (phased: 0.5 + 1 + 1.5 + 2)
**Requested:** 2026-05-31

## Summary

Expose FSM context variables, YAMLGraph node outputs, and LangSmith trace URLs through the existing WebSocket monitor UI. Currently, the Kanban board shows machine position (state name) but not contents (context, LLM results, trace links). Three concentric data layers are invisible despite existing in memory.

## Value Statement

Operators debugging live FSM+YAMLGraph systems can drill from a Kanban card into the exact context variables, LLM decisions, and full trace — without switching tools or correlating timestamps manually.

## Problem

The statemachine-engine monitor UI and YAMLGraph's LangSmith tracing are completely disconnected. Four layers of opacity:

| Layer | What's invisible | Where data lives | Already serializable? |
|-------|-----------------|------------------|----------------------|
| FSM context | Guards, counters, accumulated results | `machine.context` dict | Yes (JSON via AF_UNIX) |
| YAMLGraph result | Structured LLM output stored in context | `context["yamlgraph_result"]` | Yes |
| LangSmith trace URL | Link to full prompt/response trace | `tracer.get_run_url()` | Yes (`get_trace_url()` exists) |
| LangSmith trace data | Token counts, latency, raw prompts | LangSmith API | Via API only |

The data exists at every layer. It is not forwarded.

```
Card position (state name)     ← visible
  └─ FSM context variables     ← data exists, not forwarded
      └─ YAMLGraph node outputs ← data exists, not captured
          └─ LangSmith traces   ← data exists, not linked
```

### Related Bug

The Kanban view itself has a bug: `voice_coordinator.yaml` has `template: true` under `metadata:` but `diagrams.py:generate_metadata()` reads `config.get("template", False)` (top level only). Additionally, no diagrams have been generated for `voice_coordinator`. See `docs/diary/diary-2026-05-31-kanban-template-flag-bug.md`.

## Proposed Solution

Four phases, each independently deployable:

### Phase 1: FSM Context in Events (0.5 days)

In statemachine-engine's `_emit_event()`, include `context` in `state_change` event payload. The WebSocket server already forwards arbitrary payloads — zero protocol changes.

In `app-modular.js`, make Kanban cards expandable on click to show a key-value table of context variables.

### Phase 2: Trace URL Propagation (1 day)

In `yamlgraph_async_action.py`, capture `get_trace_url(tracer)` after graph execution. Emit it in the result event payload:

```python
trace_url = get_trace_url(tracer)
result_event = {
    "result": result,
    "trace_url": trace_url,
    "run_id": str(tracer.latest_run.id) if tracer and hasattr(tracer, 'latest_run') else None,
}
```

The `trace_url` propagates into `context["yamlgraph_result"]` → Phase 1 makes it visible → clickable link in the card detail view.

### Phase 3: Trace Panel Module (1.5 days)

New `TracePanel.js` module (9th UI module) rendering a side panel when a Kanban card with `trace_url` is clicked:

- **Link mode** (default): Opens LangSmith in new tab
- **Embed mode** (optional): Uses public share URLs in iframe via `share_trace()`, or proxies through `server.cjs`

### Phase 4: Unified Timeline (2 days)

Merge FSM event timestamps with LangSmith trace spans into a timeline view:

```
14:32:01.003  [idle → warming_up]          incoming_call
14:32:01.150  [warming_up → speaking]      yamlgraph_preload (47ms)
14:32:05.891  [listening → classifying]     silence_timeout
14:32:06.102    └─ LLM: claude-3.5-sonnet
                   tokens: 847/123, latency: 1.2s
                   result: {"intent": "prescription", "confidence": 0.94}
```

Join key: `run_id` from Phase 2 correlates FSM events with LangSmith spans.

## Acceptance Criteria

### Phase 1
- [ ] `state_change` events include `context` in payload
- [ ] Kanban card click expands to show context key-value pairs
- [ ] Context updates in real-time on subsequent `state_change` events
- [ ] Large context values truncated with expand toggle

### Phase 2
- [ ] `yamlgraph_async_action` captures and emits `trace_url` and `run_id`
- [ ] `trace_url` visible in expanded Kanban card as clickable link
- [ ] Works when LangSmith tracing is disabled (graceful None)

### Phase 3
- [ ] `TracePanel.js` module renders side panel on card click
- [ ] Link mode opens LangSmith trace in new tab
- [ ] Panel closes on Escape or click-outside

### Phase 4
- [ ] Timeline view merges FSM events with LangSmith spans
- [ ] Events correlated by `run_id`, not timestamp
- [ ] Timeline scrolls to latest event, with scroll-lock toggle

## Cross-Repo Impact

| Repo | Files affected |
|------|---------------|
| statemachine-engine | `core/machine.py` (emit context), `ui/public/app-modular.js`, `ui/public/modules/KanbanView.js` |
| statemachine-engine | `ui/public/modules/TracePanel.js` (new, Phase 3) |
| yamlgraph | `projects/ninchat_voice/actions/real/yamlgraph_async_action.py` |
| yamlgraph | `projects/ninchat_voice/config/voice_coordinator.yaml` (template flag fix, prerequisite) |

## Alternatives Considered

1. **LangSmith-only**: Continue using LangSmith as the sole observability tool. Rejected: LangSmith has no concept of FSM states, guard variables, or machine lifecycle — it sees individual LLM calls without orchestration context.

2. **OpenTelemetry bridge**: Export FSM events as OTel spans and correlate in Jaeger/Tempo. More standard, but requires OTel infrastructure setup and loses the real-time WebSocket reactivity that makes the Kanban view useful.

3. **Log correlation**: Write both FSM events and trace URLs to structured logs, query with grep/jq. Works for post-hoc analysis but not for live monitoring.

## Related

- `docs/diary/diary-2026-05-31-kanban-template-flag-bug.md` — Kanban activation bug
- `reference/patterns/fsm-as-conductor.md` — FSM+Graph pattern documentation
- `yamlgraph/utils/tracing.py` — `get_trace_url()` implementation
- `statemachine-engine/src/statemachine_engine/ui/public/app-modular.js` — Monitor UI
- `statemachine-engine/src/statemachine_engine/monitoring/websocket_server.py` — Event relay
