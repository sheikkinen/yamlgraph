# Feature Request: FR-786 — API Discovery Page-Analysis Step Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-13
**First consumer / first event:** FR-791 API discovery orchestrator,
the first time endpoint-probe returns HTML pages that need source
inspection to find embedded API references.

**Parent plan:** `docs/adaptive-probing-plan.md` §4.3

## Summary

Create the page-analysis step: an agent graph that inspects HTML page
source for embedded API URLs, JavaScript bundle references, platform
fingerprints (PxWeb, CKAN, OData, etc.), and SPA indicators. Packaged
as a `runtime.type: graph` tool manifest.

## Value Statement

The orchestrator can distinguish "this URL returned HTML because it's
a portal page with an API behind it" from "this URL is just a website"
— the critical routing decision for whether to try browser-sniff.

## Problem

When endpoint-probe gets a `200` with HTML content-type, it could be
a portal page hosting an API (Swagger UI, CKAN frontend, PxWeb table
selector) or a plain website. Page source inspection finds: `<script src>`
bundles with fetch/axios calls, `data-api-url` attributes, `/wp-json`
refs, CKAN `/api/3/action` links, PxWeb table URLs, SwaggerUI includes.

## Ideal Result

Given `html_pages: ["https://data.gov.fi"]`, the step returns
`PageAnalysis` identifying platform candidates, extracted API URLs,
and whether the page is an SPA requiring browser-sniff.

## Proposed Solution

- **Graph type:** single `type: agent` node with `fetch_page` manifest tool
- **Platform catalog:** supplied via `data_files` directive, not hardcoded in prompt
- **Output schema:** `PageAnalysis { api_found: bool, is_spa: bool, platform_candidates: list[str], api_urls: list[str] }`
- **Manifest:** `steps/page_analysis.tool.yaml` with `runtime.type: graph`

## Acceptance Criteria

- [ ] AC-01: Step graph exists under `examples/api-discovery/steps/page-analysis/graph.yaml`
- [ ] AC-02: Graph-runtime tool manifest `steps/page_analysis.tool.yaml` exists
- [ ] AC-03: Agent extracts API URLs from page source (script tags, data attributes, inline fetch calls)
- [ ] AC-04: Platform fingerprinting identifies at least CKAN, PxWeb, SwaggerUI, OData
- [ ] AC-05: SPA detection flags pages that need browser-sniff
- [ ] AC-06: Output conforms to `PageAnalysis` Pydantic schema
- [ ] AC-07: Graph authored via `scripts/author.sh`; lint and smoke pass

## Related

- FR-783 (fetch_page manifest — the tool this agent uses)
- FR-789 (browser-sniff — triggered when `is_spa == true AND api_found == false`)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.3

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
