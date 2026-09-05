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
| [abstraction_span/](abstraction_span/) | LLM-scored prompt abstraction-span + separation gate | Map node, python tools, inline schema, deterministic gate (FR-589) |
| [agent-sdk-planner/](agent-sdk-planner/) | Standalone FR planner spike | Anthropic Agent SDK, custom tools, PostToolUse audit hooks |
| [beautify/](beautify/) | Graph → HTML infographic | LLM analysis, Mermaid diagrams, Tailwind CSS |
| [book_translator/](book_translator/) | Translate books & documents | Map nodes, parallel translation, glossary, checkpointing |
| [book_reviewer/](book_reviewer/) | Critique a manuscript (decomposed map→reduce) | Map nodes, computed scores, anti-"almighty-prompt" K4 gate |
| [booking/](booking/) | Appointment booking assistant | Interrupt nodes, tool nodes, multi-turn conversation |
| [bugfix/](bugfix/) | Bug-fix pipeline with condemning test | Copilot nodes, 4-phase workflow, TDD enforcement (FR-173) |
| [codegen/](codegen/) | Implementation agent | Tool nodes, code analysis, 24 Python tools |
| [cost-router/](cost-router/) | Multi-provider routing | Router nodes, Granite/Mistral/Claude |
| [cwe-classifier/](cwe-classifier/) | CVE→CWE weakness coding | Coded-classification pattern 2nd instance, NVD gold labels, MITRE usage caps (FR-733) |
| [api-discovery/](api-discovery/) | API discovery pipeline | Shared tool manifests, agent steps, orchestrator routing (FR-783..FR-791) |
| [daily_digest/](daily_digest/) | Scheduled news digest | Fly.io deployment, background tasks, email |
| [diary_digest/](diary_digest/) | Automated diary digest | Data files, feed topics, parallel processing (FR-046) |
| [discord_bot/](discord_bot/) | Discord `/hello` slash command | Gateway bot, defer/followup, pure adapter slice, async graph seam (FR-812) |
| [dungeon_master/](dungeon_master/) | Interactive DM turn loop | Interrupt loop, parallel character planning (map), conditional-to-map routing (FR-466/467) |
| [ebook/](ebook/) | eBook authoring pipeline | File-based write→judge→amend pattern |
| [fsm-router/](fsm-router/) | FSM + YAMLGraph integration | statemachine-engine, LLM routing, job orchestration |
| [icpc-2-rfe/](icpc-2-rfe/) | ICPC-2 Reason-for-Encounter classifier | Cluster map fan-out, generated Tier-1 catalog (never committed), deterministic reducer (FR-722) |
| [memory-curation/](memory-curation/) | Memory-corpus selective amnesia | Frozen-snapshot collect, map-node judgement (keep/redact/forget), hash-gated apply (FR-875) |
| [npc/](npc/) | D&D NPC generator | Multi-graph, map nodes, parallel NPCs |
| [novel_fandom/](novel_fandom/) | Fiction canon management | Typed canon schema, ref gate, lane immutability (FR-637) |
| [ocr_cleanup/](ocr_cleanup/) | OCR text cleanup | Map nodes, PDF extraction, parallel LLM cleanup |
| [openai_proxy/](openai_proxy/) | OpenAI-compatible guardrail proxy | Echo→validate→respond pipeline, `/v1/chat/completions` |
| [philosopher/](philosopher/) | Chaplain philosopher workspace stub | Placeholder directory; active graph moved to `.chaplain/graphs/` |
| [plot_modeller/](plot_modeller/) | L4 kind-classification spike | LLM→validator→retry loop, YAML output, ground-truth evaluation (FR-570) |
| [questionnaire/](questionnaire/) | Feature request collector | Data files, interrupt loops, conditional routing |
| [rag/](rag/) | RAG pipeline | LanceDB vectorstore, document indexing, retrieval |
| [route_overlay_cli/](route_overlay_cli/) | Route overlay rendering CLI example | Direct Mermaid export APIs, route validation, mmdc rendering |
| [rtm-hello/](rtm-hello/) | TDD + requirement traceability | pytest markers, AST-based tooling |
| [storyboard/](storyboard/) | Visual story generator | Replicate API, image generation |
| [batch_image_prompts/](batch_image_prompts/) | Batch image prompt generator | Map node, parallel enrichment, style consistency |
| [image_pipeline/](image_pipeline/) | End-to-end image generation | Subgraph composition, Replicate z-image, file I/O |
| [image_pipeline_v2/](image_pipeline_v2/) | Critic-filtered image generation (FR-879) | Frozen local critic vs LLM-judge, cross-repo scorer subprocess, top-k spend cap |
| [image_pipeline_v3/](image_pipeline_v3/) | Local-model-generated prompts (FR-881) | No-LLM graph, trained 3.3M-param generator subprocess, boundary-gated first-k selection |
| [style_convert/](style_convert/) | Restyle a prompt file to a target art style | Map node, Mistral, count-preserving, reuses image_pipeline save node |
| [surplus/](surplus/) | Retained research instruments and evidence | Reproducible map/reduce research artifacts |
| [webllm-demo/](webllm-demo/) | Prompt YAML → in-browser WebLLM | Inline-schema → JSON Schema compile, grammar-enforced output, zero-key Pages demo (FR-731) |
| [yamlgraph_gen/](yamlgraph_gen/) | Pipeline generator | Meta-generation, snippet composition, validation |
| [fastapi_interview.py](fastapi_interview.py) | FastAPI integration | Async execution, interrupt handling, sessions |

