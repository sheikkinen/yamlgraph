# Judgement: FR-788 API Discovery Platform-Confirm Step Graph

**Verdict:** APPROVED - the prior revision defects have been folded into the FR, leaving a clear, bounded example-step graph with mechanical predicates, dependency gates, and named validation.

**Reviewed against:** `feature-requests/FR-788-api-discovery-platform-confirm-step.md`; `feature-requests/FR-788-api-discovery-platform-confirm-step.judgement.md`; `docs/adaptive-probing-plan.md`; `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`; `feature-requests/FR-786-api-discovery-page-analysis-step.md`; `feature-requests/FR-791-api-discovery-orchestrator.md`; `examples/api-discovery/tools/curl_probe.tool.yaml`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/copilot-instructions.md`.

## What is sound

The proposal has a concrete consumer and event: FR-791 needs platform-confirm after page-analysis emits platform candidates that require confirmation (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:8-10`; `feature-requests/FR-791-api-discovery-orchestrator.md:16-20`). The parent plan assigns this exact role to `platform-confirm`: consume platform candidates and base URLs, reuse `curl_probe`, run family-specific confirmation probes, and emit `PlatformConfirmation` (`docs/adaptive-probing-plan.md:121-126`).

The scope is minimal and aligned with the architecture. The parent plan chooses graph-runtime step manifests over subgraph nodes for reusable investigation steps (`docs/adaptive-probing-plan.md:28-32`) and separates orchestrator sequencing from step-level adaptive evidence interpretation (`docs/adaptive-probing-plan.md:63-69`). FR-788 follows that shape by authorizing one agent graph plus one `runtime.type: graph` manifest (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:44-70`). Strategic classification: **Contrib/example**, not framework primitive.

The earlier judgement defects are now folded. The FR replaces "real data" prose with a family matrix covering CKAN, PxWeb, OData, OpenAPI, WordPress REST, and JSON-stat (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:57-67`), freezes inputs and one-output cardinality (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:48-56`), promotes the FR-783 `curl_probe` dependency to a gate (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:84-91`), and names both positive and negative smoke validation (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:79-80`). Those revisions satisfy the prior judgement's R-1 through R-4 requirements (`feature-requests/FR-788-api-discovery-platform-confirm-step.judgement.md:15-57`).

The dependency is feasible. FR-783 is enforced and defines `curl_probe.tool.yaml` as a reusable manifest returning `status`, `redirect`, `content_type`, and `body_head` (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:5-19`; `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:42-62`), and the manifest exists at the expected path with `runtime.type: python` (`examples/api-discovery/tools/curl_probe.tool.yaml:5-10`).

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/api-discovery/steps/platform-confirm/graph.yaml` |
| D-2 | `examples/api-discovery/steps/platform-confirm/prompts/*.yaml` if the authored graph uses prompt files |
| D-3 | `examples/api-discovery/steps/platform_confirm.tool.yaml` with `runtime.type: graph` |
| D-4 | `tmp/draft-authoring-report.md` from the graph-authoring route, listing authored artifacts, precedent, validation, repairs, and blocked validation |
| D-5 | FR-788 implementation notes/status updates after enforcement |

Not authorized: YAMLGraph framework/runtime changes, new node types, new tool-manifest primitives, new leaf tools beyond consuming FR-783 `curl_probe`, endpoint-probe/page-analysis/browser-sniff/recon/schema-extract/orchestrator implementation, CI/hook/doctrine edits, secrets, credentials, or hardcoded API keys. Direct manual graph or prompt authoring by the enforcing session is not authorized; graph artifact creation must use `scripts/author.sh` because graph artifacts are governed by the graph-authoring route (`.github/copilot-instructions.md:15`; `.github/skills/graph-authoring/doctrine.md:86-102`).

## Revised acceptance criteria

- [ ] AC-01: `examples/api-discovery/steps/platform-confirm/graph.yaml` exists and is authored through `scripts/author.sh`.
- [ ] AC-02: `examples/api-discovery/steps/platform_confirm.tool.yaml` exists, declares `runtime.type: graph`, and points to `steps/platform-confirm/graph.yaml`.
- [ ] AC-03: The graph consumes the FR-783 `examples/api-discovery/tools/curl_probe.tool.yaml` manifest by reference and does not define an inline curl shell tool.
- [ ] AC-04: The graph accepts `platform_candidates: list[str]` and `base_urls: list[str]`, probes them deterministically, returns exactly one `PlatformConfirmation`, and returns `confirmed: false` only after all candidate/base URL pairs fail the frozen predicates.
- [ ] AC-05: The output schema validates `PlatformConfirmation { family: str, base_url: str, confirmed: bool, sample_response: str }`.
- [ ] AC-06: The authored prompt/config contains the family confirmation matrix above, including CKAN, PxWeb, OData, OpenAPI, WordPress REST, and JSON-stat predicates.
- [ ] AC-07: Positive smoke against `platform_candidates=["CKAN"], base_urls=["https://demo.ckan.org"]` returns `confirmed: true`, `family == "CKAN"`, and a `sample_response` showing `package_search.result.count > 0`.
- [ ] AC-08: Negative smoke against `platform_candidates=["CKAN"], base_urls=["https://example.com"]` returns `confirmed: false`.
- [ ] AC-09: `yamlgraph graph lint examples/api-discovery/steps/platform-confirm/graph.yaml` passes.
- [ ] AC-10: `tmp/draft-authoring-report.md` records artifacts, precedent, exact validation commands and outcomes, repairs, and any blocked validation.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-783 `curl_probe.tool.yaml` must exist and be loadable before this graph is authored. It is present at `examples/api-discovery/tools/curl_probe.tool.yaml`; if loadability fails during enforcement, stop rather than duplicating the tool. | GATE |
| C-2 | All graph and prompt artifact writes must occur inside the graph-authoring adapter route (`scripts/author.sh`) and produce `tmp/draft-authoring-report.md`; route failure is not permission to author manually. | GATE |
| C-3 | Do not change YAMLGraph framework code, hooks, CI, judge/review doctrine, graph-authoring doctrine, or sibling API-discovery steps under this FR. | GATE |
| C-4 | Positive-only validation is insufficient; the negative smoke in AC-08 or an honestly recorded blocked-validation entry is required. | GATE |
| C-5 | External-network smoke results must be reported as attempted command outcomes. If network access, rate limits, or endpoint drift block the live CKAN smoke, the authoring report must name the exact command and reason; do not silently substitute a weaker local shape check. | GATE |

Authority granted: build only the self-contained platform-confirm example step graph and its graph-runtime manifest, consuming the existing `curl_probe` manifest and proving both positive platform confirmation and false-positive rejection.
