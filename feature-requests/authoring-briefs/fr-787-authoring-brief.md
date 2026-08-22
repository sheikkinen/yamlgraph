# FR-787 API discovery recon step graph

Author the recon step of the API discovery pipeline, authorized by
`feature-requests/FR-787-api-discovery-recon-step.md` (Judged; R-1..R-4 folded)
and its committed judgement.

## Artifacts to author

1. `examples/api-discovery/steps/recon/graph.yaml`
2. `examples/api-discovery/steps/recon/prompts/recon.yaml`
3. `examples/api-discovery/steps/recon.tool.yaml` (graph-runtime tool manifest)

## Precedent

Adapt `examples/api-discovery/steps/endpoint-probe/` (graph.yaml +
prompts/probe.yaml + steps/endpoint_probe.tool.yaml) — the shipped sibling
step with the same shape: single `type: agent` node consuming a shared shell
tool manifest, `prompts_relative: true`, graph-runtime tool manifest for the
orchestrator.

## Graph contract

- `version: "1.0"`, `name: recon`, description: GitHub code-search recon for
  API discovery.
- State:
  - `hypothesis` (str): what API/service is being investigated, e.g.
    "Finnish health statistics API (thl.fi sotkanet)"
  - `max_iterations` (int, default 8): bounded tool-call iteration budget
  - `recon_result` (dict): structured ReconResult output
- Tools: `gh_code_search` via `manifest: ../../tools/gh_code_search.tool.yaml`
  (do NOT modify that manifest — FR-783 owns it).
- Single node `recon_agent`: `type: agent`, `prompt: recon`,
  tools `[gh_code_search]`, `max_iterations: 8`, `state_key: recon_result`.
- Edges: START → recon_agent → END.

## Prompt contract (prompts/recon.yaml)

- Instruct the agent to generate search-term variants from the hypothesis —
  domain forms (e.g. `thl.fi`, `sotkanet.fi`), service names, country/language
  conventions — and iterate `gh_code_search` queries within the iteration
  budget, mining other developers' code for API base URLs, auth patterns
  (keys, tokens, headers), and schema/format hints (JSON-stat, OData, REST
  paths).
- Use the `output_schema:` JSON-Schema dialect (precedent:
  `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml` after
  FR-795 — NOT the native `schema:` dialect) with top-level object:
  - `candidate_urls`: array of string — candidate API base/endpoint URLs
  - `auth_hints`: array of string — observed auth patterns
  - `schema_hints`: array of string — response format/schema observations
  - `evidence`: array of string — each entry MUST carry source identity:
    repository, file path, and URL or GitHub result link
  - all four required.
- Empty lists are a valid outcome: instruct the agent that no GitHub
  footprint is a legitimate result — return empty arrays, never invent
  findings.

## Validation

- `yamlgraph graph lint examples/api-discovery/steps/recon/graph.yaml`
- Smoke (gh CLI is authenticated in this environment):
  `yamlgraph graph run examples/api-discovery/steps/recon/graph.yaml --var hypothesis="Finnish health statistics API sotkanet thl.fi" --full`
- If gh auth or network blocks the smoke, record the exact blocked command
  and reason under Blocked validation — do not claim a pass.

## Boundaries

Do not modify the orchestrator, any other step graph, any shared tool
manifest under `examples/api-discovery/tools/`, framework code under
`yamlgraph/**`, tests, capabilities, changelog, or diary. Only the three
artifacts listed above.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
