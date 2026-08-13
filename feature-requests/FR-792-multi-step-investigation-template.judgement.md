# Judgement: FR-792 Multi-Step Investigation Template

**Verdict:** APPROVED WITH REVISIONS - the scaffold direction is sound as post-API-discovery example tooling, but authority activates only after the FR stops treating proposed plans as proven evidence, freezes the script surface, and closes the graph-authoring and smoke-test gaps.

**Reviewed against:** `feature-requests/FR-792-multi-step-investigation-template.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `docs/adaptive-probing-plan.md`; `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`; `feature-requests/FR-784-playwright-network-sniff-utility.md`; `feature-requests/FR-785-api-discovery-endpoint-probe-step.md`; `feature-requests/FR-786-api-discovery-page-analysis-step.md`; `feature-requests/FR-787-api-discovery-recon-step.md`; `feature-requests/FR-788-api-discovery-platform-confirm-step.md`; `feature-requests/FR-789-api-discovery-browser-sniff-step.md`; `feature-requests/FR-790-api-discovery-schema-extract-step.md`; `feature-requests/FR-791-api-discovery-orchestrator.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-767-graph-authoring-sole-route.judgement.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `feature-requests/FR-773-shared-document-splitter-manifest.md`; `feature-requests/FR-773-shared-document-splitter-manifest.judgement.md`.

## What is sound

The FR names a real architectural shape: an orchestrator using `type: tool_call` on graph-runtime step manifests, step graphs with typed input/output, shared leaf tool manifests, conditional edges, and terminal synthesis (`feature-requests/FR-792-multi-step-investigation-template.md:42-47`). That shape is also documented in the parent API-discovery plan's division of responsibility: orchestrator for sequencing/state hand-off, graph-runtime step tools for adaptive interpretation, and shell/python tool manifests for deterministic side effects (`docs/adaptive-probing-plan.md:63-79`).

The proposal is correctly not a runtime primitive. It says the mechanism is file generation from templates, "no runtime behavior, no new framework primitives" (`feature-requests/FR-792-multi-step-investigation-template.md:87-93`), which aligns with FR-768's implemented manifest contract: manifests translate into existing shell/python/graph tool definitions with no new execution engine (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:14-20`, `feature-requests/FR-768-tool-manifest-declaration-reuse.md:78-107`). It also preserves the graph-runtime manifest choice from the plan, where manifests were preferred over subgraph nodes because reusable investigation steps should travel as tools (`docs/adaptive-probing-plan.md:26-32`).

The first-consumer line is concrete enough to avoid pure growth-by-default: the next investigation pipeline after API discovery, such as company research, codebase audit, or incident investigation, is the first event where this structure would otherwise be re-created (`feature-requests/FR-792-multi-step-investigation-template.md:8-12`, `feature-requests/FR-792-multi-step-investigation-template.md:31-40`). Strategically, however, this is **contrib/example tooling**, not a framework primitive and not yet a CLI feature: the cited use cases are credible, but the first full instance remains planned rather than enforced.

## Required revisions

### R-1: Gate extraction on an enforced source instance

