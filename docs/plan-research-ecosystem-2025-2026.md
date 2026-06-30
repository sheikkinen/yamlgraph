# Research: LLM/AI Agent Ecosystem Developments (2025-2026)

**Relevance to**: YAMLGraph — YAML-first LLM pipeline framework on LangGraph
**Date**: 2026-06-30
**Current LangGraph version**: 1.0.5 (latest: 1.2.7)

---

## 1. LangGraph New Features (1.0 → 1.2.7)

### Key Additions
| Feature | Version | Relevance |
|---------|---------|-----------|
| **v3 streaming** (SSE + WebSocket transports) | 1.2.3 | New streaming mode with projections — stream only messages or tool calls |
| **RemoteGraph v3 streaming** | 1.2.3 | Call remote LangGraph deployments with full stream fidelity |
| **`lc_agent_name`** for tool-dispatched subagents | 1.2.3 | Name subagents for better tracing |
| **DeltaChannel** improvements | 1.2.7 | Better state delta handling for complex graphs |
| **Interleave projections** | SDK 0.4.1 | Stream interleaved data from multiple subgraphs |
| **Messages + tool call projections** | SDK 0.4.0 | Select which parts of state to stream |
| **Factory graph pattern** | 1.2.4 | Dynamic graph construction at server startup |
| **LangGraph Platform (Cloud)** | 2025+ | Managed deployment with cron, webhooks, assistants API |

### Patterns Gaining Traction
- **Supervisor pattern** (`langgraph-supervisor`): Orchestrator delegates to specialized worker agents
- **Swarm pattern** (`langgraph-swarm`): Peer agents hand off to each other without central coordinator
- **Functional API**: `@task` and `@entrypoint` decorators for simpler graph definition
- **Command primitive**: `Command(goto=..., update=...)` for dynamic routing with state updates
- **Store API**: Cross-thread persistent memory (namespaced key-value)

### YAMLGraph Example Opportunity
```yaml
# Example: supervisor_swarm/graph.yaml
# Demonstrates: supervisor delegating to swarm of specialized agents
# New: type: supervisor node that routes to sub-agents by capability
# Libraries: langgraph>=1.2.0, langgraph-supervisor, langgraph-swarm
```

**Action**: Upgrade from 1.0.5 → 1.2.7. Add v3 streaming support, interleave projections, and Store API integration.

---

## 2. MCP (Model Context Protocol) — Latest Spec: 2025-11-25

### Major Developments Since 2025-06-18
| Feature | Status | Description |
|---------|--------|-------------|
| **Streamable HTTP transport** | Stable | Replaces deprecated SSE transport; supports polling + resumption |
| **Elicitation** | Stable | Servers request info from users mid-operation (forms, URL auth) |
| **Sampling with tool calling** | New (Nov 2025) | Servers invoke LLM with tool use via `tools` + `toolChoice` params |
| **Tasks (experimental)** | New (Nov 2025) | Durable async requests with polling + deferred result retrieval |
| **OAuth + OIDC Discovery** | New (Nov 2025) | Proper auth flows with incremental scope consent |
| **Icons for tools/resources** | New (Nov 2025) | Visual metadata for tool discovery UIs |
| **Tool name guidance** | New (Nov 2025) | Standardized naming conventions |
| **JSON Schema 2020-12** | Default | Schema standard for all MCP definitions |
| **Client ID Metadata Documents** | New | Recommended client registration mechanism |

### Ecosystem Growth
- **Supported clients**: Claude, ChatGPT, VS Code Copilot, Cursor, Windsurf, MCPJam
- **SDK tiers**: Formalized with clear requirements (Tier 1: full spec, Tier 2: common features)
- **OpenTelemetry for MCP**: Dedicated semantic conventions at `open-telemetry/semantic-conventions-genai`

### YAMLGraph Already Has
- `mcp_server.py` exposing graphs as MCP tools (CAP-19)
- A2A call node for agent-to-agent communication

### YAMLGraph Example Opportunity
```yaml
# Example: mcp_elicitation/graph.yaml
# Demonstrates: MCP server that uses elicitation to collect user input mid-pipeline
# Pattern: tool requests additional context → user provides → pipeline continues
# Libraries: mcp>=1.8.0 (streamable HTTP + elicitation)

# Example: mcp_tasks/graph.yaml
# Demonstrates: Long-running graph exposed as MCP task with polling
# Pattern: start task → return task_id → client polls → get result
# Libraries: mcp>=1.8.0
```

