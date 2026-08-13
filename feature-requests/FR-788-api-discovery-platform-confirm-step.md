# Feature Request: FR-788 — API Discovery Platform-Confirm Step Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-13
**First consumer / first event:** FR-791 API discovery orchestrator,
the first time page-analysis returns platform candidates that need
confirmation with family-specific queries.

**Parent plan:** `docs/adaptive-probing-plan.md` §4.5

## Summary

Create the platform-confirm step: an agent graph that takes platform
candidates and base URLs, runs family-specific confirmation queries
(CKAN status_show, PxWeb subject tree, OData $top=1, etc.), and returns
a confirmed platform identification with sample data. Packaged as a
`runtime.type: graph` tool manifest.

## Value Statement

The orchestrator gets proof that a platform identification is correct —
not just "the URL responded 200" but "the CKAN package_search returned
real dataset records" (`plausible_wrong_answer` guard: assert substance,
not shape).

## Problem

Platform fingerprinting from page source produces candidates, not
confirmations. A page with `/api/3/action` links *probably* runs CKAN,
but could be a custom API mimicking the path structure. Confirmation
requires family-specific queries that return real data.

## Ideal Result

Given `platform_candidates: ["ckan"], base_url: "https://data.gov.fi"`,
the step returns `PlatformConfirmation` with `confirmed: true` and a
sample response proving the platform identification.

## Proposed Solution

- **Graph type:** single `type: agent` node with `curl_probe` manifest tool (reused — one tool, four consumers)
- **Family-specific confirmation queries:**
  - CKAN: `status_show`, `package_search?rows=0`
  - PxWeb: `/api/v1/{lang}/{db}`
  - OData: `?$top=1&$format=json`
  - OpenAPI: spec fetch + endpoint count
  - WordPress: `/wp-json/wp/v2/types`
  - JSON-stat: `{cube}.json`
- **Output schema:** `PlatformConfirmation { family: str, base_url: str, confirmed: bool, sample_response: str }`
- **Manifest:** `steps/platform_confirm.tool.yaml` with `runtime.type: graph`

## Acceptance Criteria

- [ ] AC-01: Step graph exists under `examples/api-discovery/steps/platform-confirm/graph.yaml`
- [ ] AC-02: Graph-runtime tool manifest `steps/platform_confirm.tool.yaml` exists
- [ ] AC-03: Agent runs family-specific queries returning real data, not just status checks
- [ ] AC-04: Output conforms to `PlatformConfirmation` Pydantic schema
- [ ] AC-05: Smoke test against a known CKAN or PxWeb instance confirms platform correctly
- [ ] AC-06: Graph authored via `scripts/author.sh`; lint and smoke pass

## Related

- FR-783 (curl_probe manifest — the tool this agent reuses)
- FR-786 (page-analysis — provides the platform candidates)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.5

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
