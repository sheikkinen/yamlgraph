# Feature Request: FR-784 — Playwright Network Sniff Utility

**Priority:** LOW
**Type:** Feature
**Status:** Enforced 2026-08-15 — AC-01..AC-11 delivered; 11/11 tests green incl. six real-Chromium witnesses against the committed fixture (REQ-YG-590, CAP-229)
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

`node network-sniff.js https://example.com --timeout 10000` outputs one
stable JSON object inventorying captured XHR/fetch requests — filtered
to data-carrying requests vs telemetry/analytics noise, with auth/CAPTCHA
walls flagged and token material redacted.

## Proposed Solution

### Output contract (R-1)

`network-sniff.js` emits exactly one JSON object on stdout:

```json
{
  "requests": [CapturedRequest, ...],
  "auth_required": false,
  "needs_manual_reason": null,
  "warnings": []
}
```

- `CapturedRequest`: `{url, method, status, content_type, body_preview,
  classification}` where `classification` is `"data" | "telemetry" | "other"`.
- `auth_required: bool` — true when any XHR/fetch response is 401/403 or
  carries `WWW-Authenticate`.
- `needs_manual_reason`: `"auth_token" | "captcha" | null` — `"captcha"`
  when CAPTCHA provider requests/markup detected (recaptcha, hcaptcha,
  turnstile); `"auth_token"` when an auth wall is detected.
- `warnings: string[]` — e.g. `"timeout: page did not settle within Nms"`.
- Auth walls and timeouts are reported IN the JSON (exit 0), never as
  tool failure.

### Filter and redaction policy (R-4)

- **Eligible resource types:** `xhr`, `fetch` only.
- **Data classification:** status 200 AND content-type matching
  `application/json`, `*+json`, `application/xml`, `text/xml`, `*+xml`.
- **Telemetry classification:** hostname suffix denylist
  (`google-analytics.com`, `googletagmanager.com`, `doubleclick.net`,
  `facebook.net`, `hotjar.com`, `matomo.cloud`, `plausible.io`,
  `segment.io`, `sentry.io`, `mixpanel.com`, `clarity.ms`) OR path
  segment denylist (`/analytics/`, `/telemetry/`, `/collect`, `/track`,
  `/beacon`, `/pixel`). Telemetry requests are classified and ranked
  behind data requests, not silently dropped (demote-never-drop).
- **Everything else:** `"other"`.
- **Preview length:** `body_preview` capped at 500 characters; read only
  for data-classified responses.
- **Redaction:** token-like query parameter values (`token`, `key`,
  `apikey`, `api_key`, `access_token`, `auth`, `authorization`,
  `session`, `secret`, `password`, `sig`, `signature`, `jwt`, `bearer`)
  are replaced with `[REDACTED]` in emitted URLs; JWT-shaped and long
  hex/base64 token literals are redacted from `body_preview`. Request
  and response headers are never emitted (only `content_type`). Cookies
  are never emitted.

### Dependency contract (R-3)

- Committed package boundary `examples/api-discovery/tools/package.json`
  + `package-lock.json` pinning `playwright`.
- One-time setup (documented in `examples/api-discovery/README.md`):

  ```bash
  cd examples/api-discovery/tools
  npm ci
  npx playwright install chromium
  ```

- Missing `playwright` package or Chromium binary → clear non-zero exit
  with a diagnostic naming the install command; never a silent empty
  success.

### `network_sniff.tool.yaml` (R-5)

```yaml
name: network_sniff
description: "Load a URL in headless Chromium, capture XHR/fetch requests, return JSON inventory of data-carrying API calls"
runtime:
  type: shell
  command: "node examples/api-discovery/tools/network-sniff.js {url} --timeout {timeout}"
  parse: json
  timeout: 30
```

FR-768 shell runtime semantics only; `parse: json`; runtime timeout (30s)
bounds the script's own default 10s page timeout plus browser launch.
Validated by the manifest-fixture test in
`tests/unit/test_fr784_network_sniff.py`.

### Deterministic test witness (R-2)

A committed local fixture (`tests/fixtures/fr784_spa/`) served by a
pytest-local HTTP server: an HTML page whose script performs one data
fetch (JSON), one telemetry fetch (denylisted path), and one
token-bearing fetch. Acceptance tests run only against this fixture —
no public website, live portal, or ambient network timing (C-2). Tests
requiring the Chromium binary skip with a named reason when the
committed setup has not been installed.

