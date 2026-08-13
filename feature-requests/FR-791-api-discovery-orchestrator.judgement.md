# Judgement: FR-791 API Discovery Orchestrator Graph

**Verdict:** APPROVED WITH REVISIONS - the orchestration direction is sound, but authority activates only after the FR freezes the v1 dependency/route boundary and replaces ambiguous smoke/schema criteria with mechanically testable checks.

**Reviewed against:** `feature-requests/FR-791-api-discovery-orchestrator.md`; cited evidence `docs/adaptive-probing-plan.md`; cited related FRs `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`, `feature-requests/FR-784-playwright-network-sniff-utility.md`, `feature-requests/FR-785-api-discovery-endpoint-probe-step.md`, `feature-requests/FR-786-api-discovery-page-analysis-step.md`, `feature-requests/FR-787-api-discovery-recon-step.md`, `feature-requests/FR-788-api-discovery-platform-confirm-step.md`, `feature-requests/FR-789-api-discovery-browser-sniff-step.md`, `feature-requests/FR-790-api-discovery-schema-extract-step.md`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`, `reference/graph-yaml.md`, `feature-requests/TEMPLATE.md`.

## What is sound

The problem is real and classified correctly as a contrib/example orchestration graph, not a new framework primitive: the FR names the first consumer and event (`feature-requests/FR-791-api-discovery-orchestrator.md:8-10`), and the parent plan records 50+ repeated source investigations taking 10-30 minutes each (`docs/adaptive-probing-plan.md:11-18`). The architecture also fits existing YAMLGraph capabilities: the parent plan explicitly chooses graph-runtime tool manifests over subgraph nodes (`docs/adaptive-probing-plan.md:28`), assigns the orchestrator responsibility for `type: tool_call` sequencing and conditional edges (`docs/adaptive-probing-plan.md:63-69`), and `reference/graph-yaml.md:1452-1464` documents manifest runtime `graph` with `input_mapping` and `output_key`. The FR preserves graph-authoring doctrine by requiring `scripts/author.sh`, lint, and smoke (`feature-requests/FR-791-api-discovery-orchestrator.md:75`; `.github/copilot-instructions.md:15`).

## Required revisions

### R-1: Freeze the v1 route and dependency set

Rewrite the Summary, Proposed Solution, Related, and AC-08 so v1 is exactly: endpoint-probe -> page-analysis -> platform-confirm when candidates exist -> schema-extract when a platform is confirmed -> synthesize. Recon and browser-sniff are not part of v1, are not referenced as graph manifests, and their absence must not affect graph load. The current FR contradicts itself by routing through recon and browser-sniff in the summary (`feature-requests/FR-791-api-discovery-orchestrator.md:16-20`) while later saying recon is optional and v1 ships without recon/browser-sniff (`feature-requests/FR-791-api-discovery-orchestrator.md:55-58`, `feature-requests/FR-791-api-discovery-orchestrator.md:75-76`). The parent implementation order supports a v1 that skips recon and browser-sniff (`docs/adaptive-probing-plan.md:207-214`).

### R-2: Add a dependency gate for required step manifests

Add a Dependencies section stating that enforcement is blocked until the FR-783 leaf manifests and the graph-runtime manifests for FR-785, FR-786, FR-788, and FR-790 exist and are enforced or otherwise committed in the same branch by their own approved FRs. Do not make FR-791 responsible for implementing those steps. The related FRs are all still `Status: Proposed` in the cited files (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:5`, `feature-requests/FR-786-api-discovery-page-analysis-step.md:5`, `feature-requests/FR-788-api-discovery-platform-confirm-step.md:5`, `feature-requests/FR-790-api-discovery-schema-extract-step.md:5`), but FR-791 depends on them (`feature-requests/FR-791-api-discovery-orchestrator.md:83-87`; `docs/adaptive-probing-plan.md:191-201`). Tests that fail because manifests are missing would be fixture/dependency failures, not proof of missing orchestrator behavior, which the judge doctrine treats as underspecification (`.github/skills/judge-fr/doctrine.md:58-61`).

### R-3: Specify the input contract and final output validation surface

