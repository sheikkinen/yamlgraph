# Judgement: FR-788 API Discovery Platform-Confirm Step Graph

**Verdict:** APPROVED WITH REVISIONS - sound example-step direction, but authority activates only after the FR defines mechanical substance predicates, input/output cardinality, dependency gates, and named validation.

**Reviewed against:** `feature-requests/FR-788-api-discovery-platform-confirm-step.md`; `docs/adaptive-probing-plan.md`; `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`; `feature-requests/FR-786-api-discovery-page-analysis-step.md`; `feature-requests/FR-791-api-discovery-orchestrator.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/copilot-instructions.md`.

## What is sound

The proposal has a real first consumer: FR-791 needs this step when page analysis returns platform candidates requiring confirmation (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:8-10`; `feature-requests/FR-791-api-discovery-orchestrator.md:16-20`). The parent plan already assigns this exact responsibility to `platform-confirm`: consume platform candidates and base URLs, reuse `curl_probe`, run family-specific confirmation probes, and emit `PlatformConfirmation` (`docs/adaptive-probing-plan.md:121-127`).

The architecture is aligned with the parent plan's reusable step-manifest pattern rather than inventing a framework primitive: graph-runtime manifests are deliberately chosen over subgraph nodes for reusable investigation steps (`docs/adaptive-probing-plan.md:26-32`), and the division of responsibility places adaptive evidence interpretation inside step graphs while the orchestrator owns sequencing (`docs/adaptive-probing-plan.md:63-69`). Strategic classification: **Contrib/example**, not framework primitive.

The dependency on `curl_probe` is coherent. FR-783 defines `curl_probe.tool.yaml` as a shared shell manifest returning status, redirect, content type, and body head, with platform-confirm named as a consumer (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:42-48`; `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:73-80`).

## Required revisions

### R-1: Replace "real data" prose with a family confirmation matrix

Revise the Proposed Solution and AC-03 so each supported family has a mechanically checkable confirmation predicate. The matrix must include at least:

| Family | Probe(s) | Confirmed only when |
|---|---|---|
| CKAN | `/api/3/action/status_show` and `/api/3/action/package_search?rows=1` | JSON has CKAN success semantics and `package_search` returns a positive count or at least one dataset record with `id`/`name`/`title`; a bare 200 or empty `rows=0` response is not sufficient. |
| PxWeb | `/api/v1/{lang}/{db}` | JSON is a non-empty subject/database/table list with platform-specific fields such as `id` and `text`. |
| OData | service endpoint with `?$top=1&$format=json` where applicable | JSON contains OData markers such as `@odata.context` and a non-empty `value` array, or the FR explicitly names the equivalent non-empty entity proof. |
| OpenAPI | spec fetch | JSON/YAML parses as OpenAPI/Swagger and exposes at least three paths, matching the parent stop-condition precedent (`docs/adaptive-probing-plan.md:166-168`). |
| WordPress | `/wp-json/wp/v2/types` | JSON object contains one or more concrete content types such as `post` or `page`; endpoint existence alone is not enough. |
| JSON-stat | candidate cube JSON | JSON-stat dataset structure is present and includes non-empty dimensions or values. |

This revision is required because the FR says confirmation must prove substance, not shape (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:24-27`), but its current query list includes CKAN `package_search?rows=0` (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:44-52`), which can prove API shape without returning dataset records.

### R-2: Freeze input and output cardinality

Revise the FR to state the exact graph inputs and the exact meaning of one output. Freeze the contract as:

- Inputs: `platform_candidates: list[str]` and `base_urls: list[str]`.
- Probe order: deterministic iteration over candidates and base URLs as listed by upstream steps.
- Output: exactly one `PlatformConfirmation` object for the first candidate/base URL pair satisfying the family predicate.
- Failure output: `confirmed: false` only after all candidate/base URL pairs have been attempted; `family`, `base_url`, and `sample_response` must identify the best failed attempt and why it did not satisfy the predicate.

This removes the current plural/singular ambiguity: the FR says the step takes candidates and base URLs (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:16-19`), but the proposed schema is singular (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:52-53`).

### R-3: Promote FR-783 from related context to an enforcement gate

Add an explicit dependency section: enforcement of FR-788 may start only after FR-783 has produced a loadable `examples/api-discovery/tools/curl_probe.tool.yaml`. The platform-confirm graph must consume that manifest by reference and must not define an inline curl shell tool.

