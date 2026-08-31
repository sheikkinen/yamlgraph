# Plan: Web Toolkit — Overview

**Date:** 2026-08-31 (rev 2 — reflection pass: consumers, alternatives, dispositions)
**Status:** Draft (pre-FR)
**Scope:** Three composable capabilities for web data acquisition and structuring:
text-only rendering, HAR→OpenAPI synthesis, TLD-scale cataloging.

## Vision

A toolkit that lets YAMLGraph pipelines treat the web as a first-class data
source: render any page as LLM-native plain text, reverse-engineer API specs
from recorded traffic, and classify entire country-code domains into a
structured catalog.

## First Consumers (would_you_use_this)

Honest ranking by named consumer and triggering event — this drives sequencing:

1. **B (har-to-spec)**: the api-discovery pipeline, at the exact moment
   discovery fails to find a published spec. Second consumer: legacy/internal
   system reverse-engineering (medical/enterprise APIs where the vendor spec
   never existed and HAR is the only spec).
2. **A (lynx_render)**: the agent itself, during Commandment-1 research —
   a fetch-as-text tool usable *inside graphs* (chat-surface `fetch_webpage`
   is not). Makes research a graph pattern.
3. **C (fi-catalog)**: weakest as a standalone dataset — no named reader.
   Becomes real when merged with api-discovery into a **public-sector platform
   census** (which Finnish municipalities run CKAN/PxWeb/OData), and as a
   scale stress test for the framework (see Framework Angle).

## Prior Art (dispositioned)

| Artifact | FR | Relation |
|----------|----|----------|
| `examples/demos/fi_domain_crawl` | FR-204 | Shipped crawl-and-summarise demo (httpx + BeautifulSoup, map fan-out, LLM synthesis). Component 3 evolves this — refit, don't duplicate. |
| `examples/api-discovery` | FR-783..790 | Tool manifests `fetch_page`, `curl_probe`, `parse_openapi`; step graphs page-analysis / platform-confirm / schema-extract. Component 2 completes this pipeline; component 1's tool lives beside these manifests. CAP-226's SPA-shell/browser-sniff distinction is the precedent for the JS policy below. |
| `examples/daily_digest/nodes/content.py` | — | BS4 article extraction; superseded for rendering purposes by lynx dump. Its committed `digest.db` dedup is the precedent for C's incremental re-crawl. |
| CAP-120 inter-run state chaining, SQLite checkpointer | — | Enables batched/resumable TLD-scale runs in component 3. |
| **mitmproxy2swagger / har2openapi (external OSS)** | — | Deterministic HAR→OpenAPI converters already exist. B must wrap, not reimplement: LLM only where they are weak — path templating, semantic naming, schema inference from body samples. Cuts B from M to S. |
| **Common Crawl WET files (external)** | — | .fi pages already crawled *and rendered to text*. C v1 needs no live crawling: classify from CC extracts, live-fetch only gaps/refresh. Kills most of the cost, politeness, and seed problems. |

## Component 1: `lynx_render` — text-only page rendering

Revival of the Lynx browser as a rendering boundary tool.

- **Form**: FR-768-style shell tool manifest wrapping `lynx -dump`.
  Two modes: `-dump -nolist` (reading text) and `-dump -listonly`
  (numbered link inventory).
- **Why lynx over BS4 extraction**: real layout rendering (tables, reading
  order, form labels), zero Python dependencies, battle-tested since 1992,
  and its output is exactly the modality LLMs consume best.
- **Boundary rules** (Commandment 6 — no silent fallbacks):
  - Fail fast if `lynx` binary missing; no httpx fallback.
  - Normalize encoding at the tool boundary; cap dump size; per-fetch timeout.
  - Finnish-encoding witness fixture (ä/ö, legacy ISO-8859-1 site) in tests.
- **JS policy (the blind spot, stated)**: lynx renders zero JavaScript; many
  modern homepages are SPA shells that dump near-empty. An empty/thin dump is
  **itself a signal**, not a failure — the tool returns it tagged
  (`render: empty|thin|full`) and consumers classify it ("JS-required").
  Headless escalation (browser-sniff, per CAP-226) is a separate optional
  tier, never a silent fallback.
- **Alternative to disposition in the FR**: `html2text`/`trafilatura` are pip
  deps — dramatically cheaper for CI than a brew/apt system binary. Lynx wins
  only on layout fidelity (tables, forms, reading order). This fork is the
  FR-A judge's main question; nostalgia is not an argument. Jina Reader
  (r.jina.ai) rejected: external service dependency.
- **Deliverable**: shared tool manifest (under `examples/api-discovery/tools/`
  or `examples/shared/`) + smoke demo graph: URL → dump → summarise.

## Component 2: `har-to-spec` — HAR → OpenAPI synthesis (map-reduce)

The api-discovery pipeline *finds* existing specs; this *synthesizes* a spec
where none is published, from a recorded browser session.

- **Wrap, don't reimplement**: mitmproxy2swagger already does deterministic
  HAR→OpenAPI conversion. The graph wraps it as a tool and applies LLM only
  where deterministic conversion is weak: path templating refinement,
  semantic operation naming, descriptions, schema inference from body samples.