---

## 3. Structured Outputs — New Patterns

### Latest Developments
| Pattern | Library | Description |
|---------|---------|-------------|
| **Streaming structured output** | Pydantic AI v2.1 | Continuously validate partial JSON as it streams |
| **Streamed Pydantic** | `instructor>=1.7` | `client.chat.completions.create_partial()` yields validated partials |
| **Union type outputs** | OpenAI, Anthropic | `anyOf` schemas — model chooses between response types |
| **Discriminated unions** | Pydantic v2 | Route to different schemas based on a discriminator field |
| **Inline schemas from YAML** | YAMLGraph ✓ | Already supported |
| **DAG-based eval metrics** | DeepEval | Graph-structured deterministic evaluation criteria |
| **Agent spec in YAML/JSON** | Pydantic AI v2 | Define agents entirely in configuration — parallel to YAMLGraph |

### What's Changed for Structured Outputs
- **All major providers** now support native JSON schema constrained decoding
- **Streaming + validation** is the new standard (not just final output)
- **Multi-schema routing** — model selects output type based on input context
- **Anthropic** supports `tool_use` based structured output with streaming

### YAMLGraph Example Opportunity
```yaml
# Example: streaming_structured/graph.yaml
# Demonstrates: Stream validated Pydantic objects token-by-token
# Pattern: node produces partial schema → downstream nodes get updates in real-time
# New YAML feature: schema.streaming: true

# Example: union_output/graph.yaml
# Demonstrates: Model chooses between different output schemas
# Schema with anyOf: [PositiveReview, NegativeReview, NeutralReview]
# Libraries: langchain-core>=0.3, Pydantic v2
```

---

## 4. Multi-Agent Patterns

### Production Patterns (2025-2026)
| Pattern | Library | Description |
|---------|---------|-------------|
| **Supervisor** | `langgraph-supervisor` | Central orchestrator routes to worker agents |
| **Swarm/Handoff** | `langgraph-swarm`, OpenAI Agents SDK | Peer agents transfer control directly |
| **Agents as Tools** | OpenAI Agents SDK 0.17 | Treat any agent as a callable tool |
| **Sandbox Agents** | OpenAI Agents SDK 0.14+ | Agent with persistent workspace (filesystem, git) |
| **Capabilities** | Pydantic AI v2 | Composable bundles (tools + hooks + instructions) |
| **Durable Execution** | Pydantic AI v2 | Survive transient failures, resume on restart |
| **A2A Protocol** | Google | Agent-to-agent communication standard |
| **AG-UI** | Community | Agent-Generic UI streaming protocol |

### Key Insight
The ecosystem is converging on:
1. **Handoff** as the primitive (not message-passing)
2. **Human-in-the-loop** as first-class (not bolt-on)
3. **Sessions** for automatic conversation state management
4. **Guardrails** at input and output boundaries

### YAMLGraph Already Has
- A2A call node (CAP-101)
- Interrupt/resume (human-in-loop)
- Subgraph composition

### YAMLGraph Example Opportunity
```yaml
# Example: agent_swarm/graph.yaml
# Demonstrates: 3 specialized agents with handoff (no supervisor)
# Agents: researcher (web tools), coder (shell tools), reviewer (eval tools)
# Pattern: each agent decides who to hand off to next
# Libraries: langgraph>=1.2.0

# Example: guardrails_pipeline/graph.yaml
# Demonstrates: Input guardrail → agent → output guardrail pattern
# Pattern: pre-check rejects harmful input, post-check validates output safety
# Libraries: langgraph>=1.2.0
```

---

## 5. Evaluation/Testing Frameworks

### Current Landscape (2026)
| Framework | Version | Key Feature |
|-----------|---------|-------------|
| **DeepEval** | v4.0.5 | MCP metrics, DAG custom metrics, agentic metrics, G-Eval |
| **Ragas** | v0.4 | Experiment-first loop, agent evaluation, testset generation |
| **Braintrust** | — | Online evals, prompt playground, dataset management |
| **Promptfoo** | v0.100+ | Red-teaming, CI integration, provider comparison |
| **Pydantic Evals** | v2 (pydantic_evals) | Type-safe eval framework built into Pydantic AI |

