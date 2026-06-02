# Diary: RAG Is Already Three Nodes

**Date:** 2026-05-31
**Context:** Evaluating a "Declarative RAG & Vector Orchestration" proposal — `yaml-rag` or native vector extension for YAMLGraph

## The Proposal

"A tool that allows developers to define document ingestion pipelines, chunking rules, and similarity search parameters entirely in YAML, abstracting away the underlying complexities of LangChain retrievers and database integrations."

## What Already Exists

```yaml
# examples/rag/graph.yaml — the entire RAG pipeline
nodes:
  setup:
    type: passthrough
    output:
      rag_collection: test_docs
      rag_query: "{state.question}"

  retrieve:
    type: python
    tool: rag_retrieve
    state_key: context

  answer:
    prompt: prompts/answer
    variables:
      context: "{state.context}"
      question: "{state.question}"
```

Three nodes. Setup → retrieve → answer. The graph is 45 lines of YAML. There is nothing left to simplify on the reasoning side.

Plus `examples/demos/tavily_rag/` — a web-RAG variant using Tavily as the retriever. Also 35 lines. Also three nodes.

## Where the Complexity Actually Lives

| Component | Language | Why |
|-----------|----------|-----|
| Chunking (boundary detection, overlap) | Python (`index_docs.py`) | Imperative: file I/O, markdown parsing, header detection |
| Embedding (API calls to OpenAI) | Python (`rag_retrieve.py`) | Side effect: network call, model selection |
| Vector DB (LanceDB connect, search, insert) | Python | Infrastructure: connection semantics vary by vendor |
| Answer generation | YAML (prompt + graph) | Already declarative |

The proposal targets the bottom three rows — the imperative parts. Wrapping them in YAML creates a DSL for ETL. That already exists as Airflow, Prefect, dbt, and a dozen others.

## Why `yaml-rag` Is Wrong-Shaped

1. **Chunking strategy is a function, not a parameter.** `chunk_size: 500, overlap: 50` covers the trivial case. The real complexity is semantic boundary detection — code blocks, headers, tables. A function, not a config knob.

2. **Vector DBs are infrastructure, not framework.** LanceDB (embedded) vs Pinecone (cloud) vs pgvector (Postgres) — each has different connection semantics, index types, and query APIs. A YAML abstraction over these is a mini-ORM for vector databases. LangChain already provides this. Duplicating it inside yamlgraph would couple the framework to infrastructure choices it has no business owning.

3. **The three-node graph is the abstraction.** The graph author writes: (a) a retrieval tool (Python, ~20 lines of actual logic), (b) an answer prompt (YAML), (c) three edges. Everything else is deployment/infrastructure.

## The Pattern

RAG in yamlgraph is not a feature — it's a **composition** of existing primitives:

- `type: python` tool → retrieval
- `type: llm` node → answer generation
- `variables:` → context injection into prompt
- `requires:` → dependency ordering

The "boilerplate" the proposal wants to eliminate is not in the graph. It's in the indexing pipeline — which is a batch ETL job, not a reasoning graph. Different tool for different job.

## Trap

`framework_costume` — the proposal dresses an ETL pipeline in graph vocabulary. Chunking, embedding, and indexing are not reasoning steps. They don't benefit from state management, conditional routing, or interrupt nodes. They're a `for` loop with an API call. Putting them in a graph YAML would be wearing a DAG costume on a pipeline.

## Heuristic

**If the "graph" has no conditionals, no loops, no interrupts, and no LLM reasoning — it's not a graph, it's a script.** The test: does removing the graph framework and writing a plain Python script make the code shorter? If yes, the graph adds ceremony, not structure.

The RAG *retrieval* graph passes this test — three nodes, one conditional (threshold filter), one LLM call. The RAG *indexing* pipeline fails it — it's a linear `read → chunk → embed → store` with no branching, no LLM, no state management.

## Seed

What if the indexing pipeline *did* need LLM reasoning? Semantic chunking (LLM decides chunk boundaries), quality filtering (LLM scores chunk relevance), metadata enrichment (LLM extracts entities from chunks). At that point, `index_docs.py` becomes a yamlgraph graph — naturally, not by force. The trigger is the LLM call, not the YAML config.
