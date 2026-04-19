# Feature Request: FR-248 A2A Consumer Phase 2 — Agent Card, Skill Selection & Streaming

**Priority:** MEDIUM
**Type:** Feature
**Status:** In Progress
**Effort:** 5 days
**Requested:** 2026-04-19
**Judged:** 2026-04-19

---

## Summary

Extend the `a2a_call` node (FR-240) with Agent Card discovery, skill selection, and SSE streaming. Agent Card fetching uses sync `httpx.get()` with a `ContextVar`-scoped cache. Skill selection validates against the discovered card at runtime. Streaming uses the `a2a-sdk` `A2AClient.send_message_streaming()` in a dedicated thread with its own event loop. Non-streaming transport remains sync `httpx.post()`.

## Value Statement

Graph authors can target specific agent skills and receive streaming responses from external A2A agents, enabling intelligent routing and real-time feedback in cross-framework multi-agent orchestration.

## Problem

FR-240 delivered a working `a2a_call` node but with significant limitations:

1. **No Agent Card discovery** — the node sends raw JSON-RPC without knowing the agent's capabilities, skills, or supported input/output modes. If the agent doesn't support the request shape, it fails at runtime with an opaque HTTP error.
2. **No skill selection** — cannot target a specific skill on multi-skill agents. The `skill` field from the 045b brainstorm was deferred.
3. **No streaming** — all calls are blocking. Long-running agent tasks provide no intermediate feedback. The `streaming: true` option from the brainstorm was deferred.

These gaps prevent two key use cases from the 045b brainstorm:
- **UC-1 (Hybrid Graphs)**: Cannot target the right skill on a multi-skill agent
- **UC-2 (Multi-Agent Mesh)**: No streaming means no real-time progress from remote agents

## Proposed Solution

### 1. Agent Card Discovery (Sync)

Fetch the Agent Card via sync `httpx.get()` to `{agent_url}/.well-known/agent.json` and parse into the SDK's `AgentCard` model. This avoids the `asyncio.run()` footgun (see Design Decisions) while providing full Agent Card data for skill validation and capability checking.

```python
import httpx
from a2a.types import AgentCard

def _fetch_agent_card(agent_url: str, timeout: float = 30) -> AgentCard:
    card_url = f"{agent_url.rstrip('/')}/.well-known/agent.json"
    response = httpx.get(card_url, timeout=timeout)
    response.raise_for_status()
    return AgentCard.model_validate(response.json())
```

### 2. Agent Card Caching (ContextVar)

Cache Agent Cards using `contextvars.ContextVar`, scoped per graph invocation context. This mirrors the established pattern in `subgraph_nodes.py` (`_loading_stack: ContextVar`). Each invocation gets its own cache; long-running processes (MCP server, FastAPI) naturally isolate invocations.

```python
from contextvars import ContextVar

_agent_card_cache: ContextVar[dict[str, AgentCard]] = ContextVar(
    "agent_card_cache"
)

def _get_agent_card(agent_url: str, timeout: float = 30) -> AgentCard:
    cache = _agent_card_cache.get({})
    if agent_url in cache:
        return cache[agent_url]
    card = _fetch_agent_card(agent_url, timeout)
    cache[agent_url] = card
    _agent_card_cache.set(cache)
    return card
```

No TTL needed — graph invocations are short-lived. Each `ContextVar` context starts with an empty cache. No explicit clear required.

### 3. Skill Selection

New optional `skill` field on `a2a_call` nodes:

```yaml
nodes:
  research:
    type: a2a_call
    agent_url: "https://research-agent.example.com"
    skill: "academic-research"
    message: "Find papers on {{ topic }}"
    state_key: research_results
```

When `skill` is specified:
1. Fetch Agent Card (or use cached)
2. Validate the skill ID exists in `card.skills` — raise `ValueError` with available skill IDs on miss
3. Include skill ID in the JSON-RPC `params` sent to the agent

### 4. Streaming Support

New optional `streaming` field:

```yaml
nodes:
  long_task:
    type: a2a_call
    agent_url: "https://slow-agent.example.com"
    message: "Generate report on {{ topic }}"
    state_key: report
    streaming: true
```