### Notable Developments
- **DeepEval MCP metrics**: Evaluate MCP tool usage quality
- **DeepEval Agentic metrics**: Task completion, tool call accuracy, agent goal accuracy
- **Ragas Agent evaluation**: Tool call F1, topic adherence, goal accuracy
- **DAG metrics** (DeepEval): Build custom deterministic evaluation graphs
- **Promptfoo** now integrates with MCP servers for evaluation
- **All frameworks** now have LangGraph integration callbacks

### YAMLGraph Already Has
- `promptfoo-router` demo
- Verification gates (FR-164)

### YAMLGraph Example Opportunity
```yaml
# Example: deepeval_pipeline/graph.yaml
# Demonstrates: Self-evaluating pipeline — generate → evaluate → retry if below threshold
# Pattern: node generates output, eval node scores it, conditional retry
# Libraries: deepeval>=4.0, ragas>=0.4

# Example: eval_dataset_gen/graph.yaml
# Demonstrates: Synthetic test data generation for RAG evaluation
# Pattern: KG extraction → scenario generation → golden dataset output
# Libraries: ragas>=0.4
```

---

## 6. Voice/Audio AI

### Latest Developments
| Technology | Library/Service | Status |
|-----------|----------------|--------|
| **OpenAI Realtime API** (`gpt-realtime-2`) | OpenAI Agents SDK | Production — full agent features in voice |
| **Chatterbox TTS** | `chatterbox-tts` | Open-source, voice cloning, multilingual |
| **ElevenLabs Conversational AI** | `elevenlabs` | Low-latency voice agents with tool use |
| **Deepgram Nova-3** | `deepgram-sdk` | Real-time STT with <300ms latency |
| **AssemblyAI Universal-2** | `assemblyai` | Multilingual STT with speaker diarization |
| **Cartesia Sonic** | `cartesia` | Ultra-low latency TTS (< 100ms TTFB) |
| **Sesame CSM** | Open-source | Conversational speech model with emotional control |
| **Whisper Large v3 Turbo** | `openai-whisper` | 8x faster than v3 with minimal quality loss |
| **Gemini Audio** | `langchain-google-genai` | Native audio understanding + generation |

### Key Pattern: Voice Agent Pipeline
```
Audio In → STT → LLM Agent (with tools) → TTS → Audio Out
                     ↕
            Barge-in detection
            Silence detection
            Turn-taking logic
```

### YAMLGraph Already Has
- Chatterbox TTS demo (CAP-100)
- Voice cloning demo
- ninchat_voice project (full voice agent)

### YAMLGraph Example Opportunity
```yaml
# Example: realtime_voice_agent/graph.yaml
# Demonstrates: Full voice pipeline with barge-in and tool use
# Pattern: STT node → agent node (with MCP tools) → TTS node → audio stream
# Libraries: deepgram-sdk, openai (realtime), chatterbox-tts

# Example: audio_understanding/graph.yaml
# Demonstrates: Gemini processes audio directly (no STT step)
# Pattern: audio file → gemini multimodal → structured analysis
# Libraries: langchain-google-genai>=2.0
```

---

## 7. RAG Innovations

### Latest Techniques (2025-2026)
| Technique | Library | Description |
|-----------|---------|-------------|
| **Contextual Retrieval** | Anthropic pattern | Prepend document-level context to each chunk before embedding |
| **Late Chunking** | `jina-embeddings-v3` | Embed full doc, then split — preserves cross-chunk context |
| **ColBERT/ColPali** | `ragatouille`, `colpali` | Token-level interaction for better relevance |
| **Graph RAG** | `graphrag`, `neo4j` | Knowledge graph + vector search hybrid |
| **Agentic RAG** | LangGraph pattern | Agent decides when/what to retrieve, iterates |
| **Multi-query RAG** | YAMLGraph ✓ | Generate multiple queries for broader recall |
| **Hybrid search** | Mem0 v3 | Semantic + BM25 + entity matching fused |
| **Reranking** | Cohere Rerank v3, Jina | Post-retrieval relevance scoring |
| **Anthropic Citations** | Anthropic API | Model returns source citations with spans |
| **Late Interaction** | ColBERT | Per-token similarity scoring at retrieval time |

### YAMLGraph Already Has
- `tavily_rag` and `tavily_deep_rag` demos
- Basic RAG example with ChromaDB

