# Feature Request: .fi Domain Crawler — Country-Level Sitemap Discovery Pipeline

**Priority:** LOW
**Type:** Feature
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-03-27

## Summary

Add an `examples/demos/fi-domain-crawl/` demo that crawls `.fi` (Finland) country-level domains, discovering and mapping site structures to produce a sitemap-style overview. Demonstrates a multi-stage pipeline: seed query planning → URL discovery → parallel page crawling → LLM-driven site summarisation.

## Value Statement

Graph authors gain a reusable crawl-and-summarise pattern that combines HTTP tool nodes, map-based parallelism, and LLM synthesis — showcasing YAMLGraph for data-gathering pipelines beyond simple Q&A.

## Problem

YAMLGraph has no demo that:

1. **Fetches live web pages** as a data-gathering step (existing demos use search APIs, not direct HTTP).
2. **Discovers link structure** from HTML, building a graph of pages from a seed URL.
3. **Produces a structured sitemap-style artifact** summarising a domain's content topology.
4. **Combines tool nodes with map fan-out** for parallel crawling of discovered URLs.

The `.fi` country domain scoping provides a natural boundary constraint, making the crawl finite and demonstrable.

## Proposed Solution

### Directory layout

```
examples/demos/fi-domain-crawl/
├── graph.yaml
├── README.md
├── nodes/
│   ├── __init__.py
│   ├── crawl_page.py        # httpx fetch + BeautifulSoup link/title extraction
│   └── seed_discovery.py    # initial .fi domain discovery via search API
└── prompts/
    ├── plan_crawl.yaml       # LLM plans which search queries to use
    └── summarise_site.yaml   # LLM synthesises sitemap overview from crawl data
```

### `graph.yaml`

```yaml
version: "1.0"
name: fi-domain-crawl
description: Crawl .fi domains and produce sitemap-style overviews
prompts_relative: true
prompts_dir: prompts

metadata:
  provider: anthropic

state:
  seed_query: str

defaults:
  temperature: 0.3

tools:
  seed_discovery:
    type: python
    module: examples.demos.fi_domain_crawl.nodes.seed_discovery
    function: discover_seeds
    description: "Discover .fi domain seed URLs via search"

  crawl_page:
    type: python
    module: examples.demos.fi_domain_crawl.nodes.crawl_page
    function: crawl_page
    description: "Fetch a URL and extract links, title, and text summary"

nodes:
  plan:
    type: llm
    prompt: plan_crawl
    parse_json: true
    variables:
      seed_query: "{state.seed_query}"
    state_key: search_queries

  discover:
    type: python
    tool: seed_discovery
    state_key: discovered_urls

  crawl:
    type: map
    over: "{state.discovered_urls}"
    as: url
    max_items: 10
    node:
      type: python
      tool: crawl_page
      state_key: page_data
    collect: crawl_results

  summarise:
    type: llm
    prompt: summarise_site
    requires: [crawl_results]
    state_key: sitemap_overview
    variables:
      seed_query: "{state.seed_query}"
      crawl_results: "{state.crawl_results}"

edges:
  - from: START
    to: plan
  - from: plan
    to: discover
  - from: discover
    to: crawl
  - from: crawl
    to: summarise
  - from: summarise
    to: END

exports:
  sitemap_overview:
    format: markdown
```

### Pipeline flow

```
START → plan → discover → crawl (map) → summarise → END
```

1. **plan** — LLM receives `seed_query`, produces a list of search queries scoped to `.fi` domains. Stored in `search_queries`.
2. **discover** — Python tool uses DuckDuckGo (`ddgs`) to execute each search query, filtering results to `.fi` TLD. Returns `discovered_urls`.
3. **crawl** — Map node fans out over `discovered_urls`, calling `crawl_page` for each URL in parallel (capped at `max_items: 10`). Collects structured page data in `crawl_results`.
4. **summarise** — LLM synthesises all crawl data into a markdown sitemap overview with domain name, page count, hierarchical link structure, and content summaries.

### Key tool nodes

**`crawl_page.py`** — Uses `httpx` to GET a URL, `BeautifulSoup` to parse HTML, extracts:
- Page title
- Internal links (same domain)
- External links
- Meta description
- Text content snippet (first 500 chars)

Returns a structured dict per page. Respects `robots.txt` via a simple check. Timeout (10s default) and error handling built-in.

