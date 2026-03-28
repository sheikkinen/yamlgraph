# Feature Request: FR-208 A2A Protocol Server — Expose Graphs as A2A Agents

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 5–7 days
**Requested:** 2026-03-28
**Capability:** CAP-81

---

## Summary

Add an A2A (Agent-to-Agent) protocol server that exposes YAMLGraph graphs as A2A-compliant agents, supporting the task lifecycle (send, get status, stream updates, cancel). Follows the established MCP server pattern (CAP-19): discover graphs from directories, expose each as a named agent with an Agent Card.

## Value Statement

Graph authors can serve any YAML graph as an A2A agent with a single CLI command, making YAMLGraph agents interoperable with any A2A-compatible orchestrator, client, or multi-agent system — no Python glue code required.

## Problem

YAMLGraph graphs can be exposed via MCP (CAP-19), CLI, or FastAPI, but **not as A2A agents**. The A2A protocol (v0.3.25 stable, backed by Google, Red Hat, AWS, Datarobot) is the emerging standard for inter-agent communication. Currently:

1. **No A2A surface exists** — graphs cannot participate in multi-agent A2A systems.
2. **No Agent Card generation** — graph metadata (name, description, capabilities) is not exposed in A2A-discoverable format.
3. **No task lifecycle mapping** — LangGraph checkpointing and YAMLGraph's interrupt/resume model are not bridged to A2A's `task/send`, `task/get`, `task/cancel`, and SSE streaming.
4. **The gap is unique** — no framework currently offers "define behavior in YAML → expose as A2A agent." This is a differentiation opportunity.

The MCP server (CAP-19) proves the pattern works: `mcp_server.py` discovers graphs, exposes them as tools, and handles invocation — all without changes to graph YAML. The A2A server replicates this pattern for the A2A protocol.

## Proposed Solution

### 1. New module: `yamlgraph/a2a_server.py`

Mirror the `mcp_server.py` architecture:

```
┌────────────────────────────────────────┐
│  a2a_server.py                         │
│                                        │
│  discover_graphs()  ─── shared via ────│── yamlgraph/discovery.py
│  AgentCard gen      ─── from graph     │   metadata (name, desc, skills)
│  TaskHandler        ─── maps A2A task  │   lifecycle to graph invoke/stream
│  SSE streaming      ─── wraps          │   run_graph_streaming_native()
└────────────────────────────────────────┘
```

### 2. Prerequisite: Extract shared graph discovery

Extract `discover_graphs()` from `mcp_server.py` into `yamlgraph/discovery.py` as a **separate prerequisite step** before building the A2A server. This is a refactor of `mcp_server.py` (~50 lines) that must:

1. Create `yamlgraph/discovery.py` with the extracted function.
2. Update `mcp_server.py` to import from the new module.
3. Verify all existing MCP server tests still pass before proceeding.

Both MCP and A2A servers then import from the shared module.

### 3. Graph discovery → Agent Card

Each discovered graph becomes an A2A agent:

```python
AgentCard(
    name=graph_config.name,
    description=graph_config.description,
    url=f"http://localhost:{port}/",
    version="0.4.63",
    skills=[AgentSkill(
        id=graph_name,
        name=graph_config.name,
        description=graph_config.description,
        tags=["yamlgraph"],
    )],
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True, pushNotifications=False),
    authentication=None,  # Unauthenticated by default (see Known Limitations)
)
```

### 4. Message Parsing Strategy

A2A messages are freeform `TextPart` content. The server must convert text into graph input variables at the boundary. The strategy is:

**Parsing modes (configured per-graph or globally):**

| Mode | Trigger | Behavior | Example |
|------|---------|----------|---------|
| `key_value` (default) | Text contains `key=value` pairs | Parse `key=value` space-separated tokens via `shlex.split()` | `"name=World style=casual"` → `{"name": "World", "style": "casual"}` |
| `single_input` | Graph has exactly one required var | Entire text assigned to that single variable | `"Hello World"` → `{"input": "Hello World"}` |
| `json` | Text is valid JSON object | Parse as JSON dict | `'{"name": "World"}'` → `{"name": "World"}` |

**Resolution order:**
1. If text is valid JSON object → use `json` mode.
2. If text contains `=` characters → use `key_value` mode.
3. If graph has exactly one required variable → use `single_input` mode.
4. Otherwise → assign full text to `input` key.

**Validation:**
- Graphs that declare `required_vars` (via `state` keys) reject messages that don't provide all required variables, returning A2A error with `code: "missing_variables"` and listing the missing keys.
- Extra variables not in the graph's state are silently ignored (same behavior as CLI `--var`).

**Multi-part messages:**
- Multiple `TextPart` entries are concatenated with newlines before parsing.
- `DataPart` (binary data, future A2A spec) is out of scope for this FR; messages containing only `DataPart` return an error with `code: "unsupported_content_type"`.

