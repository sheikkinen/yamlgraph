# Judgement: FR-790 API Discovery Schema-Extract Step Graph

**Verdict:** APPROVED WITH REVISIONS — the step is a valid example-level component, but authority activates only after the FR freezes its v1 family coverage, defines the exact input/schema contract, and replaces broad prose with fixture-backed checks.

**Reviewed against:** `feature-requests/FR-790-api-discovery-schema-extract-step.md`; `docs/adaptive-probing-plan.md`; `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`; `feature-requests/FR-788-api-discovery-platform-confirm-step.md`; `feature-requests/FR-791-api-discovery-orchestrator.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The first consumer is named: FR-790 feeds the FR-791 orchestrator when a confirmed platform needs capabilities enumerated (`feature-requests/FR-790-api-discovery-schema-extract-step.md:8-10`), and FR-791 explicitly routes through `schema-extract` before synthesis (`feature-requests/FR-791-api-discovery-orchestrator.md:16-20`). The proposal also follows the parent plan's step-manifest architecture: `schema_extract.tool.yaml` is listed as a graph-runtime tool manifest (`docs/adaptive-probing-plan.md:47-53`), and the parent plan assigns this step the exact capability-extraction responsibility (`docs/adaptive-probing-plan.md:128-134`).

The deterministic OpenAPI boundary is sound. FR-783 defines `parse_openapi.tool.yaml` as a python manifest that returns endpoint inventory without LLM involvement (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:63-69`), and FR-790 correctly requires OpenAPI specs to be parsed deterministically through that tool (`feature-requests/FR-790-api-discovery-schema-extract-step.md:55-58`). The graph-authoring route is also correctly acknowledged: FR-790 requires `scripts/author.sh`, lint, and smoke (`feature-requests/FR-790-api-discovery-schema-extract-step.md:55-60`), matching repo doctrine that graph artifacts must be authored through `scripts/author.sh` and verified by the authoring report (`.github/copilot-instructions.md:15`).

Strategic classification: **Contrib/example**, not framework primitive. The use case is concrete and reusable inside `examples/api-discovery/`, but the FR cites one immediate orchestrator consumer and one example pipeline family, not three independent framework-wide consumers (`feature-requests/FR-790-api-discovery-schema-extract-step.md:8-21`; `docs/adaptive-probing-plan.md:189-201`).

## Required revisions

### R-1: Freeze v1 family coverage to OpenAPI and CKAN

Revise the FR so v1 support is exactly:

1. OpenAPI/Swagger: call `parse_openapi` and transform its endpoint inventory into `CapabilityReport.endpoints`.
2. CKAN: extract dataset count, top organizations, recent package sample, auth model, languages when present, and freshness from the confirmed sample response.

Move PxWeb and custom schema inference out of authorized v1 scope. The current FR lists OpenAPI, CKAN, PxWeb, and custom extraction (`feature-requests/FR-790-api-discovery-schema-extract-step.md:44-50`), but its acceptance criteria only mechanically require deterministic OpenAPI parsing and schema conformance (`feature-requests/FR-790-api-discovery-schema-extract-step.md:55-60`). Freezing v1 to OpenAPI + CKAN keeps the step minimal while preserving the cited ideal CKAN result (`feature-requests/FR-790-api-discovery-schema-extract-step.md:36-40`) and the deterministic parse-openapi dependency (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:63-69`).

### R-2: Define the exact input contract from platform-confirm

Add a concrete input mapping section to the FR. It must name the fields this graph consumes from FR-788's `PlatformConfirmation { family, base_url, confirmed, sample_response }` contract (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:52-53`) and any additional optional inputs it requires, such as `openapi_spec_json`, `sample_responses`, or `source_url`. If additional inputs are required, the FR must state which upstream step provides them or require static smoke fixtures for this standalone step.

