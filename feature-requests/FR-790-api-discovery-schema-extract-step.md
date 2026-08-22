# Feature Request: FR-790 — API Discovery Schema-Extract Step Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced 2026-08-15 — AC-01..AC-08 delivered; authoring adapter report verified, lint + three independent fixture smokes passed, 13/13 tests green (REQ-YG-594, CAP-233)
**Effort:** 0.5 days
**Requested:** 2026-08-13
**First consumer / first event:** FR-791 API discovery orchestrator,
the first time a confirmed platform needs its capabilities enumerated —
endpoints, auth model, rate limits, data freshness.

**Parent plan:** `docs/adaptive-probing-plan.md` §4.6

## Summary

Create the schema-extract step: a graph that takes a confirmed platform
identification and sample responses, extracts capability information
(endpoints, parameters, auth model, rate limits, freshness, languages),
and returns a structured `CapabilityReport`. Starts as `llm` node;
promote to agent only if sampling proves adaptive iteration is needed.
Packaged as a `runtime.type: graph` tool manifest.

## Value Statement

The orchestrator gets structured API capability data ready for the
final `APIProfile` synthesis — the gap between "we found an API" and
"here's how to use it."

## Problem

A confirmed platform identification (e.g., "CKAN at data.gov.fi") tells
you *what* system it is but not *what it can do*. OpenAPI specs need
parsing; CKAN needs dataset counts and org listings; PxWeb needs subject
trees; custom APIs need response schema inference from samples.

## Ideal Result

Given `family: "ckan", base_url: "https://data.gov.fi"`, the step
returns a `CapabilityReport` with endpoint inventory, auth model,
sample response, record counts, and data freshness indicators.

## Proposed Solution

- **Graph type:** `llm` node with `tool_call` pre-steps for `parse_openapi` (python manifest); agent promotion requires separate FR authority (C-5)
- **v1 family coverage (R-1, frozen):** exactly OpenAPI and CKAN:
  - OpenAPI/Swagger: call `parse_openapi` deterministically and transform its endpoint inventory into `CapabilityReport.endpoints`
  - CKAN: extract dataset count, top organizations, recent package sample, auth model, languages when present, and freshness from the confirmed sample response
  - Any other family: return a structured limitation inside `CapabilityReport.limitations` — no PxWeb, no custom schema inference, no agent promotion (out of v1 scope)
- **Manifest:** `steps/schema_extract.tool.yaml` with `runtime.type: graph`

## Input Contract (R-2)

The graph consumes the FR-788 `PlatformConfirmation` fields:

| Input | Type | Source |
|---|---|---|
| `family` | str | `PlatformConfirmation.family` |
| `base_url` | str | `PlatformConfirmation.base_url` |
| `sample_response` | str | `PlatformConfirmation.sample_response` (singular, per FR-788) |
| `openapi_spec_json` | str (optional, default "") | static smoke fixture for the OpenAPI path; at runtime the orchestrator may pass a fetched spec |

`confirmed` is not consumed — the orchestrator only routes confirmed
platforms here. Standalone smoke execution uses static fixtures committed
under the schema-extract example directory (R-4/D-4).

## CapabilityReport Schema (R-3, graph-local)

| Field | Type | Required |
|---|---|---|
| `family` | `str` | yes |
| `base_url` | `str` | yes |
| `endpoints` | `list[EndpointInfo]` | yes |
| `auth_model` | `str` | yes |
| `rate_limits` | `str \| None` | yes |
| `freshness` | `str \| None` | yes |
| `languages` | `list[str]` | yes |
| `sample_response` | `dict` | yes |
| `limitations` | `list[str]` | yes |

`EndpointInfo`: `method: str | None`, `path: str`, `description: str | None`,
`parameters: list[str]`. The schema is graph-local (prompt `output_schema:`);
invalid output fails validation rather than being silently accepted.

## Dependency Order (R-5)

Enforcement preconditions: FR-783's `parse_openapi.tool.yaml` must exist
before OpenAPI acceptance can pass (verified — FR-783 Enforced 2026-08-13);
the FR-788 platform-confirm output contract is implemented (FR-788 Enforced
2026-08-14) — if its implemented contract differs from the cited
`PlatformConfirmation` fields, enforcement stops and this FR is amended (C-4).

## Acceptance Criteria (revised per judgement)

