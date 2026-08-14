# Feature Request: FR-788 — API Discovery Platform-Confirm Step Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced 2026-08-14 — AC-01..AC-10 delivered; 14/14 tests green (REQ-YG-589, CAP-228)
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

- **Graph type:** single `type: agent` node consuming the shared
  `examples/api-discovery/tools/curl_probe.tool.yaml` manifest from
  FR-783 by reference (dependency gate: enforcement waits until that
  manifest exists and is loadable; no inline curl tool is defined here).
- **Inputs (frozen cardinality):** `platform_candidates: list[str]` and
  `base_urls: list[str]`. The agent probes candidate/base-URL pairs
  deterministically in the order given by upstream steps.
- **Output (frozen cardinality):** exactly one `PlatformConfirmation`
  object for the first pair that satisfies its family predicate below.
  If no pair is confirmed, `confirmed: false` is returned only after all
  pairs have been attempted, with `family`/`base_url`/`sample_response`
  identifying the best failed attempt and why it did not satisfy the
  predicate.
- **Family confirmation matrix (substance predicates, not shape):**

  | Family | Probe(s) | Confirmed only when |
  |---|---|---|
  | CKAN | `/api/3/action/status_show` and `/api/3/action/package_search?rows=1` | JSON has `"success": true` and `package_search` returns `result.count > 0` with at least one result item carrying `id`/`name`/`title`. |
  | PxWeb | `/PXWeb/api/v1/{lang}/{db}` (or `/api/v1/{lang}/{db}`) | JSON is a non-empty list of database/table entries with `dbid`/`text` fields (verified live shape: `[{"dbid": "...", "text": "..."}]`). |
  | OData | service root or entity set with `?$top=1&$format=json` | JSON contains `@odata.context` and a non-empty `value` array. |
  | OpenAPI | spec fetch (`/openapi.json`, `/swagger.json`) | JSON/YAML parses as OpenAPI/Swagger with `openapi`/`swagger` version key and at least 3 entries under `paths`. |
  | WordPress REST | `/wp-json/wp/v2/types` | JSON object contains at least one concrete content type key such as `post` or `page`. |
  | JSON-stat | candidate cube JSON | Structure includes non-empty `dimension` and `value` per the JSON-stat 2.0 spec. |

- **Output schema:** `PlatformConfirmation { family: str, base_url: str, confirmed: bool, sample_response: str }`
- **Manifest:** `steps/platform_confirm.tool.yaml` with `runtime.type: graph`

## Acceptance Criteria

- [ ] AC-01: `examples/api-discovery/steps/platform-confirm/graph.yaml` exists and is authored through `scripts/author.sh`.
- [ ] AC-02: `examples/api-discovery/steps/platform_confirm.tool.yaml` exists, declares `runtime.type: graph`, and points to `steps/platform-confirm/graph.yaml`.
- [ ] AC-03: The graph consumes the FR-783 `examples/api-discovery/tools/curl_probe.tool.yaml` manifest by reference and does not define an inline curl shell tool.
- [ ] AC-04: The graph accepts `platform_candidates: list[str]` and `base_urls: list[str]`, probes them deterministically, returns exactly one `PlatformConfirmation`, and returns `confirmed: false` only after all candidate/base URL pairs fail the frozen predicates.
- [ ] AC-05: The output schema validates `PlatformConfirmation { family: str, base_url: str, confirmed: bool, sample_response: str }`.
- [ ] AC-06: The authored prompt/config contains the family confirmation matrix above, including CKAN, PxWeb, OData, OpenAPI, WordPress REST, and JSON-stat predicates.
- [ ] AC-07: Positive smoke against `platform_candidates=["CKAN"], base_urls=["https://demo.ckan.org"]` (CKAN's own public demo instance) returns `confirmed: true`, `family == "CKAN"`, and a `sample_response` showing `package_search.result.count > 0`.
- [ ] AC-08: Negative smoke against `platform_candidates=["CKAN"], base_urls=["https://example.com"]` returns `confirmed: false`.
- [ ] AC-09: `yamlgraph graph lint examples/api-discovery/steps/platform-confirm/graph.yaml` passes.
- [ ] AC-10: `tmp/draft-authoring-report.md` records artifacts, precedent, exact validation commands and outcomes, repairs, and any blocked validation.

## Conditions for Enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-783 `curl_probe.tool.yaml` must exist and be loadable before this graph is authored (confirmed present at `examples/api-discovery/tools/curl_probe.tool.yaml`). | GATE |
| C-2 | All graph and prompt artifact writes must occur inside the graph-authoring adapter route (`scripts/author.sh`) and produce `tmp/draft-authoring-report.md`; route failure is not permission to author manually. | GATE |
| C-3 | Do not change YAMLGraph framework code, hooks, CI, judge/review doctrine, or graph-authoring doctrine under this FR. | GATE |
| C-4 | A positive-only validation is insufficient; the negative smoke (AC-08) or an honestly recorded blocked-validation entry is required. | GATE |

## Related

- FR-783 (curl_probe manifest — the tool this agent reuses; dependency confirmed present)
- FR-786 (page-analysis — provides the platform candidates)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.5

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.

## Implementation Notes

- First authoring attempt hit FR-794's now-fixed shared Python tool
  manifest root-confinement bug (the `curl_probe` manifest lives
  outside `steps/platform-confirm/`); resumed after FR-794 landed by
  re-invoking `scripts/author.sh` with the identical task brief.
- Both required live smokes passed on first successful run: positive
  against CKAN's public demo (`https://demo.ckan.org`) →
  `confirmed: true`, `family: CKAN`; negative against `https://example.com`
  → `confirmed: false`. Independently re-verified outside the authoring
  sandbox with identical results.
- Added `tests/unit/test_fr788_platform_confirm.py` (14 tests),
  `capabilities/CAP-228` (REQ-YG-589); regenerated `ARCHITECTURE.md`;
  `req_coverage.py --strict` clean.
- Fixed an unrelated pre-existing over-broad assertion in FR-786's test
  suite (`test_no_sibling_step_artifacts_introduced` →
  `test_no_sibling_step_dependency_introduced`) that incorrectly assumed
  sibling step directories (like this FR's `platform-confirm/`) would
  never exist; rescoped to check dependency, not directory existence.

**Judgement revisions folded:** R-1 (mechanical substance predicates replacing "real data" prose), R-2 (frozen input/output cardinality — one `PlatformConfirmation` per run), R-3 (FR-783 dependency promoted to an enforcement gate), R-4 (named positive/negative smoke validations against `demo.ckan.org` and `example.com`) — see `feature-requests/FR-788-api-discovery-platform-confirm-step.judgement.md`.
