# Judgement: FR-768 Tool Manifests: Declaration Reuse Over Existing Runtimes

**Prior art:** FR-768-tool-manifest-declaration-reuse.md is the FR under judgement (self-hit). FR-658 (graph-as-tool, Enforced), CAP-111/FR-255 (`shared:` graphs), and FR-044 (contrib libraries; contrib.io deferred, slugify rejected) are dispositioned in the FR's Prior Art section and re-examined below — none covers cross-file tool declaration reuse.

**Verdict:** APPROVED WITH REVISIONS - the reuse problem is real and the translation-only design is aligned, but authority activates only after the manifest schema, per-runtime coverage, traceability, and human-review gates are folded into the FR.

**Reviewed against:** `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/tmp/yamlgraph-manifest-resolution-proposal.md`; `docs/tmp/yamlgraph-capability-model.md`; `docs/tmp/yamlgraph-graph-as-tool-mvp.md`; `feature-requests/FR-658-graph-as-tool.md`; `feature-requests/FR-255-extract-shared-invoke-graph.md`; `capabilities/CAP-111-shared-graph-invocation.yaml`; `feature-requests/044-shared-contrib-libraries.md`; `feature-requests/044b-contrib-migration.md`; `feature-requests/044d-plan-barebones-skipreport.md`; `reference/graph-yaml.md`; `examples/demos/planner/graph.yaml`; `examples/demos/enforcer/graph.yaml`; `examples/demos/judge/graph.yaml`.

## What is sound

The FR names a concrete first consumer and first event: the chaplain planner/enforcer/judge trio and the next edit to their shared repo toolkit (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:8-12`). The duplication evidence is specific enough to justify a framework primitive rather than pattern documentation: 333 declarations, 26 duplicated signatures, and a production chaplain trio with copied repo-tool declarations (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:30-46`). The cited graph files confirm the same shape exists in those consumers: `planner` declares shell and Python tools inline (`examples/demos/planner/graph.yaml:11-40`), `enforcer` repeats and extends that set (`examples/demos/enforcer/graph.yaml:11-70`), and `judge` repeats the core read/search/list/git/test toolkit (`examples/demos/judge/graph.yaml:11-39`).

The solution is minimal in the right direction: a manifest is declaration reuse and translation into existing shell/python/graph tool definitions, not a new execution engine (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:16-20`, `feature-requests/FR-768-tool-manifest-declaration-reuse.md:78-80`). That matches the design note's resolution flow: resolve manifest, inspect runtime type, translate to existing shell or Python definition, invoke existing runtime (`docs/tmp/yamlgraph-manifest-resolution-proposal.md:43-60`). It also distinguishes itself from the larger capability-model proposal, which adds registry/resolver/invoker tiers (`docs/tmp/yamlgraph-capability-model.md:100-123`, `docs/tmp/yamlgraph-capability-model.md:173-187`), and from FR-658, which already solved graph execution as a tool rather than declaration reuse (`feature-requests/FR-658-graph-as-tool.md:11-16`, `feature-requests/FR-658-graph-as-tool.md:61-80`).

Strategic classification: **Framework primitive**. There are 3+ cited use cases across novel_fandom, the chaplain trio, and shared example tooling (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:36-46`), and existing abstractions do not cover cross-file tool declaration reuse. YAML anchors do not cross files and a generic include mechanism would be broader than this problem (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:101-107`).

## Required revisions

### R-1: Define the manifest schema and translation contract

Add a concrete manifest schema section to the FR before enforcement. It must enumerate required and optional fields for `runtime.type: shell`, `runtime.type: python`, and `runtime.type: graph`; specify whether top-level `name` must match the graph-local tool key; specify where `description`, `parse`, `command`, `path`, `module`, `function`, `input_mapping`, and `output_key` live; and require unknown or conflicting fields to fail graph load. This is necessary because the FR currently shows only one Python example (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:58-68`) while promising translation for shell/python/graph (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:78-80`), and the existing public docs show different field sets for shell and Python tools (`reference/graph-yaml.md:1312-1359`).

### R-2: Require typed manifest validation at the load boundary

State that manifest YAML is parsed into typed validation models before translation, and that invalid manifest shape, missing files, invalid runtime type, unresolved paths, missing function/command fields, and unsupported graph-tool fields fail during graph load. This follows the repo boundary rule to normalize external data where it enters (`.github/copilot-instructions.md:49-52`) and the FR's own load-time failure requirement (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:92-94`).

### R-3: Make per-runtime acceptance tests explicit

Replace the single "inline vs manifest identical outputs" test with separate mechanically checkable tests for shell, Python-by-path, Python-by-module if supported by manifests, and graph tools. The FR promises existing shell/python/graph translation (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:78-80`), while prior graph-tool behavior includes compile-time registration and invocation-time execution details that a shell/Python-only test would not cover (`feature-requests/FR-658-graph-as-tool.md:61-80`). The tests must prove both behavior equivalence and path-resolution semantics for graph-relative manifest references and manifest-relative runtime paths (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:84-91`).

### R-4: Add traceability as a deliverable, not only a test annotation

Add a capability/requirement update to the FR's deliverables: create or update a `capabilities/CAP-XXX-*.yaml` entry with a new `REQ-YG-XXX` for manifest-declared tools, and tag tests to that requirement. The current AC requires `@pytest.mark.req` tests (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:96-97`), but repo doctrine requires a capability file when adding a new capability (`.github/copilot-instructions.md:173-176`), and CAP-111 shows the expected capability-to-FR-to-requirement shape (`capabilities/CAP-111-shared-graph-invocation.yaml:1-18`).

