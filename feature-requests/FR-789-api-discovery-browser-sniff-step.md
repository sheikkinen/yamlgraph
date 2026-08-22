# Feature Request: FR-789 — API Discovery Browser-Sniff Step Graph

**Priority:** LOW
**Type:** Feature
**Status:** Enforced 2026-08-15 — AC-01..AC-08 delivered; authoring adapter report verified, lint + both deterministic fixture smokes passed, 13/13 tests green (REQ-YG-593, CAP-232)
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
- **Output schema (R-2):** `SniffResult { api_calls: list[CapturedRequest], auth_required: bool, verdict_hint: Literal["needs_manual"] | None, manual_reason: str | None }`
- **`CapturedRequest`:** `{ url: str, method: str, status: int, content_type: str, body_preview: str }`
- **Manifest:** `steps/browser_sniff.tool.yaml` with `runtime.type: graph`
- **Failure mode (R-2):** auth token / CAPTCHA → typed `verdict_hint: "needs_manual"` with `manual_reason`, not error

## Dependency Gate (R-1)

FR-789 may not be enforced until FR-784 has provided the leaf
`network_sniff` tool manifest (`examples/api-discovery/tools/network_sniff.tool.yaml`)
and `network-sniff.js` utility. Enforcement must confirm both exist and
are referenced by the browser-sniff agent — never reimplemented here.

## Validation Contract (R-3)

Validation must be substantive and deterministic, not artifact-presence:
a deterministic smoke or test fixture must prove that the step maps
captured `network_sniff` output into a `SniffResult`, filters
telemetry/noise, preserves data-carrying JSON/XML requests, and returns
the typed `needs_manual` hint for auth/CAPTCHA evidence. Enforcement
must prove at least one retained data request, one excluded
telemetry/noise request, and one `needs_manual` path (C-4).

## Acceptance Criteria (revised per judgement)

- [x] AC-01: Step graph exists at `examples/api-discovery/steps/browser-sniff/graph.yaml`.
- [x] AC-02: Graph-runtime tool manifest exists at `examples/api-discovery/steps/browser_sniff.tool.yaml` and points to the browser-sniff step graph.
- [x] AC-03: FR-784 dependency is satisfied before enforcement: the leaf `network_sniff` manifest and Playwright utility exist and are referenced by the browser-sniff agent, not reimplemented here.
- [x] AC-04: Browser-sniff agent invokes the leaf `network_sniff` tool to capture XHR/fetch requests.
- [x] AC-05: Output conforms to `SniffResult { api_calls: list[CapturedRequest], auth_required: bool, verdict_hint: Literal["needs_manual"] | None, manual_reason: str | None }`, with `CapturedRequest { url, method, status, content_type, body_preview }`.
- [x] AC-06: Deterministic validation proves JSON/XML data requests are retained and analytics/telemetry noise is excluded from `api_calls`.
- [x] AC-07: Deterministic validation proves auth-token or CAPTCHA evidence returns `verdict_hint == "needs_manual"` without treating the graph run as an error.
- [x] AC-08: Graph is authored via `scripts/author.sh`, and `tmp/draft-authoring-report.md` records precedent search, lint, smoke, and honest validation evidence for this step.

## Conditions for Enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not write governed graph or prompt artifacts except through the graph-authoring route; use the authoring report, not exit code alone, as validation evidence. | GATE |
| C-2 | Do not implement FR-784 deliverables under FR-789; block until the leaf `network_sniff` utility and manifest exist or fold a dependency-status update into the FR. | GATE |
| C-3 | Do not accept a schema that omits the typed `needs_manual` result path while ACs require that behavior. | GATE |
| C-4 | Do not close enforcement on artifact-exists checks alone; validation must prove at least one retained data request, one excluded telemetry/noise request, and one `needs_manual` path. | GATE |

## Related

- FR-784 (network-sniff.js + manifest — the tool this agent uses)
- FR-786 (page-analysis — provides the SPA routing trigger)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.4

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.

**Judgement revisions folded:** R-1 (FR-784 enforcement dependency gate), R-2 (`SniffResult` reconciled with the `needs_manual` failure mode: `verdict_hint`/`manual_reason` typed fields), R-3 (deterministic, substantive validation: retained data request + excluded telemetry + `needs_manual` path) — see `feature-requests/FR-789-api-discovery-browser-sniff-step.judgement.md`.

## Implementation Record (2026-08-15)

- R-1/AC-03 verified before authoring: `network_sniff.tool.yaml`,
  `network-sniff.js`, committed SPA fixtures (`tests/fixtures/fr784_spa/`),
  and the pinned Playwright/Chromium install all present.
- Authored via the sole route in two runs. Run 1 created the three artifacts,
  passed lint and the CAPTCHA smoke, but died before writing the report
  (contract violation, exit 65) — root cause was the brief's own smoke
  instruction: `python3 -m http.server` serves the fixture statically, so its
  `/api/*` fetches 404 and classify as `other`, never `data`. Run 2 (corrected
  brief + `tmp/fr789_fixture_server.py` mirroring the FR-784 `_SpaHandler`)
  validated the unchanged artifacts end-to-end and wrote a substantive
  `tmp/draft-authoring-report.md` (per-command outcomes incl. one honest
  provider-transport retry; Blocked validation: none).
- Artifacts: `steps/browser-sniff/graph.yaml` (single agent node,
  `max_iterations: 4`), `steps/browser-sniff/prompts/sniff.yaml`
  (`output_schema:` dialect; `api_calls` items require all five
  CapturedRequest fields; `verdict_hint` enum `[needs_manual]`; optionality
  via omission from `required` per FR-795 convention),
  `steps/browser_sniff.tool.yaml` (graph runtime → `browser-sniff/graph.yaml`,
  `output_key: sniff_result`).
- Independent deterministic smokes (`logs/fr789-smoke-data.log`,
  `logs/fr789-smoke-captcha.log`) against the fixture server: data path
  retained `/api/data`, `/api/item`, `/api/search` (token query params
  redacted by the FR-784 tool) and excluded `/analytics/collect`;
  CAPTCHA path returned `verdict_hint: needs_manual`,
  `manual_reason: captcha` with exit 0 — C-4 satisfied (retained data,
  excluded telemetry, needs_manual path all proven).
- Tests: `tests/unit/test_fr789_browser_sniff_step.py` 13/13 green
  (REQ-YG-593, CAP-232); includes `load_and_compile` witness, both-shape
  Pydantic validation, and no-reimplementation checks.
  `req_coverage --strict` passes.
- Deviation from original plan: none beyond the two-run authoring route
  (recorded above); scope stayed inside judgement D-1..D-5.

**Brief provenance (FR-852):** authoring brief committed at
`feature-requests/authoring-briefs/fr-789-authoring-brief.md`
(the brief that carried the FR-789 static-server bug; see
`docs/diary/diary-2026-08-15-fr789-brief-is-code.md`).