- [x] AC-01: `examples/api-discovery/steps/schema-extract/graph.yaml` exists and is authored through `scripts/author.sh`, with `tmp/draft-authoring-report.md` recording the authoring route, precedent search, lint result, smoke command, and smoke result.
- [x] AC-02: `examples/api-discovery/steps/schema_extract.tool.yaml` exists with `runtime.type: graph` and points to `schema-extract/graph.yaml`.
- [x] AC-03: The graph declares or references a graph-local `CapabilityReport` schema with the exact fields and `EndpointInfo` shape listed in R-3, and invalid output fails validation rather than being silently accepted.
- [x] AC-04: The FR and graph document the input mapping from `PlatformConfirmation.family`, `base_url`, `confirmed`, and `sample_response`, plus any optional OpenAPI/fixture inputs needed for standalone smoke execution.
- [x] AC-05: The OpenAPI smoke fixture exercises `parse_openapi` deterministically and asserts that a known path and parameter appear in `CapabilityReport.endpoints`.
- [x] AC-06: The CKAN smoke fixture asserts dataset count, organization signal, sample response preservation, and freshness or language extraction when those values are present in the fixture.
- [x] AC-07: The graph supports exactly OpenAPI and CKAN in v1; unsupported families return a structured limitation inside `CapabilityReport.limitations` and do not trigger agent promotion or custom inference.
- [x] AC-08: `yamlgraph graph lint examples/api-discovery/steps/schema-extract/graph.yaml` passes, and the recorded smoke command runs the graph against the committed fixtures.

## Conditions for Enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1 through R-5 are folded into `feature-requests/FR-790-api-discovery-schema-extract-step.md`. | GATE |
| C-2 | The enforcer must use `scripts/author.sh`; direct unsentineled writes to `graph.yaml` or prompt YAML are outside authority. | GATE |
| C-3 | If FR-783's `parse_openapi` manifest is not implemented, OpenAPI support must use a static fixture only to validate this graph's mapping and must not invent a replacement parser. | GATE |
| C-4 | If FR-788's implemented output contract differs from the cited `PlatformConfirmation` fields, enforcement stops and the FR must be amended before implementation continues. | GATE |
| C-5 | Agent promotion, PxWeb extraction, custom schema inference, and framework/runtime changes require separate FR authority. | GATE |

## Related

- FR-783 (parse_openapi manifest — the tool this step uses)
- FR-788 (platform-confirm — provides the confirmed platform input)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.6

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.

**Judgement revisions folded:** R-1 (v1 frozen to OpenAPI + CKAN; PxWeb/custom inference out), R-2 (exact input contract from FR-788 `PlatformConfirmation`, `sample_response` singular), R-3 (`CapabilityReport` + `EndpointInfo` pinned, graph-local), R-4 (fixture-backed acceptance checks per retained family), R-5 (explicit dependency order on FR-783/FR-788) — see `feature-requests/FR-790-api-discovery-schema-extract-step.judgement.md`.

## Implementation Record (2026-08-15)

- Dependency gates verified before authoring (R-5): `parse_openapi.tool.yaml`
  present (FR-783 Enforced); FR-788's implemented `PlatformConfirmation`
  contract matches the cited fields (C-4 clean). Brief premises dry-run
  before launching the route: `tool_call` node precedent confirmed and
  `parse_openapi` verified to emit the exact `EndpointInfo` shape
  (`method/path/description/parameters`).
- Authored via the sole route (`scripts/author.sh tmp/fr-790-authoring-brief.md`,
  exit 0). Substantive `tmp/draft-authoring-report.md`: precedents
  (page-analysis, platform-confirm, recon dialect), three honest repairs
  (CKAN endpoints as bare strings → objects; endpoint `parameters` as
  objects → string arrays; `on_error: fail` added to all llm nodes so
  schema failures stop the run); Blocked validation: none.
- Artifacts: routed graph (passthrough `route_family` + conditional edges;
  `tool_call` `parse_openapi_spec` → llm `summarize_openapi`; llm
  `extract_ckan`; llm `unsupported_family` — no agent node, C-5 honored),
  three prompts pinning the nine-field CapabilityReport with
  `additionalProperties: false`, fixtures `openapi_petstore.json` +
  `ckan_sample.json`, manifest `schema_extract.tool.yaml`
  (input_mapping exactly family/base_url/sample_response/openapi_spec_json,
  `output_key: capability_report`).
- Independent smokes (logs/fr790-smoke-{openapi,ckan,pxweb}.log): OpenAPI —
  `/pets` with parameter `limit` in endpoints, parser evidence preserved in
  `sample_response`; CKAN — dataset count 42, `statistics-finland` org,
  freshness `metadata_modified 2026-07-31…`, languages `fi`/`en`, inferred
  action endpoints as proper objects; pxweb — empty endpoints with
  limitation "Unsupported family: pxweb. v1 supports exactly openapi and
  ckan." All exit 0.
- Tests: `tests/unit/test_fr790_schema_extract_step.py` 13/13 green
  (REQ-YG-594, CAP-233): `load_and_compile` witness, no-agent + routing
  assertions, per-prompt schema pinning, ValidationError witness for
  invalid output, deterministic fixture parse, input-mapping contract.
  `req_coverage --strict` passes.
- Deviation from original plan: none; scope stayed inside judgement D-1..D-5.

**Brief provenance (FR-852):** authoring brief committed at
`feature-requests/authoring-briefs/fr-790-authoring-brief.md`
(formerly `tmp/fr-790-authoring-brief.md`).
