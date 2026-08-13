# Judgement: FR-785 API Discovery Endpoint-Probe Step Graph

**Verdict:** APPROVED WITH REVISIONS - the endpoint-probe step is a real, example-scoped consumer with sound architecture, but authority activates only after dependency readiness, architecture choice, response-taxonomy tests, schema/manifest boundaries, and live-smoke evidence are made mechanically checkable.

**Reviewed against:** `feature-requests/FR-785-api-discovery-endpoint-probe-step.md`; `docs/adaptive-probing-plan.md`; `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`; `feature-requests/FR-791-api-discovery-orchestrator.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `feature-requests/FR-773-shared-document-splitter-manifest.md`; `feature-requests/FR-773-shared-document-splitter-manifest.judgement.md`; `feature-requests/TEMPLATE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`.

## What is sound

FR-785 has a concrete first consumer and event: FR-791 needs this step when it probes candidate URLs for live API endpoints (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:8-10`), and FR-791 confirms the orchestrator composes step graph-runtime manifests through `type: tool_call` nodes (`feature-requests/FR-791-api-discovery-orchestrator.md:16-20`, `feature-requests/FR-791-api-discovery-orchestrator.md:54-65`). That defeats `growth_as_default`: this is not an orphan demo.

The proposed shape aligns with the parent plan. The plan assigns adaptive retry and interpretation to investigation-step graphs while deterministic sequencing stays in the orchestrator (`docs/adaptive-probing-plan.md:63-78`). The endpoint-probe brief names the same inputs, tool, retry doctrine, and output schema (`docs/adaptive-probing-plan.md:93-104`). It also explains why agent iteration is the right primitive for 403/404/HTML/XML/timeout interpretation instead of a growing branch table (`docs/adaptive-probing-plan.md:71-78`), matching the FR's `regex_fourth_exclusion` rationale (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:28-35`).

The manifest foundation is feasible. FR-768 is enforced for core manifest support (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:3-5`), and its schema explicitly supports `runtime.type: graph` with `path`, optional `input_mapping`, and `output_key` (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:94-101`). FR-768's judgement froze manifest support as declaration translation over existing runtimes, not a new execution engine (`feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md:41-52`).

Strategic classification: **Contrib/example**. This is a named example pipeline step under `examples/api-discovery/`, built on existing agent, tool-call, graph-runtime manifest, and graph-authoring primitives. It is not a framework primitive because FR-768 already supplied the reusable abstraction, and FR-785 should not change core runtime behavior.

## Required revisions

### R-1: Gate enforcement on the `curl_probe` dependency

Fold an explicit dependency gate into FR-785: enforcement cannot start until FR-783's `curl_probe.tool.yaml` exists, validates, and exposes the status/content-type/redirect/body-preview contract endpoint-probe consumes. FR-785 currently depends on `curl_probe` (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:46`, `feature-requests/FR-785-api-discovery-endpoint-probe-step.md:65`) but does not gate on it. FR-783 states that `curl_probe` must exist before FR-785 can declare it (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:8-10`), and the parent implementation order puts FR-783 before FR-785 (`docs/adaptive-probing-plan.md:207-210`). Do not implement or repair `curl_probe` inside FR-785.

### R-2: Freeze the step architecture as agent-only for this FR

Remove the open question about `type: map` fan-out and state that FR-785 implements the single `type: agent` endpoint-probe step only. The FR currently says "single `type: agent` node" (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:46`) and then leaves map fan-out unresolved (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:51`). The judge rubric treats ambiguity between solution and acceptance criteria as a defect (`.github/skills/judge-fr/doctrine.md:39-44`). FR-773 is useful precedent for feeder tooling, but adding a map feeder here is an optimization and a second architecture; it is not authorized under this FR. If authoring proves agent-only cannot meet the iteration budget, stop and amend/rejudge instead of adding a map stage ad hoc.

### R-3: Make the full response taxonomy testable

