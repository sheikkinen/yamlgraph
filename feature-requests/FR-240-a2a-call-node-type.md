# Feature Request: FR-240 A2A Call Node Type

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 3–5 days
**Requested:** 2026-04-19
**Capability:** CAP-96

---

## Summary

Add a new `a2a_call` node type that lets YAML graphs invoke external A2A agents — send messages, handle responses, and store results in graph state, all declared in YAML without writing Python.

## Value Statement

Graph authors can call external A2A agents from YAML graphs declaratively, enabling cross-framework multi-agent orchestration without custom Python integration code.

## Problem

YAMLGraph graphs can call LLMs (`type: llm`), local Python tools (`type: tool`/`type: python`), subgraphs (`type: subgraph`), and expose themselves as A2A agents (FR-208). But **there is no way to call external A2A agents from within a graph** — every external agent integration requires custom Python code in the side-effects layer.

As A2A adoption grows, specialized agents (research, code review, translation) become available as network services. YAMLGraph needs a declarative way to call them from YAML, completing the A2A story: FR-208 is the server side (expose graphs as A2A agents), FR-240 is the client side (call external A2A agents from graphs).

## Proposed Solution

### Node Configuration

```yaml
nodes:
  gather_research:
    type: a2a_call
    agent_url: "https://research-agent.example.com"
    message: "Find papers on {{ topic }}"
    state_key: research_results
    timeout: 120
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `agent_url` | `str` | Base URL of the A2A agent server |
| `message` | `str` | Jinja2 template for the message text, rendered with state variables |
| `state_key` | `str` | Where to store the result in graph state |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `timeout` | `int` | `120` | Request timeout in seconds |
| `on_error` | `str` | `"fail"` | Error strategy: `skip`, `fail`, `retry`, `fallback` |
| `max_retries` | `int` | `3` | Retry count when `on_error: retry` |
| `variables` | `dict` | `{}` | Extra variable templates resolved from state |

### Execution Flow

1. Render `message` template with state variables (Jinja2)
2. Send A2A `tasks/send` JSON-RPC request to `agent_url`
3. Wait for task completion (blocking, with timeout)
4. Extract text from response artifacts
5. Store result in `state_key`

### Error Handling

Follows existing `on_error` patterns (skip/fail/retry/fallback):
- Network errors, timeouts, and A2A protocol errors are handled
- Failed tasks raise `PipelineError` with node context

## Acceptance Criteria

- [x] **REQ-YG-239**: `type: a2a_call` node type sends Jinja2-templated message to external A2A agent URL via HTTP JSON-RPC, extracts text artifacts from response, stores in `state_key`; supports `timeout`, `on_error` (skip/fail/retry/fallback), `max_retries`, `variables`; `NodeType.A2A_CALL` in constants; registered in `NODE_TYPE_HANDLERS`; linter validates required fields (`agent_url`, `message`, `state_key`) via E901–E903; graph lint `check_a2a_call_patterns()`; does not require prompt field; uses a2a-sdk optional dependency
- [x] Unit tests for node factory, linter, and node compiler registration
- [x] Added to `VALID_NODE_TYPES` in linter checks
- [x] Capability file `CAP-96-a2a-call-node.yaml` created
- [x] REQ-YG-239 added to `ARCHITECTURE.md`

## Implementation Approach

### Phase 1: Core node type (this FR)

1. Add `A2A_CALL = "a2a_call"` to `NodeType` enum in `constants.py`
2. Create `yamlgraph/node_factory/a2a_nodes.py` with `create_a2a_call_node()`
3. Register in `node_compiler.py` `NODE_TYPE_HANDLERS`
4. Export from `node_factory/__init__.py`
5. Add to `VALID_NODE_TYPES` in linter
6. Create `yamlgraph/linter/patterns/a2a.py` with structural checks
7. Register in `linter/patterns/__init__.py` and `graph_linter.py`
8. Add `NodeConfig` fields for a2a_call nodes in `graph_schema.py`

### Out of Scope

- Agent Card discovery and caching (Phase 2)
- Streaming (`sendSubscribe`) (Phase 2)
- Multi-turn (`input_required` handling) (Phase 2)
- Authentication (bearer, OAuth) (Phase 2)
- Skill selection (Phase 2)
- Dynamic agent discovery (Phase 3)

## Design Decisions

### HTTP client, not SDK dependency for node

The `a2a_call` node uses `httpx` for HTTP requests with A2A JSON-RPC protocol, keeping it simple. The a2a-sdk is already an optional dependency (`yamlgraph[a2a]`) for the server side. The client node reuses it when available but falls back to raw HTTP for the JSON-RPC call.

### Blocking invocation only

Phase 1 is blocking only (`tasks/send` → poll until done). Streaming and async are deferred to Phase 2.

### Message template, not prompt file

Unlike `type: llm` nodes which reference prompt YAML files, `a2a_call` nodes use an inline `message` field with Jinja2 templating. External agents have their own prompts — we just send them a message.

## Related

- **FR-208**: A2A Server (expose graphs as A2A agents) — complementary
- **045b-a2a-consumer.md**: Original brainstorm for A2A consumer
- **CAP-91**: Race node type — similar pattern for adding new node type
- **FR-232**: Race node — recent node type addition, pattern to follow
