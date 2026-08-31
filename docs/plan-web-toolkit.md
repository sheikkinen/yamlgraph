# Plan: Web Toolkit — Overview

**Date:** 2026-08-31
**Status:** Draft (pre-FR)
**Scope:** Three composable capabilities for web data acquisition and structuring:
text-only rendering, HAR→OpenAPI synthesis, TLD-scale cataloging.

## Vision

A toolkit that lets YAMLGraph pipelines treat the web as a first-class data
source: render any page as LLM-native plain text, reverse-engineer API specs
from recorded traffic, and classify entire country-code domains into a
structured catalog.

## Prior Art (dispositioned)

| Artifact | FR | Relation |
|----------|----|----------|
| `examples/demos/fi_domain_crawl` | FR-204 | Shipped crawl-and-summarise demo (httpx + BeautifulSoup, map fan-out, LLM synthesis). Component 3 evolves this — refit, don't duplicate. |
| `examples/api-discovery` | FR-783..790 | Tool manifests `fetch_page`, `curl_probe`, `parse_openapi`; step graphs page-analysis / platform-confirm / schema-extract. Component 2 completes this pipeline; component 1's tool lives beside these manifests. |
| `examples/daily_digest/nodes/content.py` | — | BS4 article extraction; superseded for rendering purposes by lynx dump. |
| CAP-120 inter-run state chaining, SQLite checkpointer | — | Enables batched/resumable TLD-scale runs in component 3. |

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
- **Deliverable**: shared tool manifest (under `examples/api-discovery/tools/`
  or `examples/shared/`) + smoke demo graph: URL → dump → summarise.

## Component 2: `har-to-spec` — HAR → OpenAPI synthesis (map-reduce)

The api-discovery pipeline *finds* existing specs; this *synthesizes* a spec
where none is published, from a recorded browser session.

- **Parse boundary (deterministic Python tool)**: HAR JSON → Pydantic entry
  records (method, URL template, status, MIME, request/response body samples).
  **Security: scrub cookies, auth headers, and tokens at this boundary** —
  HAR files leak credentials by design.
- **Map**: group entries by endpoint family; per group, an LLM node infers
  path templates (`/users/123` → `/users/{id}`), parameter types, and
  response schemas (inline Pydantic schema output).
- **Reduce**: assemble OpenAPI 3.1 YAML from the per-group fragments.
- **Acceptance witness**: round-trip the emitted spec through the existing
  `parse_openapi` tool — the spec we generate must parse with our own parser.
- **Placement**: `examples/api-discovery/steps/har-to-spec/`.

## Component 3: `.fi` TLD catalog — lynx + classify

Evolution of FR-204's demo into a country-scale cataloging pipeline.

- **Pipeline**: seed domains → map(lynx_render homepage) → LLM classify with
  inline schema (category, language, organisation type, API presence,
  liveness) → aggregate into a JSONL/SQLite catalog artifact.
- **Changes vs FR-204**: swap `crawl_page` (httpx+BS4) for `lynx_render`;
  add the classify stage; add catalog aggregation.
- **The hard problem is seeds, not crawling**: Traficom publishes .fi domain
  open data (~550k domains); alternatives are CT logs and the Common Crawl
  index. Requires a research step before the FR freezes scope.
- **Scale strategy**: demo caps N (map `max_items`); production runs are
  batched with the SQLite checkpointer and inter-run state chaining (CAP-120).
- **Politeness constraints**: robots.txt respect, per-host rate limits,
  identifying User-Agent — these are FR acceptance criteria, not afterthoughts.

## Sequencing

| FR | Scope | Depends on | Size |
|----|-------|------------|------|
| A | `lynx_render` tool manifest + smoke demo | — | S |
| B | `har-to-spec` step graph | — (parallel to A) | M |
| C | fi-catalog: refit FR-204 on lynx + classify + batched runs | A | M |

Each component enters as a `.chaplain/inbox/` proposal and follows
Plan → Judge → Enforce. All graph authoring goes through the
`scripts/author.sh` route per graph-authoring doctrine.

## Open Questions

1. **Seed source for .fi**: Traficom open-data domain list vs Common Crawl
   index vs CT logs — resolve in FR-C research.
2. **Lynx in CI**: demo-gate requires a runnable demo. Install lynx via
   brew/apt in CI, or mark the demo local-only with a recorded
   `demo-output.log`?
3. **HAR sourcing for the demo**: ship a scrubbed fixture HAR
   (deterministic, offline-testable) — which public API to record?
4. **Catalog artifact home**: JSONL under `outputs/` for the demo; does a
   production catalog deserve its own repo/dataset boundary?