**`seed_discovery.py`** — Uses DuckDuckGo (`ddgs`) to find `.fi` domain URLs matching the search queries from the plan node. Reads `search_queries` from state. Filters results to only `.fi` TLD. Returns a deduplicated list of seed URLs for the map node.

### Dependencies

No new dependencies — reuses existing optional extras:
- `httpx` — already in `digest` extra
- `beautifulsoup4` — already in `digest` extra
- `ddgs` — already in `websearch` extra

Install with: `pip install -e ".[digest,websearch]"`

## Acceptance Criteria

- [ ] `yamlgraph graph lint examples/demos/fi-domain-crawl/graph.yaml` passes
- [ ] `yamlgraph graph run examples/demos/fi-domain-crawl/graph.yaml --var seed_query="Helsinki libraries" --full` produces a markdown sitemap overview
- [ ] `crawl_page.py` respects timeout (10s default), returns structured dict with title/links/snippet
- [ ] `crawl_page.py` handles HTTP errors gracefully (returns error dict, does not raise)
- [ ] `seed_discovery.py` filters results to `.fi` TLD only
- [ ] Map node parallelism works (crawls multiple pages via `max_items: 10`)
- [ ] Output `sitemap_overview` contains: domain name, page count, hierarchical link structure, content summaries
- [ ] Unit tests for `crawl_page` (mocked HTTP) and `seed_discovery` (mocked search API)
- [ ] README.md with usage instructions, required extras (`digest`, `websearch`), example output
- [ ] No new core dependencies — uses existing `digest`/`websearch` extras only
- [ ] Tests added with `@pytest.mark.req` traceability
- [ ] `plan` node state_key is `search_queries` (not `seed_urls` — output is queries, not URLs)
- [ ] No `max_pages` state variable — crawl cap is controlled by map node's `max_items` config

## Amendments from Judgement

The following issues were identified during Judgement review and are resolved in this proposal:

1. **No `crawl` extra** — The original proposal introduced a new `crawl` optional extra in `pyproject.toml`, contradicting the AC that no new dependencies are needed. Resolved: use existing `digest` + `websearch` extras. Document install as `pip install -e ".[digest,websearch]"`.

2. **Removed `max_pages` state variable** — `max_pages` was declared in state but never wired to any node. The map node's `max_items: 10` config controls the crawl cap. Removed `max_pages` from state and CLI examples.

3. **Renamed `seed_urls` → `search_queries`** — The `plan` node produces search queries for the `discover` node, not URLs. Renamed `state_key` from `seed_urls` to `search_queries` to accurately reflect the data semantics. The `discover` node reads `search_queries` and outputs `discovered_urls`.

4. **Fixed `exports` syntax** — Original used list format (`- key: sitemap_overview`). Corrected to dict-keyed format (`sitemap_overview: {format: markdown}`) matching the `storage/export.py` contract.

## Alternatives Considered

### 1. Tavily-only approach (no direct crawling)
Tavily's `include_raw_content` already fetches page content. Could avoid `httpx`/`beautifulsoup4` entirely. **Rejected** because: link structure extraction requires HTML parsing that Tavily doesn't provide; the demo's value is showing direct HTTP tool integration.

### 2. Scrapy integration
Full-featured crawl framework. **Rejected** because: too heavyweight for a demo; introduces a large dependency; YAMLGraph's map node already provides the parallelism pattern.

### 3. Recursive crawl with loop node
Use YAMLGraph's loop/conditional edges to recursively crawl discovered links. **Deferred** because: adds complexity beyond the demo's scope; a single-depth crawl demonstrates the pattern sufficiently. Could be a follow-up FR for multi-depth crawling.

### 4. Generic domain crawler (not `.fi`-scoped)
Remove the country-level constraint. **Rejected** because: unbounded crawl scope is dangerous for a demo; `.fi` scoping provides a natural boundary and a concrete use case.

## Related

- `examples/demos/tavily_rag/` — Existing domain-scoped retrieval demo (FR-053, CAP-25)
- `examples/demos/web-research/` — DuckDuckGo agent research demo
- `examples/demos/python-map/` — Python tool + map node pattern demo (FR-021)
- `examples/demos/horoscope/` — Map node with collect pattern (FR-201)
- `pyproject.toml` extras: `digest` (httpx, beautifulsoup4), `websearch` (ddgs), `tavily`