The current FR says "confirmed platform identification and sample responses" (`feature-requests/FR-790-api-discovery-schema-extract-step.md:16-18`) while the upstream FR-788 contract exposes a singular `sample_response: str` (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:52-53`). That mismatch must be resolved before enforcement.

### R-3: Pin the `CapabilityReport` schema and validation surface

Define `CapabilityReport` in the FR with field types, required/optional status, and the artifact where validation lives. For this example-level step, the schema should be graph-local unless a later orchestrator FR explicitly requires a shared module. Required fields for v1 are:

| Field | Type | Required |
|---|---|---|
| `family` | `str` | yes |
| `base_url` | `str` | yes |
| `endpoints` | `list[EndpointInfo]` | yes |
| `auth_model` | `str` | yes |
| `rate_limits` | `str | None` | yes |
| `freshness` | `str | None` | yes |
| `languages` | `list[str]` | yes |
| `sample_response` | `dict` | yes |
| `limitations` | `list[str]` | yes |

`EndpointInfo` must include at least `method: str | None`, `path: str`, `description: str | None`, and `parameters: list[str]`. FR-790 currently names `CapabilityReport` but leaves its validation surface and nested endpoint shape underspecified (`feature-requests/FR-790-api-discovery-schema-extract-step.md:50-58`), which prevents direct test derivation.

### R-4: Replace broad capability prose with fixture-backed acceptance checks

Revise acceptance criteria so every retained family has a concrete fixture-backed smoke. OpenAPI must use a tiny static OpenAPI fixture and assert at least one endpoint path/parameter survives the deterministic `parse_openapi` path. CKAN must use a static CKAN-like response fixture and assert dataset count, organization signal, and freshness/language extraction when present. This is required by the judge rubric's measurability/testability standards (`.github/skills/judge-fr/doctrine.md:43-61`) and by repo doctrine that outputs must be typed and not merely plausible (`.github/copilot-instructions.md:216-218`; `.github/copilot-instructions.md:232-233`).

### R-5: Make dependency order explicit

Add enforcement preconditions that FR-783's `parse_openapi` manifest exists before OpenAPI acceptance can pass, and that the FR-788 platform-confirm output contract is either implemented or represented by static fixtures. The parent plan lists FR-790 as depending on FR-783 (`docs/adaptive-probing-plan.md:191-201`), while FR-790 only lists related FRs and does not currently gate enforcement on their contracts (`feature-requests/FR-790-api-discovery-schema-extract-step.md:61-66`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/api-discovery/steps/schema-extract/graph.yaml` |
| D-2 | `examples/api-discovery/steps/schema_extract.tool.yaml` |
| D-3 | Graph-local prompt/schema artifacts under `examples/api-discovery/steps/schema-extract/` |
| D-4 | Static smoke fixtures for OpenAPI and CKAN under the schema-extract example directory |
| D-5 | `tmp/draft-authoring-report.md` evidence from `scripts/author.sh` showing lint and smoke results |

Not authorized: framework-level changes under `yamlgraph/`; changes to the graph-runtime tool manifest primitive; implementing PxWeb extraction; implementing custom API schema inference; promoting this step to an agent; changing FR-788 or FR-791 contracts except to document the expected field mapping in this FR.

## Revised acceptance criteria

- [ ] AC-01: `examples/api-discovery/steps/schema-extract/graph.yaml` exists and is authored through `scripts/author.sh`, with `tmp/draft-authoring-report.md` recording the authoring route, precedent search, lint result, smoke command, and smoke result.
- [ ] AC-02: `examples/api-discovery/steps/schema_extract.tool.yaml` exists with `runtime.type: graph` and points to `schema-extract/graph.yaml`.
- [ ] AC-03: The graph declares or references a graph-local `CapabilityReport` schema with the exact fields and `EndpointInfo` shape listed in R-3, and invalid output fails validation rather than being silently accepted.
- [ ] AC-04: The FR and graph document the input mapping from `PlatformConfirmation.family`, `base_url`, `confirmed`, and `sample_response`, plus any optional OpenAPI/fixture inputs needed for standalone smoke execution.
- [ ] AC-05: The OpenAPI smoke fixture exercises `parse_openapi` deterministically and asserts that a known path and parameter appear in `CapabilityReport.endpoints`.
- [ ] AC-06: The CKAN smoke fixture asserts dataset count, organization signal, sample response preservation, and freshness or language extraction when those values are present in the fixture.
- [ ] AC-07: The graph supports exactly OpenAPI and CKAN in v1; unsupported families return a structured limitation inside `CapabilityReport.limitations` and do not trigger agent promotion or custom inference.
- [ ] AC-08: `yamlgraph graph lint examples/api-discovery/steps/schema-extract/graph.yaml` passes, and the recorded smoke command runs the graph against the committed fixtures.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1 through R-5 are folded into `feature-requests/FR-790-api-discovery-schema-extract-step.md`. | GATE |
| C-2 | The enforcer must use `scripts/author.sh`; direct unsentineled writes to `graph.yaml` or prompt YAML are outside authority. | GATE |
| C-3 | If FR-783's `parse_openapi` manifest is not implemented, OpenAPI support must use a static fixture only to validate this graph's mapping and must not invent a replacement parser. | GATE |
| C-4 | If FR-788's implemented output contract differs from the cited `PlatformConfirmation` fields, enforcement stops and the FR must be amended before implementation continues. | GATE |
| C-5 | Agent promotion, PxWeb extraction, custom schema inference, and framework/runtime changes require separate FR authority. | GATE |

Authority granted: after the required revisions are folded into the FR, the enforcer may author the example-level schema-extract graph and graph-runtime tool manifest for OpenAPI and CKAN capability reporting only.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
