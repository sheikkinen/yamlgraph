# Judgement: FR-789 API Discovery Browser-Sniff Step Graph

**Verdict:** APPROVED WITH REVISIONS — the direction is sound, but authority activates only after FR-789 folds in the dependency gate, schema reconciliation, and deterministic validation criteria below.

**Reviewed against:** `feature-requests/FR-789-api-discovery-browser-sniff-step.md`; `docs/adaptive-probing-plan.md`; `feature-requests/FR-784-playwright-network-sniff-utility.md`; `feature-requests/FR-786-api-discovery-page-analysis-step.md`; `feature-requests/FR-791-api-discovery-orchestrator.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The first consumer is concrete: FR-791 routes here only when page-analysis returns `is_spa == true AND api_found == false`, making this an expensive last-resort step rather than a default probe (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:8-20`; `docs/adaptive-probing-plan.md:113-119`). The architecture follows the parent plan's step-as-graph-runtime-tool pattern: investigation steps are graph tools with typed outputs, while deterministic side effects live in leaf tool manifests (`docs/adaptive-probing-plan.md:26-32`, `docs/adaptive-probing-plan.md:63-78`). The proposal also correctly keeps graph authoring under `scripts/author.sh`, matching repo doctrine that all material `graph.yaml` and prompt changes must go through the graph-authoring route (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:49-55`; `.github/copilot-instructions.md:15-16`).

Strategic classification: **Contrib/example**. This serves one concrete example family and orchestrator, using existing YAMLGraph abstractions (`agent`, graph-runtime tool manifests, Pydantic schemas) rather than creating a framework primitive (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:41-45`; `docs/adaptive-probing-plan.md:36-61`).

## Required revisions

### R-1: Declare FR-784 as an enforcement dependency

Add an explicit dependency section stating FR-789 may not be enforced until FR-784 has provided the leaf `network_sniff` tool manifest and `network-sniff.js` utility. FR-789 currently says the agent uses `network_sniff` from FR-784 (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:41-44`, `feature-requests/FR-789-api-discovery-browser-sniff-step.md:56-61`), while FR-784 still owns the actual Playwright utility and shell manifest (`feature-requests/FR-784-playwright-network-sniff-utility.md:16-18`, `feature-requests/FR-784-playwright-network-sniff-utility.md:54-68`). Without this gate, FR-789 acceptance tests can fail because the dependency is absent rather than because the browser-sniff graph is wrong, which the judge doctrine treats as underspecification (`.github/skills/judge-fr/doctrine.md:58-61`).

### R-2: Reconcile `SniffResult` with the `needs_manual` failure mode

Revise the output schema so the auth/CAPTCHA path has a typed place to land. The current schema has only `api_calls` and `auth_required` (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:41-45`), but AC-05 requires a `needs_manual` hint (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:47-55`) and the parent plan defines the same failure mode (`docs/adaptive-probing-plan.md:113-120`). Fold in a field such as `verdict_hint: Literal["needs_manual"] | None` and, if needed, `manual_reason: Literal["auth_wall", "captcha"] | None`, then update AC-04 and AC-05 to assert that shape.

### R-3: Make validation substantive and deterministic

Replace the broad "lint and smoke pass" acceptance criterion with explicit, mechanically checkable validation. The FR must require a deterministic smoke or test fixture proving that the step maps captured `network_sniff` output into a `SniffResult`, filters telemetry/noise, preserves data-carrying JSON/XML requests, and returns the typed `needs_manual` hint for auth/CAPTCHA evidence. This closes the gap between mere artifact presence and meaningful behavior (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:49-55`; `.github/copilot-instructions.md:107-116`, `.github/copilot-instructions.md:208-220`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/api-discovery/steps/browser-sniff/graph.yaml` |
| D-2 | Browser-sniff prompt/schema artifacts under `examples/api-discovery/steps/browser-sniff/` if the authoring route creates them |
| D-3 | `examples/api-discovery/steps/browser_sniff.tool.yaml` graph-runtime tool manifest |
| D-4 | Deterministic validation fixture or test needed to satisfy the revised browser-sniff ACs |
| D-5 | FR-789 status/implementation notes documenting dependency satisfaction and validation evidence |

Not authorized: implementing or modifying `examples/api-discovery/tools/network-sniff.js` or `examples/api-discovery/tools/network_sniff.tool.yaml` beyond dependency wiring owned by FR-784; changing FR-791 orchestrator routing; changing FR-786 page-analysis; adding new framework primitives; adding unrelated Playwright setup or dependency-governance changes; changing judge/review/graph-authoring doctrine or hooks.

## Revised acceptance criteria

- [ ] AC-01: Step graph exists at `examples/api-discovery/steps/browser-sniff/graph.yaml`.
- [ ] AC-02: Graph-runtime tool manifest exists at `examples/api-discovery/steps/browser_sniff.tool.yaml` and points to the browser-sniff step graph.
- [ ] AC-03: FR-784 dependency is satisfied before enforcement: the leaf `network_sniff` manifest and Playwright utility exist and are referenced by the browser-sniff agent, not reimplemented here.
- [ ] AC-04: Browser-sniff agent invokes the leaf `network_sniff` tool to capture XHR/fetch requests.
- [ ] AC-05: Output conforms to `SniffResult { api_calls: list[CapturedRequest], auth_required: bool, verdict_hint: Literal["needs_manual"] | None, manual_reason: str | None }`, with `CapturedRequest { url, method, status, content_type, body_preview }`.
- [ ] AC-06: Deterministic validation proves JSON/XML data requests are retained and analytics/telemetry noise is excluded from `api_calls`.
- [ ] AC-07: Deterministic validation proves auth-token or CAPTCHA evidence returns `verdict_hint == "needs_manual"` without treating the graph run as an error.
- [ ] AC-08: Graph is authored via `scripts/author.sh`, and `tmp/draft-authoring-report.md` records precedent search, lint, smoke, and honest validation evidence for this step.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not write governed graph or prompt artifacts except through the graph-authoring route; use the authoring report, not exit code alone, as validation evidence. | GATE |
| C-2 | Do not implement FR-784 deliverables under FR-789; block until the leaf `network_sniff` utility and manifest exist or fold a dependency-status update into the FR. | GATE |
| C-3 | Do not accept a schema that omits the typed `needs_manual` result path while ACs require that behavior. | GATE |
| C-4 | Do not close enforcement on artifact-exists checks alone; validation must prove at least one retained data request, one excluded telemetry/noise request, and one `needs_manual` path. | GATE |

Authority granted: after R-1 through R-3 are folded into FR-789, the enforcer may build only the browser-sniff example step graph, its graph-runtime tool manifest, and the validation fixture/test needed to prove the revised acceptance criteria.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
