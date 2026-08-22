# FR-791 API discovery orchestrator graph

Author the v1 API discovery orchestrator, authorized by
`feature-requests/FR-791-api-discovery-orchestrator.md` (Judged; R-1..R-4
folded) and its committed judgement.

RESUMED RUN — VALIDATION ONLY. A prior run authored all three artifacts
(`examples/api-discovery/graph.yaml`,
`examples/api-discovery/prompts/generate_candidates.yaml`,
`examples/api-discovery/prompts/synthesize.yaml`) and they pass
`yamlgraph graph lint`, but the run hit the CLI hard timeout during the
live smokes and died before writing the report. Do NOT re-read precedents
at length and do NOT rewrite artifacts unless a smoke exposes a defect.
Budget priority: (1) run the positive smoke, (2) run the negative smoke,
(3) write `tmp/draft-authoring-report.md` with Artifacts, Precedent
(one line: adapted schema-extract tool_call composition + recon
output_schema dialect), Validation (exact commands + observed results),
Repairs, Blocked validation. If only one smoke fits the budget, write the
report with the completed smoke recorded and the other listed under
Blocked validation with the exact command and reason "CLI budget
exhausted" — an honest partial report beats a dead run.

## Artifacts to author

1. `examples/api-discovery/graph.yaml` (the orchestrator)
2. `examples/api-discovery/prompts/*.yaml` — the prompt/schema artifacts the
   graph needs: a candidate-URL generation prompt and the terminal
   `synthesize` prompt (judgement D-2: "the equivalent synthesize
   prompt/schema artifact used by the graph")

Do NOT touch any step graph, step manifest, leaf tool, or the README.

## Precedent

Step composition precedent: `examples/api-discovery/steps/schema-extract/graph.yaml`
(tool_call + conditional edges + on_error: fail). Manifest consumption:
`reference/graph-yaml.md` §tool manifests (runtime `graph` with
`input_mapping`/`output_key`, identical semantics to inline `type: graph`
tools). Output-schema dialect: `examples/api-discovery/steps/recon/prompts/recon.yaml`.

## Graph contract (v1 route frozen by judgement R-1)

- `version: "1.0"`, `name: api-discovery`.
- State (R-3): required `hypothesis` (str), `purpose` (str), `country` (str);
  optional `domain_hint` (str, default ""); intermediate keys as needed
  (`candidate_urls`, `probe_result`, `page_analysis`,
  `platform_confirmation`, `capability_report`); final key `result` (dict).
- Route: candidate generation (llm) → endpoint-probe → page-analysis →
  platform-confirm (only when page-analysis yields platform candidates) →
  schema-extract (only when platform confirmation returns real data) →
  synthesize (llm, state_key `result`).
- Step invocation: `type: tool_call` nodes ONLY, consuming the committed
  graph-runtime manifests (do not modify them):
  - `endpoint_probe` via `manifest: steps/endpoint_probe.tool.yaml` —
    child inputs `candidate_urls: list[str]`, `max_iterations`; output
    `probe_result` dict with `live_endpoints`, `html_pages`, `verdict_hint`
  - `page_analysis` via `manifest: steps/page_analysis.tool.yaml` — child
    inputs `html_pages: list[str]`, `max_iterations`; output `page_analysis`
  - `platform_confirm` via `manifest: steps/platform_confirm.tool.yaml` —
    child inputs `platform_candidates: list[str]`, `base_urls: list[str]`,
    `max_iterations`; output `platform_confirmation`
    (`{family, base_url, confirmed, sample_response}`)
  - `schema_extract` via `manifest: steps/schema_extract.tool.yaml` — child
    inputs `family`, `base_url`, `sample_response`, `openapi_spec_json`;
    output `capability_report`
- NO subgraph nodes. NO recon or browser_sniff manifest references (v1
  excludes them — their absence must not affect graph load). SPA-without-API
  and absent-candidate paths route to synthesize for a terminal
  not-found/manual result — never a graph load/run failure.
- All llm nodes `on_error: fail` (schema-extract precedent).

## Candidate generation prompt

From `hypothesis`, `purpose`, `country`, `domain_hint`: emit
`candidate_urls` as an array of concrete probe-worthy URL strings
(API base guesses, documented API paths, portal pages). When `domain_hint`
contains a URL or domain, derive candidates from it first. Cap at ~8.
Never invent TLDs not implied by the inputs.

## Synthesize prompt (terminal, state_key result)

Consumes all intermediate state. `output_schema:` JSON-Schema dialect,
single terminal object:
- `verdict`: string enum `found`, `not_found`, `needs_manual` (required)
- `profile`: object (optional via omission from required) with properties
  `url` (string), `platform_family` (string), `auth_model` (string),
  `endpoints` (array of string), `sample_response` (object),
  `total_records` (string), `languages` (array of string),
  `data_freshness` (string), `confidence` (string),
  `limitations` (array of string), `probe_suggestion` (string) —
  require at least `url`, `platform_family`, `endpoints` on the profile item
- `reason`: string (required; empty when found)
- `steps_tried`: array of string (required, non-empty — name each step run)
- `alternatives`: array of string (required; may be empty when found)
Rules: `verdict: found` ONLY when a platform was confirmed AND real data
was observed (probe live endpoints or confirmation sample). When verdict
is `found`, `profile` is mandatory, its `url` must come from the actual
probed/confirmed URLs, and `endpoints` must be non-empty (live endpoints
from the probe and/or capability report). Never invent URLs or data.
Brace-free shape description in prose (no literal JSON examples).

## Validation

- `yamlgraph graph lint examples/api-discovery/graph.yaml`
- Positive smoke (live network; stat.fi PxWeb is confirmed reachable):
  `yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="Finnish official statistics API" --var purpose="statistical data lookup" --var country="FI" --var domain_hint="statfin.stat.fi PXWeb api https://statfin.stat.fi/PXWeb/api/v1/fi/StatFin/" --full`
  Passes only if: `result.verdict == "found"`, `result.profile.platform_family`
  identifies PxWeb, `result.profile.url` is a stat.fi PxWeb API URL,
  `result.profile.endpoints` non-empty, and sample data present.
- Negative smoke (deterministic absent target):
  `yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="Nonexistent test registry" --var purpose="lookup" --var country="FI" --var domain_hint="example.invalid" --full`
  Passes only if: `result.verdict` in not_found/needs_manual,
  `result.steps_tried` non-empty, `result.reason` names a stop condition.
- These smokes invoke child graphs with their own LLM calls — they are slow
  (minutes each). Run them sequentially. If a smoke is blocked (network,
  provider transport), record the exact command and reason under Blocked
  validation — do not claim a pass. One transport retry is acceptable.

## Boundaries

Do not modify step graphs, step manifests, leaf tools, framework code under
`yamlgraph/**`, tests, capabilities, changelog, or diary. Only the
orchestrator graph and its prompts listed above.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