### YAMLGraph Example Opportunity
```yaml
# Example: contextual_rag/graph.yaml
# Demonstrates: Contextual retrieval — add context to chunks before indexing
# Pattern: document → chunk → contextualize (LLM adds doc context to each chunk) → embed → store
# Libraries: chromadb, langchain-anthropic

# Example: graph_rag/graph.yaml
# Demonstrates: Knowledge graph extraction → graph traversal → answer synthesis
# Pattern: extract entities/relations → store in graph → query via Cypher + vector
# Libraries: neo4j, langchain-community

# Example: agentic_rag/graph.yaml
# Demonstrates: Agent decides retrieval strategy (single-shot vs multi-hop vs decompose)
# Pattern: query analysis → routing → retrieval → evaluation → retry/synthesize
# Libraries: langgraph>=1.2.0, chromadb
```

---

## 8. New Model Capabilities

### Major Developments
| Capability | Provider | Impact |
|-----------|----------|--------|
| **Extended thinking** | Claude 3.5+, DeepSeek-R1, Gemini 2.5 | Explicit reasoning traces before answer |
| **Computer use** | Claude, OpenAI | Agents control browser/desktop |
| **Native tool use** | All major providers | Function calling is table-stakes |
| **Vision + audio** | Gemini 2.5, GPT-4o | Multimodal inputs (images, audio, video) |
| **Code execution** | Gemini, OpenAI | Sandboxed code running during inference |
| **Streaming tool use** | Anthropic, OpenAI | Tool calls stream as they're generated |
| **Parallel tool calling** | OpenAI, Anthropic | Multiple tool calls in single response |
| **Structured output** with streaming | All providers | JSON schema constrained + streamed |
| **Citation generation** | Anthropic, Google | Model cites sources inline |
| **Context caching** | Anthropic, Google | Cache large system prompts for cost reduction |

### YAMLGraph Already Has
- Extended thinking demo (FR-071)
- Prompt caching demo (CAP-131)
- Multi-provider support

### YAMLGraph Example Opportunity
```yaml
# Example: computer_use/graph.yaml
# Demonstrates: Agent uses computer_use tool to interact with web pages
# Pattern: task → plan → computer_use actions → screenshot → evaluate → repeat
# Libraries: langchain-anthropic (computer_use tool)

# Example: multimodal_pipeline/graph.yaml
# Demonstrates: Image/audio input → multimodal analysis → structured output
# Pattern: image upload → vision model describes → text model synthesizes
# Libraries: langchain-openai, langchain-google-genai

# Example: parallel_tools/graph.yaml
# Demonstrates: Model calls multiple tools simultaneously
# Pattern: single LLM call → 3 parallel tool executions → aggregated response
# Libraries: langgraph>=1.2.0
```

---

## 9. Observability

### Current State
| Platform | Key Feature | Integration |
|----------|-------------|-------------|
| **LangSmith** | LangGraph native tracing | Built-in with LangGraph |
| **Pydantic Logfire** | OpenTelemetry-native, AI-first | Pydantic AI integration |
| **OpenTelemetry GenAI SemConv** | Standardized spans/metrics for LLM | Moved to `semantic-conventions-genai` repo |
| **Arize Phoenix** | Open-source, local tracing | LangChain callback |
| **Weights & Biases Weave** | Experiment tracking + evals | LangChain integration |

### OpenTelemetry GenAI Semantic Conventions (v1.42.0)
Now includes dedicated conventions for:
- **Agent spans** (`gen_ai.agent.*`)
- **MCP spans** (`gen_ai.mcp.*`)
- Provider-specific: Anthropic, OpenAI, Azure AI, AWS Bedrock
- **Metrics**: Token usage, latency, error rates
- **Events**: Chat completions, tool calls, content generation

### Key Trend
**OpenTelemetry is winning** as the standard. LangSmith, Logfire, Arize, Datadog all accept OTel traces. The smart play is emit OTel and let users pick their backend.

### YAMLGraph Already Has
- LangSmith tracing (CAP-13)
- YAMLGRAPH_OTEL_DIR per-node file exporter

### YAMLGraph Example Opportunity
```yaml
# Example: otel_tracing/graph.yaml
# Demonstrates: Full OTel instrumentation with GenAI semantic conventions
# Pattern: each node emits OTel spans with gen_ai.* attributes
# Libraries: opentelemetry-sdk, opentelemetry-instrumentation-langchain

# Example: cost_tracking/graph.yaml
# Demonstrates: Per-node cost tracking and budget gates
# Pattern: token counter accumulates → budget check → halt if exceeded
# Libraries: langgraph>=1.2.0, opentelemetry-sdk
```