> **Note:** Chaplain infrastructure (copilot, enforce, philosopher) relocated to `.chaplain/graphs/` per FR-196.

## Demos Index

### Learning Demos

Standalone demos that teach a single YAMLGraph concept. Ordered by the learning path, then alphabetically.

| Demo | Node Types | Description |
|------|------------|-------------|
| [hello](demos/hello/) | `llm` | Minimal example — start here |
| [hello-runpod](demos/hello-runpod/) | `llm` | Hello via the RunPod OpenAI-compatible provider (FR-766) |
| [hellograph-speed](demos/hellograph-speed/) | `llm` | Provider latency comparison across Google, Vertex, and Azure |
| [router](demos/router/) | `router` | Tone-based conditional routing |
| [router-race-candidates](demos/router-race-candidates/) | `router`, `tool` | Router `candidates` race with default-route fallback (FR-272) |
| [promptfoo-router](demos/promptfoo-router/) | `router` | Promptfoo evaluation suite for tone router (FR-299) |
| [map](demos/map/) | `map`, `llm` | Parallel fan-out processing |
| [req_witness_audit](demos/req_witness_audit/) | `map`, `llm`, `python` | Requirement-witness batch grading — plausibility verdicts with deterministic post-map reconciliation (FR-851) |
| [file-hook](demos/file-hook/) | `tool_call`, `map` | macOS launchd WatchPaths hook — vision-described artwork publishing with confidence gate (FR-781) |
| [self-portrait](demos/self-portrait/) | `python`, `interrupt`, `llm` | macOS PersonalizationPortrait → typed rows → exact-payload consent gate → agent-first self-portrait JSON (FR-782) |
| [reflexion](demos/reflexion/) | `llm` | Self-correction with loop limits |
| [research-agent](demos/research-agent/) | `agent`, `llm` | 5-step agentic research (extract → plan → execute → validate → respond) |
| [git-report](demos/git-report/) | `agent` | Git analysis with tools |
| [graph-tool](demos/graph-tool/) | `agent`, `graph` | Agent using a graph pipeline as an opaque tool (FR-658) |
| [guards](demos/guards/) | `llm` | Deterministic pre/post node guards with explicit policy (FR-344) |
| [horoscope](demos/horoscope/) | `map`, `llm` | Parallel daily horoscope for 12 zodiac signs |
| [chinese-horoscope](demos/chinese-horoscope/) | `map`, `llm` | Parallel daily horoscope for the 12 Chinese zodiac animals |
| [corpus_census](demos/corpus_census/) | `slot`, `map`, `python` | Discover–extract–map–reduce census pipeline with invocation-time tool slots (FR-892) |
| [pattern_model_census](demos/pattern_model_census/) | `slot`, `map`, `python` | Mercury-pinned architectural-pattern + LLM-model census over commit metadata only (FR-896) |
| [repo_census](demos/repo_census/) | `slot`, `map`, `python` | Azure-pinned GitHub org repository census — purpose/persons/activity ledger with preflight-gated gh discovery (FR-899) |
| [person_profile_census](demos/person_profile_census/) | `slot`, `map`, `python` | Azure-pinned GitHub authored-PR person profile census — classifies each PR, mechanical rollups + FR-895 URL-cited brief (FR-962) |
| [cap_journey_census](demos/cap_journey_census/) | `map`, `python` | Capability-registry census — per-CAP customer journey (closed catalog), blast kind, keep/retire/extend disposition, value proposition; LLM-free reduce with canary gate (docs/2026-09-05-research-plan-cap-journey-census.md) |
| [image-that-speaks](demos/image-that-speaks/) | `race`, `python`, `llm` | Adversarial content audit — model-judging-model blindness (FR-666) |
| [chatterbox](demos/chatterbox/) | `map`, `python` | Multilingual TTS with Chatterbox (5 languages → WAV) |
| [chatterbox_clone](demos/chatterbox_clone/) | `python` | Voice cloning with Chatterbox reference audio → WAV (FR-236) |
| [interview](demos/interview/) | `interrupt` | Human-in-the-loop |
| [subgraph](demos/subgraph/) | `subgraph` | Graph composition |
| [code-analysis](demos/code-analysis/) | `tool`, `llm` | Code quality tools |
| [compaction](demos/compaction/) | `llm`, `python` | Context compaction pattern with guard-gated summarization (FR-616) |
| [data-files](demos/data-files/) | `llm` | External data loading |
| [write_data_file](demos/write_data_file/) | `llm`, `python` | Accumulating world bible via read→augment→write-back (FR-626) |
| [wiki-memory](demos/wiki-memory/) | `llm`, `python` | Wiki with reference-integrity gate and inter-run state (FR-628) |
| [diary-index](demos/diary_index/) | `map`, `python`, `llm` | Diary corpus cross-reference index (FR-254) |
| [enforcer](demos/enforcer/) | `agent` | Standalone FR implementation agent (FR-462) — completes plan→judge→enforce trilogy |
| [feature-brainstorm](demos/feature-brainstorm/) | `agent` | Self-analysis |
| [forensic-failure-diary](demos/forensic-failure-diary/) | `llm`, `tool` | Automated failure analysis with structured diary generation (FR-285) |
| [fi_domain_crawl](demos/fi_domain_crawl/) | `map`, `python`, `llm` | .fi domain crawl + sitemap overview |
| [five-whys](demos/five-whys/) | `llm` | Fixed-count loop with iterative deepening |
| [fr-atlas](demos/fr-atlas/) | `python`, `map`, `llm` | Feature-request corpus → newcomer-facing themed atlas with coverage guarantee (FR-748) |
| [innovation_matrix](demos/innovation_matrix/) | `llm` | Capability-constraint innovation matrix |
| [interactive_tool](demos/interactive_tool/) | `interactive_tool` | Multi-turn trivia quiz with user interrupts |
| [judge](demos/judge/) | `agent` | Standalone FR judgment agent (FR-450) — evaluates FRs before enforcement |
| [memory](demos/memory/) | `agent` | Multi-turn with memory |
| [book-summary](demos/book-summary/) | `tool_call`, `map`, `llm` | PDF → per-page summaries → book summary via shared document splitter manifest (FR-773) |
| [meta](demos/meta/) | `tool`, `llm` | Apply a natural-language verb to a code artifact, including its own YAML (FR-464) |
| [multi-turn](demos/multi-turn/) | `interrupt`, `llm` | Multi-turn streaming with checkpoints (FR-028) |
| [typescript-node](demos/typescript-node/) | `python` | Cross-runtime: Node.js/TypeScript subprocess calls `yamlgraph graph run --json` (FR-375) |
| [novel_generator](demos/novel_generator/) | `llm`, `map` | Three-phase story generation with quality gates |
| [persona_scenarios](demos/persona_scenarios/) | `map`, `python`, `llm` | Persona & scenario generation with interlinked markdown output (FR-461) |
| [planner](demos/planner/) | `agent` | Standalone FR planning agent (FR-452) — transforms topics into FRs |
| [python-map](demos/python-map/) | `map`, `python` | Parallel Python tools |
| [ramp_doctrine](demos/ramp_doctrine/) | `python`, `map`, `llm` | Scripture transferability judgement → draft disposition for a target repo (FR-866) |
| [ramp_rtm](demos/ramp_rtm/) | `python`, `map`, `llm` | Derive candidate requirements + coverage gaps for a target repo (FR-866) |
| [ramp_incidents](demos/ramp_incidents/) | `python`, `map`, `llm` | Reconcile target failure narratives into an incident register draft (FR-866) |
| [research-route](demos/research-route/) | `python`, `llm`, `agent` | Closed-input alternatives research: five orthogonal personas + LLM-free reduce to a dispositioned table (FR-890) |
| [salvage_classify](demos/salvage_classify/) | `python`, `map`, `llm` | Classify a stale source repo's assets for retirement — duplicate/lift/obsolete disposition draft (FR-868) |
| [python-variables](demos/python-variables/) | `python` | Variables expression resolution on python nodes (FR-252) |
| [map-timeout](demos/map-timeout/) | `map`, `python` | Per-branch timeout for map nodes (FR-069) |
| [safety-guards](demos/safety-guards/) | `llm`, `map` | Execution safety with recursion limits (FR-027) |
| [session-continuation](demos/session-continuation/) | `copilot` | Session persistence across runs |
| [shared-vision-tool](demos/shared-vision-tool/) | `python` | Image → structured description via shared vision tool (FR-769) |
| [soul](demos/soul/) | `llm`, `data_files` | Agent personality pattern |
| [streaming](demos/streaming/) | `llm` | Token-by-token output |
| [system-status](demos/system-status/) | `tool` | Shell tool execution |
| [tavily_rag](demos/tavily_rag/) | `python`, `llm` | Domain-specific RAG with Tavily retrieval |
| [thinking](demos/thinking/) | `llm` | Extended thinking with configurable depth (FR-071) |
| [tool-call](demos/tool-call/) | `python`, `tool_call` | Dynamic tool dispatch from graph state |
| [verified-search](demos/verified-search/) | `agent`, `llm` | Evaluation-first search with verification |
| [web-research](demos/web-research/) | `agent` | Web search agent |
| [yamlgraph](demos/yamlgraph/) | `llm` | Multi-step pipeline |
| [cache](demos/cache/) | `llm` | Per-node result caching with CachePolicy (FR-032) |
| [prompt-caching](demos/prompt-caching/) | `llm` | Anthropic prompt caching with system_segments (FR-219) |
| [prompt_theme_analyzer](demos/prompt_theme_analyzer/) | `map`, `python`, `llm` | Prompt theme classification with deterministic aggregation (FR-402) |
| [philosopher_book](demos/philosopher_book/) | `copilot`, `map`, `python` | 21-chapter philosophical work on cognitive traps, one chapter per trap (FR-404) |

