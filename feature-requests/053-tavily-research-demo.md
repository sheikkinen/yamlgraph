# Feature Request: Tavily Web Research Demo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-02-20

## Summary

Add a Tavily-powered web research example to `examples/demos/tavily-research/` that demonstrates structured search results, Pydantic-validated outputs, and the map-reduce deep research pattern. Complements the existing DuckDuckGo-based `web-research` demo with Tavily's richer API (answer extraction, relevance scoring, raw content).

## Problem

The existing `examples/demos/web-research/` demo uses DuckDuckGo via `ddgs`, which returns simple title/URL/snippet results with no API key required. This is great for zero-config demos, but production research pipelines need:

1. **Higher-quality results** — Tavily is optimized for AI agents; returns relevance-scored, deduplicated content.
2. **Answer extraction** — Tavily's `include_answer=True` provides a pre-synthesized answer alongside raw results.
3. **Raw content** — `include_raw_content=True` returns full page text, not just snippets.
4. **Structured schema validation** — Tavily results map naturally to Pydantic models, demonstrating YAMLGraph's inline schema feature.
5. **Deep research pattern** — A map-reduce example that fans out sub-queries in parallel, showcasing YAMLGraph's map nodes with Tavily.

No existing demo shows Tavily integration or the "plan → parallel search → synthesize" pattern.

## Proposed Solution

### File Structure

```
examples/demos/tavily-research/
├── README.md
├── graph.yaml              # Simple: search → summarize
├── graph-deep.yaml         # Advanced: plan → map(search) → synthesize
├── prompts/
│   ├── researcher.yaml     # System prompt for search synthesis
│   ├── planner.yaml        # Breaks query into sub-queries (deep)
│   └── synthesizer.yaml    # Merges parallel results (deep)
└── nodes/
    └── tavily_search.py    # Tavily tool wrapper
```

### A. Tavily Tool (`nodes/tavily_search.py`)

```python
"""Tavily search tool for YAMLGraph.

Provides structured web search via Tavily API.
Requires: pip install tavily-python
          export TAVILY_API_KEY="your-key"

Usage in graph YAML (agent or tool node):
    tools:
      tavily_search:
        type: python
        module: examples.demos.tavily_research.nodes.tavily_search
        function: tavily_search
        description: "Search the web using Tavily AI-optimized search"
"""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)


def tavily_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily.

    Args:
        query: Search query string
        max_results: Maximum number of results (default: 5)

    Returns:
        Formatted string with search results including answer and sources
    """
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
        response = client.search(
            query=query,
            max_results=max_results,
            include_answer=True,
        )

        lines = [f"Search results for '{query}':\n"]

        # Include Tavily's pre-synthesized answer if available
        answer = response.get("answer")
        if answer:
            lines.append(f"Quick Answer: {answer}\n")

        # Format individual results
        for i, result in enumerate(response.get("results", []), 1):
            title = result.get("title", "No title")
            url = result.get("url", "No URL")
            content = result.get("content", "")
            score = result.get("score", 0)

            lines.append(f"{i}. [{score:.2f}] {title}")
            lines.append(f"   URL: {url}")
            if content:
                lines.append(f"   {content}")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"Tavily search failed: {e}")
        return f"Error: Search failed - {e}"
```

### B. Simple Graph (`graph.yaml`)

```yaml
version: "1.0"
name: tavily-research
description: Research a topic using Tavily AI-optimized search
prompts_relative: true
prompts_dir: prompts

state:
  topic: str

tools:
  tavily_search:
    type: python
    module: examples.demos.tavily_research.nodes.tavily_search
    function: tavily_search
    description: "Search the web using Tavily AI-optimized search engine"

nodes:
  research:
    type: agent
    prompt: researcher
    tools: [tavily_search]
    max_iterations: 5
    state_key: research

  summarize:
    type: llm
    prompt: researcher_summarize
    requires: [research]
    state_key: summary
    variables:
      research: "{state.research}"
      topic: "{state.topic}"

edges:
  - from: START
    to: research
  - from: research
    to: summarize
  - from: summarize
    to: END
```

### C. Deep Research Graph (`graph-deep.yaml`)

Uses plan → map(search) → synthesize pattern:

