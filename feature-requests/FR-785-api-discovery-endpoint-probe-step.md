# Feature Request: FR-785 — API Discovery Endpoint-Probe Step Graph

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-13
**First consumer / first event:** FR-791 API discovery orchestrator,
the first time it needs to probe candidate URLs for live API endpoints —
this is the core adaptive loop of the entire pipeline.

**Parent plan:** `docs/adaptive-probing-plan.md` §4.2

## Summary

Create the endpoint-probe step: an agent graph that takes candidate URLs,
probes them with `curl_probe`, interprets HTTP responses adaptively (retries,
path variants, content-type discrimination), and returns structured
`ProbeResult` with live endpoints and HTML pages for further analysis.
Packaged as a `runtime.type: graph` tool manifest.

## Value Statement

The orchestrator gets a self-contained, reusable "is there an API at
this URL?" tool that handles the full retry/interpretation doctrine —
the core value of the entire API discovery pipeline.

## Problem

URL probing is not a single curl call. A `403` might mean "try a different
User-Agent." A `404` on `/api` might mean "try `/api/v1`." A `200` returning
HTML is a portal page, not an API. Encoding each case as YAML branches
reproduces the `regex_fourth_exclusion` trap. An agent with the strategies
as prompt doctrine and `curl_probe` as its tool handles the open-ended
interpretation naturally.

## Ideal Result

Given `candidate_urls: ["https://stat.fi/api", "api.stat.fi"]`, the step
returns `ProbeResult` with confirmed live endpoints, their content types,
and any HTML pages that need page-analysis — all within a bounded
`max_iterations` budget.

## Proposed Solution

- **Graph type:** single `type: agent` node with `curl_probe` manifest tool
- **Prompt doctrine:** adaptive retry strategies (§4.2 of parent plan)
- **Output schema:** `ProbeResult { live_endpoints: list[EndpointHit], html_pages: list[str], verdict_hint: str | None }`
- **`EndpointHit`:** `{ url: str, status: int, content_type: str, body_preview: str }`
- **Manifest:** `steps/endpoint_probe.tool.yaml` with `runtime.type: graph`
- **Open question:** whether to use `type: map` fan-out for the initial fixed-pattern scan, feeding results to the agent for interpretation (feeder pattern, FR-773)

## Acceptance Criteria

- [ ] AC-01: Step graph exists under `examples/api-discovery/steps/endpoint-probe/graph.yaml`
- [ ] AC-02: Graph-runtime tool manifest `steps/endpoint_probe.tool.yaml` exists
- [ ] AC-03: Agent handles 403 → User-Agent retry, 404 → path variants, 200+HTML → html_pages
- [ ] AC-04: Output conforms to `ProbeResult` Pydantic schema
- [ ] AC-05: `max_iterations` budget prevents runaway probing
- [ ] AC-06: Smoke test against a known Finnish API (e.g., stat.fi PxWeb) returns correct result
- [ ] AC-07: Graph authored via `scripts/author.sh`; lint and smoke pass

## Related

- FR-783 (curl_probe manifest — the tool this agent uses)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.2

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
