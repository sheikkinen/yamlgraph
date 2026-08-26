# Feature Request: Corpus-Census Pipeline — Prebaked Skeleton, Injected Adapters

**Priority:** HIGH
**Type:** Feature
**Status:** Completed (enforced 2026-08-26 on worktree feat/fr-892; RED 3cbf9581, GREEN 4c40393a/a895cb16/a67c7729)
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
reference fail-closed ledger; reducer safety lineage per judgement R-5),
FR-891 (boundary-centralization pressure: safety enforcement belongs in
the framework, not per-graph), FR-767 (authoring sole
route — the pipeline is authored ONCE through it; consumers thereafter
supply only manifests, never graphs). Study:
docs/mercury-census/findings.md ("The pattern, fleshed out").

## Summary

One shared `corpus_census` pipeline graph codifying
**discover–extract–map(cheap)–reduce(–tail)**: the skeleton owns model
pinning, `on_error: skip`, abstention, the fail-closed evidence-stamped
reducer, and disagreement preservation; the caller supplies exactly two
FR-768 tool manifests — discovery (enumerate corpus items) and
extraction (fetch one item) — bound at invocation time. The rubric
prompt and reduce schema are ordinary graph inputs consumed through
EXISTING mechanisms (graph variables / files) — no new override
mechanism (R-2). This FR ships the pipeline plus exactly TWO proof
configurations (P0a PDF census, git-PR timeline); migrating the five
existing census graphs is a follow-up chore, not performed here (R-3).

## Value Statement

Census-style analyses stop being blocked by skeleton re-authoring cost:
new corpus = two manifests + one prompt, with safety properties
(pinning, fail-closed reduce, ledger) inherited instead of re-remembered.

## Problem

See the closed brief
([corpus-census-skeleton-reuse.md](research-briefs/corpus-census-skeleton-reuse.md)):
five in-repo instances decompose into identical five-stage pipelines with
zero shared code; 28/33 map graphs lost the model-pinning discipline in
re-authoring; FR-891 witnessed the boundary-centralization pressure
(fluent failure laundering cured at the framework boundary, not
per-graph — R-5 attribution); the mercury-census P0 family is blocked
by marginal re-authoring cost, not capability.

## Proposed Solution

Per the research table (5 classes; 3-persona convergence on the
parametric template; os-infra dissent and Hydra precedent preserved in
FR-892.research.md):

1. **Invocation-time tool binding — the slot contract (R-1, frozen):**
   - Slot declaration: a graph `tools:` entry may declare
     `slot: true` with a required `contract:` block naming the expected
     input args and output shape (discovery: no required input → returns
     a list of item refs; extraction: takes one item ref → returns item
     content string/dict).
   - Binding interface (the ONE authorized surface): CLI
     `yamlgraph graph run … --tool SLOT=path/to/manifest.yaml`,
     repeatable per slot. Manifest path resolves relative to CWD.
   - All FR-768 runtime types (shell/python/graph) are allowed in any
     slot; translation and execution reuse FR-768 exactly — no new
     execution engine.
   - Failure semantics (typed error family, preflight BEFORE any LLM
     call, R-6): missing binding for a declared slot = fatal; duplicate
     binding = fatal; binding an undeclared slot = fatal; invalid
     manifest YAML or runtime type = fatal; contract mismatch = fatal.
2. **The `corpus_census` pipeline graph** — authored once via the sole
   authoring route: discovery node (slot) → extraction inside a
   `type: map` over items (slot; pinned cheap model, `on_error: skip`,
   abstention required in the rubric output schema) → LLM-free reducer
   in the FR-890 lineage → optional tail synthesis node. Rubric prompt
   and reduce schema enter as ordinary graph variables/files (R-2).
3. **Ledger artifact contract (R-4, frozen):** markdown table + JSONL
   sibling; required columns: item ref / judgement / confidence /
   evidence span / model / prompt version / abstention marker+reason /
   disagreement flag. Rejection rules: empty required cell, error-string
   judgement, dropped abstention. Proof run evidence committed under
   `docs/mercury-census/runs/` as .txt.
4. **Two shipped configurations as proof (R-3: exactly these, nothing
   else)**: (a) P0a PDF-library census on a committed bounded fixture
   folder, (b) git-PR timeline census on a bounded history window of
   this repository — each a manifest pair + rubric, zero new graph YAML.
5. **Dissent recorded, not built**: the os-infra Unix-process
   decomposition is the fallback if slot binding proves invasive; Hydra
   is precedent for config-group composition, not a dependency.

## Acceptance Criteria (revised per judgement — supersede the original set)