## Acceptance Criteria (revised per judgement)

- [x] AC-01: `examples/api-discovery/tools/network-sniff.js` exists and accepts `URL` plus `--timeout <ms>`.
- [x] AC-02: The Playwright/Chromium dependency setup is pinned in a committed package boundary with an exact reproducible install command; missing package/browser produces a clear non-zero error.
- [x] AC-03: Running the utility against the committed local SPA fixture captures at least one XHR/fetch data request.
- [x] AC-04: Output is valid JSON object with `requests`, `auth_required`, `needs_manual_reason`, and `warnings`; each request includes `url`, `method`, `status`, `content_type`, and `body_preview`.
- [x] AC-05: Request capture is limited to the declared resource types and content types, including JSON and XML data responses.
- [x] AC-06: The committed fixture proves analytics/telemetry requests are excluded or classified behind data requests according to the declared denylist/ranking policy.
- [x] AC-07: The hard timeout bounds browser launch, page navigation, and response-body reads; the timeout path exits cleanly with valid JSON and a warning.
- [x] AC-08: Auth-token and CAPTCHA indicators set `auth_required`/`needs_manual_reason` without treating the run as a tool failure.
- [x] AC-09: Token-like values in URLs, headers, and body previews are redacted in output while preserving enough evidence to diagnose the auth requirement.
- [x] AC-10: `examples/api-discovery/tools/network_sniff.tool.yaml` uses the FR-768 shell manifest schema with `parse: json` and a runtime timeout, and validates when referenced by a minimal graph or manifest fixture.
- [x] AC-11: The change does not create or materially modify graph or prompt artifacts; FR-789 owns the browser-sniff graph.

## Implementation Notes (2026-08-15)

- Tests: `tests/unit/test_fr784_network_sniff.py` — 5 static-contract tests
  (manifest schema, package boundary, missing-playwright diagnostic) run
  everywhere; 6 browser witnesses (slow-marked) run against the committed
  fixture `tests/fixtures/fr784_spa/` served by a pytest-local
  ThreadingHTTPServer, skipping with the exact install command when the
  pinned setup is absent (C-2/C-3 honored: no public site, no ambient
  global Playwright — the package resolves from the committed
  `package.json`/`package-lock.json` boundary).
- Redaction (C-4): token-like query params → `[REDACTED]`; JWT/long-hex/
  base64 literals scrubbed from body previews; headers and cookies never
  emitted (only `content_type`). Canary-leak test proves no raw token in
  the full stdout.
- Telemetry policy: demote-never-drop — denylisted requests are kept,
  classified `telemetry`, and ranked behind `data` in the output.
- Deviation: none — scope exactly D-1..D-6.

### Live validation (2026-08-15, post-enforcement)

Operator-requested smoke against live sites (not part of the test
suite; C-2 tests remain fixture-only):

- `avoindata.fi` (server-rendered CKAN): 0 XHR/fetch captured — the
  correct negative signal for FR-789's routing.
- `hn.algolia.com` (real SPA): captured the hidden Algolia query API,
  and exposed two defects the fixture missed:
  1. `x-algolia-api-key=<32-hex>` leaked — exact-name matching missed
     vendor-prefixed params. Fixed: segment-based param-name matching
     (`x-algolia-api-key` → segment `key`) plus token-shaped value
     redaction (32+ hex / base64 / JWT) under any param name.
  2. `telemetry.algolia.com/1/settings` classified `data` — hostname
     labels now checked against telemetry vocabulary (telemetry,
     analytics, metrics, tracking, stats, beacon, collect).
  Both condemned RED-first in `test_fr784_network_sniff.py` (Node-level
  helper units via exported `classify`/`redactUrl` + fixture canary);
  14/14 green after fix; live re-run confirms zero token material and
  correct demotion.

## Alternatives Considered

- **Python + selenium:** heavier, worse network interception API
- **mitmproxy:** too complex for this use case; a proxy between browser and server when we only need to observe
- **Chrome DevTools Protocol directly:** Playwright wraps this; no reason to go lower

## Related

- FR-768 (tool manifests)
- FR-789 (browser-sniff step graph — the consumer)
- `docs/adaptive-probing-plan.md` §4.4
- CAP-229 / REQ-YG-590 (traceability)

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
