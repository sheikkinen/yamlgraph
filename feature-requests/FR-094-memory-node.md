# Feature Request: Declarative Memory Nodes (memory_read / memory_write)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-02-25
**Judged:** 2026-02-25

## Summary

Add two new declarative node types — `memory_read` and `memory_write` — that provide first-class YAML-driven semantic memory operations, enabling cross-session knowledge accumulation without writing Python.

## Value Statement

Graph authors gain declarative cross-session memory (store and recall by semantic similarity) so pipelines can learn from past runs without custom Python tools.

## Problem

YAMLGraph's current memory story has two gaps:

1. **AgentState (Pattern 7)** accumulates messages within a single thread but provides no cross-session persistence or semantic retrieval.
2. **Checkpointers** persist full execution state for resume/replay but do not support selective knowledge accumulation or similarity-based recall.

The existing `examples/rag/` pattern proves vector retrieval works, but it requires:
- A custom Python tool (`tools/rag_retrieve.py`) and a state wrapper function
- Manual state plumbing (`rag_collection`, `rag_query`, `rag_db_path`)
- No write-back path — retrieval only, no learning loop

The result: building a self-improving pipeline (e.g., storing successful outputs and recalling them in future runs) requires hand-written Python for both read and write, breaking YAMLGraph's "60–80% in YAML" promise for this class of workflow.

## Proposed Solution

Two new node types in `yamlgraph/node_factory/memory_nodes.py`, backed by **LanceDB** (already in `[rag]` optional dependency).

### memory_read

Queries a vector collection by semantic similarity and writes results to state.

```yaml
nodes:
  recall_patterns:
    type: memory_read
    collection: story_patterns
    query: "successful {state.genre} story patterns"
    top_k: 5
    threshold: 0.7          # optional, minimum similarity score
    db_path: ./vectorstore   # optional, default ./vectorstore
    state_key: recalled
```

Compiled behavior:
1. Resolve `query` via standard variable interpolation
2. Embed query using collection's embedding model (read from metadata table)
3. Search LanceDB collection, return top_k results above threshold
4. Write `[{content, source, score, metadata}]` to `state_key`

### memory_write

Writes content with metadata to a vector collection.

```yaml
nodes:
  store_success:
    type: memory_write
    collection: story_patterns
    content: "{state.synopsis}"
    metadata:
      genre: "{state.genre}"
      grade: "{state.analysis.grade}"
      run_id: "{state.run_id}"
    db_path: ./vectorstore   # optional
    embedding_model: text-embedding-3-small  # optional, default text-embedding-3-small; stored in collection metadata
```

Compiled behavior:
1. Resolve `content` and `metadata` values via variable interpolation
2. Embed content using specified or collection-default embedding model (fallback: `text-embedding-3-small` on first write)
3. Upsert row into LanceDB collection (create table if first write)
4. Store embedding model in `{collection}_metadata` table
5. Return empty dict (no state mutation beyond side effect)

### Graph-Level Example: Self-Improving Novel Generator

```yaml
nodes:
  recall:
    type: memory_read
    collection: novel_patterns
    query: "successful {state.genre} synopsis"
    top_k: 3
    state_key: past_successes

  generate:
    prompt: prompts/generate_synopsis
    variables:
      genre: "{state.genre}"
      past_successes: "{state.past_successes}"
    state_key: synopsis

  evaluate:
    prompt: prompts/evaluate
    variables:
      synopsis: "{state.synopsis}"
    state_key: evaluation

  store:
    type: memory_write
    collection: novel_patterns
    content: "{state.synopsis}"
    metadata:
      genre: "{state.genre}"
      grade: "{state.evaluation.grade}"

edges:
  - from: START
    to: recall
  - from: recall
    to: generate
  - from: generate
    to: evaluate
  - from: evaluate
    to: store
  - from: store
    to: END
```

## Acceptance Criteria

