# Feature Request: FR-784 — Playwright Network Sniff Utility

**Priority:** LOW
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-13
**First consumer / first event:** FR-789 browser-sniff step graph,
the first time it needs to capture XHR/fetch requests from an SPA
page that hides its API behind client-side rendering.

**Parent plan:** `docs/adaptive-probing-plan.md` §5

## Summary

Create `network-sniff.js` — a Playwright-based utility that loads a URL
headless, captures XHR/fetch network requests, and outputs structured
JSON — plus its `network_sniff.tool.yaml` FR-768 manifest.

## Value Statement

The browser-sniff step graph (FR-789) gets a deterministic, timeboxed
tool for capturing API calls from SPAs that cannot be discovered by
static page analysis alone.

## Problem

Some government data portals (Liferay AJAX, React SPAs) load their
data APIs entirely through client-side JavaScript. Static `curl` analysis
finds HTML, not API endpoints. The only way to discover the actual API
URLs is to load the page in a browser and observe network traffic.

## Ideal Result

`node network-sniff.js https://example.com --timeout 10000` outputs a
JSON array of captured XHR/fetch requests with URL, method, status,
content-type, and response body preview — filterable to data-carrying
requests vs telemetry/analytics noise.

## Proposed Solution

### `network-sniff.js`

```javascript
// Playwright script: load URL, capture network, output JSON
// - Launch headless Chromium
// - Intercept XHR/fetch requests via page.route() or response events
// - Filter: status 200, content-type JSON/XML, exclude known analytics domains
// - Output: [{url, method, status, content_type, body_preview}]
// - Hard timeout parameter (default 10s)
// - Exit cleanly on timeout or page load complete
```

### `network_sniff.tool.yaml`

```yaml
name: network_sniff
description: "Load a URL in headless Chromium, capture XHR/fetch requests, return JSON inventory of data-carrying API calls"
runtime:
  type: shell
  command: "node examples/api-discovery/tools/network-sniff.js {url} --timeout {timeout}"
```

### Dependencies

- Node.js (assumed available)
- Playwright (`npx playwright install chromium` — one-time setup)
- No Python dependencies

## Acceptance Criteria

- [ ] AC-01: `network-sniff.js` exists under `examples/api-discovery/tools/`
- [ ] AC-02: Running against a known SPA URL captures at least one XHR/fetch request
- [ ] AC-03: Output is valid JSON array with `url`, `method`, `status`, `content_type` fields
- [ ] AC-04: Hard timeout prevents hanging on slow/broken pages
- [ ] AC-05: Analytics/telemetry domains filtered from output
- [ ] AC-06: `network_sniff.tool.yaml` manifest passes `yamlgraph graph lint` when referenced
- [ ] AC-07: Auth tokens / CAPTCHA detected → flagged in output, not treated as error

## Alternatives Considered

- **Python + selenium:** heavier, worse network interception API
- **mitmproxy:** too complex for this use case; a proxy between browser and server when we only need to observe
- **Chrome DevTools Protocol directly:** Playwright wraps this; no reason to go lower

## Related

- FR-768 (tool manifests)
- FR-789 (browser-sniff step graph — the consumer)
- `docs/adaptive-probing-plan.md` §4.4

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