- **Parse boundary (deterministic Python tool)**: HAR JSON → Pydantic entry
  records (method, URL template, status, MIME, request/response body samples).
  **Security: scrub cookies, auth headers, and tokens at this boundary** —
  HAR files leak credentials by design.
- **Map**: group entries by endpoint family; per group, an LLM node infers
  path templates (`/users/123` → `/users/{id}`), parameter types, and
  response schemas (inline Pydantic schema output).
- **Reduce**: assemble OpenAPI 3.1 YAML from the per-group fragments.
- **HAR capture path (closing the loop)**: HARs need not be manual DevTools
  exports — Chrome DevTools MCP tools (network request listing) let an agent
  capture its own traffic: browse → capture → synthesize. Record as a usage
  pattern in the README; not a build item for v1.
- **Acceptance witness**: round-trip the emitted spec through the existing
  `parse_openapi` tool — the spec we generate must parse with our own parser.
- **Placement**: `examples/api-discovery/steps/har-to-spec/`.

## Component 3: `.fi` TLD catalog — lynx + classify

Evolution of FR-204's demo into a country-scale cataloging pipeline.

- **v1 is Common Crawl, not crawling**: CC WET files carry pre-rendered text
  for .fi pages — classify from those, live-fetch (lynx_render) only for gaps
  and refresh. Solves seeds, cost, and politeness in one move; the Traficom
  open-data domain list (~550k domains) serves as the completeness reference.
- **Pipeline**: CC/seed domains → deterministic pre-filter (DNS resolve +
  HTTP HEAD; LLM never sees dead sites) → map(text extract) → LLM classify
  with inline schema (category, language, organisation type, API presence,
  liveness, `render: empty|thin|full` from component 1's JS signal) →
  aggregate into a JSONL/SQLite catalog artifact.
- **Changes vs FR-204**: swap `crawl_page` (httpx+BS4) for CC extract /
  `lynx_render`; add pre-filter, classify stage, catalog aggregation.
- **Cost model (required before scope freeze)**: haiku-class model pinned,
  token cap per page dump, measured cost per 1k domains from a pilot batch.
  550k × classify is real money — no full run without the pilot number.
- **Evaluation (read_raw_output_first)**: before any aggregate accuracy claim,
  dump N classified samples with their source text and read them; spot-check
  accuracy criterion in the FR. A catalog nobody has audited is a liability.
- **Incremental semantics**: dedup + change detection + entry TTL (precedent:
  daily_digest's committed digest.db). Liveness re-check is deterministic and
  LLM-free.
- **Scale strategy**: demo caps N (map `max_items`); production runs are
  batched with the SQLite checkpointer and inter-run state chaining (CAP-120).
- **Politeness constraints** (live-fetch tier only): robots.txt respect,
  per-host rate limits, identifying User-Agent — FR acceptance criteria,
  not afterthoughts.

## Framework Angle

C at 550k items is a scale yamlgraph's map node has never seen. The durable
output for this repo may not be the catalog but the primitive the attempt
forces out: **resumable chunked map**. `max_items` + CAP-120 chaining is a
workaround, not a primitive. If C's pilot confirms the gap, that becomes its
own framework FR — likely more valuable than the catalog itself.

## Sequencing (revised: consumer-strength order)

| FR | Scope | Depends on | Size |
|----|-------|------------|------|
| B | `har-to-spec`: wrap mitmproxy2swagger + LLM refinement map-reduce | — | S–M |
| A | text-render tool (lynx vs html2text fork resolved by judge) + smoke demo | — (parallel to B) | S |
| C | fi-catalog: CC-first classify pipeline, pilot batch + cost number before full run | A | M |

B moves first: clearest consumer, smallest honest scope after the
mitmproxy2swagger disposition. C ships pilot-first.

Each component enters as a `.chaplain/inbox/` proposal and follows
Plan → Judge → Enforce. All graph authoring goes through the
`scripts/author.sh` route per graph-authoring doctrine.

## Use Cases

- **Agent self-service research**: lynx_render inside graphs makes
  Commandment-1 research a graph pattern, not a chat-tool pattern.
- **Public-sector platform census**: api-discovery at catalog scale — which
  municipalities expose which platforms; gives C its named consumer.
- **Legacy reverse-engineering**: har-to-spec for undocumented internal or
  medical-domain APIs where HAR is the only spec that will ever exist.
- **Liveness monitoring**: deterministic re-crawl of the catalog for
  dead/parked domain detection — no LLM cost.

## Open Questions

1. **A's dependency fork**: system binary (lynx) vs pip dep (html2text/
   trafilatura) — CI cost vs rendering fidelity; the judge decides on
   evidence (same-page dumps compared), not preference.
2. **Lynx in CI** (if lynx wins): brew/apt install in CI, or local-only demo
   with recorded `demo-output.log`?
3. **HAR fixture for B**: ship a scrubbed, deterministic fixture HAR — which
   public API to record?
4. **Catalog artifact home**: JSONL under `outputs/` for the demo; a
   production catalog likely deserves its own repo/dataset boundary.
5. **CC WET freshness**: how stale is Common Crawl for .fi long tail, and
   what refresh fraction does that imply for the live-fetch tier?
