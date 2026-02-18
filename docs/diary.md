# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-17.md](diary-2026-02-17.md) — 10 entries, 10 named traps, one insight: every trap is an unasked verification question.

---

## 2026-02-18: Tool Reflection — When the Hammer Looks for Nails

**Context:** After the diary rotation, asked: "are there tools to propose — either for yamlgraph or metacognition?" Surveyed all ~35 MCP-exposed graphs. Existing meta-tools: `feature-brainstorm` (agent reads codebase, researches web, proposes, prioritizes), `run-analyzer` (post-mortem via LangSmith traces), `code-analysis` (static quality: ruff/radon/vulture/bandit/coverage).

**The inventory of what I almost proposed:**

| Candidate | Verdict | Why not |
|-----------|---------|---------|
| Verification question generator | No | One-line heuristic, not a tool. "Name the verification question" is a mental pause, not an LLM call. |
| Diary trap matcher | No | 10-entry lookup table. A cheat sheet, not a pipeline. |
| FR evidence checker | No | It's `grep`. |
| FR judgment assistant | No | Judgment is the human's job. Automating it defeats the purpose. |
| Metacognitive dashboard | No | Performative meta-recursion. Generates observations about observations. |

**What survived: one new tool, one approved FR to build.**

1. **Pipeline audit** (new graph, built today): Cross-pipeline structural analysis — quality gate coverage, silent fallback census, `on_error:skip` without reporting, shared pattern detection. This is the work I did manually in "The Constraint Shift" (3,000 words, ~2 hours surveying 10 pipelines). The graph does it in one command: `yamlgraph graph run examples/demos/pipeline-audit/graph.yaml`. Three Python tools scan all graph YAMLs and Python nodes, then two LLM nodes analyze and recommend. Smoke test: found 87 graphs, 333 nodes, 18 `on_error:skip`, 32 map nodes, 8 quality gate nodes.

2. **FR-043 Evaluation framework** (already approved, not built): The gap between "generate 81 lessons" and "know if they're good." The diary's constraint shift entry identified this as the primary bottleneck. The pipeline audit tool surfaces *where* evaluation is missing; FR-043 provides *what* to do about it.

**The trap I caught:** **Tool-solution bias.** When you build tools for a living, every insight looks like it needs a tool. But three of the five metacognitive candidates were heuristics (one-liners), one was a lookup table, and one was `grep`. The verification question — "does this need to be a pipeline, or is it a sentence?" — killed 5 of 7 candidates.

**The useful distinction:** A tool is justified when the work is (a) tedious to do manually, (b) needs to be repeated, and (c) benefits from LLM analysis beyond what `grep` provides. The pipeline audit passes all three: manually surveying 87 graphs for structural patterns took hours; it needs re-running as the ecosystem grows; pattern detection across graphs is genuinely analytical. The metacognitive candidates fail (b) — you name the trap once and remember it.

**What the audit graph covers:**
- `scan_graphs_tool`: parses all graph YAMLs, extracts node types, edges, `on_error` settings, quality gate presence, loops
- `scan_python_nodes_tool`: scans Python node/tool files for silent fallbacks (`bare except`, `or []`), inline `model_dump`, manual `.get('result')`
- `count_patterns_tool`: aggregate counts across all graphs (18 skip, 32 map, 8 quality gates, etc.)
- LLM analyze: structural issues, gap analysis, risk rating
- LLM recommend: prioritized, actionable improvements grouped by effort

**Heuristic:** Before proposing a tool, ask: "Is this a pipeline or a sentence?" If the insight fits in one line of documentation, it's a heuristic, not a tool. If it requires scanning N files and synthesizing patterns, it's a tool.

**Meta-heuristic:** The existing meta-tools (feature-brainstorm, run-analyzer, code-analysis) cover ideation, post-mortem, and static quality. The pipeline audit fills the structural health gap — the space between "does the code pass lint" and "does the pipeline architecture make sense." FR-043 will fill the output quality gap — "is what the pipeline produces any good." After that, the meta-tool inventory is complete. Further proposals should clear a high bar.

---

## 2026-02-18: Protocol Archaeology — Ninchat Integration Research

**Context:** Asked to research Ninchat (customer chat platform) integration for a healthcare chatbot RAG source. Given: cloned repos (`ninchat-go`, `ninchat-nodejs`, `hello-bot`), raw planning notes with bot credentials.

**Research method:** Protocol archaeology — reading SDK source to extract protocol-level understanding.

**What I excavated:**

