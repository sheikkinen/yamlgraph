# Judgement: FR-892 Corpus-Census Pipeline — Prebaked Skeleton, Injected Adapters

**Prior art:** dispositioned in FR-892 header (FR-768/658/884/890 positive precedent; migration and template-inheritance explicitly not authorized).

**Verdict:** APPROVED WITH REVISIONS — the shared census skeleton is a justified framework primitive, but authority activates only after the FR defines the invocation-time slot contract and removes the ambiguity between configuration, rubric/schema injection, and future migration.

**Reviewed against:** feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md; feature-requests/FR-892.research.md; feature-requests/research-briefs/corpus-census-skeleton-reuse.md; docs/mercury-census/findings.md; feature-requests/FR-768-tool-manifest-declaration-reuse.md; feature-requests/FR-658-graph-as-tool.md; capabilities/CAP-111-shared-graph-invocation.yaml; feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md; feature-requests/FR-890-research-sole-route-closed-input-alternatives.md; feature-requests/FR-891-fail-closed-agent-tool-boundary.md; .github/skills/judge-fr/doctrine.md; .github/skills/judge-fr/judgement.template.md; repo doctrine in project instructions.

## What is sound

The problem is real and evidenced: the closed brief states that at least five graphs share the same enumerate/fetch/map/reduce/tail shape while only enumeration and retrieval differ, and that 28 of 33 map graphs inherit an expensive default because pinning is not preserved during re-authoring (feature-requests/research-briefs/corpus-census-skeleton-reuse.md:8-27, 55-71). The mercury study independently names the same cheap-map/code-reduce pattern and records the model-pinning defect (docs/mercury-census/findings.md:10-18, 39-47).

The proposal aligns with existing architecture rather than inventing a second execution engine. FR-768 already provides typed manifest translation into existing shell/python/graph runtimes with load-time validation and no new runtime (feature-requests/FR-768-tool-manifest-declaration-reuse.md:14-20, 78-107). FR-658 and CAP-111 establish graph composition and shared graph invocation (feature-requests/FR-658-graph-as-tool.md:11-16, 20-30; capabilities/CAP-111-shared-graph-invocation.yaml:1-13). Extending binding from graph-load declaration reuse to invocation-time slot filling is a coherent next primitive.

The strategic classification is **Framework primitive**: the FR names more than three concrete consumers or instances, including five existing census graphs, the P0 PDF-library census, and the git-PR timeline census (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:8-12, 43-51, 72-76). The P0 study also identifies PDF-library and git-history/time-axis corpora as same-architecture consumers (docs/mercury-census/findings.md:214-253).

The research record satisfies the local research gate in substance: it contains five personas, a dispositioned alternatives table, preserved os-infra dissent, Hydra as external precedent, and explicit `is_this_a_graph` answers (feature-requests/FR-892.research.md:1-18). The selected direction is not merely author preference; three rows converge on a parameterized skeleton or invocation-time tool-slot binding while the process-boundary alternative is retained as dissent (feature-requests/FR-892.research.md:13-16).

## Required revisions

### R-1: Define the invocation-time tool-slot contract

Add a concrete syntax section to the FR for graph-declared tool slots and invocation binding. It must specify: the graph YAML field that declares a slot; allowed runtime types per slot or that all FR-768 runtimes are allowed; required input/output schema checks for discovery and extraction; whether a missing binding is fatal; whether duplicate bindings are fatal; path resolution for `--tool SLOT=manifest.yaml`; and the typed error class or error message family for failed preflight. Replace "`--tool discover=path/to/manifest.yaml` or equivalent config" with one authorized interface, or name the exact config surface if both are in scope.

### R-2: Constrain rubric prompt and reduce-schema injection to existing surfaces

The summary says callers supply "a rubric prompt and reduce schema" at invocation time (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:28-35), while the out-of-scope section says only tool-slot binding is authorized and general graph template inheritance is not (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:92-99). Revise the FR to state that rubric and schema are ordinary graph variables or files consumed by the `corpus_census` graph through existing mechanisms. If they require a new generic prompt/schema override mechanism, split that mechanism into a separate FR.

### R-3: Resolve the migration/configuration contradiction

Line 34 says "The five existing census graphs become configurations," but lines 94-95 say migrating those graphs is out of scope. Revise the summary and scope so this FR authorizes exactly two proof configurations only: P0a PDF-library census and git-PR timeline census. Migration of the five existing graphs remains a follow-up chore and must not be performed under this FR.

### R-4: Freeze the ledger and demo artifact contract

Replace "valid ledger artifact" with a concrete artifact shape: file format, required columns, rejection rules, and where committed proof logs/artifacts live. The minimum ledger columns must include item reference, judgement, confidence, evidence span, model, prompt version, abstention marker or reason, and disagreement rows, matching the FR-890 fail-closed reducer lineage (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:65-71; feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:106-116).

### R-5: Correct the FR-891 prior-art claim

Do not claim FR-891 proves "per-graph reducers lose safety properties" unless the FR cites reducer-specific evidence. FR-891 proves the broader boundary failure class: an agent node can launder total tool failure into fluent output unless the framework consumes failure flags and fails closed (feature-requests/FR-891-fail-closed-agent-tool-boundary.md:26-37, 47-63). Attribute reducer safety directly to FR-890 and boundary centralization pressure to FR-891.

### R-6: Add a no-token preflight witness