When `streaming: true`:
1. Fetch Agent Card and check `card.capabilities.streaming` is `True` — fail with clear error if not
2. Use `A2AClient.send_message_streaming()` in a dedicated thread with its own event loop (see Design Decisions)
3. Collect streaming events, extract text from final artifact
4. The node still returns a complete result in `state_key` — streaming is for transport, not for partial state updates

Streaming events are logged at DEBUG level for observability.

### 5. Updated Node Configuration

```yaml
my_agent_call:
  type: a2a_call

  # Required (unchanged from FR-240)
  agent_url: "https://agent.example.com"
  message: "{{ state.input }}"
  state_key: result

  # New optional fields (FR-248)
  skill: "specific-skill-id"
  streaming: false

  # Existing optional fields (FR-240)
  timeout: 120
  on_error: fail
  max_retries: 3
  variables: {}
```

### 6. Schema Changes

Add to `NodeConfig` in `models/graph_schema.py`:

```python
# A2A call node fields — Phase 2 (FR-248)
skill: str | None = Field(
    default=None,
    description="Target skill ID on the remote A2A agent",
)
streaming: bool | None = Field(
    default=None,
    description="Use SSE streaming transport for A2A calls",
)
```

The `streaming` field is new to `NodeConfig` — it does not exist today.

### 7. Linter Checks

Add to `yamlgraph/linter/patterns/a2a.py`:

- **W901** (warning): `skill` field present on `a2a_call` node — advisory that skill validation occurs at runtime only (agent not reachable during lint)
- **E904** (error): `streaming: true` used on a node type other than `a2a_call`

## Acceptance Criteria

- [x] **REQ-YG-246**: `a2a_call` node fetches Agent Card via sync `httpx.get()` to `{agent_url}/.well-known/agent.json`; Agent Cards cached per `agent_url` within a graph invocation using `ContextVar`; cache is isolated across invocations in long-running processes
- [x] **REQ-YG-247**: `skill` field on `a2a_call` node selects a specific agent skill; validated against Agent Card skills at runtime; `ValueError` raised on skill ID miss with available skills listed in error message
- [x] **REQ-YG-248**: `streaming: true` on `a2a_call` node uses `A2AClient.send_message_streaming()` via dedicated thread; requires `card.capabilities.streaming == True`; result still written as complete string to `state_key`; streaming events logged at DEBUG level
- [x] **REQ-YG-249**: Linter check W901 warns when `skill` field is present on `a2a_call` (informational); linter check E904 errors when `streaming: true` is used on a non-`a2a_call` node type
- [x] Unit tests for Agent Card fetching, caching isolation, skill validation, streaming event collection (all in `tests/unit/test_a2a_call_node.py`)
- [x] Existing FR-240 unit tests continue to pass (no regression)
- [ ] Demo in `examples/demos/a2a_call/` updated to demonstrate `skill` and `streaming` options
- [x] `skill` and `streaming` fields added to `NodeConfig` in `graph_schema.py`
- [x] Capability file `capabilities/CAP-104-a2a-consumer-phase2.yaml` created
- [x] REQ-YG-246, REQ-YG-247, REQ-YG-248, REQ-YG-249 added to `ARCHITECTURE.md`

## Implementation Approach

### Files to Modify

| File | Change |
|------|--------|
| `yamlgraph/node_factory/a2a_nodes.py` | Add Agent Card fetch (sync httpx), ContextVar cache, skill routing, streaming via A2AClient in thread |
| `yamlgraph/models/graph_schema.py` | Add `skill` and `streaming` fields to `NodeConfig` |
| `yamlgraph/linter/patterns/a2a.py` | Add W901 (skill advisory), E904 (streaming type check) |
| `tests/unit/test_a2a_call_node.py` | Tests for Agent Card, caching, skill validation, streaming collection |
| `examples/demos/a2a_call/graph.yaml` | Add skill and streaming examples |
| `capabilities/CAP-104-a2a-consumer-phase2.yaml` | New capability file |
| `ARCHITECTURE.md` | REQ-YG-246 through REQ-YG-249 entries |

