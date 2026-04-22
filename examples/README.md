# YAMLGraph Examples

Example applications demonstrating YAMLGraph capabilities.

## Inclusion Criteria

Every listed example must have:
1. A `README.md` explaining what it does and how to run it
2. At least one runnable YAML graph (or a `demo.sh` / runnable Python script for demos that require programmatic setup)
3. A clear statement of which YAMLGraph feature it demonstrates

Examples that fail this bar are moved to `purgatory/` (see [purgatory/README.md](../purgatory/README.md)).

## 🎓 Learning Path

Start here and progress through the demos in order:

| Step | Demo | Concept | Time |
|------|------|---------|------|
| 1 | [demos/hello](demos/hello/) | Basic LLM node, variables | 5 min |
| 2 | [demos/router](demos/router/) | Conditional routing | 10 min |
| 3 | [demos/map](demos/map/) | Parallel fan-out | 15 min |
| 4 | [demos/reflexion](demos/reflexion/) | Self-correction loops | 15 min |
| 5 | [demos/git-report](demos/git-report/) | Tool-using agents | 15 min |
| 6 | [demos/interview](demos/interview/) | Human-in-the-loop | 15 min |
| 7 | [demos/subgraph](demos/subgraph/) | Graph composition | 20 min |

After the learning path, explore production examples below.

## Quick Reference

| Example | Description | Key Features |
|---------|-------------|--------------|
| [beautify/](beautify/) | Graph → HTML infographic | LLM analysis, Mermaid diagrams, Tailwind CSS |
| [book_translator/](book_translator/) | Translate books & documents | Map nodes, parallel translation, glossary, checkpointing |
| [booking/](booking/) | Appointment booking assistant | Interrupt nodes, tool nodes, multi-turn conversation |
| [bugfix/](bugfix/) | Bug-fix pipeline with condemning test | Copilot nodes, 4-phase workflow, TDD enforcement (FR-173) |
| [codegen/](codegen/) | Implementation agent | Tool nodes, code analysis, 24 Python tools |
| [cost-router/](cost-router/) | Multi-provider routing | Router nodes, Granite/Mistral/Claude |
| [daily_digest/](daily_digest/) | Scheduled news digest | Fly.io deployment, background tasks, email |
| [diary_digest/](diary_digest/) | Automated diary digest | Data files, feed topics, parallel processing (FR-046) |
| [ebook/](ebook/) | eBook authoring pipeline | File-based write→judge→amend pattern |
| [fsm-router/](fsm-router/) | FSM + YAMLGraph integration | statemachine-engine, LLM routing, job orchestration |
| [npc/](npc/) | D&D NPC generator | Multi-graph, map nodes, parallel NPCs |
| [ocr_cleanup/](ocr_cleanup/) | OCR text cleanup | Map nodes, PDF extraction, parallel LLM cleanup |
| [openai_proxy/](openai_proxy/) | OpenAI-compatible guardrail proxy | Echo→validate→respond pipeline, `/v1/chat/completions` |
| [philosopher/](philosopher/) | Chaplain philosopher workspace stub | Placeholder directory; active graph moved to `.chaplain/graphs/` |
| [questionnaire/](questionnaire/) | Feature request collector | Data files, interrupt loops, conditional routing |
| [rag/](rag/) | RAG pipeline | LanceDB vectorstore, document indexing, retrieval |
| [rtm-hello/](rtm-hello/) | TDD + requirement traceability | pytest markers, AST-based tooling |
| [storyboard/](storyboard/) | Visual story generator | Replicate API, image generation |
| [batch_image_prompts/](batch_image_prompts/) | Batch image prompt generator | Map node, parallel enrichment, style consistency |
| [image_pipeline/](image_pipeline/) | End-to-end image generation | Subgraph composition, Replicate z-image, file I/O |
| [yamlgraph_gen/](yamlgraph_gen/) | Pipeline generator | Meta-generation, snippet composition, validation |
| [fastapi_interview.py](fastapi_interview.py) | FastAPI integration | Async execution, interrupt handling, sessions |

> **Note:** Chaplain infrastructure (copilot, enforce, philosopher) relocated to `.chaplain/graphs/` per FR-196.

## Demos Index

### Learning Demos

Standalone demos that teach a single YAMLGraph concept. Ordered by the learning path, then alphabetically.

