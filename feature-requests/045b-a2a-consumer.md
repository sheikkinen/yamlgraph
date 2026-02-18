# A2A Consumer — YAMLGraph as A2A Client

**Date**: 2026-02-18
**Status**: Brainstorm
**Prerequisite**: [045-a2a-protocol-brainstorm.md](045-a2a-protocol-brainstorm.md) (protocol research)

---

## Problem

YAMLGraph graphs can only call LLMs and local Python tools. There is no way to invoke external agents from within a graph YAML — every external integration requires custom Python code in the side-effects layer.

As A2A adoption grows, specialized agents (research, code review, translation, image generation) become available as network services. YAMLGraph needs a declarative way to call them.

## Solution

A new `a2a_call` node type that lets YAML graphs invoke external A2A agents — discover their capabilities, send messages, handle multi-turn interactions, and collect artifacts, all without Python.

---

## Use Cases

### UC-1: Hybrid Graphs — LLM Nodes + External Agent Nodes

Mix internal LLM processing with external agent calls in a single graph:

```yaml
nodes:
  gather_research:
    type: a2a_call
    agent_url: "https://research-agent.example.com"
    skill: "academic-research"
    message: "Find papers on {{ state.topic }}"
    state_key: research_results

  synthesize:
    type: llm
    prompt: synthesize-research
    state_key: synthesis

  peer_review:
    type: a2a_call
    agent_url: "https://review-agent.example.com"
    skill: "scientific-review"
    message: "Review this synthesis: {{ state.synthesis }}"
    state_key: review_feedback

edges:
  - gather_research >> synthesize >> peer_review
```

**Value**: Graph orchestrates agents built on any framework — ADK, CrewAI, AutoGen, other YAMLGraph instances — without writing Python.

### UC-2: Multi-Agent Mesh — Cross-Framework Collaboration

Multiple YAMLGraph and non-YAMLGraph agents collaborate via A2A:

```
┌─────────────────┐     A2A      ┌─────────────────┐
│  Research Agent  │◄────────────►│  Writing Agent   │
│  (yamlgraph)    │              │  (yamlgraph)     │
└────────┬────────┘              └────────┬─────────┘
         │ A2A                            │ A2A
         ▼                                ▼
┌─────────────────┐              ┌─────────────────┐
│  Review Agent   │              │   Code Agent     │
│  (CrewAI)       │              │   (Google ADK)   │
└─────────────────┘              └─────────────────┘
```

**Scenario**: Novel Generator
1. **Research Agent** (yamlgraph) → world-building material
2. **Writing Agent** (yamlgraph) → chapter generation
3. **Review Agent** (CrewAI) → editorial feedback
4. **Illustration Agent** (Replicate-backed) → art generation

Agents are independently deployable, discoverable, and replaceable.

### UC-3: Federated Graph Execution — Data Sovereignty

Graph nodes deployed on different machines/clouds. The orchestrator routes via A2A, unaware of location:

```yaml
nodes:
  eu_compliant_analysis:
    type: a2a_call
    agent_url: "https://eu-agent.internal:8080"
    skill: "gdpr-analysis"
    message: "Analyse {{ state.eu_data }}"
    state_key: eu_results

  us_market_analysis:
    type: a2a_call
    agent_url: "https://us-agent.internal:8080"
    skill: "market-analysis"
    message: "Analyse {{ state.us_data }}"
    state_key: us_results
```

**Value**: Data sovereignty, privacy compliance, distributed compute — managed in YAML.

### UC-4: Agent Discovery & Dynamic Routing

Discover agents at runtime and route based on Agent Card skills:

```yaml
nodes:
  find_agent:
    type: a2a_discover
    registry_url: "https://agents.internal/registry"
    query: "translation AND {{ state.target_language }}"
    state_key: translator_agent

  translate:
    type: a2a_call
    agent_url: "{{ state.translator_agent.url }}"
    skill: "{{ state.translator_agent.skill_id }}"
    message: "Translate: {{ state.text }}"
    state_key: translation
```

