# A2A Protocol × YAMLGraph — Research & Brainstorm

**Date**: 2026-02-18
**Status**: Research / Ideation

**Split documents:**
- [045a-a2a-provider.md](045a-a2a-provider.md) — YAMLGraph as A2A Server (expose graphs as agent skills)
- [045b-a2a-consumer.md](045b-a2a-consumer.md) — YAMLGraph as A2A Client (`a2a_call` node type)

---

## 1. What is A2A?

**Agent-to-Agent (A2A)** is an open protocol (Linux Foundation, contributed by Google) that standardises how independent, opaque AI agents discover each other, negotiate interaction modalities, and collaborate on tasks — without exposing their internal state, memory, or tool implementations.

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Agent Card** | JSON manifest at `/.well-known/agent-card.json` — identity, skills, capabilities, auth requirements, supported interfaces |
| **Task** | Stateful unit of work with lifecycle: `submitted → working → completed/failed/canceled/rejected` + interrupted states (`input_required`, `auth_required`) |
| **Message** | Communication turn (role: user/agent) containing Parts |
| **Part** | Atomic content unit: text, file (raw bytes / URL), or structured data (JSON) |
| **Artifact** | Task output composed of Parts (separate from Messages — output vs. communication) |
| **Skill** | Declared capability on Agent Card — what an agent can do, with examples, input/output modes |
| **Context** | Groups related tasks/messages into a logical conversation |

### Protocol Bindings

A2A supports three official transport bindings (agents can expose multiple):

1. **JSON-RPC 2.0** over HTTP(S) — simplest, SSE for streaming
2. **gRPC** over HTTP/2 — high-performance, strongly-typed
3. **HTTP+JSON/REST** — RESTful resource-oriented URLs

### Core Operations

| Operation | Purpose |
|-----------|---------|
| `SendMessage` | Client → agent, sync or returns task for async |
| `SendStreamingMessage` | Same, but SSE/gRPC stream for real-time updates |
| `GetTask` | Poll task state |
| `ListTasks` | Query tasks with filters + pagination |
| `CancelTask` | Request cancellation |
| `SubscribeToTask` | Subscribe to ongoing task updates |
| Push Notifications | Webhook-based async delivery for long-running tasks |
| `GetExtendedAgentCard` | Authenticated card with additional skills |

### Key Properties

- **Opaque execution**: agents collaborate without sharing internals
- **Async-first**: designed for long-running tasks and human-in-the-loop
- **Multi-turn**: `input_required` state enables clarification dialogs
- **Rich content**: text, files, structured JSON, media types
- **Enterprise-ready**: OAuth2, OpenID Connect, API keys, JWS-signed Agent Cards
- **Extensible**: extension points on messages, artifacts, and agent capabilities

### A2A vs. MCP — Complementary

| MCP | A2A |
|-----|-----|
| Agent ↔ Tools (function calling) | Agent ↔ Agent (peer collaboration) |
| "How do I use this capability?" | "How do we work together?" |
| Synchronous, tool-level | Async tasks, streaming, multi-turn |
| Internal to an agent | Between independent agents |

**They compose**: an agent can use MCP to call tools internally while exposing itself to other agents via A2A externally.

---

## 2. YAMLGraph Today — Relevant Capabilities

| Capability | A2A Relevance |
|-----------|---------------|
| **YAML-defined graphs** with LLM nodes, routing, subgraphs | Each graph = potential A2A skill |
| **MCP server** (`mcp_server.py`, CAP-19) | Already exposes graphs as tools; A2A is the inter-agent counterpart |
| **Multi-provider LLM** (7 providers) | A2A agents don't expose provider details — opacity preserved |
| **Streaming** (token-level, graph-level, SSE via FastAPI) | Maps directly to A2A `SendStreamingMessage` / SSE |
| **Checkpointers** (memory, SQLite, Redis) | Persistent task state maps to A2A Task lifecycle |
| **Human-in-the-loop** (`interrupt_before` + `Command(resume=)`) | Maps to A2A `input_required` state |
| **Map nodes** (parallel fan-out) | Internal optimisation, invisible to A2A consumers |
| **Pydantic-typed outputs** | Map to A2A structured data Parts |
| **Error handling** (retry, fallback, skip) | Maps to A2A `failed` / error responses |
| **Graph discovery** (scan dirs, parse YAML metadata) | Foundation for Agent Card skill generation |
| **CLI** (`yamlgraph graph run/list/lint/validate`) | Development-time tooling; A2A is runtime API |

---

## 3. Strategic Fit: Why A2A for YAMLGraph?

### The Gap

YAMLGraph today has:
- **MCP**: Copilot-internal tool integration (single-user, in-IDE)
- **FastAPI examples**: custom HTTP APIs per application (npc, interview)
- **CLI**: developer-facing execution

What's missing: **a standard protocol for YAMLGraph agents to interoperate with agents built on other frameworks** (ADK, CrewAI, AutoGen, BeeAI, LangGraph-native, etc.).

### The Opportunity