This is required because the parent plan says FR-783 is implemented first and FR-788 depends on it (`docs/adaptive-probing-plan.md:189-203`; `docs/adaptive-probing-plan.md:207-214`), while the FR currently lists FR-783 only under Related (`feature-requests/FR-788-api-discovery-platform-confirm-step.md:64-69`).

### R-4: Name positive and negative smoke validations

Revise AC-05 into two command-backed validations:

1. A positive smoke against one exact public CKAN or PxWeb URL named in the FR, asserting `confirmed: true`, the expected `family`, and a `sample_response` satisfying the family predicate from R-1.
2. A negative smoke against a non-matching URL, such as CKAN candidate plus `https://example.com`, asserting `confirmed: false`.

If external network access blocks either smoke during authoring, the authoring report must record the exact blocked command and reason. This follows the graph-authoring validation contract: lint is mandatory, smoke must be attempted, and blocked validation must be reported honestly (`.github/skills/graph-authoring/doctrine.md:71-84`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/api-discovery/steps/platform-confirm/graph.yaml` |
| D-2 | `examples/api-discovery/steps/platform-confirm/prompts/*.yaml` if the authored graph uses prompt files |
| D-3 | `examples/api-discovery/steps/platform_confirm.tool.yaml` with `runtime.type: graph` |
| D-4 | `tmp/draft-authoring-report.md` from the graph-authoring route, listing authored artifacts, precedent, validation, repairs, and blocked validation |
| D-5 | FR-788 text updated with the required revisions before enforcement begins |

Not authorized: framework runtime changes, new node types, new tool-manifest primitives, new leaf tools beyond consuming FR-783 `curl_probe`, browser-sniff, recon, schema-extract, orchestrator implementation, CI/hook/doctrine edits, secrets, credentials, or hardcoded API keys. Direct manual graph authoring by the requesting/enforcing session is not authorized; graph artifact creation must go through `scripts/author.sh` because graph creation is governed by the artifact-class route (`.github/copilot-instructions.md:15`; `.github/skills/graph-authoring/doctrine.md:86-102`).

## Revised acceptance criteria

- [ ] AC-01: `examples/api-discovery/steps/platform-confirm/graph.yaml` exists and is authored through `scripts/author.sh`.
- [ ] AC-02: `examples/api-discovery/steps/platform_confirm.tool.yaml` exists, declares `runtime.type: graph`, and points to `steps/platform-confirm/graph.yaml`.
- [ ] AC-03: The graph consumes the FR-783 `examples/api-discovery/tools/curl_probe.tool.yaml` manifest by reference and does not define an inline curl shell tool.
- [ ] AC-04: The graph accepts `platform_candidates: list[str]` and `base_urls: list[str]`, probes them deterministically, returns exactly one `PlatformConfirmation`, and returns `confirmed: false` only after all candidate/base URL pairs fail the frozen predicates.
- [ ] AC-05: The output schema validates `PlatformConfirmation { family: str, base_url: str, confirmed: bool, sample_response: str }`.
- [ ] AC-06: The authored prompt/config contains the R-1 family confirmation matrix, including CKAN, PxWeb, OData, OpenAPI, WordPress, and JSON-stat predicates.
- [ ] AC-07: Positive smoke against the exact public CKAN or PxWeb URL named in the revised FR returns `confirmed: true`, the expected family, and a sample response satisfying the corresponding predicate.
- [ ] AC-08: Negative smoke against a non-matching URL returns `confirmed: false`.
- [ ] AC-09: `yamlgraph graph lint examples/api-discovery/steps/platform-confirm/graph.yaml` passes.
- [ ] AC-10: `tmp/draft-authoring-report.md` records artifacts, precedent, exact validation commands and outcomes, repairs, and any blocked validation per the graph-authoring doctrine.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into FR-788 before implementation authority activates. | GATE |
| C-2 | FR-783 `curl_probe.tool.yaml` must exist and be loadable before this graph is authored; otherwise FR-788 waits. | GATE |
| C-3 | All graph and prompt artifact writes must occur inside the graph-authoring adapter route and produce `tmp/draft-authoring-report.md`; route failure is not permission to author manually. | GATE |
| C-4 | The enforcer must not change YAMLGraph framework code, hooks, CI, judge/review doctrine, or graph-authoring doctrine under this FR. | GATE |
| C-5 | A positive-only validation is insufficient; at least one negative confirmation smoke or equivalent recorded blocked command is required. | GATE |

Authority granted: after the required revisions are folded into FR-788, build only the self-contained platform-confirm example step graph and its graph-runtime manifest, consuming the existing `curl_probe` manifest and proving both positive confirmation and false-positive rejection.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
