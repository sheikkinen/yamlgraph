# Context Helpers — Codebase Intelligence for AI Agents

**Date:** 2026-05-19
**Status:** Research survey
**Purpose:** Evaluate tools that index repos and/or dependencies, offering efficient search for agents to orient in a codebase with fewer tokens and tool calls.

---

## Problem

AI coding agents spend 40–60% of their tokens on orientation — grepping for symbols, reading files to understand structure, hunting for callers and callees. Every session starts from zero. The agent has source code but no memory of how the codebase got there, no dependency graph, no ownership map, no architectural decisions.

## Taxonomy

Three approaches have emerged:

1. **Full intelligence platforms** — index everything (AST, git history, docs, decisions, health), expose via MCP. Heavy init, rich queries.
2. **Token-efficient context engines** — focus on reducing input tokens via chunking, compression, and embeddings. Measurable cost savings.
3. **Lightweight static indexers** — generate a committed artifact (JSON/markdown) that agents read instead of scanning. Near-zero overhead.

---

## Tier 1: Full Codebase Intelligence Platforms

### Repowise

- **Repo:** [repowise-dev/repowise](https://github.com/repowise-dev/repowise)
- **Stars:** 1,700 | **Language:** Python | **License:** AGPL-3.0
- **Install:** `pip install repowise` / `uv tool install repowise`

Five intelligence layers:

| Layer | What it builds |
|-------|---------------|
| Graph | tree-sitter AST → file + symbol nodes, call resolution, heritage extraction, Leiden community detection, PageRank, betweenness centrality. 14 languages. |
| Git | Hotspots (churn × complexity), ownership %, co-change pairs (hidden coupling), bus factor, contributor profiles, reviewer suggestions. |
| Docs | LLM-generated wiki per module/file, rebuilt incrementally. Freshness scoring. Semantic search via RAG. |
| Decisions | ADRs from git history, inline markers, CLI. Linked to graph nodes. Staleness tracking. |
| Health | 12 deterministic biomarkers → 1–10 score per file. McCabe complexity, deep nesting, brain methods, duplication, untested hotspots. LCOV/Cobertura/Clover ingest. |

**MCP tools (9):** `get_overview`, `get_answer`, `get_context`, `get_symbol`, `search_codebase`, `get_risk`, `get_why`, `get_dead_code`, `get_health`.

**Proactive hooks:** PreToolUse enriches every grep/glob with top-3 related files (symbols, importers, dependencies). PostToolUse detects stale wiki after commits.

**Multi-repo:** Workspaces with cross-repo co-change detection, API contract extraction (HTTP, gRPC, topics), federated MCP queries.

**Benchmarks (Flask, claude-sonnet-4-6):** 36% cheaper, 19% faster, 49% fewer tool calls, 89% fewer file reads vs baseline. 27× fewer tokens per query (pooled).

**Trade-offs:** ~25 min init (one-time LLM doc generation), AGPL license, requires LLM API key for docs layer. `repowise init --index-only` skips LLM for graph+git+dead-code only.

---

### CodeGraph

- **Repo:** [codegraph-ai/CodeGraph](https://github.com/codegraph-ai/CodeGraph)
- **Stars:** 4 | **Language:** Rust (single binary) | **License:** Apache-2.0

Semantic graph engine. 37 tree-sitter parsers. Persistent RocksDB graph + HNSW vector index with full-body BGE embeddings. Single binary serves both MCP and LSP protocols.

**MCP tools (61 total):**
- Community (34): `get_ai_context`, `get_edit_context`, `analyze_impact`, `analyze_complexity`, `find_circular_deps`, `find_hot_paths`, `symbol_search` (hybrid BM25 + semantic), callers/callees, dependency graph, call graph, memory store/search, reindex.
- Pro (27): security scanning (40+ patterns, source-to-sink taint tracing, SBOM, SARIF export), coupling metrics, dead code detection, duplicate detection, git history mining, cross-project search.

**Performance:** ~60 files/sec indexing. Sub-100ms queries. Incremental via FNV-1a content hashing. Instant startup from persisted graph.

**VS Code extension** included (registers tools as Language Model Tools for Copilot).

**Trade-offs:** Very new (4 stars), Pro features are paid. Heavy on C tree-sitter grammar code.

---

### Srclight

- **Repo:** [srclight/srclight](https://github.com/srclight/srclight)
- **Stars:** 41 | **Language:** Python | **License:** MIT

42 MCP tools in 7 tiers. SQLite FTS5 (3 indexes: names, content/trigram, docs/stemmed) + tree-sitter + optional embeddings (Ollama/Voyage).

**Unique features:**
- Community detection (Louvain on call-graph edges with TF-IDF auto-labeling)
- Execution flow tracing (BFS from entry points)
- Impact analysis with risk scoring (LOW/MEDIUM/HIGH/CRITICAL)
- `detect_changes()` — maps git diff to affected symbols with aggregate blast radius
- Build system awareness (CMake, .csproj, #ifdef platform guards)
- Document extraction: PDF, DOCX, XLSX, HTML, CSV, images w/ OCR (PaddleOCR, pytesseract)
- Optional GPU-accelerated vector search (~3ms for 27K vectors on modern GPU)

**Multi-repo:** SQLite ATTACH+UNION. Each repo keeps its own index.db; query time joins them.

**Trade-offs:** 11 languages (less than CodeGraph's 37). Only 2 contributors. No git intelligence beyond blame/hotspots.

---

## Tier 2: Token-Efficient Context Engines

### Code Context Engine (CCE)

- **Repo:** [elara-labs/code-context-engine](https://github.com/elara-labs/code-context-engine)
- **Stars:** 127 | **Language:** Python | **License:** MIT
- **Install:** `uv tool install code-context-engine && cce init`

Focused on measurable token savings. Tree-sitter AST → semantic chunks → vector embeddings (sqlite-vec). Hybrid vector + BM25 search with Reciprocal Rank Fusion. Code graph walks CALLS/IMPORTS edges.

**Savings (benchmarked on FastAPI, 53 files, 20 queries):**

| Layer | Savings |
|-------|---------|
| Retrieval (full files → relevant chunks) | 94% |
| Chunk compression (chunks → signatures + docstrings) | 89% |
| Grammar compression (article/filler removal) | 13% |
| Output compression (response verbosity) | 25–80% |

**Important baseline note:** The 94% is measured against full-file reads, not against what Claude Code actually does with its built-in grep/partial-read tools. Real-world savings vs normal agent behavior will be lower.

**MCP tools (9):** `context_search`, `expand_chunk`, `related_context`, `session_recall`, `record_decision`, `record_code_area`, `index_status`, `reindex`, `set_output_compression`.

**Cross-session memory:** Decisions and code areas persist in SQLite. `session_recall` surfaces them in next session.

**Auto-configures:** Claude Code, Cursor, VS Code/Copilot, Gemini CLI, Codex, OpenCode, Tabnine — all in one `cce init` command.

**Embedding backends:** Ollama (zero deps) or fastembed+ONNX (local, ~189 MB). Content-hash cache gives 96% embedding cache hit rate on re-index.

**Trade-offs:** 7 languages with full AST support (Python, JS, TS, PHP, Go, Rust, Java). No git intelligence. No call graph beyond CALLS/IMPORTS edges.

---

### Context-Router

- **Repo:** [mohankrishnaalavala/context-router](https://github.com/mohankrishnaalavala/context-router)
- **Stars:** 9 | **Language:** Python | **License:** Apache-2.0
- **Install:** `uv tool install context-router-cli && context-router init && context-router index`

Memory-aware context engine with pack modes.

**Pack modes:** review (PR), implement (feature), debug (failure), handover (onboarding), minimal (triage). Each returns a ranked context pack at different token budgets (800–4,000 tokens).

**Memory system:** Observations + ADR decisions stored as git-committed markdown in `.context-router/memory/`. Auto-capture via git post-commit hook. Feedback learning tunes per-file confidence after ≥3 reports.

**Benchmarks:** 91% fewer tokens, 17/18 rank-1 across 6 OSS projects (gin, actix-web, django, gson, requests, zod).

**Multi-repo:** `workspace detect-links` infers cross-repo edges from Python imports + OpenAPI/protobuf/GraphQL contracts. `workspace pack` returns unified ranked pack with `[repo]` labels.

**MCP tools (17):** `get_context_pack`, `get_debug_pack`, `get_minimal_context`, `generate_handover`, `explain_selection`, `build_index`, `update_index`, `get_call_chain`, `suggest_next_files`, `save_observation`, `search_memory`, `list_memory`, `save_decision`, `get_decisions`, `mark_decision_superseded`, `record_feedback`, `get_context_summary`.

**Trade-offs:** Very new (9 stars, 2 contributors). 9 languages. Optional cross-encoder reranking needs separate `[semantic]` extra.

---

## Tier 3: Lightweight Indexers / Maps

### Stacklit

- **Repo:** [glincker/stacklit](https://github.com/glincker/stacklit)
- **Stars:** 81 | **Language:** Go | **License:** MIT
- **Install:** `npx stacklit init`

Generates three files in <1 second:

| File | Purpose | Commit? |
|------|---------|---------|
| `stacklit.json` | Structured codebase index for agents | Yes |
| `DEPENDENCIES.md` | Mermaid dependency diagram | Yes |
| `stacklit.html` | Interactive visual map (4 views) | No (gitignored) |

**The `stacklit.json` format:** Modules with purpose, file/line counts, exports with signatures, dependencies, git activity heatmap, framework detection, and hints for where to add features and how to run tests.

**Token efficiency:** ~250 tokens replaces 50,000+ tokens of exploration. Measured: Express.js 21K→3.7K, FastAPI 108K→4.1K, Gin 24K→3.4K.

**11 languages** via tree-sitter. Merkle hashing skips regeneration when only docs/configs changed. Git hook keeps it fresh (~50ms on 10K-line repo).

**MCP server** included (`stacklit serve`). Auto-configures Claude/Cursor/Aider via `stacklit setup`.

**Trade-offs:** No semantic search, no git intelligence, no call graphs. It's a map, not an engine. But the map is cheap and committed to the repo — every agent benefits with zero setup.

---

### Codanna

- **Repo:** [bartolli/codanna](https://github.com/bartolli/codanna)
- **Stars:** 673 | **Language:** Rust | **License:** Apache-2.0
- **Install:** `curl -fsSL --proto '=https' --tlsv1.2 https://install.codanna.sh | sh`

Fast local code intelligence CLI + MCP server. "X-ray vision for your agent."

**Features:** Semantic search (natural language against code + docs), relationship tracking (call graphs, implementations, dependencies), document search (markdown/text RAG), profiles for different project types.

**Performance:** Sub-10ms lookups, 75,000+ symbols/second parsing. ~150MB for embedding model.

**15 languages:** Rust, Python, JS, TS, Java, Kotlin, Go, PHP, C, C++, C#, Clojure, Lua, Swift, GDScript.

**MCP integration:** stdio, HTTP, HTTPS transports. Works with Claude Code, Cursor, Windsurf, any MCP client.

**Trade-offs:** No git intelligence. No dashboard. No multi-repo workspaces. Focused on being fast and simple.

---

### Ctxo

- **Repo:** [alperhankendi/Ctxo](https://github.com/alperhankendi/Ctxo)
- **Stars:** 53 | **Language:** TypeScript/Node | **License:** MIT
- **Install:** `npm install -g @ctxo/cli && ctxo init && ctxo index`

Dependency graphs, git intent classification, blast radius, anti-pattern detection. Plugin architecture. 14 MCP tools.

**Deep analysis** for TypeScript, Go, C# (any language gets basic support).

**Dashboard:** 8 views — File Tree, Heatmap, Co-Changes, Timeline, Architecture, MCP Explorer, Diff. Deployed to GitHub Pages.

**Visualization:** `ctxo visualize` generates self-contained HTML with force-directed graph, PageRank sizing, layer coloring, blast radius on click.

**Trade-offs:** Node.js ecosystem only (npm install). Deep analysis limited to 3 languages.

---

## Comparison Matrix

| Tool | Stars | Lang | License | MCP Tools | AST Languages | Git Intel | Memory | Multi-repo | Init Time | Token Savings |
|------|-------|------|---------|-----------|---------------|-----------|--------|------------|-----------|---------------|
| Repowise | 1.7k | Python | AGPL-3.0 | 9 | 14 | Deep (hotspots, co-changes, ownership, bus factor) | Decisions | Yes (federated) | ~25 min | 27× fewer tokens |
| Codanna | 673 | Rust | Apache-2.0 | ~15 | 15 | None | None | None | seconds | — |
| CCE | 127 | Python | MIT | 9 | 7+40 | None | Decisions, code areas | None | <1 min | 94% (vs full-file) |
| Stacklit | 81 | Go | MIT | 5 | 11 | Activity heatmap | None | Polyrepo | <1s | ~250 tokens/repo |
| Ctxo | 53 | TS | MIT | 14 | 3 deep | Intent classification | None | None | seconds | — |
| Srclight | 41 | Python | MIT | 42 | 11 | Blame, hotspots | None | ATTACH+UNION | seconds | — |
| Context-Router | 9 | Python | Apache-2.0 | 17 | 9 | None | Observations + ADRs | Yes (edges) | <30s | 91% fewer tokens |
| CodeGraph | 4 | Rust | Apache-2.0 | 61 | 37 | Mining (Pro) | Persistent (RocksDB) | Multi-workspace | seconds | — |

---

## Tools Not Found

- **GitHits** — no public repo found on GitHub
- **oo** (codestory) — 404, possibly renamed or private
- **colgrep** — no public repo found
- **pruner** — no public repo matched "codebase context agent"

These may be private, early-stage, or renamed. Need URLs to investigate further.

---

## Relevance to YAMLGraph

### Already in place
- `reference/module-map.md` — static module map (similar to Stacklit's approach)
- `CLAUDE.md` / `.github/copilot-instructions.md` — agent orientation docs
- `vulture` for dead code, `radon` for complexity, `jscpd` for duplication
- `scripts/req_coverage.py` for requirement traceability

### Gaps these tools could fill
1. **Call graph / blast radius** — currently no way for agents to ask "what breaks if I change X?"
2. **Git co-change intelligence** — hidden coupling not visible in import graphs
3. **Cross-session memory** — agents restart from zero every session
4. **Token-efficient orientation** — agents still read full files for context

### Candidates worth evaluating

| Need | Best fit | Why |
|------|----------|-----|
| Cheapest experiment | **Stacklit** | Commit `stacklit.json`, agents read ~250 tokens. Zero infrastructure. 1 min to try. |
| Token cost reduction | **CCE** | Python, MIT, works with Copilot. Measurable savings. Light footprint. |
| Full codebase intelligence | **Repowise** | Git intelligence + decisions + health scores align with Scripture's diary/FR/decision patterns. Python. But AGPL and ~25 min init. |
| Fast call graphs | **Codanna** | Rust, Apache-2.0, sub-10ms. No git intelligence but best at pure code navigation. |