A2A turns any YAMLGraph graph into an **interoperable agent endpoint**. A graph that generates book translations, analyses code, or runs questionnaires can be discovered and invoked by any A2A client — regardless of the client's framework.

### Natural Alignment

| A2A Concept | YAMLGraph Mapping |
|-------------|-------------------|
| Agent Card | Auto-generated from graph YAML metadata (`name`, `description`, `state`) |
| Skill | Each graph or graph-family = one skill |
| Task | Graph invocation with `thread_id` for checkpointed multi-turn |
| `input_required` | `interrupt_before` nodes → A2A waits for client message |
| Artifact | Final state output serialised as structured Part |
| Streaming | `executor_async` SSE streaming → A2A SSE/gRPC stream |
| Push Notifications | Long-running graphs (storyboard, book translator) → webhook |

---

## 4. Use Cases — Summary

Detailed use cases are split by role:

### Provider (YAMLGraph as A2A Server) → [a2a-provider.md](a2a-provider.md)

| # | Use Case | Impact | Effort | Priority |
|---|----------|--------|--------|----------|
| 1 | `yamlgraph a2a serve` — zero-code agent server | HIGH | LOW | **P0** |
| 2 | Human-in-the-loop via A2A (`interrupt_before` → `input_required`) | HIGH | MEDIUM | **P1** |
| 3 | Long-running graphs with push notifications | MEDIUM | MEDIUM | **P2** |
| 4 | Agent Card CLI generation (`yamlgraph graph agent-card`) | MEDIUM | LOW | **P0** |
| 5 | A2A gateway for existing FastAPI apps | MEDIUM | LOW | **P1** |
| 6 | Ninchat/customer service via A2A | MEDIUM | MEDIUM | **P2** |

### Consumer (YAMLGraph as A2A Client) → [a2a-consumer.md](a2a-consumer.md)

| # | Use Case | Impact | Effort | Priority |
|---|----------|--------|--------|----------|
| 1 | Hybrid graphs — LLM + external agent nodes | HIGH | MEDIUM | **P1** |
| 2 | Multi-agent mesh — cross-framework collaboration | HIGH | HIGH | **P2** |
| 3 | Federated execution — data sovereignty | MEDIUM | HIGH | **P3** |
| 4 | Dynamic agent discovery & routing | MEDIUM | HIGH | **P3** |
| 5 | Handling remote multi-turn (`input_required`) | MEDIUM | MEDIUM | **P2** |
| 6 | Agent marketplace consumption | LOW | HIGH | **P3** |

---

## 5. Competitive Landscape

| Framework | A2A Support |
|-----------|-------------|
| Google ADK | Native A2A server/client |
| LangGraph (standalone) | Community samples, no native |
| CrewAI | Community adapter |
| AutoGen | Community integration |
| BeeAI | A2A tutorial in DeepLearning.AI course |
| **YAMLGraph** | **Not yet — this is the opportunity** |

YAMLGraph's unique advantage: **A2A support would be declarative**. No Python code needed to expose agents — just write the graph YAML and `yamlgraph a2a serve`.

---

## 9. Decision Matrix

| Use Case | Impact | Effort | Priority |
|----------|--------|--------|----------|
| UC-1: A2A Server (graphs as skills) | HIGH | LOW | **P0** |
| UC-6: Agent Card CLI generation | MEDIUM | LOW | **P0** |
| UC-4: Human-in-loop via A2A | HIGH | MEDIUM | **P1** |
| UC-2: A2A Client node type | HIGH | MEDIUM | **P1** |
| UC-7: FastAPI adapter | MEDIUM | LOW | **P1** |
| UC-5: Push notifications | MEDIUM | MEDIUM | **P2** |
| UC-8: Ninchat via A2A | MEDIUM | MEDIUM | **P2** |
| UC-3: Multi-agent mesh | HIGH | HIGH | **P2** |
| UC-9: Federated execution | MEDIUM | HIGH | **P3** |
| UC-10: Marketplace | LOW | HIGH | **P3** |

---

## 10. Next Steps

1. **Spike**: Install `a2a-sdk`, build minimal A2A server wrapping one graph (hello example)
2. **Feature Request**: Write FR for Phase 1 (A2A Server) in `feature-requests/`
3. **Prototype**: Agent Card generation from graph YAML metadata
4. **Validate**: Test interop with Google ADK A2A client sample
5. **Document**: Update ARCHITECTURE.md with CAP-20: A2A Protocol Support

---

## References

- [A2A Protocol Specification (RC v1.0)](https://a2a-protocol.org/latest/specification/)
- [A2A GitHub Repository](https://github.com/a2aproject/A2A)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python) — `pip install a2a-sdk`
- [A2A Samples](https://github.com/a2aproject/a2a-samples)
- [A2A DeepLearning.AI Course](https://goo.gle/dlai-a2a)
- [A2A + MCP Relationship](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)
- YAMLGraph MCP Server: `yamlgraph/mcp_server.py` (CAP-19)
- YAMLGraph FastAPI patterns: `ARCHITECTURE.md` §Building APIs