```yaml
version: "1.0"
name: tavily-deep-research
description: Deep research with parallel sub-query fan-out via Tavily
prompts_relative: true
prompts_dir: prompts

state:
  topic: str

tools:
  tavily_search:
    type: python
    module: examples.demos.tavily_research.nodes.tavily_search
    function: tavily_search
    description: "Search the web using Tavily"

nodes:
  plan:
    type: llm
    prompt: planner
    variables:
      topic: "{state.topic}"
    state_key: sub_queries
    schema:
      name: SubQueries
      fields:
        queries:
          type: list[str]
          description: "3-5 focused sub-queries to research"

  search:
    type: map
    prompt: researcher
    tools: [tavily_search]
    over: sub_queries.queries
    item_var: query
    state_key: search_results
    max_iterations: 3

  synthesize:
    type: llm
    prompt: synthesizer
    requires: [search]
    state_key: report
    variables:
      topic: "{state.topic}"
      search_results: "{state.search_results}"

edges:
  - from: START
    to: plan
  - from: plan
    to: search
  - from: search
    to: synthesize
  - from: synthesize
    to: END
```

### D. Prompts

**`prompts/researcher.yaml`**
```yaml
system: |
  You are a research assistant with access to Tavily web search.
  Search for current, accurate information about the user's topic.
  Make multiple searches if needed. Note sources (URLs) for key facts.

user: |
  Research the following topic: {topic}
```

**`prompts/planner.yaml`**
```yaml
system: |
  You are a research planner. Break a broad topic into 3-5 focused
  sub-queries that together will provide comprehensive coverage.
  Each sub-query should target a different aspect of the topic.

user: |
  Break this topic into focused research sub-queries: {topic}
```

**`prompts/synthesizer.yaml`**
```yaml
system: |
  You are a research synthesizer. Combine multiple search results into
  a coherent, well-organized report. Cite sources with URLs.
  Resolve contradictions. Highlight areas of consensus and uncertainty.

user: |
  Topic: {topic}

  Research Results:
  {search_results}

  Create a comprehensive report with:
  1. Executive summary
  2. Key findings by sub-topic
  3. Sources cited
  4. Areas needing further research
```

### E. Shared Library Consideration

The Tavily tool could live in `examples/shared/tavily_search.py` alongside the existing `websearch.py` (DuckDuckGo). Both implement the same interface (`query: str, max_results: int -> str`) but with different backends. Decision: start in the demo's `nodes/` dir; promote to `examples/shared/` if reuse emerges.

## Acceptance Criteria

- [ ] `examples/demos/tavily-research/graph.yaml` runs: `yamlgraph graph run examples/demos/tavily-research/graph.yaml --var topic="LangGraph tutorials"`
- [ ] `examples/demos/tavily-research/graph-deep.yaml` runs with map fan-out
- [ ] Both graphs pass `yamlgraph graph lint`
- [ ] `nodes/tavily_search.py` returns structured results with relevance scores
- [ ] Graceful error when `TAVILY_API_KEY` not set (no crash, clear message)
- [ ] Graceful error when `tavily-python` not installed
- [ ] `README.md` documents prerequisites, usage, and architecture
- [ ] Unit test for `tavily_search()` with mocked API response
- [ ] Integration test guarded by `TAVILY_API_KEY` availability
- [ ] `pyproject.toml` updated — add `tavily` optional extra: `tavily = ["tavily-python>=0.5.0"]`
- [ ] Diary entry in `docs/diary.md`

## Alternatives Considered

### 1. Extend existing `web-research` demo
Rejected. The DuckDuckGo demo is valuable as a zero-config example. Tavily requires an API key and offers different capabilities (answer extraction, scoring). Separate demos serve different audiences.

### 2. Use `langchain-tavily` instead of `tavily-python`
Considered. `langchain-tavily` wraps Tavily as a LangChain tool, which would work with YAMLGraph's agent nodes directly. However, using `tavily-python` directly gives more control over the response format and avoids adding a LangChain community dependency. Could offer both as options in the README.

### 3. Generic "search provider" abstraction
Over-engineering for a demo. The tool function is 40 lines. If multiple search providers emerge, abstract then (YAGNI).

## Implementation Notes

- The `tavily-python` package requires Python 3.9+. YAMLGraph requires 3.11+, so no conflict.
- Tavily free tier: 1,000 searches/month — sufficient for demos and testing.
- The deep research graph exercises map nodes (FR-030, FR-052), inline schemas (Pydantic), and multi-hop agent patterns — good integration stress test.
- Consider adding `--provider tavily` or `--search-engine tavily` flag to the existing `web-research` demo in a follow-up, not in this FR.

## Related

- `examples/demos/web-research/` — Existing DuckDuckGo-based research demo
- `examples/shared/websearch.py` — DuckDuckGo tool implementation
- FR-030: Map concurrency control (parallel sub-queries)
- FR-031: Native retry policy (Tavily API retries)
- FR-032: Node-level caching (cache repeated Tavily searches)
- FR-052: Map output flattening (search result aggregation)
