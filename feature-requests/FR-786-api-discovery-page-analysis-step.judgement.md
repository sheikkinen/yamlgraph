# Judgement: FR-786 API Discovery Page-Analysis Step Graph

**Verdict:** APPROVED WITH REVISIONS - the page-analysis step is a sound contrib/example graph, but authority activates only after the FR makes its tool dependency, data catalog, deterministic fixtures, and validation commands mechanically enforceable.

**Reviewed against:** `feature-requests/FR-786-api-discovery-page-analysis-step.md`; cited evidence `docs/adaptive-probing-plan.md` lines 35-60, 63-78, 81-112, 170-185, 189-214; cited sibling FRs `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md` and `feature-requests/FR-789-api-discovery-browser-sniff-step.md`; consumer FR `feature-requests/FR-791-api-discovery-orchestrator.md`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/copilot-instructions.md` lines 15, 173-176, 208-226, 230-233, and `.github/skills/graph-authoring/doctrine.md` lines 9-17, 33-69, 71-108.

## What is sound

FR-786 names a real first consumer: FR-791 needs this result when endpoint-probe returns HTML pages that may hide APIs (`feature-requests/FR-786-api-discovery-page-analysis-step.md:8-10`; `feature-requests/FR-791-api-discovery-orchestrator.md:16-20`). The parent plan already assigns page-analysis a narrow responsibility - inspect page source using `fetch_page`, extract API references and platform fingerprints, and emit `PageAnalysis` (`docs/adaptive-probing-plan.md:106-112`).

The strategic classification is **Contrib/example**. The parent plan places the work under `examples/api-discovery/` and marks FR-786 as an Example sub-FR (`docs/adaptive-probing-plan.md:39-60`, `docs/adaptive-probing-plan.md:191-201`). The architecture aligns with existing repo doctrine: LLM judgement remains in a YAML graph, deterministic side effects stay in shared tool manifests, and typed output normalizes the boundary (`docs/adaptive-probing-plan.md:63-78`; `.github/copilot-instructions.md:212-216`).

## Required revisions

### R-1: Declare the exact dependency on the shared `fetch_page` manifest

Revise the FR so implementation is blocked until FR-783's `examples/api-discovery/tools/fetch_page.tool.yaml` exists and is consumed by reference. The page-analysis graph must not duplicate the curl command inline or create a second fetch tool. This follows the parent plan's split between step manifests and shared tools (`docs/adaptive-probing-plan.md:39-60`, `docs/adaptive-probing-plan.md:173-185`) and FR-783's definition of `fetch_page` as the page-analysis consumer tool (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:49-54`).

### R-2: Name the platform catalog artifact and schema boundary

Revise the FR to name `examples/api-discovery/steps/page-analysis/data/platform_catalog.yaml` as the platform catalog and require the graph to load it through `data_files`, not hardcoded prompt text. The catalog must include at least CKAN, PxWeb, SwaggerUI, OData, Liferay, JSF, WordPress REST, and EntryScape markers because the FR and parent plan list those families as page-analysis behavior (`feature-requests/FR-786-api-discovery-page-analysis-step.md:31-45`; `docs/adaptive-probing-plan.md:106-112`). Also state where `PageAnalysis` is declared and require the exact fields `api_found: bool`, `is_spa: bool`, `platform_candidates: list[str]`, and `api_urls: list[str]`.

### R-3: Replace prose-only extraction criteria with deterministic fixture checks

Revise AC-03 through AC-05 into fixture-backed checks. Add committed HTML fixtures under `examples/api-discovery/steps/page-analysis/fixtures/` that exercise script-tag URLs, `data-api-url`, inline `fetch()`/axios calls, platform fingerprints, and an SPA-without-API case. The smoke command must run the graph against local fixture URLs and assert the returned `PageAnalysis` values. The current ACs say what the agent should do, but not what command or assertion proves it (`feature-requests/FR-786-api-discovery-page-analysis-step.md:48-57`), while judge doctrine requires mechanically checkable acceptance criteria (`.github/skills/judge-fr/doctrine.md:43-44`) and graph-authoring doctrine requires lint plus meaningful smoke evidence (`.github/skills/graph-authoring/doctrine.md:71-84`).

### R-4: Freeze the boundary away from browser-sniff and orchestrator work

