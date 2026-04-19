# Feature Request: FR-240 A2A Consumer Node Type (`a2a_call`)

**Priority:** HIGH
**Type:** Feature
**Status:** Approved
**Effort:** 5 days
**Requested:** 2026-04-19

## Summary

Add a new `type: a2a_call` node to the graph compiler so YAML graphs can invoke external A2A agents — discover their Agent Card, send a message, and map response artifacts to a `state_key`. This completes the A2A story: FR-208/209/225 made YAMLGraph an A2A *server*; this FR makes it an A2A *client*.

## Value Statement

Graph authors can orchestrate agents built on any framework (ADK, CrewAI, AutoGen, other YAMLGraph instances) from YAML, without writing Python.

## Problem

YAMLGraph graphs can call LLMs, local tools, subgraphs, and other internal node types. There is no declarative way to call an external agent over the network. Every external agent integration requires custom Python in the side-effects layer, violating the YAML-first design philosophy.

The A2A protocol (Agent-to-Agent) provides a standard JSON-RPC interface for inter-agent communication. YAMLGraph already serves graphs as A2A agents (`yamlgraph a2a serve`). The missing piece is the consumer side — calling *out* to other A2A agents from within a graph.

## Proposed Solution

A new `a2a_call` node type that sends a message to a remote A2A agent and maps the response to graph state.

### Minimal YAML interface

```yaml
nodes:
  ask_researcher:
    type: a2a_call
    agent_url: "https://research-agent.example.com"
    message: "Find papers on {{ state.topic }}"
    state_key: research_results
```

### Full configuration (Phase 1 scope)

```yaml
nodes:
  ask_researcher:
    type: a2a_call

    # Required
    agent_url: "https://research-agent.example.com"
    message: "Find papers on {{ state.topic }}"
    state_key: research_results

    # Optional — skill selection
    skill: "academic-research"

    # Optional — timeout
    timeout: 120

    # Optional — auth
    auth:
      scheme: bearer
      token_env: AGENT_API_TOKEN

    # Optional — error handling (reuses existing on_error strategies)
    on_error: retry
    max_retries: 3
```

### Execution flow

1. **Discover**: `GET {agent_url}/.well-known/agent.json` → Agent Card
2. **Validate**: Confirm skill exists (if specified) and input mode supported
3. **Build message**: Render `message` template with Jinja2 against current state
4. **Send**: `SendMessage` JSON-RPC call via `a2a-sdk` (blocking)
5. **Handle response**:
   - `COMPLETED` → extract first text artifact → write to `state_key`
   - `FAILED` → apply `on_error` strategy (skip/fail/retry/fallback)
   - `CANCELED` → treat as failure
6. **Return**: `{state_key: extracted_text}` dict

### New files

| File | Purpose |
|------|---------|
| `yamlgraph/node_factory/a2a_nodes.py` | `create_a2a_call_node()` factory |
| `yamlgraph/utils/a2a_client.py` | Agent Card fetch, message build, SDK invocation |
| `tests/unit/test_a2a_nodes.py` | Unit tests (mocked HTTP) |
| `examples/demos/a2a_consumer/` | Demo: two YAMLGraph instances, one calling the other |

### Registration

1. Add `A2A_CALL = "a2a_call"` to `NodeType` enum in `constants.py`
2. Add `_compile_a2a_call_node` handler in `node_compiler.py`
3. Register in `NODE_TYPE_HANDLERS` dict

### Three-layer alignment

The `a2a_call` node lives in the **Logic layer** (YAML config). Its implementation in `node_factory/a2a_nodes.py` delegates HTTP calls to `utils/a2a_client.py` in the **Side Effects layer**. The Presentation layer is unchanged.

## Acceptance Criteria

- [ ] `NodeType.A2A_CALL = "a2a_call"` added to `constants.py`
- [ ] `_compile_a2a_call_node` registered in `NODE_TYPE_HANDLERS`
- [ ] `node_factory/a2a_nodes.py` creates a node function from `(node_name, node_config)` following existing factory pattern
- [ ] `utils/a2a_client.py` handles Agent Card discovery, message building, and `SendMessage` invocation via `a2a-sdk`
- [ ] Jinja2 templating works in `message` field (consistent with other node types)
- [ ] `skill` field filters to a specific Agent Card skill (validated at discovery time)
- [ ] `auth.scheme: bearer` reads token from env var specified in `auth.token_env`
- [ ] `on_error` strategies (skip/fail/retry/fallback) work identically to LLM nodes
- [ ] `timeout` config propagated to HTTP client
- [ ] `yamlgraph graph lint` validates `a2a_call` nodes (required fields: `agent_url`, `message`, `state_key`)
- [ ] Unit tests with mocked HTTP achieve ≥85% coverage on new modules
- [ ] Demo in `examples/demos/a2a_consumer/` shows two YAMLGraph instances: one served via `yamlgraph a2a serve`, one graph calling it via `a2a_call`
- [ ] `a2a-sdk` optional dependency — graceful `ImportError` with install hint when missing
- [ ] Requirements REQ-YG-239, REQ-YG-240, REQ-YG-242 through REQ-YG-245 added to `ARCHITECTURE.md`
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-XXX")`
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary entry in `docs/diary/`