### Implementation Steps

1. **Add `skill` and `streaming` fields** to `NodeConfig` in `graph_schema.py`
2. **Add Agent Card discovery** — sync `httpx.get()` to `/.well-known/agent.json`, parse into SDK `AgentCard`, `ContextVar` cache
3. **Add skill validation** — fetch card, match `skill` against `card.skills[].id`, include in JSON-RPC params; raise `ValueError` on miss
4. **Add streaming path** — when `streaming: true`, verify `card.capabilities.streaming`, run `A2AClient.send_message_streaming()` in dedicated thread, collect SSE events, extract final artifact text
5. **Linter checks** — W901 advisory for `skill`, E904 for `streaming` on wrong node type
6. **Tests** — mock `httpx.get` for Agent Card; mock `A2AClient` with `AsyncMock` for streaming; test cache isolation via `ContextVar`; test skill miss error message
7. **Demo update** — add `skill` and `streaming: true` to the existing `a2a_call` demo graph

### Design Decisions

#### Sync httpx for non-streaming, A2AClient for streaming only

The `A2AClient` is async-only (`httpx.AsyncClient`). Node factory functions are synchronous. Calling `asyncio.run()` inside a node function fails under `graph.ainvoke()` with `RuntimeError: This event loop is already running` — `asyncio.run()` is only safe at top-level entry points (CLI `graph_commands.py:238`, MCP `mcp_server.py:274`).

**Decision (Issue 3 resolution):** Keep sync `httpx.post()` for non-streaming `send_message` (proven, no async needed). Use `A2AClient` exclusively for streaming, where it runs in a dedicated thread with its own event loop:

```python
def _send_streaming(client_url: str, request: SendMessageRequest) -> str:
    """Run A2AClient streaming in a dedicated thread with its own event loop."""
    def _run() -> str:
        async def _stream():
            async with httpx.AsyncClient() as http_client:
                client = A2AClient(httpx_client=http_client, url=client_url)
                collected = []
                async for event in client.send_message_streaming(request):
                    logger.debug("A2A streaming event: %s", type(event).__name__)
                    collected.append(event)
                return _extract_text_from_streaming_events(collected)
        return asyncio.run(_stream())

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        return future.result()
```

This mirrors the `mcp_server.py` pattern (`loop.run_in_executor(_executor, sync_function)`), is safe inside existing event loops, and isolates the async boundary.

Agent Card fetching uses sync `httpx.get()` — a simple GET request with no need for the async SDK.

#### ContextVar-scoped Agent Card cache (Issue 2 resolution)

A module-level `dict` persists across calls in long-running processes (MCP server, FastAPI apps). `ContextVar` provides natural per-invocation scoping, matching the established pattern in `subgraph_nodes.py` (`_loading_stack: ContextVar`).

Each graph invocation runs in its own context. The cache dict is created on first access and discarded when the context ends. No explicit clear mechanism needed. No TTL needed — graph invocations are short-lived.

For MCP server integration: `run_in_executor` preserves `contextvars` context by default in Python 3.11+ (via `contextvars.copy_context()`), ensuring cache isolation between concurrent invocations.

#### Streaming collects full result

`streaming: true` changes the *transport* but not the *return contract*. The node still returns a complete string in `state_key`. Streaming benefits: lower time-to-first-byte on the HTTP layer, server can start processing earlier, and intermediate events are logged for observability. Partial state updates are out of scope (would require graph-level streaming infrastructure from FR-030).

#### Skill validation is runtime-only

The linter cannot reach the remote agent to validate skill IDs. W901 is advisory ("skill field present — will be validated at runtime"). Runtime validation fetches the Agent Card and raises `ValueError` with the list of available skill IDs if the specified skill is not found.

## Alternatives Considered

### 1. Full A2AClient migration for all paths (non-streaming and streaming)