| Demo | Node Types | Description |
|------|------------|-------------|
| [hello](demos/hello/) | `llm` | Minimal example — start here |
| [router](demos/router/) | `router` | Tone-based conditional routing |
| [router-race-candidates](demos/router-race-candidates/) | `router`, `tool` | Router `candidates` race with default-route fallback (FR-272) |
| [map](demos/map/) | `map`, `llm` | Parallel fan-out processing |
| [reflexion](demos/reflexion/) | `llm` | Self-correction with loop limits |
| [research-agent](demos/research-agent/) | `agent`, `llm` | 5-step agentic research (extract → plan → execute → validate → respond) |
| [git-report](demos/git-report/) | `agent` | Git analysis with tools |
| [horoscope](demos/horoscope/) | `map`, `llm` | Parallel daily horoscope for 12 zodiac signs |
| [chatterbox](demos/chatterbox/) | `map`, `python` | Multilingual TTS with Chatterbox (5 languages → WAV) |
| [chatterbox_clone](demos/chatterbox_clone/) | `python` | Voice cloning with Chatterbox reference audio → WAV (FR-236) |
| [interview](demos/interview/) | `interrupt` | Human-in-the-loop |
| [subgraph](demos/subgraph/) | `subgraph` | Graph composition |
| [a2a_server](demos/a2a_server/) | `a2a` | A2A protocol server exposing graphs as agents (FR-208) |
| [a2a_call](demos/a2a_call/) | `a2a_call`, `llm` | Call an external A2A agent from a graph (FR-240) |
| [code-analysis](demos/code-analysis/) | `tool`, `llm` | Code quality tools |
| [data-files](demos/data-files/) | `llm` | External data loading |
| [diary-index](demos/diary_index/) | `map`, `python`, `llm` | Diary corpus cross-reference index (FR-254) |
| [feature-brainstorm](demos/feature-brainstorm/) | `agent` | Self-analysis |
| [fi_domain_crawl](demos/fi_domain_crawl/) | `map`, `python`, `llm` | .fi domain crawl + sitemap overview |
| [five-whys](demos/five-whys/) | `llm` | Fixed-count loop with iterative deepening |
| [innovation_matrix](demos/innovation_matrix/) | `llm` | Capability-constraint innovation matrix |
| [interactive_tool](demos/interactive_tool/) | `interactive_tool` | Multi-turn trivia quiz with user interrupts |
| [memory](demos/memory/) | `agent` | Multi-turn with memory |
| [multi-turn](demos/multi-turn/) | `interrupt`, `llm` | Multi-turn streaming with checkpoints (FR-028) |
| [novel_generator](demos/novel_generator/) | `llm`, `map` | Three-phase story generation with quality gates |
| [python-map](demos/python-map/) | `map`, `python` | Parallel Python tools |
| [python-variables](demos/python-variables/) | `python` | Variables expression resolution on python nodes (FR-252) |
| [map-timeout](demos/map-timeout/) | `map`, `python` | Per-branch timeout for map nodes (FR-069) |
| [safety-guards](demos/safety-guards/) | `llm`, `map` | Execution safety with recursion limits (FR-027) |
| [session-continuation](demos/session-continuation/) | `copilot` | Session persistence across runs |
| [soul](demos/soul/) | `llm`, `data_files` | Agent personality pattern |
| [streaming](demos/streaming/) | `llm` | Token-by-token output |
| [system-status](demos/system-status/) | `tool` | Shell tool execution |
| [tavily_rag](demos/tavily_rag/) | `python`, `llm` | Domain-specific RAG with Tavily retrieval |
| [thinking](demos/thinking/) | `llm` | Extended thinking with configurable depth (FR-071) |
| [verified-search](demos/verified-search/) | `agent`, `llm` | Evaluation-first search with verification |
| [web-research](demos/web-research/) | `agent` | Web search agent |
| [yamlgraph](demos/yamlgraph/) | `llm` | Multi-step pipeline |
| [cache](demos/cache/) | `llm` | Per-node result caching with CachePolicy (FR-032) |

### Utility Demos

Tools for codebase analysis — useful for maintainers, not for learning.

| Demo | Description |
|------|-------------|
| [pipeline_audit](demos/pipeline_audit/) | Cross-pipeline structural analysis |
| [req-cross-check](demos/req-cross-check/) | Architecture requirement traceability audit |
| [run-analyzer](demos/run-analyzer/) | Run output analysis utilities |

### FR Validation Demos

Used primarily to validate specific feature requests.

| Demo | FR | Description |
|------|-----|-------------|
| [interrupt](demos/interrupt/) | FR-006 | Subgraph interrupt integration tests |
| [verification-gate](demos/verification-gate/) | FR-164 | Deterministic post-execution verification gates |

> **Archived:** `commit-delta-gate` and `session-test` moved to `purgatory/` — see [purgatory/README.md](../purgatory/README.md).

## Running Examples

Most examples can be run with the CLI:

```bash
# From project root
yamlgraph graph run examples/<name>/graph.yaml --full
```

Or with specific variables:

```bash
yamlgraph graph run examples/npc/npc-creation.yaml \
  -v 'concept=grumpy dwarf blacksmith' --full
```

## By Feature

### Map Nodes (Parallel Processing)
- **book_translator/** - Parallel chapter translation and proofreading
- **npc/** - Multiple NPC encounters processed simultaneously
- **ocr_cleanup/** - Parallel page cleanup with LLM

### Router Nodes
- **cost-router/** - Route to different LLM providers by query complexity

### Tool Nodes
- **codegen/** - 24 code analysis tools (AST, grep, jedi)
- **yamlgraph_gen/** - Meta-generation with validation tools

### Guardrails (Input Validation)
- **openai_proxy/** - Echo → validate → respond pipeline as OpenAI-compatible proxy

### Interrupt Nodes (Human-in-the-Loop)
- **questionnaire/** - Interactive data collection with probe/recap loops
- **fastapi_interview.py** - Web-based multi-turn conversations

### Data Files (External Schema Loading)
- **questionnaire/** - Schema-driven field collection
- **demos/data-files/** - Simple data_files demonstration

### Soul Pattern (Agent Personality)
- **soul/** - Give AI agents consistent personality via data_files

### RAG (Retrieval-Augmented Generation)
- **rag/** - LanceDB vectorstore with document chunking

### External APIs
- **storyboard/** - Replicate image generation
- **daily_digest/** - Resend email, Hacker News API

### Deployment
- **daily_digest/** - Fly.io Docker deployment with GitHub Actions

## Shared Utilities

The `shared/` directory contains reusable tools:

- `replicate_tool.py` - Unified Replicate API wrapper for image generation

## Prerequisites

Each example has its own requirements. Common patterns:

```bash
# Core yamlgraph
pip install -e .

# With Replicate support (storyboard, cost-router)
pip install -e ".[replicate]"

# With RAG support (rag)
pip install -e ".[rag]"

# With digest extras (daily_digest)
pip install -e ".[digest]"
```

See individual example READMEs for specific setup instructions.