Strengthen AC-06 so contaminated bindings are validated before discovery, extraction, or any LLM node runs. The tests must assert no LLM prompt execution is invoked when a manifest is missing, has the wrong runtime type, fails schema compatibility, or names an undeclared slot.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Invocation-time binding for declared graph tool slots via `yamlgraph graph run --tool SLOT=manifest.yaml` |
| D-2 | Graph YAML slot declaration schema and typed validation for bound FR-768 manifests |
| D-3 | Reuse of FR-768 manifest translation and existing shell/python/graph runtimes; no new execution engine |
| D-4 | One shared `corpus_census` graph artifact, authored through `scripts/author.sh`, with lint/smoke evidence recorded in `tmp/draft-authoring-report.md` |
| D-5 | LLM-free corpus-census reducer with deterministic tests for frozen ledger columns, abstention, disagreement preservation, empty-cell rejection, and error-string rejection |
| D-6 | P0a PDF-library census proof configuration: manifest pair, rubric, bounded fixture corpus, committed run evidence, and ledger artifact |
| D-7 | Git-PR timeline census proof configuration: manifest pair, rubric, bounded repository-history window, committed run evidence, and ledger artifact |
| D-8 | Reference documentation for invocation-time tool binding and census configuration |
| D-9 | Capability/requirement wiring, changelog fragment, FR implementation-status update, and diary reflection |

Not authorized: migrating the five existing census graphs; Hydra or any external configuration framework; general graph template inheritance; graph generation/codegen from templates; new LLM provider/runtime machinery; new reducer behavior outside the corpus-census pipeline; remaining P-series verticals; enforcement-infrastructure edits except ordinary CAP/REQ/test/changelog wiring. If implementation discovers that rubric/schema injection needs a new generic configuration override primitive, stop and file a separate FR.

## Revised acceptance criteria

- [ ] AC-01: RED first — a failing test demonstrates that binding an FR-768 manifest to a declared graph tool slot at invocation is rejected today; GREEN accepts `--tool SLOT=manifest.yaml` and executes through existing runtimes.
- [ ] AC-02: Graph tool slots have a documented YAML schema and typed validation covering declared slot name, allowed runtime type, required input/output contract, missing binding, duplicate binding, undeclared binding, and manifest path resolution.
- [ ] AC-03: Bound manifests reuse FR-768 translation exactly: manifest internals resolve relative to the manifest file, runtime execution uses the existing shell/python/graph tool runtimes, and no new execution engine is introduced.
- [ ] AC-04: Contaminated bindings fail closed with typed errors before discovery, extraction, or any LLM prompt execution: missing manifest, invalid manifest YAML, wrong runtime type, schema mismatch, duplicate slot, and undeclared slot are each covered by deterministic tests.
- [ ] AC-05: The shared `corpus_census` graph exists and is authored through `scripts/author.sh`; the resulting `tmp/draft-authoring-report.md` records graph lint and smoke evidence, and every map-stage LLM node explicitly pins a cheap model and uses `on_error: skip`.
- [ ] AC-06: The corpus-census rubric output schema requires abstention as a first-class output, and tests prove abstentions become ledger rows rather than dropped or synthesized decisions.
- [ ] AC-07: The reducer is LLM-free and deterministic; tests prove required ledger columns, disagreement preservation, empty-cell rejection, and error-string rejection.
- [ ] AC-08: The P0a PDF-library configuration runs end-to-end on a committed bounded fixture folder using only a discovery manifest, extraction manifest, and rubric/config inputs; it produces the frozen ledger artifact and committed run evidence without authoring a second graph.
- [ ] AC-09: The git-PR timeline configuration runs end-to-end on a bounded repository-history window using only a discovery manifest, extraction manifest, and rubric/config inputs; it produces the frozen ledger artifact and committed run evidence without authoring a second graph.
- [ ] AC-10: A shell-runtime binding with hostile variable content is tested against the existing shlex-quoted shell path and proves no command injection.
- [ ] AC-11: `reference/graph-yaml.md` or the appropriate reference page documents invocation-time tool binding, slot schema, path semantics, failure modes, and the census configuration pattern.
- [ ] AC-12: Capability/requirement metadata is added or updated; all new tests carry `@pytest.mark.req(...)`; requirement coverage passes; a changelog fragment, FR status update, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-6 are folded into the FR. | GATE |
| C-2 | The only new framework primitive authorized is invocation-time binding of declared tool slots to FR-768 manifests. | GATE |
| C-3 | All graph or prompt artifacts created or materially modified for `corpus_census` and its proofs must go through the graph-authoring route and be supported by the authoring report artifact, not by exit code alone. | GATE |
| C-4 | Bound manifests are untrusted input: validate and translate them before execution, and fail before any LLM call on invalid bindings. | GATE |
| C-5 | No migration of existing census graphs is allowed under this FR; only the two named proof configurations may be shipped. | GATE |
| C-6 | If implementation requires general graph template inheritance, Hydra, template code generation, or a generic prompt/schema override mechanism, enforcement must stop and a separate FR must enter the pipeline. | GATE |
| C-7 | Any changes to hooks, CI, judge/review doctrine, or other enforcement infrastructure require explicit human review before merge. | GATE |

Authority granted: after the required revisions are folded into FR-892, the enforcer may implement invocation-time tool-slot binding and one shared `corpus_census` graph with the two named proof configurations, within the frozen scope above.
