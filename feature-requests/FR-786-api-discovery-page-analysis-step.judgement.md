# Judgement: FR-786 API Discovery Page-Analysis Step Graph

**Verdict:** APPROVED - the revised FR is clear, example-scoped, mechanically testable, and authority may proceed for the page-analysis graph only.

**Reviewed against:** `feature-requests/FR-786-api-discovery-page-analysis-step.md`; cited evidence `docs/adaptive-probing-plan.md`; cited dependency `examples/api-discovery/tools/fetch_page.tool.yaml`; cited prior art and dependency FR `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`; cited prior judgement `feature-requests/FR-783-api-discovery-leaf-tool-manifests.judgement.md`; cited sibling/consumer FRs `feature-requests/FR-789-api-discovery-browser-sniff-step.md` and `feature-requests/FR-791-api-discovery-orchestrator.md`; prior FR-786 judgement `feature-requests/FR-786-api-discovery-page-analysis-step.judgement.md`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/skills/graph-authoring/doctrine.md`, and `.github/copilot-instructions.md`.

## What is sound

FR-786 now names a concrete first consumer and event: FR-791 needs page-analysis when endpoint-probe returns HTML pages requiring source inspection (`feature-requests/FR-786-api-discovery-page-analysis-step.md:8-10`; `feature-requests/FR-791-api-discovery-orchestrator.md:16-20`, `feature-requests/FR-791-api-discovery-orchestrator.md:54-57`). The parent plan assigns this exact role to page-analysis: consume `html_pages`, use `fetch_page`, inspect page source for API references and platform fingerprints, and return `PageAnalysis` (`docs/adaptive-probing-plan.md:106-112`).

Scope is now minimal and single-responsibility. The FR authorizes only the page-analysis step graph, its graph-runtime manifest, fixtures, data catalog, prompts if needed, and validation evidence (`feature-requests/FR-786-api-discovery-page-analysis-step.md:41-60`, `feature-requests/FR-786-api-discovery-page-analysis-step.md:62-69`). It explicitly excludes browser-sniff, orchestrator routing, platform-confirm, schema-extract, runtime primitives, hooks, CI, and doctrine changes (`feature-requests/FR-786-api-discovery-page-analysis-step.md:64-69`, `feature-requests/FR-786-api-discovery-page-analysis-step.md:81-91`). Those exclusions match sibling ownership: FR-789 owns browser-sniff (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:15-20`) and FR-791 owns routing and synthesis (`feature-requests/FR-791-api-discovery-orchestrator.md:52-77`).

The strategic classification is **Contrib/example**. The work lives under `examples/api-discovery/`, implements one step in the parent example pipeline, and uses existing YAMLGraph primitives rather than adding framework runtime behavior (`docs/adaptive-probing-plan.md:36-60`, `docs/adaptive-probing-plan.md:63-78`, `docs/adaptive-probing-plan.md:189-203`). The proposal conforms to graph-authoring doctrine by requiring `scripts/author.sh`, lint, smoke evidence, and the `tmp/draft-authoring-report.md` artifact (`feature-requests/FR-786-api-discovery-page-analysis-step.md:73-80`, `.github/skills/graph-authoring/doctrine.md:55-84`, `.github/skills/graph-authoring/doctrine.md:86-102`).

The prior judgement's required revisions have been folded. The FR now blocks duplicate fetch tooling and depends on the shared manifest (`feature-requests/FR-786-api-discovery-page-analysis-step.md:43-46`, `feature-requests/FR-786-api-discovery-page-analysis-step.md:87-88`), names the platform catalog and exact schema fields (`feature-requests/FR-786-api-discovery-page-analysis-step.md:47-53`), requires deterministic local fixtures (`feature-requests/FR-786-api-discovery-page-analysis-step.md:54-58`, `feature-requests/FR-786-api-discovery-page-analysis-step.md:78-80`), and freezes adjacent work out of scope (`feature-requests/FR-786-api-discovery-page-analysis-step.md:62-69`). The cited dependency exists as `fetch_page` with `runtime.type: shell` and text parsing (`examples/api-discovery/tools/fetch_page.tool.yaml:1-8`), and FR-783 records it as an enforced shared leaf tool (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:5`, `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:64-78`, `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:121-132`).

Acceptance is mechanically checkable. AC-01 through AC-05 check file existence, route provenance, manifest wiring, catalog contents and loading mechanism, and exact typed output shape (`feature-requests/FR-786-api-discovery-page-analysis-step.md:73-77`). AC-06 and AC-07 require fixture-backed assertions for positive API extraction and SPA-without-API routing (`feature-requests/FR-786-api-discovery-page-analysis-step.md:78-79`). AC-08 and AC-09 bind validation and scope policing (`feature-requests/FR-786-api-discovery-page-analysis-step.md:80-81`). These criteria are sufficient to derive failing enforcement tests or smoke checks without importing missing fixtures before implementation.

## Required revisions

None. Authority is granted as written.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/api-discovery/steps/page-analysis/graph.yaml` |
| D-2 | `examples/api-discovery/steps/page-analysis/prompts/*.yaml` as needed by the graph |
| D-3 | `examples/api-discovery/steps/page-analysis/data/platform_catalog.yaml` |
| D-4 | `examples/api-discovery/steps/page-analysis/fixtures/*.html` |
| D-5 | `examples/api-discovery/steps/page_analysis.tool.yaml` with `runtime.type: graph` pointing at `steps/page-analysis/graph.yaml` |
| D-6 | `tmp/draft-authoring-report.md` produced by `scripts/author.sh`, with substantive artifacts, precedent, validation, repairs, and blocked-validation sections |

Not authorized: browser-sniff or Playwright/network-sniff work; orchestrator graph or routing changes; platform-confirm or schema-extract graphs; recon changes; framework runtime primitives; hook, CI, judge/review doctrine, or graph-authoring doctrine changes; duplicate leaf tool manifests; live-web-only validation as the sole proof.

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
| C-1 | Use `scripts/author.sh <task-brief.md>` for graph/prompt authoring and verify `tmp/draft-authoring-report.md` by substance, not exit code. | GATE |
| C-2 | If `examples/api-discovery/tools/fetch_page.tool.yaml` is absent, unloadable, or incompatible with the graph call shape, stop and record the dependency blockage; do not duplicate the tool locally. | GATE |
| C-3 | Validation must include deterministic local fixture smoke evidence; live-web probing may be additional evidence but cannot be the only acceptance proof. | GATE |
| C-4 | Keep the platform catalog in `data_files`; hardcoding the catalog into prompt prose fails the FR. | GATE |
| C-5 | Do not modify framework runtime primitives, hooks, CI, or doctrine while enforcing this example graph FR. | GATE |
| C-6 | The implemented graph must pass the required `url` and `user_agent` arguments when invoking the shared `fetch_page` manifest, because FR-783 defines both as required. | GATE |

Authority granted: enforcement may build only the FR-786 page-analysis graph artifact, graph-runtime manifest, prompt files if needed, platform catalog, deterministic fixtures, and authoring validation report described above.
