# A2A Provider — YAMLGraph as A2A Server

**Date**: 2026-02-18
**Status**: Brainstorm
**Prerequisite**: [045-a2a-protocol-brainstorm.md](045-a2a-protocol-brainstorm.md) (protocol research)

---

## Problem

YAMLGraph graphs are network-inaccessible outside of:
- **MCP** — single-user, in-IDE (Copilot)
- **FastAPI examples** — custom HTTP per app (npc, interview)
- **CLI** — developer-facing, no API

No standard protocol for external agents, platforms, or services to discover and invoke YAMLGraph graphs.

## Solution

Expose YAMLGraph graphs as **A2A-compliant agent skills** — discoverable via Agent Card, invocable via standard A2A operations.

---

## Use Cases

### UC-1: `yamlgraph a2a serve` — Zero-Code Agent Server

A single command starts an A2A HTTP server that auto-discovers graphs and publishes them as skills.

```bash
yamlgraph a2a serve --port 8080
# Agent Card at http://localhost:8080/.well-known/agent-card.json
```

Any A2A client can:
1. Discover the Agent Card
2. `SendMessage`: "Analyse the authentication module for security issues"
3. Receive Task with structured artifacts

**Generated Agent Card:**
```json
{
  "name": "YAMLGraph Agent",
  "description": "YAML-defined LLM pipelines exposed as A2A skills",
  "supportedInterfaces": [
    {"url": "http://localhost:8080", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}
  ],
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "defaultInputModes": ["text/plain", "application/json"],
  "defaultOutputModes": ["application/json"],
  "skills": [
    {
      "id": "code-analysis",
      "name": "Code Analysis",
      "description": "Analyse Python codebase for quality, patterns, complexity",
      "tags": ["code", "python", "analysis"],
      "examples": ["Analyse yamlgraph/ for code quality"],
      "inputModes": ["text/plain", "application/json"],
      "outputModes": ["application/json"]
    },
    {
      "id": "beautify",
      "name": "Beautify Text",
      "description": "Rewrite text with enhanced style and tone",
      "tags": ["writing", "style"],
      "examples": ["Make this paragraph more engaging"]
    }
  ]
}
```

### UC-2: Human-in-the-Loop via A2A

YAMLGraph's `interrupt_before` maps to A2A `TASK_STATE_INPUT_REQUIRED`. External systems participate in multi-turn flows without custom integration.

**Scenario**: Interview/Questionnaire
1. Client: `SendMessage` → "Start interview for data engineer position"
2. Agent: Task created, first question in status message, state = `INPUT_REQUIRED`
3. Client: `SendMessage` with `taskId` → answer
4. Agent: resumes via `Command(resume=answer)`, next question → `INPUT_REQUIRED`
5. Repeat until → `COMPLETED` with assessment artifact

**Value**: Ninchat, Slack, web UIs — any A2A client becomes an interview frontend.

### UC-3: Long-Running Graphs with Push Notifications

Storyboard, book translation, large codegen — tasks that take minutes/hours.

1. Client: `SendMessage` with `pushNotificationConfig` (webhook URL)
2. Agent: returns `TASK_STATE_WORKING`
3. Per-chapter completion → `TaskArtifactUpdateEvent` POSTed to webhook
4. Done → `TASK_STATE_COMPLETED` notification

**Value**: No open connection. CI/CD, Slack, Teams receive updates natively.

### UC-4: Agent Card as CLI Tool

Even without running a server:

```bash
yamlgraph graph agent-card examples/demos/hello/graph.yaml
# → Agent Card JSON to stdout
```

Machine-readable capability documentation. Registries can index YAMLGraph graphs.

### UC-5: A2A Gateway for Existing FastAPI Apps

Wrap existing NPC/interview FastAPI apps with A2A protocol:

```python
from yamlgraph.a2a import create_a2a_app

app = create_a2a_app(
    graphs=["graphs/npc.yaml", "graphs/interview.yaml"],
    capabilities={"streaming": True, "pushNotifications": False},
)
```

Gradual adoption — existing apps gain A2A compatibility without restructuring.

### UC-6: Ninchat/Customer Service via A2A

Replace bespoke RTM/REST integration with standard A2A:

