# FR-790 API discovery schema-extract step graph

Author the schema-extract step of the API discovery pipeline, authorized by
`feature-requests/FR-790-api-discovery-schema-extract-step.md` (Judged;
R-1..R-5 folded) and its committed judgement.

## Artifacts to author

1. `examples/api-discovery/steps/schema-extract/graph.yaml`
2. `examples/api-discovery/steps/schema-extract/prompts/*.yaml` (as needed)
3. `examples/api-discovery/steps/schema_extract.tool.yaml` (graph-runtime tool manifest)
4. Static smoke fixtures under `examples/api-discovery/steps/schema-extract/fixtures/`:
   - a tiny OpenAPI spec JSON (at least one path with one parameter, e.g.
     `/pets` with query param `limit`)
   - a CKAN-like sample response JSON (dataset count, organizations list,
     recent packages, and a language/freshness signal)

## Precedent

Adapt `examples/api-discovery/steps/page-analysis/` (graph + prompts +
fixtures + data) and `examples/api-discovery/steps/platform-confirm/` for
step shape; `examples/api-discovery/steps/recon/prompts/recon.yaml` for the
`output_schema:` JSON-Schema dialect convention. The manifest follows
`steps/platform_confirm.tool.yaml`.

## Graph contract

- `version: "1.0"`, `name: schema-extract`.
- State inputs (R-2, from FR-788 PlatformConfirmation; `confirmed` NOT consumed):
  - `family` (str): confirmed platform family, e.g. `openapi`, `ckan`
  - `base_url` (str)
  - `sample_response` (str): singular sample response text
  - `openapi_spec_json` (str, default ""): OpenAPI spec JSON text; supplied by
    fixture in smoke, by orchestrator at runtime
  - `capability_report` (dict): output
- **NO agent node** (judgement C-5): use `llm` node(s), optionally a router
  node on `family`, and a `tool_call` node for `parse_openapi` on the OpenAPI
  path. `parse_openapi` via
  `manifest: ../../tools/parse_openapi.tool.yaml` (FR-783 owns it — do not
  modify; note it raises ValueError on invalid/empty JSON, so only invoke it
  on the OpenAPI path).
- v1 family coverage frozen (R-1): exactly `openapi` and `ckan`.
  - openapi: tool_call `parse_openapi(spec_json=openapi_spec_json)` →
    llm transforms the endpoint inventory into `CapabilityReport.endpoints`.
  - ckan: llm extracts dataset count, top organizations, recent package
    sample, auth model, languages, freshness from `sample_response`.
  - any other family: return a well-formed CapabilityReport with empty
    endpoints and a structured entry in `limitations` naming the unsupported
    family — never an error, never inference.

## Output schema (R-3, graph-local, output_schema: JSON-Schema dialect)

Top-level object CapabilityReport, ALL nine fields required:
- `family`: string
- `base_url`: string
- `endpoints`: array of object — EndpointInfo items with properties
  `method` (string), `path` (string), `description` (string),
  `parameters` (array of string); `path` and `parameters` required on the
  item (method/description optional via omission from item `required`)
- `auth_model`: string
- `rate_limits`: string (empty when unknown — dialect has no null type)
- `freshness`: string (empty when unknown)
- `languages`: array of string
- `sample_response`: object
- `limitations`: array of string

Do NOT put literal JSON examples with braces in prompts (templating
conflict); describe shapes brace-free.

## Validation

- `yamlgraph graph lint examples/api-discovery/steps/schema-extract/graph.yaml`
- OpenAPI smoke (deterministic parse + llm mapping):
  `yamlgraph graph run examples/api-discovery/steps/schema-extract/graph.yaml --var family="openapi" --var base_url="https://petstore.example.com" --var sample_response="" --var openapi_spec_json="$(cat examples/api-discovery/steps/schema-extract/fixtures/openapi_petstore.json)" --full`
  — passes only if a known fixture path (e.g. `/pets`) and parameter
  (e.g. `limit`) appear in `capability_report.endpoints`.
- CKAN smoke:
  `yamlgraph graph run examples/api-discovery/steps/schema-extract/graph.yaml --var family="ckan" --var base_url="https://data.gov.fi" --var sample_response="$(cat examples/api-discovery/steps/schema-extract/fixtures/ckan_sample.json)" --full`
  — passes only if dataset count and an organization signal from the fixture
  appear in the report and `sample_response` is preserved.
- Unsupported-family smoke:
  run with `--var family="pxweb"` and empty spec — passes only if the result
  is a well-formed report whose `limitations` names the unsupported family.
- If anything blocks a smoke, record the exact blocked command and reason
  under Blocked validation — do not claim a pass.

## Boundaries

Do not modify `parse_openapi.tool.yaml`/`parse_openapi.py`, any other step
graph, the orchestrator, framework code under `yamlgraph/**`, tests,
capabilities, changelog, or diary. Only the artifacts listed above.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
