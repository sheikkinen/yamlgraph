# Research: Agent-to-Agent Comms for Fact-Checking in novel_fandom

**Date:** 2026-07-03
**Context:** novel_fandom worldgen creates entities that reference non-existent IDs (ghosts like `kaelen`, `emberwrights` from Ashfall). The question: can an agent validate its own output by calling a fact-checking agent — and should that agent be a YAMLGraph pipeline disguised as a tool?

## The Two Protocols

### MCP (Model Context Protocol)
- **What:** Tool-level integration. Server exposes tools, resources, prompts. Client (LLM host) discovers and calls them.
- **Relationship:** Master-servant. The LLM decides when to call; the tool has no autonomy.
- **Strength:** IDE integration (Copilot, Cursor), typed tool schemas, real-time notifications.
- **Limitation:** Tools are stateless, request-response. No multi-turn negotiation. No peer-to-peer.
- **YAMLGraph already has:** `yamlgraph/mcp_server.py` — graphs exposed as MCP tools for Copilot.

### A2A (Agent-to-Agent Protocol)
- **What:** Peer-level integration. Agents discover each other via Agent Cards, exchange tasks via JSON-RPC.
- **Relationship:** Peer-to-peer. Either side can be autonomous. Multi-turn, streaming, task lifecycle.
- **Strength:** Agent Card discovery, skill matching, SSE streaming, `INPUT_REQUIRED` state.
- **Limitation:** Network overhead, HTTP transport, heavier setup.
- **YAMLGraph already has:** `yamlgraph/a2a_server.py` (serve graphs as agents), `yamlgraph/contrib/a2a_client.py` (call external agents from graphs).

### The Key Distinction
```
MCP:  LLM ──calls──> Tool (stateless, synchronous)
A2A:  Agent ──delegates──> Agent (stateful, multi-turn)
```

MCP is for tools that don't think. A2A is for agents that do.

## The Use Case: Fact-Checking During Entity Creation

**Problem:** When worldgen's `deepen` or `create_skeleton` nodes generate new entities, they may:
1. Reference IDs that don't exist in canon (red-link ghosts)
2. Contradict existing canon facts (birth_year conflicts, dead characters acting)
3. Produce schema-invalid output (consequences as string, missing valence)

**Current mitigation:** `ref_gate` checks orphan references post-generation. But it only checks presence, not semantic consistency.

### What a Fact-Checker Would Do

```
Input:  proposed entity (dict) + current canon (dict)
Output: { valid: bool, violations: [{field, expected, actual, severity}] }
```

Checks:
- All `references` resolve to existing canon IDs
- `birth_year` is consistent with referenced events
- Dead characters (referenced in death events) don't appear in new events post-death
- `faction` matches a faction ID
- `valence` is in the allowed enum
- `consequences` is list[str], not str
- Synopsis references premise

## Evaluation: Should YAMLGraph Be the Tool?

### Option A: Graph-as-MCP-Tool (transparent wrapping)

```yaml
# fact_check.yaml — a YAMLGraph pipeline
nodes:
  validate:
    type: llm
    prompt: fact_check_entity
    state_key: violations
```

Exposed via MCP: `yamlgraph_run_graph("fact_check.yaml", {entity: ..., canon: ...})`

An agentic `deepen` node calls it as a tool without knowing it's a subagent:
```yaml
deepen:
  type: agent
  tools:
    - fact_check  # ← this is actually a YAMLGraph pipeline
```

**Verdict:** This is the MCP pattern. The agent sees a tool, calls it, gets a result. The tool happens to be a full pipeline internally. **This already works** — MCP server exposes graphs as tools, and `type: agent` nodes can bind tools.

### Option B: Graph-as-A2A-Agent (explicit delegation)

```yaml
deepen:
  type: python
  tool: a2a_send
  variables:
    agent_url: "http://localhost:9241/"
    message: "Check entity: {state.drafted_entity}"
```

**Verdict:** Heavier. Requires running a separate A2A server. Useful for distributed systems, overkill for in-process fact-checking.

### Option C: Subgraph Node (native LangGraph)

```yaml
fact_check:
  type: subgraph
  graph: fact_check.yaml
```

**Verdict:** Already supported. No protocol overhead. But it's visible in the graph — the caller knows it's calling a subgraph.

### Option D: Deterministic Python Gate (no LLM)

```python
def fact_check_gate(state):
    entity = state["drafted_entity"]
    canon = state["canon"]
    violations = []
    for ref in entity.get("references", []):
        if ref not in canon:
            violations.append({"field": "references", "value": ref, "error": "orphan"})
    # ... more checks ...
    return {"gate_result": {"valid": not violations, "violations": violations}}
```

**Verdict:** For structural checks (orphan refs, type validation, enum values), this is fastest and most reliable. LLM adds nothing here.

## Recommendation

**Hybrid — Option D + Option A for semantic checks:**

| Check | Method | Why |
|-------|--------|-----|
| Orphan references | Python gate (D) | Deterministic, fast, already exists as `ref_gate` |
| Schema validation | Python gate (D) | `validate_page()` already exists |
| Birth year consistency | Python gate (D) | Arithmetic, not judgment |
| Dead-character contradiction | Python gate (D) | Cross-reference event death with new event participants |
| Tone/personality consistency | LLM via MCP tool (A) | Requires semantic understanding |
| Plot coherence | LLM via MCP tool (A) | Only for narrative judgment calls |

**The wrapping question:** Yes, YAMLGraph should be wrappable as a tool that an agent node calls without knowing it's a pipeline. This is exactly what MCP already does. The missing piece is **in-process invocation** — currently MCP requires a server process. A lighter pattern:

```yaml
# In the worldgen graph itself:
tools:
  coherence_check:
    type: graph
    path: coherence_check.yaml  # ← new tool type: invoke a graph as a tool
```

This would be a new tool type that calls `invoke_graph()` directly, no network, no MCP server. The agent sees a tool; the tool is a pipeline. **This is the FR to write.**

## Seed

If a graph can be a tool, can a tool be a graph? The `type: graph` tool would let any agent node compose pipelines without knowing the implementation. But the inverse — wrapping arbitrary tools as graphs — would let the pipeline system absorb any external capability. The convergence point: tools and graphs are the same thing at different abstraction levels. Which one should be primary?