Replace the inconsistent example commands with one input contract: required `hypothesis`, `purpose`, and `country`; optional `domain_hint`. Name the final state key `result`, and state where the output schema is declared. The schema must be mechanically validatable as exactly one terminal result: either an API profile with the fields listed in the FR or a not-found/manual verdict with `verdict`, `reason`, `steps_tried`, and `alternatives`. The current value command omits `purpose` (`feature-requests/FR-791-api-discovery-orchestrator.md:24-25`) while the ideal command includes it (`feature-requests/FR-791-api-discovery-orchestrator.md:40-45`) and the parent plan declares it as an input (`docs/adaptive-probing-plan.md:135-138`).

### R-4: Replace vague smoke checks with exact commands and assertions

Revise AC-05 and AC-06 to name the exact smoke commands and expected assertions. For the positive smoke, use stat.fi/PxWeb with a `domain_hint` and assert at minimum: `result.verdict == "found"`, `result.profile.platform_family` is PxWeb, the profile URL is a stat.fi PxWeb API URL, endpoints are non-empty, and sample data is present. For the negative smoke, use a deterministic absent target such as `domain_hint="example.invalid"` and assert `result.verdict in {"not_found", "needs_manual"}`, `steps_tried` is non-empty, and `reason` is one of the FR's enumerated stop reasons. The current criteria use "e.g." and "known-absent/geo-blocked" without naming a target or assertions (`feature-requests/FR-791-api-discovery-orchestrator.md:73-74`), so they are not mechanically checkable under the judge measurability/testability criteria (`.github/skills/judge-fr/doctrine.md:43-45`, `.github/skills/judge-fr/doctrine.md:58-61`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/api-discovery/graph.yaml` orchestrator graph |
| D-2 | `examples/api-discovery/prompts/synthesize.yaml` or the equivalent synthesize prompt/schema artifact used by the graph |
| D-3 | Authoring validation record produced by `scripts/author.sh` and cited from `tmp/draft-authoring-report.md` |

Not authorized: implementing FR-783, FR-784, FR-785, FR-786, FR-787, FR-788, FR-789, or FR-790 inside this FR; adding `network-sniff.js`; adding recon or browser-sniff v1 routing; modifying YAMLGraph framework runtime, `tool_call`, graph-runtime manifest semantics, CI, hooks, judge/review doctrine, or the control-plane repository; replacing graph-runtime manifests with subgraph nodes.

## Revised acceptance criteria

- [ ] AC-01: `examples/api-discovery/graph.yaml` exists and was authored via `scripts/author.sh`; the authoring report records precedent search, graph lint, smoke commands, and outcomes.
- [ ] AC-02: The graph input contract is documented and exercised with required `hypothesis`, `purpose`, `country`, and optional `domain_hint`.
- [ ] AC-03: The graph uses `type: tool_call` nodes against committed graph-runtime manifests for endpoint-probe, page-analysis, platform-confirm, and schema-extract; it uses no subgraph nodes.
- [ ] AC-04: The graph does not reference recon or browser-sniff manifests in v1; SPA-without-API and absent-candidate paths route to a terminal not-found/manual result instead of failing graph load.
- [ ] AC-05: Conditional routing skips platform-confirm when page-analysis returns no platform candidates and only enters schema-extract after platform confirmation returns real data.
- [ ] AC-06: The final state key `result` validates against the declared output schema as exactly one terminal result: found API profile or not-found/manual verdict.
- [ ] AC-07: Positive smoke command against stat.fi/PxWeb returns `found`, PxWeb platform family, a stat.fi PxWeb API URL, non-empty endpoints, and sample data.
- [ ] AC-08: Negative smoke command against the selected deterministic absent target returns `not_found` or `needs_manual` with non-empty `steps_tried`, a permitted `reason`, and alternatives or manual guidance.
- [ ] AC-09: `yamlgraph graph lint examples/api-discovery/graph.yaml` passes.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not begin FR-791 enforcement until the required dependency manifests from FR-783, FR-785, FR-786, FR-788, and FR-790 are present and governed by their own approved/enforced FRs. | GATE |
| C-2 | Use the graph-authoring route for graph and prompt writes; manual unsentineled edits to governed graph artifacts are not authorized. | GATE |
| C-3 | Do not implement missing step graphs, leaf tools, recon, browser-sniff, Playwright utilities, or framework runtime changes under this FR. | GATE |
| C-4 | If either smoke target is unavailable, enforcement is blocked until the FR names a replacement target with equivalent explicit assertions; do not substitute a shape-only smoke. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR and C-1 through C-4 are satisfied, implement only the v1 API discovery orchestrator example graph and its synthesis prompt/schema, composing already-governed graph-runtime step manifests through `type: tool_call`.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
