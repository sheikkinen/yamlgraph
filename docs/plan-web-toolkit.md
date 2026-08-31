# Plan: Web Toolkit — Overview

**Date:** 2026-08-31 (rev 3 — operator steer: C is the primary focus; map
primitive promoted to component D; B parked for research)
**Status:** Draft (pre-FR)
**Scope:** A TLD-scale classification pipeline (C, primary) and the two
foundations it stands on: a text-render graph tool (A) and a resumable
storage-backed map primitive (D). HAR→OpenAPI (B) parked pending research.

## Vision

Catalog and classify an entire country-code domain (*.fi) with a YAMLGraph
pipeline. The build forces two durable framework assets into existence: a
fetch-as-text tool usable inside any graph, and a map primitive that survives
500k-item runs.

## Priority Order

1. **C — .fi TLD catalog**: the primary analysis focus and the driving use case.
2. **D — resumable storage-backed map**: new framework primitive C requires;
   likely the most durable output for the repo.
3. **A — lynx_render**: graph tool consumed by C's live-fetch tier and by any
   future research graph.
4. **B — har-to-spec**: parked; needs more info before an FR (see Parked).

## Prior Art (dispositioned)

| Artifact | FR | Relation |
|----------|----|----------|
| `examples/demos/fi_domain_crawl` | FR-204 | Shipped crawl-and-summarise demo (httpx + BeautifulSoup, map fan-out, LLM synthesis). C evolves this — refit, don't duplicate. |
| `examples/api-discovery` | FR-783..790 | Tool manifests `fetch_page`, `curl_probe`, `parse_openapi`; step graphs. A's tool lives beside these manifests; CAP-226's SPA-shell/browser-sniff distinction is the precedent for A's JS policy. |
| `examples/daily_digest/nodes/content.py` | — | BS4 extraction; its committed `digest.db` dedup is the precedent for C's incremental re-crawl. |
| map `max_items` + CAP-120 inter-run state chaining + SQLite checkpointer | — | The current workaround stack D replaces with a primitive. |
| **Common Crawl WET files (external)** | — | .fi pages already crawled *and rendered to text*. C v1 classifies from CC extracts; live-fetch only gaps/refresh. Kills most cost, politeness, and seed problems. |
| **mitmproxy2swagger / har2openapi (external OSS)** | — | Deterministic HAR→OpenAPI converters exist; any future B wraps, not reimplements. |

## Component C (primary): `.fi` TLD catalog — classify at country scale

Evolution of FR-204's demo into the toolkit's driving analysis pipeline.

- **v1 is Common Crawl, not crawling**: CC WET files carry pre-rendered text
  for .fi pages — classify from those, live-fetch (A) only for gaps and
  refresh. The Traficom open-data domain list (~550k domains) is the
  completeness reference.
- **Pipeline**: CC/seed domains → deterministic pre-filter (DNS resolve +
  HTTP HEAD; LLM never sees dead sites) → **D-map**(text extract → LLM
  classify with inline schema: category, language, organisation type, API
  presence, liveness, `render: empty|thin|full`) → catalog artifact
  (SQLite/JSONL).
- **Cost model (required before scope freeze)**: haiku-class model pinned,
  token cap per page dump, measured cost per 1k domains from a pilot batch.
  550k × classify is real money — no full run without the pilot number.
- **Evaluation (read_raw_output_first)**: before any aggregate accuracy claim,
  dump N classified samples with their source text and read them; spot-check
  accuracy criterion in the FR. An unaudited catalog is a liability.