- [ ] `memory_read` node type retrieves documents by semantic similarity from a LanceDB collection
- [ ] `memory_write` node type stores content with metadata and auto-generated embeddings
- [ ] Variable interpolation works in `query`, `content`, and `metadata` fields
- [ ] `memory_write` auto-creates the collection on first write (no separate indexing step required)
- [ ] Graceful error when `[rag]` dependency not installed (`ImportError` with install hint)
- [ ] Graceful error when collection does not exist for `memory_read` (clear message, not crash)
- [ ] `db_path` defaults to `./vectorstore`; configurable per node
- [ ] `embedding_model` stored in collection metadata; consistent between read and write
- [ ] Both node types registered in `NodeType` enum and dispatched in `node_compiler.py`
- [ ] Unit tests with mocked LanceDB (no API keys required)
- [ ] Integration test with real LanceDB (local, no API key) using a local embedding stub
- [ ] `yamlgraph graph lint` validates memory node configs (required fields, known params)
- [ ] Documentation: reference section added to `reference/graph-yaml.md`
- [ ] Requirements added to `ARCHITECTURE.md` (REQ-YG-091, REQ-YG-092)
- [ ] Example graph in `examples/demos/memory/` demonstrating read/write loop

## Alternatives Considered

### A. Document the existing `type: python` pattern better

The `examples/rag/` pattern already works for read. We could add a write wrapper and better docs. **Rejected** because it still requires Python for every graph and doesn't support `memory_write` at all — the write path doesn't exist today.

### B. ChromaDB backend

The inbox file suggested ChromaDB. **Rejected** in favor of LanceDB because:
- LanceDB is already an optional dependency (`[rag]`)
- LanceDB is embedded (zero-config, no server)
- The existing `rag_retrieve.py` tool and `index_docs.py` are LanceDB-based
- Adding ChromaDB would mean a second vector store backend with no incremental value

### C. Generic `type: vectorstore` with pluggable backends

Over-engineered for current needs. Can be refactored later if a second backend is needed. Start with LanceDB-only and extract an interface if/when necessary.

### D. Promote `rag_retrieve` to a built-in tool instead of a node type

Would solve read but not write. Node types give better YAML ergonomics (no tool registration boilerplate) and enable lint-time validation of memory-specific fields.

## Implementation Notes

- Reuse core logic from `examples/rag/tools/rag_retrieve.py` — extract to `yamlgraph/tools/memory.py`
- Factory functions: `create_memory_read_node()`, `create_memory_write_node()` in `yamlgraph/node_factory/memory_nodes.py`
- Registration: add `memory_read` and `memory_write` to `NodeType` enum in `constants.py`, dispatch in `node_compiler.py`
- Linter: add required-field checks for `collection` (both), `query` (read), `content` (write) in `graph_linter.py`
- For unit tests: mock `lancedb.connect()` and `_get_embedding()` to avoid API/disk dependency

## Related

- `examples/rag/` — existing RAG pattern (read-only, Python-based)
- `examples/rag/tools/rag_retrieve.py` — reusable retrieval logic to extract
- `feature-requests/037-persistent-logbook.md` — related persistence pattern (SQLite, not vector)
- `feature-requests/FR-053-tavily-domain-rag-demo.md` — live RAG pattern (API, not stored)
- `ARCHITECTURE.md` — requirements registry (add REQ-YG-091, REQ-YG-092)
- Inbox source: `.chaplain/inbox/memory-node.md` (brainstorming session 2025-02-24)

## Judgement Notes (2026-02-25)

**Verdict:** APPROVED — scope frozen, authority granted.

**Corrections applied:**
1. REQ-YG-090/091 → REQ-YG-091/092 (REQ-YG-090 already claimed by FR-093).
2. Default `embedding_model` made explicit: `text-embedding-3-small` on first collection write when no metadata exists (consistent with existing `rag_retrieve.py`).

**Strengths:**
- Well-scoped: two complementary node types, no over-engineering.
- Correct rejection of ChromaDB and generic backend alternatives.
- Reuses existing LanceDB dependency and proven `rag_retrieve.py` logic.
- All 15 acceptance criteria are binary testable.

**Risks acknowledged:**
- OpenAI embedding dependency remains (acceptable: embeddings ≠ LLM provider; document in README).
- 3-day estimate assumes clean extraction from `rag_retrieve.py`; unforeseen LanceDB API changes may add time.