Expand the acceptance criteria beyond the current three examples. AC-03 covers only `403`, `404`, and `200` HTML (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:57`), while the parent §4.2 doctrine also includes `000` timeout handling and XML discrimination (`docs/adaptive-probing-plan.md:97-103`). The revised FR must require deterministic evidence for each branch: recorded `curl_probe` calls and final `ProbeResult` assertions for 403 -> alternate User-Agent, 404 `/api` -> version/path variants, 200 HTML -> `html_pages`, repeated 000 -> `verdict_hint: geo_blocked`, and XML -> OData/SOAP/RSS/Atom classification or a live endpoint with correct content type.

### R-4: Specify the graph-runtime manifest and schema boundary exactly

Replace the manifest shorthand with the exact artifact and boundary contract: `examples/api-discovery/steps/endpoint_probe.tool.yaml` uses `runtime.type: graph`, resolves `path: endpoint-probe/graph.yaml` relative to the manifest, maps `candidate_urls` and `max_iterations` into the child graph, and returns the child result under a named output key. FR-785 currently names only `steps/endpoint_probe.tool.yaml` (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:50`, `feature-requests/FR-785-api-discovery-endpoint-probe-step.md:55-56`), while FR-768 requires typed manifest fields and load-time validation (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:84-107`).

Also state where the `ProbeResult` and `EndpointHit` schema lives: either a YAML prompt schema in the endpoint-probe artifact or a named Pydantic model if shared reuse is required. The schema must require `live_endpoints: list[EndpointHit]`, `html_pages: list[str]`, `verdict_hint: str | None`, and `EndpointHit { url, status, content_type, body_preview }` as FR-785 proposes (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:48-49`).

### R-5: Replace the vague live smoke with an exact command and assertions

