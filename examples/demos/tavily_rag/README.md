# Tavily Domain RAG

Domain-scoped RAG using Tavily as a zero-indexing retrieval layer.

## Prerequisites

```bash
pip install tavily-python
```

Set environment variables:

```bash
export TAVILY_API_KEY="your-key"
export TAVILY_TARGET_DOMAIN="example.com"  # optional, scopes retrieval
```

## Usage

### Simple RAG (retrieve → answer)

```bash
yamlgraph graph run examples/demos/tavily_rag/graph.yaml \
  --var question="What services are available?"
```

### Deep RAG (plan → parallel retrieve → synthesize)

```bash
yamlgraph graph run examples/demos/tavily_rag/graph-deep.yaml \
  --var question="Compare pricing and availability of different services"
```

### Example: Scryfall (MTG card lore)

Override the domain at runtime to query any site:

```bash
# Simple — single retrieval
TAVILY_TARGET_DOMAIN=scryfall.com \
  yamlgraph graph run examples/demos/tavily_rag/graph.yaml \
  --var question="lore of Giada" --full

# Deep — plan + parallel fan-out + synthesize
TAVILY_TARGET_DOMAIN=scryfall.com \
  yamlgraph graph run examples/demos/tavily_rag/graph-deep.yaml \
  --var question="lore of Giada" --full --async
```

The deep graph decomposes "lore of Giada" into 5 sub-queries (origins,
card appearances, crossovers, etc.), retrieves each in parallel via Tavily,
and synthesizes a grounded answer citing Scryfall sources.

## How It Works

### Simple Graph

1. **Retrieve** — Calls Tavily API scoped to `TAVILY_TARGET_DOMAIN` (if set)
2. **Answer** — LLM answers using ONLY the retrieved context

### Deep Graph

1. **Plan** — LLM breaks the question into 3-5 focused sub-queries
2. **Retrieve** — Map node runs Tavily retrieval for each sub-query in parallel
3. **Synthesize** — LLM combines all retrieved contexts into a grounded answer

## Domain Configuration

| Variable | Effect |
|----------|--------|
| `TAVILY_TARGET_DOMAIN` set | Retrieval scoped to that domain only |
| `TAVILY_TARGET_DOMAIN` unset | Open web retrieval (no domain filter) |

## Key Concepts

- **`type: python`** tool node — receives full state dict, not keyword args
- **Domain scoping** — `include_domains` parameter in Tavily API
- **Raw content** — `include_raw_content=True` gets full page text (truncated to 2000 chars)
- **Map fan-out** — Parallel retrieval via LangGraph `Send()`

## Related

- [web-research](../web-research/) — DuckDuckGo agent (zero-config, no API key)
- [../../rag/](../../rag/) — ChromaDB vector store RAG (requires pre-indexing)
- [python-map](../python-map/) — Map node with `type: python` sub-nodes
