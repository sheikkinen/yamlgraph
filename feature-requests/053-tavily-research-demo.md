# Feature Request: Tavily Domain RAG Demo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-02-20

## Summary

Add a Tavily-powered domain-scoped RAG example to `examples/demos/tavily-rag/` that retrieves content from a configured target domain (`TAVILY_TARGET_DOMAIN`) and grounds LLM answers in the retrieved results. Demonstrates the "retrieve → answer" RAG pattern using Tavily as a zero-indexing retrieval layer — no vector store setup needed, just set a domain and ask questions.

## Problem

The existing RAG example (`examples/rag/`) requires pre-indexing documents into a local ChromaDB vector store before querying. This is the right pattern for production but creates friction for demos and prototyping:

1. **Setup overhead** — Must run `index_docs.py` before querying; cold start for new domains.
2. **Static corpus** — Only answers from pre-indexed documents; no fresh web content.
3. **Domain exploration** — When scoping to a specific website (e.g., `terveystalo.com`), you want live retrieval of current pages, not a snapshot.

Tavily solves this by searching a specific domain in real-time with `include_domains`, returning relevance-scored content that the LLM treats as retrieved context — a "live RAG" pattern with zero indexing.

**Key insight:** Tavily's `include_domains` + `include_raw_content` turns any website into a queryable knowledge base without indexing infrastructure.

## Proposed Solution

### File Structure

```
examples/demos/tavily-rag/
├── README.md
├── graph.yaml              # Core: retrieve → answer (domain-scoped RAG)
├── graph-deep.yaml         # Advanced: plan → map(retrieve) → synthesize
├── prompts/
│   ├── answer.yaml         # Ground answer in retrieved context
│   ├── planner.yaml        # Breaks query into sub-queries (deep)
│   └── synthesizer.yaml    # Merges parallel results (deep)
└── nodes/
    ├── __init__.py
    └── tavily_retrieve.py  # Tavily retrieval tool (domain-scoped)
```

### A. Tavily Retrieval Tool (`nodes/tavily_retrieve.py`)

```python
"""Tavily domain-scoped retrieval tool for YAMLGraph.

Retrieves content from a target domain via Tavily API.
Acts as a zero-indexing RAG retrieval layer.

Requires: pip install tavily-python
          export TAVILY_API_KEY="your-key"
          export TAVILY_TARGET_DOMAIN="example.com"  # optional, scopes search

Usage in graph YAML:
    tools:
      tavily_retrieve:
        type: python
        module: examples.demos.tavily_rag.nodes.tavily_retrieve
        function: tavily_retrieve
        description: "Retrieve content from target domain via Tavily"
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def tavily_retrieve(state: dict) -> str:
    """Retrieve domain-scoped content using Tavily.

    Called by YAMLGraph as a type: python node. Receives full state dict.
    Reads query from state["query"] (map sub-node) or state["question"].

    Args:
        state: Full state dictionary from YAMLGraph

    Returns:
        Formatted context string with sources and content
    """
    query = state.get("query") or state.get("question", "")
    max_results = state.get("max_results", 5)

    if not query or not query.strip():
        return "Error: Search query is empty"

    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable not set"

    try:
        from tavily import TavilyClient
    except ImportError:
        return "Error: tavily-python not installed. Run: pip install tavily-python"

    try:
        client = TavilyClient(api_key=api_key)
        kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": True,
        }
        # Scope to target domain if configured
        target_domain = os.environ.get("TAVILY_TARGET_DOMAIN")
        if target_domain:
            kwargs["include_domains"] = [target_domain]

        response = client.search(**kwargs)

        sections: list[str] = []

        # Tavily's pre-synthesized answer
        answer = response.get("answer")
        if answer:
            sections.append(f"Summary: {answer}\n")

        # Individual retrieved pages
        for i, result in enumerate(response.get("results", []), 1):
            title = result.get("title", "No title")
            url = result.get("url", "No URL")
            content = result.get("content", "")
            raw = result.get("raw_content", "")
            score = result.get("score", 0)

            sections.append(f"[Source {i}] (relevance: {score:.2f})")
            sections.append(f"Title: {title}")
            sections.append(f"URL: {url}")
            # Prefer raw_content (full page) over snippet
            text = raw[:2000] if raw else content
            if text:
                sections.append(text)
            sections.append("---")

        if not sections:
            domain_note = f" on {target_domain}" if target_domain else ""
            return f"No results found for '{query}'{domain_note}"

        return "\n".join(sections)

    except Exception as e:
        logger.warning(f"Tavily retrieval failed: {e}")
        return f"Error: Retrieval failed - {e}"
```