### 5. Task lifecycle → Graph execution mapping

| A2A Method           | YAMLGraph Implementation                              |
|----------------------|-------------------------------------------------------|
| `task/send`          | `compile_graph()` → `app.ainvoke()` with thread_id    |
| `task/get`           | Checkpointer lookup by thread_id (task_id = thread_id)|
| `task/cancel`        | Cancel running asyncio task                            |
| `task/sendSubscribe` | `run_graph_streaming_native()` → SSE events           |

Task state mapping:

| A2A TaskState    | YAMLGraph State                                 |
|------------------|-------------------------------------------------|
| `submitted`      | Graph compiled, invoke called                   |
| `working`        | Graph executing (streaming tokens)              |
| `input-required` | `__interrupt__` key present in state            |
| `completed`      | Graph returned final state                      |
| `failed`         | Exception raised during execution               |
| `canceled`       | Asyncio task cancelled                          |

### 6. Error mapping

`PipelineError` objects map to A2A structured error responses:

| `PipelineError.type`    | A2A Error Code          | HTTP Status |
|-------------------------|-------------------------|-------------|
| `LLM_ERROR`             | `internal_error`        | 500         |
| `VALIDATION_ERROR`      | `invalid_input`         | 400         |
| `PROMPT_ERROR`          | `invalid_input`         | 400         |
| `STATE_ERROR`           | `internal_error`        | 500         |
| `VERIFICATION_ERROR`    | `invalid_input`         | 400         |
| `UNKNOWN_ERROR`         | `internal_error`        | 500         |

The `PipelineError.message` becomes the A2A error `message`, and `PipelineError.details` is included in the error `data` field. `PipelineError.retryable` is surfaced as `data.retryable` to inform clients.

### 7. CLI entry point

```bash
# Serve a single graph as A2A agent
yamlgraph a2a serve examples/demos/hello/graph.yaml --port 8080

# Serve all discoverable graphs (multi-agent)
yamlgraph a2a serve --port 8080

# Print Agent Card JSON for a graph
yamlgraph a2a card examples/demos/hello/graph.yaml
```

### 8. Optional dependency

```toml
# pyproject.toml
[project.optional-dependencies]
a2a = ["a2a-sdk[http-server]>=0.3,<1.0"]
```

Pinned to `>=0.3,<1.0` — targets A2A spec v0.3.25 stable. The v1.0-alpha introduces breaking changes (renamed fields, new auth model). A follow-up FR handles v1.0 migration once it stabilizes.

### 9. No graph YAML changes required

Basic text agents work with existing YAML. The server derives everything from the graph's `name`, `description`, and state keys. Future FRs may add optional A2A-specific metadata (e.g., `supported_modes`, `authentication`), but this is out of scope.

## Acceptance Criteria

- [ ] **REQ-YG-206**: `yamlgraph/discovery.py` extracts shared `discover_graphs()` from `mcp_server.py`; MCP server tests still pass
- [ ] **REQ-YG-207**: `yamlgraph/a2a_server.py` discovers graphs using shared `discover_graphs()`
- [ ] **REQ-YG-208**: Agent Card auto-generated from graph YAML metadata (name, description, skills) with `authentication: null` default
- [ ] **REQ-YG-209**: `task/send` invokes graph with variables parsed via Message Parsing Strategy; returns A2A-compliant task response
- [ ] **REQ-YG-210**: `task/get` retrieves task status via LangGraph checkpointer (thread_id = task_id)
- [ ] **REQ-YG-211**: `task/sendSubscribe` streams graph execution via SSE using `run_graph_streaming_native()`
- [ ] **REQ-YG-212**: `task/cancel` cancels running graph execution
- [ ] **REQ-YG-213**: `input-required` state emitted when graph hits `__interrupt__` node
- [ ] `yamlgraph a2a serve <path>` CLI command starts A2A HTTP server
- [ ] `yamlgraph a2a card <path>` prints Agent Card JSON
- [ ] Optional dependency: `pip install yamlgraph[a2a]` installs `a2a-sdk>=0.3,<1.0`
- [ ] No changes to existing graph YAML schema required
- [ ] Messages with missing `required_vars` are rejected with structured error
- [ ] `PipelineError` objects map to A2A error response format per Error Mapping table
- [ ] Unit tests with mocked A2A SDK (REQ-YG-207, REQ-YG-208, REQ-YG-209)
- [ ] Integration test: A2A client sends task to hello graph, receives streamed response
- [ ] Documentation in `reference/a2a-server.md`

## Implementation Approach

### Phase 0: Discovery extraction (prerequisite, 0.5 day)

1. Extract `discover_graphs()` from `mcp_server.py` into `yamlgraph/discovery.py`
2. Update `mcp_server.py` to import from `yamlgraph/discovery.py`
3. Run existing MCP server tests — all must pass before proceeding
4. Commit this refactor separately

### Phase 1: Core server (2.5 days)

