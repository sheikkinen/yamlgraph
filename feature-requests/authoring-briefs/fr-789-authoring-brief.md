# FR-789 API discovery browser-sniff step graph

Author the browser-sniff step of the API discovery pipeline, authorized by
`feature-requests/FR-789-api-discovery-browser-sniff-step.md` (Judged;
R-1..R-3 folded) and its committed judgement.

RESUMED RUN: a prior interrupted authoring run already created the three
target artifacts (they exist untracked in the working tree) and verified
lint plus the CAPTCHA needs-manual smoke. Do not recreate from scratch —
review, repair if needed, complete the remaining data-retention smoke with
the CORRECTED fixture server below, and write the full authoring report
(the prior run died before writing it, which is the contract violation
this rerun cures).

## Artifacts to author

1. `examples/api-discovery/steps/browser-sniff/graph.yaml`
2. `examples/api-discovery/steps/browser-sniff/prompts/sniff.yaml`
3. `examples/api-discovery/steps/browser_sniff.tool.yaml` (graph-runtime tool manifest)

## Precedent

Adapt `examples/api-discovery/steps/recon/` (graph.yaml + prompts/recon.yaml +
steps/recon.tool.yaml, FR-787) and `examples/api-discovery/steps/endpoint-probe/`
— same shape: single `type: agent` node consuming a shared shell tool manifest,
`prompts_relative: true`, graph-runtime step manifest for the orchestrator.

## Graph contract

- `version: "1.0"`, `name: browser-sniff`, description: headless-browser
  network sniff for SPAs that hide APIs behind client-side rendering.
- State:
  - `url` (str): the SPA page URL to load and observe
  - `timeout` (str, default "15000"): sniff timeout in milliseconds, passed to
    the tool
  - `max_iterations` (int, default 4): bounded tool-call iteration budget
  - `sniff_result` (dict): structured SniffResult output
- Tools: `network_sniff` via `manifest: ../../tools/network_sniff.tool.yaml`
  (FR-784 owns it — do NOT modify or reimplement it; the shell command runs
  from the repo root, so its relative `node examples/...` path works as-is).
- Single node `sniff_agent`: `type: agent`, `prompt: sniff`,
  tools `[network_sniff]`, `max_iterations: 4`, `state_key: sniff_result`.
- Edges: START → sniff_agent → END.

## Prompt contract (prompts/sniff.yaml)

- Instruct the agent to call `network_sniff(url, timeout)` once on the given
  URL (retry once only if the tool itself errors), then map the tool's JSON
  output (`{requests, auth_required, needs_manual_reason, warnings}`, each
  request `{url, method, status, content_type, body_preview, classification}`)
  into the final SniffResult:
  - keep only requests with `classification == "data"` in `api_calls`
    (drop `body_preview` never — carry all five CapturedRequest fields);
    exclude telemetry/analytics/noise requests entirely;
  - `auth_required` mirrors the tool's boolean;
  - if the tool reports `needs_manual_reason` non-null OR `auth_required`
    is true, set `verdict_hint` to `needs_manual` and `manual_reason` to the
    tool's reason string (e.g. `auth_token`, `captcha`); otherwise both null.
  - An auth wall or CAPTCHA is a legitimate result, never an error — always
    return a well-formed SniffResult.
- Use the `output_schema:` JSON-Schema dialect (precedent:
  `examples/api-discovery/steps/recon/prompts/recon.yaml`) with top-level
  object:
  - `api_calls`: array of object — items with properties `url` (string),
    `method` (string), `status` (integer), `content_type` (string),
    `body_preview` (string), all required on the item
  - `auth_required`: boolean
  - `verdict_hint`: string — `needs_manual` or empty/null when not needed
  - `manual_reason`: string — reason like `auth_token` or `captcha`, empty/null
    when not needed
  - required: `api_calls`, `auth_required` (verdict_hint and manual_reason
    stay optional via omission from `required`, matching the FR-795 optionality
    convention).
- Do NOT put literal JSON examples with braces in the prompt (templating
  conflict — FR-787 repair history); describe the shape brace-free.

## Validation

- `yamlgraph graph lint examples/api-discovery/steps/browser-sniff/graph.yaml`
- Deterministic smoke against the committed FR-784 SPA fixture
  (no external network). IMPORTANT: do NOT use `python3 -m http.server` —
  static serving 404s the fixture's `/api/*` fetches so nothing classifies
  as `data`. Use the provided dynamic fixture server that mirrors the
  FR-784 test handler (JSON for `/api/*`, 204 for `/analytics/collect`):
  1. Serve: `python3 tmp/fr789_fixture_server.py 8931 &`
  2. `yamlgraph graph run examples/api-discovery/steps/browser-sniff/graph.yaml --var url="http://127.0.0.1:8931/index.html" --var timeout="15000" --full`
  3. Kill the server afterwards.
  The smoke passes only if `sniff_result.api_calls` retains at least one
  `/api/*` data request and excludes the `/analytics/collect` telemetry one.
- needs-manual path: repeat with `--var url="http://127.0.0.1:8931/captcha.html"`
  and confirm `verdict_hint == "needs_manual"` (the prior run already proved
  this once; re-record it in the report).
- If Chromium/Playwright or the local server blocks the smoke, record the
  exact blocked command and reason under Blocked validation — do not claim
  a pass.

## Boundaries

Do not modify `examples/api-discovery/tools/network-sniff.js`,
`network_sniff.tool.yaml`, any other step graph, the orchestrator, framework
code under `yamlgraph/**`, tests, capabilities, changelog, or diary. Only the
three artifacts listed above.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