### B. RAG Graph (`graph.yaml`)

```yaml
version: "1.0"
name: tavily-rag
description: Domain-scoped RAG using Tavily as retrieval layer
prompts_relative: true
prompts_dir: prompts

state:
  question: str

tools:
  tavily_retrieve:
    type: python
    module: examples.demos.tavily_rag.nodes.tavily_retrieve
    function: tavily_retrieve
    description: "Retrieve content from target domain via Tavily"

nodes:
  retrieve:
    type: python
    tool: tavily_retrieve
    state_key: context

  answer:
    type: llm
    prompt: answer
    requires: [retrieve]
    state_key: answer
    variables:
      context: "{state.context}"
      question: "{state.question}"

edges:
  - from: START
    to: retrieve
  - from: retrieve
    to: answer
  - from: answer
    to: END
```

### C. Deep RAG Graph (`graph-deep.yaml`)

Plan → parallel retrieve → synthesize, for broad questions that need multiple angles:

```yaml
version: "1.0"
name: tavily-deep-rag
description: Multi-query RAG with parallel retrieval via Tavily
prompts_relative: true
prompts_dir: prompts

state:
  question: str

tools:
  tavily_retrieve:
    type: python
    module: examples.demos.tavily_rag.nodes.tavily_retrieve
    function: tavily_retrieve
    description: "Retrieve content from target domain via Tavily"

nodes:
  plan:
    type: llm
    prompt: planner
    variables:
      question: "{state.question}"
    state_key: sub_queries
    schema:
      name: SubQueries
      fields:
        queries:
          type: list[str]
          description: "3-5 focused retrieval queries"

  retrieve:
    type: map
    over: "{state.sub_queries.queries}"
    as: query
    node:
      type: python
      tool: tavily_retrieve
      state_key: context
    collect: contexts

  synthesize:
    type: llm
    prompt: synthesizer
    requires: [retrieve]
    state_key: answer
    variables:
      question: "{state.question}"
      contexts: "{state.contexts}"

edges:
  - from: START
    to: plan
  - from: plan
    to: retrieve
  - from: retrieve
    to: synthesize
  - from: synthesize
    to: END
```

### D. Prompts

**`prompts/answer.yaml`**
```yaml
system: |
  You are a helpful assistant. Answer the user's question using ONLY
  the retrieved context below. If the context doesn't contain the
  answer, say so — do not make up information.

  Always cite sources with their URLs.

user: |
  Question: {question}

  Retrieved Context:
  {context}

  Answer the question based on the context above. Cite sources.
```

**`prompts/planner.yaml`**
```yaml
system: |
  You are a query planner. Break a broad question into 3-5 focused
  retrieval queries that together will gather enough context to
  answer comprehensively. Each query should target a different
  aspect of the question.

user: |
  Break this question into focused retrieval queries: {question}
```

**`prompts/synthesizer.yaml`**
```yaml
system: |
  You are a research synthesizer. Combine multiple retrieved contexts
  into a coherent, well-sourced answer. Use ONLY the provided context.
  Cite sources with URLs. If contexts conflict, note the discrepancy.
  Do not make up information.

user: |
  Question: {question}

  Retrieved Contexts:
  {contexts}

  Synthesize a comprehensive answer from the contexts above.
  Cite sources with URLs.
```