Revise AC-06 so it names one exact Finnish API URL, the exact smoke command, and the expected assertions. "e.g., stat.fi PxWeb" and "returns correct result" are not mechanically checkable (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:60`). The parent plan requires command-backed lint/smoke evidence for authored graphs (`docs/adaptive-probing-plan.md:217`), and graph-authoring doctrine requires exact validation commands plus honest blocked-validation reporting (`.github/skills/graph-authoring/doctrine.md:55-84`). Enforcement is complete only when the live smoke proves the expected endpoint/content type in `ProbeResult`; a blocked external network run may be recorded, but it is not success.

### R-6: Add a short alternatives/prior-art disposition section

Add an `Alternatives Considered` or `Prior Art` section to FR-785 that dispositions: YAML branch table vs agent, subgraph node vs graph-runtime manifest, agent-only vs map feeder, and one-big-orchestrator-agent vs contained step graph. The parent plan already contains most of this reasoning (`docs/adaptive-probing-plan.md:22-32`, `docs/adaptive-probing-plan.md:71-78`), but the FR itself omits the template's alternatives section (`feature-requests/TEMPLATE.md:60-67`) and leaves the map feeder as an open question. Local judge doctrine requires prior art to be dispositioned before authority (`.github/skills/judge-fr/doctrine.md:112-117`; `.github/copilot-instructions.md:232-232`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-785-api-discovery-endpoint-probe-step.md` revised to fold R-1 through R-6 before enforcement authority activates |
| D-2 | `examples/api-discovery/steps/endpoint-probe/graph.yaml` authored through the graph-authoring route |
| D-3 | Endpoint-probe prompt YAML under `examples/api-discovery/steps/endpoint-probe/prompts/` containing the bounded retry doctrine and `ProbeResult` schema, unless the revised FR names a shared Pydantic schema instead |
| D-4 | `examples/api-discovery/steps/endpoint_probe.tool.yaml` as a `runtime.type: graph` manifest for the endpoint-probe step |
| D-5 | Tests or validation artifacts proving deterministic response-taxonomy behavior, max-iteration enforcement, manifest loading, and schema conformance |
| D-6 | `tmp/draft-authoring-report.md` from `scripts/author.sh` and committed smoke evidence required by the authoring/reporting contract |
| D-7 | Changelog fragment and diary reflection required by repo gates for feature work |

Not authorized: changes under `yamlgraph/`; changes to manifest schema or graph-tool invocation semantics; implementation of FR-783 `curl_probe`, FR-791 orchestrator, page-analysis, platform-confirm, recon, browser-sniff, schema-extract, Playwright/network-sniff utilities, authentication bypasses, CAPTCHA solving, broad crawling outside supplied candidate URLs, `type: map` feeder fan-out, new provider/runtime primitives, CI/hook/doctrine changes, or migration of unrelated examples.

## Revised acceptance criteria

- [ ] AC-01: FR-783's `curl_probe` manifest exists and validates before FR-785 enforcement begins; FR-785 does not create or modify `curl_probe`.
- [ ] AC-02: `examples/api-discovery/steps/endpoint-probe/graph.yaml` exists and is authored via `scripts/author.sh` as an agent-only endpoint-probe graph with a bounded `max_iterations` input/default.
- [ ] AC-03: Endpoint-probe prompt/schema artifacts exist under the endpoint-probe artifact boundary, or the revised FR names the shared Pydantic model used instead.
- [ ] AC-04: `examples/api-discovery/steps/endpoint_probe.tool.yaml` exists with `runtime.type: graph`, manifest-relative path resolution to `endpoint-probe/graph.yaml`, explicit input mapping for `candidate_urls` and `max_iterations`, and a named output key for `ProbeResult`.
- [ ] AC-05: `ProbeResult` and `EndpointHit` validation rejects missing required fields and accepts the exact proposed shape: live endpoints, HTML pages, optional verdict hint, and endpoint URL/status/content type/body preview.
- [ ] AC-06: Deterministic validation proves response handling for 403 alternate User-Agent retry, 404 path variants, 200 HTML routed to `html_pages`, repeated 000 timeout to `verdict_hint: geo_blocked`, and XML discrimination per parent §4.2.
- [ ] AC-07: Validation proves `max_iterations` prevents runaway probing by asserting the tool-call count or equivalent graph state evidence, not just the presence of a config field.
- [ ] AC-08: The revised FR names one exact Finnish API smoke target and expected assertions; the smoke output proves `ProbeResult.live_endpoints` contains the expected endpoint with status/content type/body preview.
- [ ] AC-09: `yamlgraph graph lint examples/api-discovery/steps/endpoint-probe/graph.yaml` passes, and the narrow smoke command recorded in the authoring report passes; blocked external validation is recorded as blocked and does not satisfy AC-08.
- [ ] AC-10: No files under `yamlgraph/` change; if endpoint-probe requires framework changes, enforcement stops and a separate FR enters judgement.
- [ ] AC-11: A changelog fragment and diary reflection are added.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-785-api-discovery-endpoint-probe-step.md`. | GATE |
| C-2 | FR-783's `curl_probe` contract must be available before endpoint-probe authoring begins; implementing or repairing leaf tools under FR-785 is scope creep. | GATE |
| C-3 | The graph remains agent-only. Adding `type: map` fan-out, feeder optimization, or framework/runtime changes requires amended scope and rejudgement. | GATE |
| C-4 | Graph and prompt artifacts must be authored through `scripts/author.sh`, and `tmp/draft-authoring-report.md` must record lint, smoke, failures, repairs, and blocked validation honestly. | GATE |
| C-5 | Response-taxonomy success must be judged from tool-call/final-state evidence and schema-validated `ProbeResult`, not from prose claims that the prompt "handles" a status code. | GATE |
| C-6 | The live Finnish API smoke must pass before the FR can be marked enforced; if network or service availability blocks it, record the block and leave enforcement incomplete. | GATE |
| C-7 | The implementation must not crawl beyond supplied/generated candidate URL variants or attempt auth/CAPTCHA bypass; such findings become `verdict_hint` / downstream-step inputs only. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may author the endpoint-probe agent graph and graph-runtime manifest, add only directly related prompt/schema/tests/smoke evidence/changelog/diary artifacts, and nothing else.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