## Requirements

| ID | Description |
|----|-------------|
| REQ-YG-239 | `a2a_call` node type sends a message to an external A2A agent and writes response artifacts to `state_key` |
| REQ-YG-240 | Agent Card is fetched and validated before sending a message |
| REQ-YG-242 | `message` field supports Jinja2 templating against graph state |
| REQ-YG-243 | `on_error` strategies (skip/fail/retry/fallback) apply to `a2a_call` nodes |
| REQ-YG-244 | Bearer token auth reads credentials from environment variable |
| REQ-YG-245 | `a2a-sdk` is an optional dependency with graceful import error |

## Explicit Scope Boundaries

### In scope (Phase 1)

- Blocking `SendMessage` (synchronous request/response)
- Single text-part messages
- Agent Card discovery and skill validation
- Bearer token auth
- `on_error` strategies
- Configurable timeout

### Out of scope (future FRs)

- Streaming (`SendStreamingMessage` / SSE) — separate FR
- Multi-turn (`input_required` handling) — separate FR
- Dynamic agent discovery (`a2a_discover` node type) — separate FR
- File/binary message parts — separate FR
- OAuth2/OIDC auth flows — separate FR
- Agent Card caching across invocations — separate FR
- Map node integration for parallel A2A calls — works naturally once base node exists

## Alternatives Considered

1. **Python tool wrapper**: Write a Python tool that calls A2A agents, use `type: tool` nodes. Rejected — requires Python for every agent call; violates YAML-first principle. The `a2a_call` node keeps agent orchestration declarative.

2. **Extend `subgraph` node with remote mode**: Add `remote: true` to subgraph nodes. Rejected — conflates local graph composition with remote network calls. Different error modes, timeouts, and auth requirements warrant a distinct node type.

3. **Generic `http_call` node**: A general HTTP node that could be used for A2A. Rejected — too low-level; requires users to understand JSON-RPC, Agent Cards, and artifact extraction. The `a2a_call` node abstracts the protocol.

## Judgement

**Verdict:** APPROVE — Scope frozen, authority granted.

**Review (2026-04-19):**

1. **Scope** — Clear and minimal. Phase 1 is well-bounded (blocking sync, single text part, bearer auth). Future phases explicitly deferred with named FRs.
2. **Contradictions** — One REQ ID collision found and corrected: REQ-YG-241 was already assigned to Pipeline Accumulated State (FR-238). Shifted to REQ-YG-242–245.
3. **Acceptance criteria** — Measurable: ≥85% coverage, lint validation rules, demo proving end-to-end flow, specific files and registration points.
4. **Feasibility** — Straightforward. Follows established `node_factory/` pattern (closest: `subgraph_nodes.py`). `a2a-sdk` already in `pyproject.toml` as optional `[a2a]` extra. `NODE_TYPE_HANDLERS` registry is mechanical to extend.
5. **Architecture alignment** — Three-layer split is explicitly addressed and correct: YAML config → `node_factory/` logic → `utils/` side effects.
6. **Single responsibility** — Yes. Consumer node type only; no bundled concerns.
7. **Alternatives** — Three alternatives considered and rejected with sound reasoning.

**No amendments required.** Proceed to implementation.

## Related

- `feature-requests/045b-a2a-consumer.md` — original brainstorm (6 use cases, 3-phase plan)
- `feature-requests/FR-208-a2a-graph-support.md` — A2A server (implemented)
- `feature-requests/FR-209-a2a-demo-streaming-response.md` — A2A demo (implemented)
- `feature-requests/FR-225-a2a-test-coverage.md` — A2A test coverage (implemented)
- `yamlgraph/a2a_server.py` — existing server-side A2A implementation
- `yamlgraph/node_compiler.py` — `NODE_TYPE_HANDLERS` registry
- `yamlgraph/node_factory/subgraph_nodes.py` — closest pattern (external invocation)
- `examples/demos/a2a_server/` — existing A2A server demo