### E. Shared Library Consideration

The Tavily retrieval tool could live in `examples/shared/tavily_retrieve.py` alongside the existing `websearch.py` (DuckDuckGo). Decision: start in the demo's `nodes/` dir; promote to `examples/shared/` if reuse emerges (e.g., the Ninchat project needs domain-scoped retrieval).

## Acceptance Criteria

- [ ] `examples/demos/tavily-rag/graph.yaml` runs: `yamlgraph graph run examples/demos/tavily-rag/graph.yaml --var question="What services are available?"`
- [ ] `examples/demos/tavily-rag/graph-deep.yaml` runs with map fan-out
- [ ] Both graphs pass `yamlgraph graph lint`
- [ ] `nodes/tavily_retrieve.py` returns full page content with source URLs
- [ ] `TAVILY_TARGET_DOMAIN` scopes retrieval to a single domain when set
- [ ] Works without `TAVILY_TARGET_DOMAIN` (open web fallback)
- [ ] Graceful error when `TAVILY_API_KEY` not set (no crash, clear message)
- [ ] Graceful error when `tavily-python` not installed
- [ ] `README.md` documents prerequisites, usage, and domain configuration
- [ ] Unit test for `tavily_retrieve()` with mocked API response
- [ ] Integration test guarded by `TAVILY_API_KEY` availability
- [ ] `pyproject.toml` updated — add `tavily` optional extra: `tavily = ["tavily-python>=0.5.0"]`
- [ ] Diary entry in `docs/diary.md`

## Alternatives Considered

### 1. Extend existing `examples/rag/` with Tavily retriever
Rejected. The existing RAG example demonstrates vector store indexing (ChromaDB), which is a fundamentally different pattern. Tavily domain RAG is "live retrieval" with zero indexing — different audience, different lesson.

### 2. Use `langchain-tavily` instead of `tavily-python`
Considered. `langchain-tavily` wraps Tavily as a LangChain tool. However, using `tavily-python` directly gives control over `include_domains` and `include_raw_content` params without LangChain community dependency overhead.

### 3. General web research demo (original FR-053 scope)
Narrowed. The original scope was open web research. Refocused to domain-scoped RAG because: (a) `TAVILY_TARGET_DOMAIN` is already configured in `.env`, (b) domain-scoped retrieval is a more practical pattern for real projects (e.g., customer support, knowledge base), (c) it complements the existing `web-research` demo rather than competing.

## Implementation Notes

- `TAVILY_API_KEY` and `TAVILY_TARGET_DOMAIN` are already configured in `.env`.
- The `tavily-python` package requires Python 3.9+. YAMLGraph requires 3.11+, so no conflict.
- Tavily free tier: 1,000 searches/month — sufficient for demos and testing.
- `include_raw_content=True` returns full page text (truncated to 2000 chars per source in the tool to fit LLM context windows).
- The deep RAG graph uses the correct map node syntax: `over` + `as` + `node:` + `collect:` with `type: python` sub-nodes.
- Pattern mirrors `examples/rag/` (retrieve → answer) but swaps ChromaDB for Tavily — making it a useful comparison point.
- `type: python` nodes receive the full state dict as a single argument — the function must use `state: dict` signature, not keyword args. The `variables:` section is ignored for python nodes.
- The framework wraps non-dict returns into `{state_key: result}`, so returning a plain string is valid.

## Related

- `examples/rag/` — Existing vector store RAG example (ChromaDB)
- `examples/demos/web-research/` — DuckDuckGo-based open web research
- `examples/shared/websearch.py` — DuckDuckGo tool implementation
- `examples/demos/python-map/` — Map node with `type: python` sub-nodes (pattern reference)
- FR-030: Map concurrency control (parallel sub-queries)
- FR-032: Node-level caching (cache repeated Tavily retrievals)