### Utility Demos

Tools for codebase analysis — useful for maintainers, not for learning.

| Demo | Description |
|------|-------------|
| [pipeline_audit](demos/pipeline_audit/) | Cross-pipeline structural analysis |
| [req-cross-check](demos/req-cross-check/) | Architecture requirement traceability audit |
| [run-analyzer](demos/run-analyzer/) | Run output analysis utilities |
| [hook_classifier](demos/hook_classifier/) | FSM daemon for async hook event classification (FR-425) |
| [agent-json](demos/agent-json/) | Agent structured JSON output (FR-449) |

Chaplain and watcher2 infrastructure witnesses live under [`.chaplain/demos/`](../.chaplain/demos/).

### FR Validation Demos

Used primarily to validate specific feature requests.

| Demo | FR | Description |
|------|-----|-------------|
| [interrupt](demos/interrupt/) | FR-006 | Subgraph interrupt integration tests |
| [verification-gate](demos/verification-gate/) | FR-164 | Deterministic post-execution verification gates |
| [session-shapes](demos/session-shapes/) | FR-884 | Task-shape classification of chat-session skeletons (map+reduce, pinned mini model) |

> **Archived:** `commit-delta-gate` and `session-test` moved to `purgatory/` — see [purgatory/README.md](../purgatory/README.md).

## Running Examples

Most examples can be run with the CLI:

```bash
# From project root
yamlgraph graph run examples/<name>/graph.yaml --full
```

For TypeScript integrations, use `demos/typescript-node/`: `graph run --json` over a subprocess (`child_process.execFile`) for direct request/response.

Or with specific variables:

```bash
yamlgraph graph run examples/npc/npc-creation.yaml \
  -v 'concept=grumpy dwarf blacksmith' --full
```

## By Feature

### Map Nodes (Parallel Processing)
- **book_translator/** - Parallel chapter translation and proofreading
- **book_reviewer/** - Decomposed map→reduce manuscript critique with computed scores
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
- **demos/write_data_file/** - Read→augment→write-back cycle (world bible)
- **demos/wiki-memory/** - Wiki with reference-integrity gate and inter-run state

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