Revise the FR to state explicitly that browser-sniff, network-sniff, orchestrator routing, platform-confirm, schema-extract, and new runtime primitives are not authorized by FR-786. FR-789 owns browser-sniff (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:15-20`, `feature-requests/FR-789-api-discovery-browser-sniff-step.md:47-55`), and FR-791 owns the routing that decides when browser-sniff runs (`feature-requests/FR-791-api-discovery-orchestrator.md:52-77`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/api-discovery/steps/page-analysis/graph.yaml` |
| D-2 | `examples/api-discovery/steps/page-analysis/prompts/*.yaml` as needed by the graph |
| D-3 | `examples/api-discovery/steps/page-analysis/data/platform_catalog.yaml` |
| D-4 | `examples/api-discovery/steps/page-analysis/fixtures/*.html` |
| D-5 | `examples/api-discovery/steps/page_analysis.tool.yaml` with `runtime.type: graph` pointing at `page-analysis/graph.yaml` |
| D-6 | `tmp/draft-authoring-report.md` produced by `scripts/author.sh`, with artifacts, precedent, validation, repairs, and blocked-validation sections |

Not authorized: browser-sniff or Playwright/network-sniff work; orchestrator graph or routing changes; platform-confirm or schema-extract graphs; creation or alteration of framework runtime primitives; changes to hooks, CI, judge/review doctrine, or graph-authoring doctrine; duplicate leaf tool manifests when FR-783 provides the shared tool.

## Revised acceptance criteria

- [ ] AC-01: `examples/api-discovery/steps/page-analysis/graph.yaml` exists and is authored through `scripts/author.sh`, with `tmp/draft-authoring-report.md` listing it as an authored artifact.
- [ ] AC-02: `examples/api-discovery/steps/page_analysis.tool.yaml` exists and declares `runtime.type: graph` with a path resolving to `steps/page-analysis/graph.yaml`.
- [ ] AC-03: The graph references `examples/api-discovery/tools/fetch_page.tool.yaml`; no inline curl/fetch-page duplicate is added under the step graph.
- [ ] AC-04: `examples/api-discovery/steps/page-analysis/data/platform_catalog.yaml` exists, contains CKAN, PxWeb, SwaggerUI, OData, Liferay, JSF, WordPress REST, and EntryScape markers, and is loaded through the graph/prompt `data_files` mechanism.
- [ ] AC-05: The graph declares or uses a `PageAnalysis` schema with exactly `api_found: bool`, `is_spa: bool`, `platform_candidates: list[str]`, and `api_urls: list[str]`; lint or smoke output proves returned values conform to it.
- [ ] AC-06: A local fixture smoke run containing script tags, `data-api-url`, inline fetch/axios calls, and platform markers returns `api_found == true`, includes the expected extracted API URLs, and includes at least CKAN, PxWeb, SwaggerUI, and OData in `platform_candidates`.
- [ ] AC-07: A local fixture smoke run for an SPA page with no static API references returns `is_spa == true` and `api_found == false`, establishing the routing signal consumed by FR-789/FR-791 without implementing browser-sniff.
- [ ] AC-08: `yamlgraph graph lint examples/api-discovery/steps/page-analysis/graph.yaml` passes and the narrow fixture smoke command is recorded in `tmp/draft-authoring-report.md` with its actual outcome.
- [ ] AC-09: The diff contains no browser-sniff, orchestrator, platform-confirm, schema-extract, runtime-primitive, hook, CI, or doctrine changes under this FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Use `scripts/author.sh <task-brief.md>` for graph/prompt authoring and verify `tmp/draft-authoring-report.md` by substance, not exit code, per graph-authoring doctrine. | GATE |
| C-2 | If `examples/api-discovery/tools/fetch_page.tool.yaml` from FR-783 is absent or unloadable, stop and record the dependency blockage; do not duplicate the tool locally. | GATE |
| C-3 | Validation must include deterministic local fixture smoke evidence; live-web probing may be additional evidence but cannot be the only acceptance proof. | GATE |
| C-4 | Keep the platform catalog in `data_files`; hardcoding the catalog into prompt prose fails the FR. | GATE |
| C-5 | Do not modify framework runtime primitives, hooks, CI, or doctrine while enforcing this example graph FR. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, enforcement may build only the page-analysis graph, its graph-runtime manifest, platform catalog, fixtures, prompt files, and authoring validation report described above.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