### R-5: Gate chaplain graph migration through graph-authoring and human review

Add an enforcement condition that any material edits to `examples/demos/planner/graph.yaml`, `examples/demos/enforcer/graph.yaml`, or `examples/demos/judge/graph.yaml` must follow the graph-authoring route and produce its validation record. Repo doctrine says graph artifacts are governed by the graph-authoring workflow (`.github/copilot-instructions.md:15-16`), and judge doctrine requires human review as a gate for enforcement-infrastructure changes (`.github/skills/judge-fr/doctrine.md:96-103`). The FR itself classifies the chaplain trio as production agents, not merely pedagogical demos (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:40-42`), so this is a hard gate, not an optional caution.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Graph tool parser/model layer that accepts `tools.<name>.manifest` and loads the referenced manifest at graph load |
| D-2 | Manifest path resolution relative to the referencing graph; runtime paths inside a manifest resolved relative to the manifest file |
| D-3 | Translation from manifest runtime declarations into existing shell, Python, and graph tool configs without adding an execution engine |
| D-4 | Load-time validation errors for missing/invalid manifests and invalid runtime bindings |
| D-5 | Unit tests with requirement markers proving per-runtime equivalence, path resolution, and load-time failures |
| D-6 | Documentation in `reference/graph-yaml.md` for manifest syntax, schema, path semantics, and failure mode |
| D-7 | Capability/requirement registry update and changelog fragment |
| D-8 | Chaplain planner/enforcer/judge migration to a shared manifest set, performed only under graph-authoring and human-review gates |

Not authorized: capability registries, generic YAML include/import mechanisms, remote registries, package management, plugin marketplaces, a new tool invoker/execution engine, runtime-neutral `type: tool` redesign, graph interface changes, graph-tool invocation semantics changes, MCP/A2A changes, or unrelated contrib/library extraction. The capability-model registry/resolver/invoker stack remains out of scope (`docs/tmp/yamlgraph-capability-model.md:100-123`, `docs/tmp/yamlgraph-capability-model.md:173-187`), and the graph-as-tool interface/import ideas remain out of scope because FR-658 already covers invocation (`docs/tmp/yamlgraph-graph-as-tool-mvp.md:101-121`, `feature-requests/FR-658-graph-as-tool.md:171-177`).

## Revised acceptance criteria

- [ ] AC-01: `tools.<name>.manifest` is accepted in graph YAML and resolved relative to the referencing graph.
- [ ] AC-02: Paths inside a manifest are resolved relative to the manifest file, with tests proving sibling and nested manifest locations.
- [ ] AC-03: Manifest YAML is validated through typed models at graph load; missing manifest, invalid YAML, unknown runtime type, missing required runtime fields, unsupported field combinations, and unresolved paths fail before invocation.
- [ ] AC-04: A shell manifest translates to the same effective tool config and runtime output as the equivalent inline shell declaration, including `command`, `description`, and `parse`.
- [ ] AC-05: A Python `path` manifest translates to the same effective tool config and runtime output as the equivalent inline Python `path` declaration, including manifest-relative path resolution.
- [ ] AC-06: If Python `module` manifests are supported, a Python `module` manifest translates to the same effective tool config and runtime output as the equivalent inline Python `module` declaration; if not supported, the FR must explicitly exclude it.
- [ ] AC-07: A graph manifest translates to the same effective tool config and runtime output as the equivalent inline `type: graph` declaration without changing FR-658 invocation behavior.
- [ ] AC-08: Existing inline shell, Python, graph, and other tool declarations continue to load and run unchanged.
- [ ] AC-09: The chaplain planner/enforcer/judge graphs consume one shared manifest set for their duplicated repo toolkit, and their graph lint/smoke evidence is recorded by the graph-authoring validation artifact.
- [ ] AC-10: `reference/graph-yaml.md` documents manifest syntax, schema, path semantics, examples for each supported runtime, and load-time error behavior.
- [ ] AC-11: A capability/requirement entry is created or updated for manifest-declared tools, all new tests are tagged with the new `REQ-YG-XXX`, and requirement coverage passes for the new mapping.
- [ ] AC-12: A changelog fragment is added.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No new execution engine, registry/resolver/invoker tier, remote registry, package manager, or generic include/import system may be introduced under this FR. | GATE |
| C-2 | Manifest parsing must fail closed at graph load; invalid or missing manifest data must not be silently ignored or deferred to first invocation. | GATE |
| C-3 | Per-runtime tests must cover every runtime the schema claims to support: shell, Python path, Python module if included, and graph. | GATE |
| C-4 | Material edits to `examples/demos/planner/graph.yaml`, `examples/demos/enforcer/graph.yaml`, or `examples/demos/judge/graph.yaml` require graph-authoring validation evidence before enforcement is complete. | GATE |
| C-5 | Because the chaplain trio participates in planning/enforcement/judgement workflows, the migrated graph/tool-manifest diff requires human review before merge. | GATE |
| C-6 | The implementation must not change FR-658 graph-tool invocation semantics; manifest support is declaration reuse only. | GATE |

Authority granted: after R-1 through R-5 are folded into the FR, the enforcer may implement manifest-backed tool declarations as a translation layer over existing tool runtimes and migrate only the cited chaplain trio shared toolkit within the gates above.
