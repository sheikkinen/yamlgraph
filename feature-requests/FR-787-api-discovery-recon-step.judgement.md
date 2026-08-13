# Judgement: FR-787 API Discovery Recon Step Graph

**Verdict:** APPROVED WITH REVISIONS - the recon step is a sound contrib/example graph, but authority activates only after the FR folds in dependency gating, mechanical output validation, and the optional-orchestrator boundary.

**Reviewed against:** `feature-requests/FR-787-api-discovery-recon-step.md`; `docs/adaptive-probing-plan.md`; `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`; `feature-requests/FR-791-api-discovery-orchestrator.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`.

## What is sound

The first consumer is named: FR-791 wants prior-art evidence before blind probing, while explicitly tolerating recon's absence (`feature-requests/FR-787-api-discovery-recon-step.md:8-11`). That passes the consumer test and avoids `growth_as_default`; local doctrine requires naming the first consumer/event (`feature-requests/TEMPLATE.md:8-10`, `.github/copilot-instructions.md:125`, `.github/copilot-instructions.md:143`).

The strategic classification is **Contrib/example**, not a framework primitive: the parent plan places the work under `examples/api-discovery/`, packages investigation steps as graph-runtime tool manifests, and keeps deterministic side effects in shared tool manifests (`docs/adaptive-probing-plan.md:38-60`, `docs/adaptive-probing-plan.md:63-69`). The FR asks for one step graph and one manifest (`feature-requests/FR-787-api-discovery-recon-step.md:43-46`), not new runtime infrastructure.

The architecture direction aligns with the parent plan: each investigation step is its own agent graph with a typed output contract, while the orchestrator handles sequencing and skip logic (`docs/adaptive-probing-plan.md:65-78`). Recon's behavior and schema are also explicitly specified in the plan (`docs/adaptive-probing-plan.md:85-91`).

## Required revisions

### R-1: Gate implementation on the `gh_code_search` manifest dependency

Add an explicit dependency and enforcement gate: FR-787 may not author or validate the recon graph until the FR-783 `gh_code_search.tool.yaml` deliverable exists under `examples/api-discovery/tools/` and is loadable by a consumer graph. FR-787 depends on that tool (`feature-requests/FR-787-api-discovery-recon-step.md:43`, `feature-requests/FR-787-api-discovery-recon-step.md:59`), but FR-783 is still proposed (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:3-6`) and defines `gh_code_search` separately (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:56-61`). The parent index also states FR-787 depends on FR-783 (`docs/adaptive-probing-plan.md:191-198`).

### R-2: Make `ReconResult` validation mechanically checkable

Replace the current broad AC-04 with concrete schema checks: the graph must define or reference `ReconResult` with exactly `candidate_urls`, `auth_hints`, `schema_hints`, and `evidence` as `list[str]`; the smoke output must be validated against that schema; and each non-empty evidence entry must include enough source identity to audit the claim, at minimum repository, path, and URL or GitHub result link. The ideal result promises evidence links (`feature-requests/FR-787-api-discovery-recon-step.md:37-39`), but the acceptance criterion only says "conforms" (`feature-requests/FR-787-api-discovery-recon-step.md:52-54`). Judge doctrine requires mechanically checkable criteria (`.github/skills/judge-fr/doctrine.md:43-44`) and directly derivable tests (`.github/skills/judge-fr/doctrine.md:58-61`).

### R-3: Specify the validation evidence and credential handling

Fold the graph-authoring validation contract into the FR: enforcement must produce `tmp/draft-authoring-report.md` with `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation`; list the exact precedent adapted; run `yamlgraph graph lint examples/api-discovery/steps/recon/graph.yaml`; and run a narrow smoke command with concrete variables. If `gh` authentication blocks the smoke, the report must record the exact blocked command and reason, and the FR must not claim "smoke pass" for that run. FR-787 currently requires authoring via `scripts/author.sh` and lint/smoke pass (`feature-requests/FR-787-api-discovery-recon-step.md:55`), while graph-authoring doctrine requires precedent search (`.github/skills/graph-authoring/doctrine.md:33-45`), a parseable authoring report (`.github/skills/graph-authoring/doctrine.md:55-69`), and honest validation/blocked-validation reporting (`.github/skills/graph-authoring/doctrine.md:71-84`).

