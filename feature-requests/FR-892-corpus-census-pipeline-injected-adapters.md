# Feature Request: Corpus-Census Pipeline — Prebaked Skeleton, Injected Adapters

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 3 days
**Requested:** 2026-08-26
**First consumer / first event:** the P0a PDF-library census — its author
binds a discovery manifest (walk a folder) and an extraction manifest
(read page window) to the shared census pipeline and gets a ledgered
census without authoring a graph; second consumer immediately behind it:
the git-PR timeline census.
**Research:** [FR-892.research.md](FR-892.research.md)

**Prior art:** FR-768 (tool manifests — the injection FORMAT exists;
this FR adds invocation-time binding), FR-658/CAP-111 (graph-as-tool —
composition exists but inverts ownership: user authors the outer graph,
which is the re-authoring problem), FR-884 (classifier architecture —
the reference map/reduce), FR-890 (research-route reducer — the
reference fail-closed ledger), FR-891 (proved per-graph reducers lose
safety properties → skeleton must own them), FR-767 (authoring sole
route — the pipeline is authored ONCE through it; consumers thereafter
supply only manifests, never graphs). Study:
docs/mercury-census/findings.md ("The pattern, fleshed out").

## Summary

One shared `corpus_census` pipeline graph codifying
**discover–extract–map(cheap)–reduce(–tail)**: the skeleton owns model
pinning, `on_error: skip`, abstention, the fail-closed evidence-stamped
reducer, and disagreement preservation; the caller supplies exactly two
FR-768 tool manifests — discovery (enumerate corpus items) and
extraction (fetch one item) — plus a rubric prompt and reduce schema, at
invocation time. The five existing census graphs become configurations;
the P0 product family becomes buildable per-corpus in hours.

## Value Statement

Census-style analyses stop being blocked by skeleton re-authoring cost:
new corpus = two manifests + one prompt, with safety properties
(pinning, fail-closed reduce, ledger) inherited instead of re-remembered.

## Problem

See the closed brief
([corpus-census-skeleton-reuse.md](research-briefs/corpus-census-skeleton-reuse.md)):
five in-repo instances decompose into identical five-stage pipelines with
zero shared code; 28/33 map graphs lost the model-pinning discipline in
re-authoring; FR-891 proved reducer safety properties don't survive
per-instance re-implementation; the mercury-census P0 family is blocked
by marginal re-authoring cost, not capability.

## Proposed Solution

Per the research table (5 classes; 3-persona convergence on the
parametric template; os-infra dissent and Hydra precedent preserved in
FR-892.research.md):

1. **Invocation-time tool binding** — extend graph run so tool slots
   declared in the pipeline graph can be bound to FR-768 manifest files
   at invocation (CLI `--tool discover=path/to/manifest.yaml` or
   equivalent config), reusing the existing manifest translation and
   runtimes; untrusted-manifest handling identical to today's load-time
   path (translation-only, shlex-quoted shell, no new execution engine).
2. **The `corpus_census` pipeline graph** — authored once via the sole
   authoring route: discovery node (slot) → extraction inside a
   `type: map` over items (slot; pinned cheap model, `on_error: skip`,
   abstention output required in the rubric schema) → LLM-free reducer
   in the FR-890 lineage (frozen ledger columns: item ref / judgement /
   confidence / evidence span / model+prompt version; disagreement rows;
   error-string and empty-cell rejection) → optional tail synthesis node.
3. **Two shipped configurations as proof**: (a) P0a PDF-library census
   (book-summary's manifest/window tools rebound), (b) git-PR timeline
   census (discovery = `gh pr list`/git log shell manifest; extraction =
   `git show` shell manifest) — each a manifest pair + rubric, zero new
   graph YAML.
4. **Dissent recorded, not built**: the os-infra Unix-process
   decomposition is the fallback if slot binding proves invasive; Hydra
   is precedent for config-group composition, not a dependency.

## Acceptance Criteria

- [ ] AC-01: RED first — failing test: binding a tool manifest to a graph tool slot at invocation is rejected today; GREEN accepts and executes it through existing runtimes.
- [ ] AC-02: The census pipeline graph exists, authored via scripts/author.sh with lint + smoke evidence; all map-stage LLM nodes pin a cheap model explicitly.
- [ ] AC-03: The reducer is LLM-free and fail-closed: ledger columns frozen, abstention as first-class output, disagreement preserved as rows, error strings rejected — witnessed by deterministic tests.
- [ ] AC-04: PDF-library census configuration runs end-to-end on a fixture folder producing a valid ledger artifact; committed demo evidence.
- [ ] AC-05: Git-PR timeline census configuration runs on this repository's own history window producing a valid ledger artifact; committed evidence.
- [ ] AC-06: A contaminated binding (manifest missing, wrong runtime type, tool name not a declared slot) fails closed with a typed error before any LLM tokens are spent.
- [ ] AC-07: Security witness: a shell-runtime manifest with a hostile variable value executes shlex-quoted; test proves no injection.
- [ ] AC-08: Changelog fragment, CAP/REQ wiring, FR status update, diary reflection.

## Out of Scope

- Migrating the five existing census graphs (follow-up chore once the
  pipeline proves out).
- Hydra or any external configuration framework dependency.
- Graph template inheritance as a general mechanism (only tool-slot
  binding is authorized here).
- The remaining P-series verticals (they consume this; they are not it).

## Alternatives Considered

See [FR-892.research.md](FR-892.research.md): Unix process pipeline
(os-infra dissent — fallback), graph-template inheritance (heavier
framework surface), graph generation from templates (secondary canary;
codegen drift risk), Hydra-style config composition (external precedent,
not a dependency), status quo copy-the-graph (the witnessed defect).

## Related

- docs/mercury-census/findings.md (study; "The pattern, fleshed out")
- FR-768, FR-658/CAP-111, FR-884, FR-890, FR-891
- Scripture: `constraint_over_code`, `normalize at the boundary`,
  `is_this_a_graph`, cheap-map/code-reduce diary 2026-08-26