Replace claims that the API-discovery family has "established" or "proven" the template with an explicit dependency gate. FR-792 says the API-discovery family established the pattern over 9 FRs and about 7 days (`feature-requests/FR-792-multi-step-investigation-template.md:27-29`) and that templates encode the contract "proven by FR-783..FR-791" (`feature-requests/FR-792-multi-step-investigation-template.md:91-93`). The cited artifacts do not prove that yet: the parent document is still a plan (`docs/adaptive-probing-plan.md:3-5`), the leaf tools are `Status: Proposed` (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:1-6`), and the orchestrator is also `Status: Proposed` (`feature-requests/FR-791-api-discovery-orchestrator.md:1-6`).

Fold into the FR: enforcement authority for FR-792 activates only after API discovery has a committed, linted, smoke-run source instance that demonstrates the orchestrator -> graph-runtime step manifest -> step graph -> shared leaf tool manifest shape. Cite the exact committed source artifact and validation evidence in FR-792 before implementation. Until that evidence exists, the FR may remain Proposed or explicitly Blocked, but it must not authorize extracting a template from a still-hypothetical pattern.

### R-2: Freeze the command surface as a script, not a CLI subcommand

Resolve the command-surface contradiction mechanically. The ideal result shows `yamlgraph graph scaffold investigation ...` (`feature-requests/FR-792-multi-step-investigation-template.md:54-62`), while the proposed solution says the feature is a `yamlgraph graph scaffold` subcommand or a documented script (`feature-requests/FR-792-multi-step-investigation-template.md:87-90`), and the scope boundaries then declare the CLI `scaffold` subcommand out of scope (`feature-requests/FR-792-multi-step-investigation-template.md:124-126`). AC-01 repeats the ambiguity as "script/command" (`feature-requests/FR-792-multi-step-investigation-template.md:136-139`).

Fold into the FR: the authorized surface is exactly `python scripts/scaffold_investigation.py --name <slug> --steps <csv> --home <path>` or one other exact script path chosen in the FR. `yamlgraph graph scaffold`, CLI parser changes, package entry points, and runtime graph-loader changes are not authorized by this FR. If a CLI command is desired later, file a separate FR after the script has at least one enforced consumer.

### R-3: Close the graph-authoring route gap for generated graph and prompt artifacts

State how the scaffold coexists with the graph-authoring sole route. FR-792 generates `graph.yaml` and step `graph.yaml` files under an `examples/...` home (`feature-requests/FR-792-multi-step-investigation-template.md:63-76`), creates prompt stubs (`feature-requests/FR-792-multi-step-investigation-template.md:107-113`), and targets `examples/` as a stand-alone example location (`feature-requests/FR-792-multi-step-investigation-template.md:129-134`). Repo doctrine says creation or material modification of `graph.yaml` or `prompts/*.yaml` artifacts is graph authoring and must route through `scripts/author.sh`, with the re-entry guard as the only exception (`.github/copilot-instructions.md:15`). FR-792 only says generated graphs still go through `scripts/author.sh` for customization (`feature-requests/FR-792-multi-step-investigation-template.md:153-159`); it does not cover the initial generation event.

Fold into the FR: enforcement tests must generate into a temporary non-governed directory and remove or ignore those artifacts; any committed generated example graph/prompt under governed paths must be produced through the graph-authoring route with its validation record. The scaffold script may be documented as an operator tool, but FR-792 does not create a new bypass route for agents to author governed graph artifacts directly.

### R-4: Make the "runs end-to-end" criterion executable without hidden provider assumptions

Define a real smoke contract. The ideal says each step graph contains a single `type: agent` node with a TODO prompt and empty tool list, while the orchestrator has a terminal `synthesize` LLM node (`feature-requests/FR-792-multi-step-investigation-template.md:79-83`, `feature-requests/FR-792-multi-step-investigation-template.md:97-112`). AC-06 nevertheless requires the generated orchestrator to run end-to-end with stub/placeholder results (`feature-requests/FR-792-multi-step-investigation-template.md:142-143`). As written, that is not mechanically checkable: TODO prompts and LLM/agent nodes imply provider configuration, not deterministic stub output.

Fold into the FR one exact model: either generate a `--stub` skeleton whose step graphs use deterministic non-LLM placeholders suitable for `yamlgraph graph run`, or make AC-06 a committed pytest smoke using the repository's LLM mocking pattern and explicit state assertions. The criterion must name the command or test, generated input variables, and the expected final state shape. Process exit alone is insufficient.

### R-5: Add traceability and generated-artifact tests as first-class deliverables

Add requirement traceability and tests that prove both 3-step and 6-step generation. FR-792's AC-07 asks for 3-step and 6-step skeletons to be valid and lintable (`feature-requests/FR-792-multi-step-investigation-template.md:143-145`), but it does not name committed tests, requirement markers, or capability registry updates. Repo doctrine requires every test to carry `@pytest.mark.req("REQ-YG-XXX")` and requires a capability YAML file when adding a new capability (`.github/copilot-instructions.md:173-176`).

Fold into the FR: add a new capability/requirement entry for the investigation scaffold, tag all new tests with that exact requirement ID, and include tests that generate 3-step and 6-step skeletons in a temporary directory, assert exact file paths, verify graph-runtime manifest path references, verify each step graph's typed output schema, run graph lint on the generated graphs, and prove the README documents tools, edges, and prompts.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-792-multi-step-investigation-template.md` revised to fold R-1 through R-5 before implementation authority activates |
| D-2 | `scripts/scaffold_investigation.py` or one exact script path named by the revised FR |
| D-3 | Template assets needed by that script, limited to orchestrator graph, step graph, step manifest, prompt stub, and README generation |
| D-4 | Unit/artifact tests for 3-step and 6-step generation into a temporary directory, with exact requirement markers |
| D-5 | Capability/requirement registry entry for the scaffold capability |
| D-6 | Direct documentation for the script invocation and generated skeleton contract |
| D-7 | Changelog fragment and diary reflection if required by repository gates |

Not authorized: `yamlgraph graph scaffold` or any CLI parser/entry-point change; YAMLGraph runtime, graph-loader, node-factory, manifest-schema, or graph-tool invocation changes; implementing API-discovery leaf tools, step graphs, browser sniffing, or orchestrator behavior from FR-783..FR-791; adding new external dependencies such as cookiecutter/copier; generating or committing new `examples/**/graph.yaml` or `examples/**/prompts/*.yaml` outside the graph-authoring route; conditional-edge DSLs, tool pre-population, remote template registries, package management, or migration of existing examples.

## Revised acceptance criteria

- [ ] AC-01: FR-792 cites a committed, linted, smoke-run source investigation instance demonstrating the orchestrator -> graph-runtime step manifest -> step graph -> shared leaf tool manifest shape; until that evidence exists, enforcement remains blocked.
- [ ] AC-02: The revised FR names exactly one script invocation surface, and no `yamlgraph graph scaffold` CLI or entry-point change is included.
- [ ] AC-03: The scaffold script generates the full directory structure for a requested home path: orchestrator `graph.yaml`, one `steps/{step}.tool.yaml` per step, one `steps/{step}/graph.yaml` per step, one prompt stub per step, and a generated `tools/README.md`.
- [ ] AC-04: Generated orchestrator graph uses `type: tool_call` nodes that reference graph-runtime step manifests, not subgraph nodes.
- [ ] AC-05: Generated step manifests use `runtime.type: graph` with paths that resolve correctly from the manifest location.
- [ ] AC-06: Generated step graphs contain the authorized placeholder node shape and a typed output schema for each step result.
- [ ] AC-07: Tests generate both 3-step and 6-step skeletons in temporary directories, assert exact file paths, validate manifest path references, and run graph lint on all generated graphs.
- [ ] AC-08: The end-to-end smoke criterion uses the exact stub or mocked-LLM model defined by R-4 and asserts final state shape, not merely process exit.
- [ ] AC-09: Generated README documentation explains how to add shared leaf tool manifests, customize conditional edges, and replace TODO prompts.
- [ ] AC-10: Any committed generated graph or prompt artifact under governed paths is authored through `scripts/author.sh` and has validation evidence; ordinary scaffold tests do not write governed paths.
- [ ] AC-11: A capability/requirement entry exists for the scaffold capability, every new test has the exact requirement marker, and requirement coverage passes for the new mapping.
- [ ] AC-12: No files under YAMLGraph runtime/CLI surfaces change, and no API-discovery implementation work from FR-783..FR-791 is performed under this FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into the FR and the API-discovery source instance evidence required by R-1 exists. | GATE |
| C-2 | Keep this as a script/template feature. Any CLI command, runtime primitive, graph-loader behavior, or manifest schema change must stop and re-enter the pipeline as a separate FR. | GATE |
| C-3 | The scaffold must not become an agent-side bypass of the graph-authoring route; governed graph/prompt artifacts committed under `examples/` require `scripts/author.sh` validation evidence. | GATE |
| C-4 | Generated skeleton validation must be deterministic in CI/local tests and must not require live provider keys unless the FR explicitly supplies a mocked/stubbed execution model. | GATE |
| C-5 | Do not implement or modify API-discovery FR-783..FR-791 deliverables under FR-792; this FR extracts a template after that source exists. | GATE |
| C-6 | All scaffold tests must be traceable through a capability/requirement entry and exact `@pytest.mark.req` markers. | GATE |

Authority granted: after the required revisions are folded in and the source-instance dependency exists, the enforcer may implement the named investigation scaffold script, template assets, deterministic generation/lint/smoke tests, directly related docs, traceability, changelog, and diary within the frozen surfaces above.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