5. Add `a2a-sdk[http-server]>=0.3,<1.0` optional dependency in `pyproject.toml`
6. Create `yamlgraph/a2a_server.py` — import shared discovery from `yamlgraph/discovery.py`
7. Implement Message Parsing Strategy (key_value, single_input, json modes)
8. Implement `AgentCard` generation from graph config (with `authentication: null`)
9. Implement `task/send` → `compile_graph()` + `app.ainvoke()` with thread_id mapping
10. Implement `task/get` → checkpointer state lookup
11. Implement `task/cancel` → asyncio task cancellation
12. Implement `PipelineError` → A2A error response mapping

### Phase 2: Streaming + interrupts (2 days)

13. Implement `task/sendSubscribe` → `run_graph_streaming_native()` wrapped as SSE
14. Map `__interrupt__` state to A2A `input-required` task state
15. Handle resume: `task/send` with existing task_id → `Command(resume=user_input)`

### Phase 3: CLI + docs (1 day)

16. Add `yamlgraph a2a serve` and `yamlgraph a2a card` CLI commands
17. Write `reference/a2a-server.md` with usage examples
18. Add capability YAML (`capabilities/CAP-81-a2a-server.yaml`)
19. Add requirements REQ-YG-206 through REQ-YG-213 to `ARCHITECTURE.md`

## Design Decisions

### Shared vs. separate discovery

The `mcp_server.py` discovery logic (~50 lines) is extracted into `yamlgraph/discovery.py` as Phase 0 prerequisite. Both MCP and A2A servers import from it. The refactor is committed separately to isolate risk and verify MCP tests pass.

### Task ID = Thread ID

A2A task IDs map directly to LangGraph thread IDs. This gives free persistence via the existing checkpointer infrastructure (SQLite/Redis) and enables resume-after-interrupt without new state management.

### Message parsing at the boundary

Following the One Law ("normalize at the boundary where external data enters"), A2A text messages are parsed into typed variables in `a2a_server.py` before reaching graph execution. The resolution order (JSON → key_value → single_input → fallback) handles the most structured format first, degrading gracefully.

### Single-graph vs. multi-agent server

The `serve` command supports both modes: a single graph path (one agent) or directory discovery (multiple agents as skills). Single-graph mode is simpler for development; multi-agent mode mirrors MCP's discovery behavior.

### Target A2A spec v0.3 (stable)

v1.0-alpha introduces breaking changes (renamed fields, new auth model). Build for v0.3 first; pin `a2a-sdk>=0.3,<1.0` to prevent silent breakage. A follow-up FR handles v1.0 migration once it stabilizes.

## Known Limitations

- **Authentication**: Agent Cards are generated with `authentication: null` (unauthenticated). A2A authentication (API keys, OAuth2, JWS) is deferred to a future FR. This is acceptable for local development and internal networks; production deployments should use a reverse proxy for auth.
- **Push notifications**: Not supported in this FR. A2A push notification callbacks require webhook infrastructure beyond the scope of a CLI-started server.
- **DataPart**: Binary data parts in A2A messages are not supported; only `TextPart` is handled. Messages with only `DataPart` return an error.

## Alternatives Considered

### 1. Extend MCP server to also speak A2A

Rejected — the protocols have fundamentally different transport models (stdio vs. HTTP), task lifecycles, and client expectations. Separate modules with shared discovery is cleaner.

### 2. Generic "protocol adapter" abstraction

Rejected — premature abstraction. MCP and A2A are the only two protocols today. Extract a shared interface only if a third protocol emerges.

### 3. Require A2A metadata in graph YAML

Rejected — violates the constraint that existing graphs work without modification. Agent Cards can be fully derived from existing `name`, `description`, and state keys.

## Demo Plan

```bash
# Terminal 1: Start A2A server
yamlgraph a2a serve examples/demos/hello/graph.yaml --port 8080

# Terminal 2: Discover agent
curl http://localhost:8080/.well-known/agent.json | jq .

# Terminal 3: Send task via curl (key_value parsing)
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "id": "1",
    "params": {
      "id": "test-1",
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "name=World style=casual"}]
      }
    }
  }'

# Expected: A2A JSON-RPC response with completed task containing greeting output
```

## Related

- **CAP-19**: MCP Server Interface (`yamlgraph/mcp_server.py`) — pattern to replicate
- **FR-045/045a/045b**: A2A protocol brainstorm, provider, and consumer research
- **FR-029/FR-062**: Native streaming — `run_graph_streaming_native()` used for SSE
- **FR-050**: Skip-if-exists — interrupt/resume checkpointing patterns
- **A2A Spec**: https://google.github.io/A2A/ (v0.3.25 stable)
- **A2A Python SDK**: `pip install a2a-sdk[http-server]`
- `examples/questionnaire/` — session-based agent with interrupt/resume (prior art)
- `yamlgraph/executor_async.py` — async graph execution and streaming