| Layer | Source | Key Finding |
|-------|--------|-------------|
| Transport | `ninchat-go/websocket_go.go` | WSS primary (`wss://api.ninchat.com/v2/socket`), HTTP polling fallback |
| Session | `ninchat-go/session.go` | Action/event protocol, 724-line state machine |
| Messages | `ninchat-go/ninchatmessage/text.go` | JSON frame format: `{"text": "content"}` |
| Bot framework | `ninchat-nodejs/Bot.md` | Event-driven: `begin`, `messages`, `end`, `transfer` |
| Auth | planning notes | Email/password → `create_session` → `session_id` |
| Metadata | Bot.md | `audience.secureMetadata` — encrypted auth context |

**The key architectural insight:** Ninchat's `secureMetadata` is the critical RAG context for healthcare. It contains authenticated identity (patient ID, auth tokens) that cannot be spoofed by the web widget. This is what connects the chat session to existing patient records in Vertex AI.

**What I built:**
1. `projects/ninchat/docs/ninchat-integration-whitepaper.md` — white paper level documentation covering protocol, message types, bot framework, security model, YAMLGraph integration architecture
2. `projects/ninchat/ninchat_tool.py` — skeleton tool implementation showing `NinchatClient`, context extraction, message handling

**The trap I avoided:** **Premature implementation.** The SDK source was Go/Node.js, not Python. Rather than build a full Python WebSocket client from first principles, I created a well-documented skeleton that shows the architecture. The actual implementation can wait for when the integration is prioritized. Research first, build when validated.

**Heuristic:** When researching external systems, read the SDK source — not the marketing docs. The protocol-level truth is in the transport layer code. Look for: (1) endpoint URLs, (2) authentication flow, (3) message framing, (4) error handling.

**What's ready for implementation:**
- Protocol fully documented
- Tool architecture designed
- Security model understood (`secureMetadata` for auth context)
- YAML graph pattern defined for Ninchat-as-RAG

**What's deferred:**
- Full async WebSocket client
- Event loop for real-time message handling
- Multiple queue support
- Production reconnection logic

---

## 2026-02-18: A2A Protocol Research — The Interoperability Layer

**Context:** Research the Google-originated A2A (Agent-to-Agent) protocol and brainstorm YAMLGraph use cases.

**Research scope:** Full specification (RC v1.0) — 14 sections covering data model, 3 protocol bindings (JSON-RPC, gRPC, HTTP+REST), Agent Cards, task lifecycle, streaming, push notifications, security, extensions.

**Key architectural insight:** A2A occupies a different layer than MCP. MCP = agent↔tools (internal capability access). A2A = agent↔agent (external peer collaboration). They compose naturally: a YAMLGraph agent uses MCP internally to call tools, and exposes itself via A2A for other agents to discover and invoke.

**The mapping that clicked:** YAMLGraph's existing abstractions map almost 1:1 to A2A concepts:

| A2A | YAMLGraph | Notes |
|-----|-----------|-------|
| Agent Card | Graph YAML metadata | `name`, `description`, `state` → skills, input/output modes |
| Task lifecycle | Graph invocation + checkpointers | `submitted/working/completed` = `invoke()` lifecycle |
| `input_required` | `interrupt_before` | The exact same pattern — wait for human/client input |
| Artifact | Final state output | Pydantic-typed results → structured JSON Parts |
| Streaming | `executor_async` SSE | Already have token + node-level streaming |
| Skill | Individual graph | Each graph YAML defines one capability |

**The strategic observation:** YAMLGraph already has an MCP server (CAP-19) that auto-discovers graphs and exposes them as tools. An A2A server is architecturally the same pattern — discover graphs, generate metadata, expose via protocol. The `discover_graphs()` and `_invoke_graph()` functions from `mcp_server.py` can be reused almost directly.

**Brainstorm output:** 10 use cases documented in `docs-planning/a2a-protocol-brainstorm.md`. The high-value, low-effort ones:
1. **A2A Server** — `yamlgraph a2a serve` exposes all graphs as A2A skills (reuses MCP server pattern)
2. **Agent Card CLI** — `yamlgraph graph agent-card` generates discoverable metadata from YAML
3. **A2A Client node** — `type: a2a_call` in graph YAML lets graphs invoke external agents

**The trap I watched for:** **Protocol fascination.** A2A spec is massive (14 sections, 3 bindings, extensions, signing, etc.). The temptation is to implement everything. But the 80/20 is clear: JSON-RPC binding + Agent Card + SendMessage covers most use cases. gRPC, push notifications, JWS signing, and multi-tenant are Phase 3 concerns.

**Heuristic:** When mapping a new protocol to existing architecture, start from your existing abstractions and find where they naturally align. Don't start from the protocol spec and try to build new abstractions. The mapping from `discover_graphs()` → Agent Card and `interrupt_before` → `input_required` was immediate because it matched existing code, not because I designed for A2A.

**Decision deferred:** Whether to proceed to FR and implementation. The brainstorm document provides enough context for informed decision-making.
