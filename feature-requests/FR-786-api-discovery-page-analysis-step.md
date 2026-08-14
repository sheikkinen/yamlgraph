# Feature Request: FR-786 — API Discovery Page-Analysis Step Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced 2026-08-14 — AC-01..AC-09 delivered; 17/17 tests green (REQ-YG-587, CAP-226)
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

- **Graph type:** single `type: agent` node consuming the shared
  `examples/api-discovery/tools/fetch_page.tool.yaml` manifest from
  FR-783 by reference. No inline curl/fetch duplicate is created under
  this step.
- **Platform catalog:** `examples/api-discovery/steps/page-analysis/data/platform_catalog.yaml`,
  loaded through the graph/prompt `data_files` mechanism (never
  hardcoded into prompt prose). Must contain markers for CKAN, PxWeb,
  SwaggerUI, OData, Liferay, JSF, WordPress REST, and EntryScape.
- **Output schema:** `PageAnalysis` with exactly the fields
  `api_found: bool`, `is_spa: bool`, `platform_candidates: list[str]`,
  `api_urls: list[str]`.
- **Fixtures:** committed HTML fixtures under
  `examples/api-discovery/steps/page-analysis/fixtures/` covering
  script-tag URLs, `data-api-url`, inline `fetch()`/axios calls,
  platform fingerprints, and an SPA-without-API case — the deterministic
  proof for AC-06/AC-07, not live-web probing.
- **Manifest:** `examples/api-discovery/steps/page_analysis.tool.yaml`
  with `runtime.type: graph` pointing at `steps/page-analysis/graph.yaml`.

## Scope Boundary (frozen)

Not authorized under this FR: browser-sniff or Playwright/network-sniff
work (FR-789), orchestrator graph or routing changes (FR-791),
platform-confirm or schema-extract graphs (FR-788/FR-790), creation or
alteration of framework runtime primitives, changes to hooks, CI,
judge/review doctrine, or graph-authoring doctrine, and duplicate leaf
tool manifests when FR-783 already provides `fetch_page`.

## Acceptance Criteria

- [ ] AC-01: `examples/api-discovery/steps/page-analysis/graph.yaml` exists and is authored through `scripts/author.sh`, with `tmp/draft-authoring-report.md` listing it as an authored artifact.
- [ ] AC-02: `examples/api-discovery/steps/page_analysis.tool.yaml` exists and declares `runtime.type: graph` with a path resolving to `steps/page-analysis/graph.yaml`.
- [ ] AC-03: The graph references `examples/api-discovery/tools/fetch_page.tool.yaml`; no inline curl/fetch-page duplicate is added under the step graph.
- [ ] AC-04: `examples/api-discovery/steps/page-analysis/data/platform_catalog.yaml` exists, contains CKAN, PxWeb, SwaggerUI, OData, Liferay, JSF, WordPress REST, and EntryScape markers, and is loaded through the graph/prompt `data_files` mechanism.
- [ ] AC-05: The graph declares or uses a `PageAnalysis` schema with exactly `api_found: bool`, `is_spa: bool`, `platform_candidates: list[str]`, and `api_urls: list[str]`; lint or smoke output proves returned values conform to it.
- [ ] AC-06: A local fixture smoke run containing script tags, `data-api-url`, inline fetch/axios calls, and platform markers returns `api_found == true`, includes the expected extracted API URLs, and includes at least CKAN, PxWeb, SwaggerUI, and OData in `platform_candidates`.
- [ ] AC-07: A local fixture smoke run for an SPA page with no static API references returns `is_spa == true` and `api_found == false`, establishing the routing signal consumed by FR-789/FR-791 without implementing browser-sniff.
- [ ] AC-08: `yamlgraph graph lint examples/api-discovery/steps/page-analysis/graph.yaml` passes and the narrow fixture smoke command is recorded in `tmp/draft-authoring-report.md` with its actual outcome.
- [ ] AC-09: The diff contains no browser-sniff, orchestrator, platform-confirm, schema-extract, runtime-primitive, hook, CI, or doctrine changes under this FR.

## Conditions for Enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Use `scripts/author.sh <task-brief.md>` for graph/prompt authoring and verify `tmp/draft-authoring-report.md` by substance, not exit code. | GATE |
| C-2 | If `examples/api-discovery/tools/fetch_page.tool.yaml` from FR-783 is absent or unloadable, stop and record the dependency blockage; do not duplicate the tool locally. | GATE |
| C-3 | Validation must include deterministic local fixture smoke evidence; live-web probing may be additional evidence but cannot be the only acceptance proof. | GATE |
| C-4 | Keep the platform catalog in `data_files`; hardcoding the catalog into prompt prose fails the FR. | GATE |
| C-5 | Do not modify framework runtime primitives, hooks, CI, or doctrine while enforcing this example graph FR. | GATE |

## Related

- FR-783 (fetch_page manifest — the tool this agent uses; dependency confirmed present at `examples/api-discovery/tools/fetch_page.tool.yaml`)
- FR-789 (browser-sniff — triggered when `is_spa == true AND api_found == false`)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.3

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.

**Judgement revisions folded:** R-1 (explicit `fetch_page` dependency, no duplicate tool), R-2 (named platform catalog artifact + exact schema fields), R-3 (fixture-backed deterministic ACs replacing prose-only criteria), R-4 (frozen scope boundary away from FR-788/789/790/791) — see `feature-requests/FR-786-api-discovery-page-analysis-step.judgement.md`.

## Implementation Notes

- Authored via `scripts/author.sh tmp/task-fr786-page-analysis.md`. The
  wrapper reported a contract violation because the copilot CLI child
  process hit the graph's 900s node timeout before signalling
  completion back to `yamlgraph graph run`; `tmp/draft-authoring-report.md`
  was nonetheless written to disk with all required sections (Artifacts,
  Precedent, Validation, Repairs, Blocked validation) and every listed
  artifact path exists — the artifact-existence contract passed on
  manual re-check.
- Independently re-ran `yamlgraph graph lint` (0 errors, 1 expected W026
  warning matching the 4-field `PageAnalysis` schema) and both fixture
  smokes outside the wrapper; results matched the authoring report
  exactly: `portal_with_api.html` → `api_found=true`, all 3 embedded API
  URLs extracted, `platform_candidates=[CKAN, PxWeb, SwaggerUI, OData]`;
  `spa_no_api.html` → `is_spa=true`, `api_found=false`, empty candidates.
- Added `tests/unit/test_fr786_page_analysis.py` (17 tests) and
  `capabilities/CAP-226-api-discovery-page-analysis.yaml` (REQ-YG-587),
  regenerated `ARCHITECTURE.md` via `scripts/aggregate_capabilities.py`,
  and confirmed `scripts/req_coverage.py --strict` closes the gap.
- No sibling-step (browser-sniff/orchestrator/platform-confirm/
  schema-extract), hook, CI, or doctrine files were touched.