---

## 10. Memory Systems

### Landscape (2026)
| System | Version | Key Feature |
|--------|---------|-------------|
| **Mem0** | v3.0 (April 2026 algo) | Single-pass extraction, entity linking, temporal reasoning |
| **LangGraph Store** | Built-in | Cross-thread namespaced key-value store |
| **Zep** | v2 | Fact extraction + temporal knowledge graph |
| **Letta (MemGPT)** | v0.6 | Self-editing memory with memory hierarchy |
| **LangMem** | langchain-ai | Memory formation from conversations |

### Mem0 v3 Algorithm (April 2026) — Major Breakthrough
- **91.6** on LoCoMo benchmark (+20 pts over v2)
- **94.8** on LongMemEval (+27 pts)
- **Single-pass ADD-only extraction** — one LLM call, no UPDATE/DELETE
- **Entity linking** across memories
- **Multi-signal retrieval**: semantic + BM25 + entity matching
- **Temporal reasoning** — time-aware retrieval

### LangGraph Store API
- **Namespaced key-value** storage across threads
- **Semantic search** over stored memories
- **TTL** for automatic expiration
- Built into LangGraph Platform deployments

### YAMLGraph Already Has
- `memory_demo` example (multi-turn with memory)
- Checkpointing (SQLite, Redis)

### YAMLGraph Example Opportunity
```yaml
# Example: mem0_memory/graph.yaml
# Demonstrates: Conversation with persistent user memory via Mem0
# Pattern: retrieve memories → inject into prompt → generate → extract new memories
# Libraries: mem0ai>=2.0, langgraph>=1.2.0

# Example: langgraph_store/graph.yaml
# Demonstrates: Cross-conversation memory using LangGraph Store API
# Pattern: agent stores facts → next conversation retrieves relevant facts
# Libraries: langgraph>=1.2.0 (built-in store)

# Example: episodic_memory/graph.yaml
# Demonstrates: Agent with episodic + semantic memory layers
# Pattern: short-term (thread state) + episodic (recent events) + semantic (facts)
# Libraries: langgraph>=1.2.0, chromadb
```

---

## Priority Recommendations for YAMLGraph

### High Priority (immediate value, low effort)
1. **Upgrade LangGraph to 1.2.7** — 1.0.5 is 7 months behind. Critical streaming improvements.
2. **v3 streaming support** — Expose projections (messages-only, tool-calls-only) in YAML config
3. **Store API integration** — Add `store:` section to graph.yaml for cross-thread memory
4. **OTel GenAI semconv** — Emit standardized agent/MCP spans

### Medium Priority (valuable, moderate effort)
5. **MCP elicitation/tasks** — Update MCP server to spec 2025-11-25
6. **Agentic RAG example** — Agent-driven retrieval with iterative refinement
7. **DeepEval integration** — YAML-configured evaluation nodes
8. **Mem0 integration** — Memory tool for persistent user state
9. **Supervisor/swarm patterns** — New node types for multi-agent orchestration

### Lower Priority (exploratory)
10. **Computer use** — Anthropic's tool in a graph pipeline
11. **Graph RAG** — Knowledge graph extraction + retrieval
12. **Streaming structured output** — Partial schema validation during stream
13. **Pydantic AI interop** — YAMLGraph graphs callable from Pydantic AI capabilities

---

## Competitive Landscape Note

**Pydantic AI v2** (released last week, v2.1.1) is the most direct competitor to YAMLGraph's positioning:
- Agents defined in **YAML/JSON** (new "agent spec" feature)
- **Graph support** via `pydantic_graph` (type-hinted node graphs)
- **Capabilities** = composable tool/hook bundles (≈ YAMLGraph's tool system)
- **Durable execution** (≈ YAMLGraph's checkpointing)
- 18.1k stars, 511 contributors, backed by Pydantic team

**Differentiation for YAMLGraph**:
- YAMLGraph's graph YAML is more expressive (routing, conditions, loops, map, race)
- YAMLGraph has a deeper prompt template system (Jinja2, inline schemas)
- YAMLGraph's MCP server exposes graphs directly as tools
- YAMLGraph's pipeline audit / verification gate patterns are unique