### R-4: Freeze recon as optional and prohibit orchestrator coupling

Add a scope boundary stating that FR-787 does not modify `examples/api-discovery/graph.yaml`, orchestrator routing, or other step graphs, and must not make FR-791 depend on recon. The FR itself says the orchestrator tolerates recon's absence (`feature-requests/FR-787-api-discovery-recon-step.md:8-11`), and FR-791 explicitly ships v1 without recon and browser-sniff (`feature-requests/FR-791-api-discovery-orchestrator.md:58`, `feature-requests/FR-791-api-discovery-orchestrator.md:76`). This keeps the change single-responsibility as required by judge doctrine (`.github/skills/judge-fr/doctrine.md:49-50`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-787-api-discovery-recon-step.md`, revised with R-1 through R-4 and later implementation evidence |
| D-2 | `examples/api-discovery/steps/recon/graph.yaml` |
| D-3 | `examples/api-discovery/steps/recon/prompts/*.yaml`, if the authored graph uses prompt files |
| D-4 | `examples/api-discovery/steps/recon.tool.yaml` |
| D-5 | `tmp/draft-authoring-report.md` as validation evidence during enforcement |

Not authorized: changes to YAMLGraph framework code; new node types, provider/runtime primitives, hooks, CI, or doctrine; changes to `examples/api-discovery/tools/gh_code_search.tool.yaml` except through FR-783; changes to the API discovery orchestrator; changes to endpoint-probe, page-analysis, browser-sniff, platform-confirm, or schema-extract step graphs.

## Revised acceptance criteria

- [ ] AC-01: `examples/api-discovery/steps/recon/graph.yaml` exists and was authored through `scripts/author.sh` with a non-empty `tmp/draft-authoring-report.md`.
- [ ] AC-02: `examples/api-discovery/steps/recon.tool.yaml` exists and declares a graph runtime pointing to `recon/graph.yaml`.
- [ ] AC-03: Enforcement confirms the FR-783 `examples/api-discovery/tools/gh_code_search.tool.yaml` dependency exists and is loadable before authoring or smoking recon.
- [ ] AC-04: The recon agent prompt or config generates domain/service/country search-term variants and iterates `gh_code_search` within a bounded iteration budget.
- [ ] AC-05: The graph output validates as `ReconResult` with `candidate_urls`, `auth_hints`, `schema_hints`, and `evidence` as `list[str]`.
- [ ] AC-06: Non-empty evidence entries include source identity sufficient for audit: repository, path, and URL or GitHub result link.
- [ ] AC-07: Empty results are valid: a no-hit or blocked-footprint scenario returns empty lists under `ReconResult`, not a graph error.
- [ ] AC-08: `yamlgraph graph lint examples/api-discovery/steps/recon/graph.yaml` is run and recorded in `tmp/draft-authoring-report.md`.
- [ ] AC-09: A narrow smoke command is run with concrete variables and recorded; if blocked by missing `gh` auth, the exact command and blocker are recorded without claiming a pass.
- [ ] AC-10: FR-787 does not modify the orchestrator or make FR-791 require recon.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement FR-787 until FR-783's `gh_code_search.tool.yaml` exists and loads from a consumer graph. | GATE |
| C-2 | Use the graph-authoring adapter route for governed graph artifacts; do not author `graph.yaml` or prompt artifacts manually from the requesting session. | GATE |
| C-3 | Do not claim smoke success when GitHub CLI authentication or network access blocks the recon smoke; record the blocked command and reason instead. | GATE |
| C-4 | Do not change orchestrator routing or other API discovery steps under this FR. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, enforcement may build only the recon step graph, its prompt artifacts if needed, and its graph-runtime tool manifest within the frozen surfaces above.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
