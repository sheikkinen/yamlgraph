# .fi Domain Crawler Demo

Country-level sitemap discovery pipeline for `.fi` domains (FR-205).

## What It Does

1. **Plan** — LLM generates 3–5 DuckDuckGo search queries scoped to `.fi`
2. **Discover** — Executes queries via DuckDuckGo, filters results to `.fi` TLD
3. **Crawl** — Map node fans out over discovered URLs (max 10), fetching pages in parallel
4. **Summarise** — LLM synthesises crawl data into a sitemap-style Markdown overview

## Prerequisites

```bash
pip install -e ".[digest,websearch]"
```

- `digest` provides `httpx` and `beautifulsoup4` for page crawling
- `websearch` provides `ddgs` for DuckDuckGo search

## Usage

```bash
yamlgraph graph lint examples/demos/fi_domain_crawl/graph.yaml

yamlgraph graph run examples/demos/fi_domain_crawl/graph.yaml \
  --var seed_query="Helsinki libraries" --full
```

## Pipeline

```
START → plan → discover → crawl (map: max 10) → summarise → END
         ↓        ↓            ↓                    ↓
   search_queries  discovered_urls  crawl_results[]  sitemap_overview
```

## Output

The `sitemap_overview` contains:
- Domain name(s) crawled
- Page count
- Hierarchical link structure
- Per-page content summaries

Exported to `sitemap_overview.md` via the `exports` section.

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Pipeline definition with map node and exports |
| `prompts/plan_crawl.yaml` | LLM prompt to generate `.fi`-scoped search queries |
| `prompts/summarise_site.yaml` | LLM prompt to synthesise sitemap overview |
| `nodes/crawl_page.py` | HTTP fetch + BeautifulSoup link/title extraction |
| `nodes/seed_discovery.py` | DuckDuckGo search filtered to `.fi` TLD |

## Key Concepts

- **`parse_json: true`** on plan node — LLM returns a JSON array of search queries
- **Map `max_items: 10`** — caps parallel crawls to avoid excessive HTTP requests
- **Graceful error handling** — `crawl_page` returns error dicts, never raises
- **`.fi` TLD filtering** — `seed_discovery` enforces country-level domain boundary
