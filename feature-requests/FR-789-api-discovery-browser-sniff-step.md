# Feature Request: FR-789 — API Discovery Browser-Sniff Step Graph

**Priority:** LOW
**Type:** Feature
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-13
**First consumer / first event:** FR-791 API discovery orchestrator,
when page-analysis returns `is_spa == true AND api_found == false` —
the expensive last resort for SPAs that hide APIs behind client-side
rendering.

**Parent plan:** `docs/adaptive-probing-plan.md` §4.4

## Summary

Create the browser-sniff step: an agent graph that loads a URL in
headless Chromium via the `network_sniff` tool (FR-784), captures
XHR/fetch requests, and identifies data-carrying API calls vs
telemetry noise. Packaged as a `runtime.type: graph` tool manifest.

## Value Statement

The orchestrator can discover APIs hidden behind client-side rendering
— the only remaining path when static analysis fails, covering SPAs
like Liferay AJAX portals and React data dashboards.

## Problem

Some government portals load data APIs entirely via JavaScript — no
API URLs appear in the page source. The only discovery method is to
load the page in a browser and observe what network requests it makes.

## Ideal Result

Given a known SPA URL, the step returns `SniffResult` with captured
API calls, their URL patterns, and whether authentication is required.

## Proposed Solution

- **Graph type:** single `type: agent` node with `network_sniff` manifest tool (FR-784)
- **Output schema:** `SniffResult { api_calls: list[CapturedRequest], auth_required: bool }`
- **`CapturedRequest`:** `{ url: str, method: str, status: int, content_type: str, body_preview: str }`
- **Manifest:** `steps/browser_sniff.tool.yaml` with `runtime.type: graph`
- **Failure mode:** auth token / CAPTCHA → `needs_manual` verdict hint, not error

## Acceptance Criteria

- [ ] AC-01: Step graph exists under `examples/api-discovery/steps/browser-sniff/graph.yaml`
- [ ] AC-02: Graph-runtime tool manifest `steps/browser_sniff.tool.yaml` exists
- [ ] AC-03: Agent uses `network_sniff` to capture XHR/fetch requests
- [ ] AC-04: Output conforms to `SniffResult` Pydantic schema
- [ ] AC-05: Auth/CAPTCHA detection returns `needs_manual` hint, not error
- [ ] AC-06: Graph authored via `scripts/author.sh`; lint and smoke pass

## Related

- FR-784 (network-sniff.js + manifest — the tool this agent uses)
- FR-786 (page-analysis — provides the SPA routing trigger)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.4

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