**Value**: Agents are resolved dynamically — swap providers, A/B test agents, failover to alternatives.

### UC-5: Handling Remote Multi-Turn (input_required)

When a remote agent returns `INPUT_REQUIRED`, the graph can handle it automatically:

```yaml
nodes:
  book_flight:
    type: a2a_call
    agent_url: "https://travel-agent.example.com"
    skill: "flight-booking"
    message: "Book me a flight from {{ state.origin }} to {{ state.destination }}"
    state_key: booking
    on_input_required: prompt_user  # or: auto_respond, fail

  prompt_user:
    type: interrupt
    state_key: user_response
```

The graph mediates between the remote agent's clarification requests and the human user.

### UC-6: Agent-as-a-Service Marketplace Consumption

Consume enterprise-published agents without knowing their implementation:

```yaml
nodes:
  compliance_check:
    type: a2a_call
    agent_url: "https://compliance.internal"
    skill: "gdpr-assessment"
    auth:
      scheme: bearer
      token_env: COMPLIANCE_API_TOKEN
    message: "Assess GDPR compliance for: {{ state.data_description }}"
    state_key: compliance_report
```

---

## Architecture

### `a2a_call` Node Type

```
graph.yaml
  └── node: type: a2a_call
        │
        ▼
  node_factory/a2a_nodes.py
        │
        ├── 1. Discover Agent Card (GET /.well-known/agent-card.json)
        ├── 2. Validate skill exists + input modes supported
        ├── 3. Build A2A Message from template + state
        ├── 4. SendMessage (or SendStreamingMessage)
        ├── 5. Handle response:
        │     ├── Task (COMPLETED) → extract artifacts → state_key
        │     ├── Task (INPUT_REQUIRED) → route to handler node
        │     ├── Task (WORKING) → poll/subscribe until terminal
        │     ├── Task (FAILED) → on_error strategy
        │     └── Message (direct) → extract parts → state_key
        └── 6. Return state update dict
```

### Node Configuration Schema

```yaml
# Full a2a_call node config
my_agent_call:
  type: a2a_call
  
  # Required
  agent_url: "https://agent.example.com"       # A2A server base URL
  message: "{{ state.input }}"                  # Jinja2 template for message text
  state_key: result                             # Where to store output
  
  # Optional — skill selection
  skill: "specific-skill-id"                    # Target specific skill
  
  # Optional — interaction mode
  streaming: false                              # Use SendStreamingMessage
  blocking: true                                # Wait for completion
  timeout: 120                                  # Seconds
  
  # Optional — auth
  auth:
    scheme: bearer                              # bearer, basic, apikey
    token_env: AGENT_API_TOKEN                  # Env var with credential
  
  # Optional — input enrichment
  input_parts:                                  # Additional message parts
    - type: data
      value: "{{ state.structured_input }}"
    - type: file
      url: "{{ state.document_url }}"
  
  # Optional — output handling
  output_mode: "application/json"               # Preferred output media type
  extract: "artifacts[0].parts[0].data"         # JSONPath to extract from result
  
  # Optional — error/multi-turn handling
  on_error: retry                               # skip, fail, retry, fallback
  on_input_required: fail                       # fail, prompt_user, auto_respond
  max_retries: 3
```

### Agent Card Caching

```
First call to agent_url:
  1. GET /.well-known/agent-card.json
  2. Cache by (url, version) tuple
  3. Validate skill exists
  4. Validate input/output modes

Subsequent calls:
  → Use cached Agent Card (honor version field)
```

### Three-Layer Pattern

```
┌─────────────────────────────────────┐
│  CLI / MCP / A2A Server             │ ← Presentation (unchanged)
├─────────────────────────────────────┤
│  YAML Graphs                        │ ← Logic layer
│  ┌───────────┐ ┌──────────────┐     │
│  │ LLM nodes │ │ a2a_call     │     │   ← NEW: A2A client nodes
│  └───────────┘ │ (remote call)│     │
│                └──────────────┘     │
├─────────────────────────────────────┤
│  Python Tools + LLMs + A2A SDK      │ ← Side effects
└─────────────────────────────────────┘
```