- [ ] AC-01: RED first — failing test shows manifest-to-slot binding at invocation is rejected today; GREEN accepts `--tool SLOT=manifest.yaml` through existing runtimes.
- [ ] AC-02: Slot YAML schema + typed validation: slot name, allowed runtime type, input/output contract, missing/duplicate/undeclared binding, path resolution.
- [ ] AC-03: Bound manifests reuse FR-768 translation exactly (manifest-relative paths, existing runtimes, no new engine).
- [ ] AC-04: Contaminated bindings fail closed with typed errors BEFORE discovery, extraction, or any LLM call — each case deterministically tested (missing, invalid YAML, wrong runtime, schema mismatch, duplicate, undeclared).
- [ ] AC-05: `corpus_census` authored via scripts/author.sh with lint+smoke in the authoring report; every map-stage LLM node pins a cheap model and uses `on_error: skip`.
- [ ] AC-06: Rubric output schema requires abstention as first-class output; tests prove abstentions become ledger rows.
- [ ] AC-07: Reducer LLM-free and deterministic; tests prove frozen ledger columns, disagreement preservation, empty-cell and error-string rejection.
- [ ] AC-08: P0a PDF-library configuration runs end-to-end on a committed bounded fixture using only manifests + rubric/config; frozen ledger artifact + committed evidence; no second graph authored.
- [ ] AC-09: Git-PR timeline configuration runs on a bounded history window, same conditions as AC-08.
- [ ] AC-10: Hostile shell-runtime binding tested against the shlex-quoted path; no injection.
- [ ] AC-11: Reference docs cover slot schema, binding, path semantics, failure modes, census configuration pattern.
- [ ] AC-12: CAP/REQ wiring, `@pytest.mark.req` on all new tests, req coverage passes, changelog fragment, FR status update, diary reflection.

## Out of Scope

- Migrating the five existing census graphs (follow-up chore; explicitly
  NOT performed under this FR — judgement C-5).
- Hydra or any external configuration framework dependency.
- Graph template inheritance, template codegen, or any generic
  prompt/schema override mechanism — if implementation needs one, STOP
  and file a separate FR (judgement C-6).
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

## Implementation Record (2026-08-26)

Enforced on worktree `feat/fr-892` (FR-888 route). TDD: RED 3cbf9581
(13 slot-binding witnesses, SKIP=pytest), GREEN across three commits.
CAP-249 / REQ-YG-624. All judgement gates C-1..C-7 honored.

**Deliverables (judgement D-1..D-9):**

- D-1/D-2/D-3: `yamlgraph/tools/tool_slots.py` — `slot: true` +
  `contract:` declaration, `parse_tool_bindings` (`--tool SLOT=path`,
  repeatable), `resolve_tool_slots` preflight (five fatal cases, typed
  `ToolSlotBindingError`, before any node executes); FR-768 translation
  reused via new public `translate_manifest` (key-match check skipped
  for explicit bindings — a reusable manifest legitimately has its own
  name). CLI wired in `cli/__init__.py` + `graph_commands.py`;
  `load_graph_config(path, tool_bindings=...)`.
- D-4: `examples/demos/corpus_census/` authored via `scripts/author.sh`
  (C-3); authoring report recorded lint pass + 3-row fixture smoke.
  Authoring discovered and repaired two real constraints: map sub-nodes
  cannot invoke shell tools (python-runtime manifests used for map-stage
  slots) and per-item index needed preserving through the structured
  schema.
- D-5: LLM-free reducer (demo tools.py) with abstention cross-validation;
  9 deterministic witnesses in tests/unit/test_fr892_census_reducer.py
  (frozen columns, abstention-as-row, dropped/duplicate finding
  rejection, error-string and empty-cell rejection, map-error rejection)
  + hostile shell-variable injection witness (AC-10).
- D-6: PDF-library proof (`proofs/pdf-library/`): committed 3-PDF
  bounded fixture (pages split from book-summary's fixture.pdf), pypdf
  extraction adapter, 3-row ledger + run evidence. Real extraction
  verified: German Rotkäppchen text, correctly classified.
- D-7: Git-timeline proof (`proofs/git-timeline/`): bounded 10-commit
  window of this repo, subprocess-git adapter (fixed argv, no shell,
  confessed CONF-422/423), 10-row intent ledger + run evidence.
- D-8: reference/graph-yaml.md "Tool Slots — Invocation-Time Binding"
  section: slot schema, binding semantics table, failure modes,
  committed consumer.
- D-9: CAP-249/REQ-YG-624 wiring, ARCHITECTURE.md regenerated, changelog
  fragment, diary reflection.

**Decisions / deviations:**

- Binding-path resolution bug caught by the demo run itself: paths
  initially resolved against the graph directory; R-1 froze CWD
  resolution — fixed and witnessed (the authoring smoke had silently
  adapted to the bug by using graph-relative paths).
- Slot entries translate at load to inline declarations (not re-entering
  `expand_tool_manifests`) to skip only the name/key-match check; every
  other FR-768 semantic identical.
- Module-map ratchet 291→293 for tools/tool_slots.py (documented
  convention).
- Shell-runtime slots are invocable only from top-level `type: tool`
  nodes (current map execution surface) — documented as a constraint,
  not silently worked around; a follow-up FR may extend map sub-node
  tool support if a consumer needs it (C-6 discipline: not built here).