- **Incremental semantics**: dedup + change detection + entry TTL (precedent:
  daily_digest's digest.db). Liveness re-check is deterministic and LLM-free.
- **Politeness constraints** (live-fetch tier only): robots.txt respect,
  per-host rate limits, identifying User-Agent — FR acceptance criteria.
- **Named consumer**: public-sector platform census (which municipalities run
  CKAN/PxWeb/OData) extends api-discovery to catalog scale; plus liveness
  monitoring as a free LLM-less byproduct.

## Component D: resumable storage-backed map primitive

C at 500k items is a scale the map node has never seen; `max_items` +
CAP-120 chaining is a workaround, not a primitive. D makes it one.

- **Contract sketch**: a map variant (or map option set) with
  - **item-level durability**: each completed item's result persists to
    storage (SQLite; same family as the checkpointer) the moment it finishes —
    a crash at item 312,401 loses one item, not the run;
  - **resume-by-skip**: re-running the graph skips items whose results exist
    (keyed by stable item id), extending `skip_if_exists` semantics from
    node-level to item-level;
  - **chunked execution**: bounded batches with configurable concurrency, so
    memory and rate limits hold at 500k;
  - **progress observability**: counts/failures queryable mid-run (FR-723
    route-log style JSONL or the OTel spans from FR-759).
- **Boundary decision for the FR**: extend the existing map node vs a new
  `durable_map` type — judged against LangGraph checkpointer granularity
  (superstep-level, not item-level at fan-out) so the primitive is built where
  LangGraph actually stops helping.
- **Witness**: kill -9 mid-run at scale N, re-run, prove completed items are
  not re-executed and the final catalog is identical to an uninterrupted run.
- **C is the acceptance demo**: the pilot batch runs on D.

## Component A: `lynx_render` — text-render tool for graphs

A graph tool (FR-768-style manifest), consumed by C's live-fetch tier and by
research graphs generally — fetch-as-text *inside* a graph, which the
chat-surface `fetch_webpage` is not.

- **Form**: shell tool manifest wrapping `lynx -dump`; modes `-nolist`
  (reading text) and `-listonly` (numbered link inventory).
- **Boundary rules** (no silent fallbacks): fail fast if binary missing;
  normalize encoding; cap dump size; per-fetch timeout; Finnish-encoding
  witness fixture (ä/ö, legacy ISO-8859-1 site).
- **JS policy**: empty/thin dump is **a signal, not a failure** — returned
  tagged (`render: empty|thin|full`), classified downstream as "JS-required".
  Headless escalation (per CAP-226) is a separate optional tier.
- **Fork for the judge**: lynx (system binary, better layout fidelity) vs
  html2text/trafilatura (pip dep, cheaper CI) — decided on same-page dump
  evidence, not preference. Jina Reader rejected: external service dependency.
- **Deliverable**: tool manifest + smoke demo graph (URL → dump → summarise).

## Parked: B — `har-to-spec` (needs more info)

HAR→OpenAPI synthesis is deferred until these are answered; no FR yet:

1. Concrete first HAR: which real system's traffic do we convert first
   (public API fixture vs an actual undocumented internal API)?
2. mitmproxy2swagger evaluation: run it on that HAR — how much does the
   deterministic converter already deliver, and what precisely is left for
   the LLM (naming, path templating, schema inference from samples)?
3. Capture path: manual DevTools export vs agent-captured via Chrome DevTools
   MCP network tools.
4. Credential scrubbing boundary: mandatory in any variant.

When answered, B lands as `examples/api-discovery/steps/har-to-spec/` with the
`parse_openapi` round-trip as acceptance witness.

## Sequencing

| FR | Scope | Depends on | Size |
|----|-------|------------|------|
| D | resumable storage-backed map primitive + kill-and-resume witness | — | M |
| A | text-render tool (fork resolved by judge) + smoke demo | — (parallel to D) | S |
| C | fi-catalog pilot on D + A: pre-filter, classify, catalog artifact, cost number | D, A | M |
| C2 | full-run decision gated on C's pilot cost/accuracy numbers | C | — |
| B | parked — research questions above | — | — |

Each component enters as a `.chaplain/inbox/` proposal and follows
Plan → Judge → Enforce. All graph authoring goes through the
`scripts/author.sh` route per graph-authoring doctrine.

## Open Questions

1. **D's home**: map node option set vs new node type — where does LangGraph's
   checkpointer actually stop helping at fan-out scale?
2. **A's dependency fork**: lynx vs html2text/trafilatura, evidence-based.
3. **CC WET freshness**: how stale is Common Crawl for the .fi long tail, and
   what refresh fraction does that imply for the live-fetch tier?
4. **Catalog artifact home**: SQLite under `outputs/` for the pilot; a full
   production catalog likely deserves its own repo/dataset boundary.