The `a2a_call` node lives in the logic layer (YAML) but its implementation in `node_factory/a2a_nodes.py` calls the A2A SDK in the side-effects layer.

---

## Implementation Plan

### Phase 1: Basic A2A Client Node (5-8 days)

**SDK**: `pip install a2a-sdk`

**New files:**
- `yamlgraph/node_factory/a2a_nodes.py` — `a2a_call` node type
- `yamlgraph/utils/a2a_client.py` — Agent Card discovery, message building, invocation

**Scope:**
- `a2a_call` node type in graph YAML
- Agent Card discovery and caching
- `SendMessage` (blocking) → extract artifacts → state_key
- Jinja2 message templating from state
- Bearer token auth from env var
- Error handling: `on_error` strategies (skip/fail/retry/fallback)

**Out of scope (Phase 1):**
- Streaming
- Multi-turn (`input_required` handling)
- Dynamic agent discovery (`a2a_discover`)
- File/binary parts
- gRPC transport

### Phase 2: Multi-Turn + Streaming (3-5 days)

- Handle `INPUT_REQUIRED` from remote agent
- `on_input_required` routing to interrupt nodes
- `SendStreamingMessage` support
- Task polling/subscription for async tasks
- Multiple message parts (text + data + file)

### Phase 3: Advanced Features (5-8 days)

- Dynamic agent discovery via registries
- `a2a_discover` node type
- Agent Card-based routing (skill matching)
- OAuth2/OIDC auth flows
- Map node integration (parallel A2A calls to multiple agents)
- Response caching
- Circuit breaker / failover patterns

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Network latency in graphs | Configurable timeout; async execution; map-node parallel calls |
| Remote agent unavailability | `on_error: fallback` to local LLM node |
| A2A SDK maturity | Isolate SDK usage in `utils/a2a_client.py`; easy to swap |
| Auth complexity | Phase 1 = bearer token only; OAuth in Phase 3 |
| Output format variability | `extract` field for JSONPath; Pydantic validation of results |
| Agent Card schema drift | Cache with version check; re-fetch on error |

## Open Questions

1. **Blocking vs. async invocation** — should `a2a_call` default to blocking (`blocking: true` in config)?
   → Recommendation: yes, blocking default (simpler mental model for YAML authors)
2. **How to handle binary artifacts** — file downloads, images from remote agents?
   → Recommendation: store URL in state; download only if needed by subsequent node
3. **Agent Card refresh** — how often to re-discover?
   → Recommendation: cache per graph invocation; force refresh via `refresh_card: true`
4. **Integration with map nodes** — parallel A2A calls?
   → Recommendation: Phase 3; `a2a_call` inside map subgraph works naturally
5. **Dependency**: Does this require A2A Provider first?
   → No. Consumer can call any external A2A agent independently.

---

## Comparison: a2a_call vs. Existing Node Types

| Feature | `llm` node | `tool` node | `a2a_call` node |
|---------|-----------|------------|----------------|
| Execution | Local LLM | Local Python | Remote A2A agent |
| Config | YAML | Python function | YAML |
| Output typing | Pydantic schema | Return dict | A2A Artifact → state_key |
| Streaming | Token-level | N/A | SSE events |
| Multi-turn | N/A | N/A | `input_required` handling |
| Error handling | `on_error` | `on_error` | `on_error` + `on_input_required` |
| Auth | LLM API key | N/A | A2A auth (bearer/OAuth) |
| Discovery | N/A | Function registry | Agent Card |

---

## References

- [a2a-protocol-brainstorm.md](a2a-protocol-brainstorm.md) — full protocol research
- [a2a-provider.md](a2a-provider.md) — YAMLGraph as A2A server
- [A2A Specification](https://a2a-protocol.org/latest/specification/)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)
- `yamlgraph/node_factory/` — existing node type patterns to follow