- Customer messages → `SendMessage`
- Bot responses → Task artifacts
- Escalation to human → `input_required` state
- Agent handoff → A2A to a different agent

One A2A server works with any A2A-compatible chat frontend.

---

## Architecture

### Agent Card Generation from YAML

```yaml
# graph.yaml metadata → Agent Card fields
name: "Code Analysis Pipeline"
description: "Analyses Python codebases for quality and patterns"
version: "1.0.0"

state:
  path: {type: str, description: "Path to analyse"}
  package: {type: str, description: "Package name"}
```

Auto-generates skill with input schema derived from `state` keys.

### Task Lifecycle Mapping

```
A2A TaskState          ←→  YAMLGraph
─────────────────────────────────────────
SUBMITTED              ←→  graph.invoke() called
WORKING                ←→  nodes executing
INPUT_REQUIRED         ←→  interrupt_before triggered
COMPLETED              ←→  graph returns final state
FAILED                 ←→  PipelineError raised
CANCELED               ←→  (new: cancellation support needed)
```

### Three-Layer Pattern

```
┌─────────────────────────────────────┐
│  A2A Server (HTTP/JSON-RPC)         │ ← NEW presentation layer
├─────────────────────────────────────┤
│  YAML Graphs                        │ ← Unchanged logic layer
├─────────────────────────────────────┤
│  Python Tools + LLMs                │ ← Unchanged side effects
└─────────────────────────────────────┘
```

A2A is a presentation layer — parallel to CLI and MCP. No core changes.

### Reuse from MCP Server (CAP-19)

| MCP Server Component | A2A Reuse |
|----------------------|-----------|
| `discover_graphs()` | Same — scan dirs, parse YAML headers |
| `_invoke_graph()` | Same — load, compile, invoke |
| Tool listing | → Agent Card skill listing |
| Tool invocation | → `SendMessage` → graph invocation |

~80% of the MCP server logic applies directly.

---

## Implementation Plan

### Phase 1: Minimal A2A Server (3-5 days)

**SDK**: `pip install a2a-sdk`

**New files:**
- `yamlgraph/a2a_server.py` — A2A HTTP server (JSON-RPC binding)
- `yamlgraph/cli/a2a_commands.py` — `yamlgraph a2a serve`, `yamlgraph graph agent-card`

**Scope:**
- Agent Card auto-generation from discovered graphs
- `SendMessage` → graph invocation → Task with artifacts
- Well-known URI (`/.well-known/agent-card.json`)
- API key auth (simple)

**Out of scope (Phase 1):**
- Streaming (SSE)
- Push notifications
- Multi-turn / `input_required`
- Extended Agent Cards
- gRPC binding

### Phase 2: Streaming + Multi-Turn (3-5 days)

- SSE streaming via `SendStreamingMessage`
- `interrupt_before` → `INPUT_REQUIRED` state
- Resume via subsequent `SendMessage` with `taskId`
- Task state persistence via checkpointers

### Phase 3: Enterprise Features (5-10 days)

- Push notifications (webhook delivery)
- Extended Agent Cards (auth-gated skills)
- Agent Card signing (JWS)
- OAuth2/OIDC auth
- Multi-tenant support
- gRPC binding

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| A2A spec RC, not final | Use `a2a-sdk`; isolate protocol layer for easy updates |
| Auth complexity | Start with API key; OAuth in Phase 3 |
| Scope creep | Phase 1 = SendMessage only, no streaming/push |
| Performance | JSON-RPC sufficient initially; gRPC in Phase 3 |

## Open Questions

1. **One agent card, many skills** vs. one agent per graph?
   → Recommendation: many skills (mirrors MCP server)
2. **Task persistence** — reuse checkpointers or separate store?
   → Recommendation: reuse checkpointers (thread-based state)
3. **Streaming granularity** — per-token or per-node?
   → Recommendation: per-node status updates (simpler, sufficient)

---

## References

- [a2a-protocol-brainstorm.md](a2a-protocol-brainstorm.md) — full protocol research
- [A2A Specification](https://a2a-protocol.org/latest/specification/)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)
- `yamlgraph/mcp_server.py` — pattern to reuse (CAP-19)
