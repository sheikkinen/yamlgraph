# Feature Request: FR-785 — API Discovery Endpoint-Probe Step Graph

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced 2026-08-13 — AC-01..AC-08 delivered; 19/19 tests green (REQ-YG-586, CAP-225)
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
- **Manifest:** `examples/api-discovery/steps/endpoint_probe.tool.yaml` with `runtime.type: graph`, path `endpoint-probe/graph.yaml`, input mapping for `candidate_urls` and `max_iterations`, output key `probe_result`
- **Architecture:** agent-only. No `type: map` fan-out — the agent iterates internally using tool calls. If the iteration budget proves insufficient, a separate FR will add map feeder optimization.
- **Schema location:** inline YAML prompt schema under `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml`

### Dependency gate (R-1)

Enforcement cannot begin until FR-783's `curl_probe.tool.yaml` exists, validates,
and exposes the `status`/`content_type`/`redirect`/`body_head` contract. FR-783
is Enforced as of 2026-08-13 — gate satisfied.

### Response taxonomy (R-3)

The agent must handle these cases deterministically:

| Status | Interpretation | Action |
|--------|---------------|--------|
| 403 | Possibly blocked User-Agent | Retry with alternate UA |
| 404 on `/api` | Path not found | Try `/api/v1`, `/api/v2`, `/v1` |
| 200 + HTML content | Portal page, not API | Route to `html_pages` |
| 200 + JSON/XML | Live API endpoint | Add to `live_endpoints` |
| 000 (timeout) repeated | Geo-blocked or down | Set `verdict_hint: "geo_blocked"` |
| 200 + XML | OData/SOAP/RSS/Atom | Classify and add to `live_endpoints` with content_type |

### Live smoke target (R-5)

Exact smoke command:
```bash
yamlgraph graph run examples/api-discovery/steps/endpoint-probe/graph.yaml \
  --var candidate_urls='["https://pxdata.stat.fi/PxWeb/api/v1/fi"]' \
  --var max_iterations=5 --full
```

Expected assertions:
- `probe_result.live_endpoints` contains entry with `url` matching `pxdata.stat.fi`
- That entry has `status: 200` and `content_type` containing `json`
- `probe_result.html_pages` is empty (direct API hit)

If network/service unavailable, record as blocked — does not satisfy AC-08.

## Alternatives Considered (R-6)

| Alternative | Disposition |
|---|---|
| YAML branch table for each status | Rejected: `regex_fourth_exclusion` — grows unbounded with new cases |
| Subgraph node (not manifest) | Rejected: tool manifest provides reuse across consumers (FR-768 doctrine) |
| Map feeder + agent | Deferred: optimization for a separate FR if agent-only proves too slow |
| One-big-orchestrator agent | Rejected: contained step graph is independently testable and reusable |

## Acceptance Criteria

- [ ] AC-01: FR-783's `curl_probe` manifest exists and validates before FR-785 enforcement begins
- [ ] AC-02: `examples/api-discovery/steps/endpoint-probe/graph.yaml` exists as agent-only graph with bounded `max_iterations`
- [ ] AC-03: Prompt/schema artifacts under `examples/api-discovery/steps/endpoint-probe/prompts/`
- [ ] AC-04: `examples/api-discovery/steps/endpoint_probe.tool.yaml` with `runtime.type: graph`, relative path, input mapping, output key
- [ ] AC-05: `ProbeResult`/`EndpointHit` schema rejects missing fields, accepts proposed shape
- [ ] AC-06: Deterministic tests prove 403→UA retry, 404→path variants, 200+HTML→html_pages, 000→geo_blocked, XML→classification
- [ ] AC-07: `max_iterations` prevents runaway (assertion on tool-call count or state)
- [ ] AC-08: Live smoke against `pxdata.stat.fi/PxWeb/api/v1/fi` proves ProbeResult
- [ ] AC-09: `yamlgraph graph lint` passes; authoring report honest
- [ ] AC-10: No files under `yamlgraph/` change
- [ ] AC-11: Changelog fragment and diary reflection

## Related

- FR-783 (curl_probe manifest — the tool this agent uses) — **Enforced**
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.2

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