Rejected. The `A2AClient` is async-only. Wrapping async calls in `asyncio.run()` inside node functions is unsafe under `graph.ainvoke()` (raises `RuntimeError: This event loop is already running`). The sync `httpx.post()` path is proven and reliable for non-streaming calls. Full SDK migration can be revisited when LangGraph provides first-class async node support or when `a2a-sdk` offers a sync client.

### 2. Module-level dict for Agent Card cache

Rejected. Persists across invocations in long-running processes (MCP server, FastAPI), causing stale data and cross-invocation leakage. `ContextVar` provides natural per-invocation scoping with zero lifecycle management, matching the established `subgraph_nodes.py` pattern.

### 3. Make streaming surface partial state updates

Rejected for Phase 2. Partial state updates during node execution would require changes to the graph executor and LangGraph state management. FR-030 (streaming infrastructure) tracks this separately. Phase 2 streaming is transport-only.

### 4. Add authentication (bearer/OAuth) in this FR

Deferred. Auth adds complexity (env var resolution, token refresh, multiple schemes). Separating it keeps this FR minimal and single-responsibility. Auth gets its own FR.

### 5. nest_asyncio to allow asyncio.run() inside event loops

Rejected. `nest_asyncio` monkey-patches the event loop policy and is widely considered a code smell. The dedicated-thread approach is standard and safe.

## Out of Scope

- Multi-turn `input_required` handling (Phase 3 — needs interrupt node integration)
- Authentication schemes (separate FR)
- Dynamic agent discovery / `a2a_discover` node type (Phase 3)
- Binary artifact parts / file downloads (Phase 3)
- Map node integration for parallel A2A calls (works already via subgraph)
- Full `A2AClient` migration for non-streaming path (revisit when sync SDK available)

## Related

- **FR-240**: A2A Call Node Type — Phase 1 (this FR extends it)
- **045b-a2a-consumer.md**: Original brainstorm document
- **FR-208**: A2A Server (expose graphs as A2A agents)
- **FR-209**: A2A Demo Streaming Response (server-side streaming)
- **FR-225**: A2A Test Coverage
- **FR-030**: Streaming infrastructure (graph-level streaming)
- **CAP-101**: A2A call node capability (Phase 1)

---

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

### Evaluation

1. **Scope clarity**: Clear and minimal. Three tightly coupled features (Agent Card, skill, streaming) sharing a single prerequisite (Agent Card discovery). Agent Card alone has no user-facing value — it exists to enable skill validation and streaming capability checks. Splitting would create overhead without benefit.

2. **Contradictions/ambiguities**: None found. The sync-for-non-streaming / async-thread-for-streaming split is well-reasoned and backed by the `asyncio.run()` footgun analysis. The `ContextVar` cache pattern is consistent with `subgraph_nodes.py:_loading_stack`.

3. **Acceptance criteria**: All four REQs are measurable and testable via unit tests with mocked `httpx.get` and `A2AClient`. Cache isolation is testable via `ContextVar` scoping. Skill miss error message content is assertable.

4. **Feasibility**: Verified. `a2a-sdk 0.3.26` installed; `AgentCard` and `A2AClient` imports confirmed. `httpx 0.28.1` available. Threading approach (`ThreadPoolExecutor` + `asyncio.run()`) is standard Python. All files to modify exist and are in expected state.

5. **Architecture alignment**: Extends `a2a_nodes.py` (FR-240) without breaking existing contract. Schema changes follow `NodeConfig` flat-model convention (type-specific optional fields). Linter additions follow existing `a2a.py` pattern structure. Error handling uses established `PipelineError` pattern.

6. **Single responsibility**: The three features share a dependency graph (Agent Card → skill validation, Agent Card → streaming capability check). They collectively complete the Phase 2 contract outlined in the 045b brainstorm. Not orthogonal — cohesive.

### Notes for Implementer

- The `streaming` field on `NodeConfig` is transport-only. Do not conflate with FR-030 graph-level streaming. Document this boundary in a code comment.
- The `_agent_card_cache.get({})` default creates a new dict only on first access per context. This is correct but subtle — add a comment.
- E904 should also check non-`a2a_call` nodes that set `skill` — consider extending to catch misplaced `skill` field as well (advisory W902).
