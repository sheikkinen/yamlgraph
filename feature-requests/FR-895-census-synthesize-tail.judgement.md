# Judgement: FR-895 Census Synthesize Tail — The Stage the Human Reads

**Verdict:** APPROVED WITH REVISIONS — the human-readable census tail is a real, well-precedented gap, but authority activates only after the FR freezes citation-checkable output shape, resolves fail-closed semantics, and specifies the bounded invocation contract for existing corpus-census runs.

**Reviewed against:** feature-requests/FR-895-census-synthesize-tail.md; feature-requests/FR-895.research.md; feature-requests/research-briefs/census-human-readable-tail.md; reference/patterns/corpus-map-reduce.md; feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md; feature-requests/FR-892-corpus-census-pipeline-injected-adapters.judgement.md; feature-requests/FR-893-diary-trap-census.md; feature-requests/FR-893-diary-trap-census.judgement.md; docs/diary/diary-2026-08-27-optional-is-where-value-goes-to-die.md; docs/mercury-census/canary-census-tail.md; examples/demos/fr-atlas/graph.yaml; examples/demos/fr-atlas/README.md; examples/demos/corpus_census/README.md; examples/demos/corpus_census/graph.yaml; .github/skills/judge-fr/doctrine.md; .github/skills/judge-fr/judgement.template.md; .github/copilot-instructions.md.

## What is sound

The problem is real and specifically witnessed. The closed brief records that corpus-census currently emits machine-consumer artifacts, while the operator opened `examples/demos/corpus_census/proofs/pdf-library/ledger.md` and found no human-readable summary (feature-requests/research-briefs/census-human-readable-tail.md:8-23, 50-56). The diary record confirms the lineage defect: the executive-brief output was named in the study artifact, demoted to optional in FR-892, then cut from the authoring brief as scope pressure (docs/diary/diary-2026-08-27-optional-is-where-value-goes-to-die.md:4-10, 14-25).

The proposed direction conforms to the repo's existing pattern. The corpus map-reduce reference already ends in `render`, requiring both a machine-readable dossier and a compact human index linking synthesis claims back to primary results and sources (reference/patterns/corpus-map-reduce.md:184-194). It also states that reduction must not erase primary findings and that readers must be able to move from reduced claims back to source items (reference/patterns/corpus-map-reduce.md:170-182). FR-895's single synthesis call over the aggregated artifact plus LLM-free citation boundary follows that trust split: model authors meaning; code reconciles identity and coverage (feature-requests/FR-895-census-synthesize-tail.md:34-43, 72-83; reference/patterns/corpus-map-reduce.md:141-168).

The research gate is substantively satisfied. FR-895 has a committed research record with five personas, preserved dissents, explicit `is_this_a_graph` answers, and a canary result showing the intended single pinned synthesis stage was rediscovered by two personas while the citation boundary was independently supported (feature-requests/FR-895.research.md:1-18; docs/mercury-census/canary-census-tail.md:5-12). The alternatives are dispositioned rather than ignored: LLM-free rendering and deterministic summary-only output are folded as fallback and summary-head constraints (feature-requests/FR-895-census-synthesize-tail.md:110-118).

Strategic classification: **Contrib/pattern-completion**, not a new framework primitive. The FR has concrete consumers in corpus-census proof configurations and the diary census, and it extends an already-shipped graph/pattern rather than introducing a general summarization framework (feature-requests/FR-895-census-synthesize-tail.md:8-12, 101-108; examples/demos/corpus_census/graph.yaml:1-5, 87-102). It is a single concern: making the census render stage readable by humans while preserving provenance.

## Required revisions

### R-1: Freeze a citation-checkable brief contract

Revise the FR so the LLM output is not arbitrary markdown that a code boundary must semantically interpret. Define a parseable intermediate or constrained markdown shape where each narrative claim is a discrete claim block with required citations, for example `claim_id`, `text`, `citations`, and optional `confidence`. The citation boundary may validate only what code can prove: every cited `[label]` or `[row:item_ref]` exists in the source artifact, every claim block has at least one citation, no citation points outside the reduced/ledger source, and the rendered markdown is generated only after that validation passes. Replace the broad phrase "uncited claims fail" with this mechanical rule, because general prose-claim detection is not LLM-free (feature-requests/FR-895-census-synthesize-tail.md:37-40, 78-80).

### R-2: Resolve the deterministic-summary versus fail-closed contradiction

Clarify the output behavior when narrative validation fails. The proposed solution says the citation boundary prepends a deterministic summary head so the brief "degrades to useful even if the narrative is rejected" (feature-requests/FR-895-census-synthesize-tail.md:81-83), while AC-01 requires "brief rejected without partial output" (feature-requests/FR-895-census-synthesize-tail.md:93). Pick one enforceable contract: either no `brief-<date>.md` is emitted when narrative validation fails and the deterministic summary is emitted to a separate failure artifact, or the committed brief is explicitly a deterministic-only artifact marked `narrative_rejected: true`. The enforcer must not have to infer whether partial output is allowed.

### R-3: Specify activation and required inputs for existing corpus-census runs

Replace "optional-input, mandatory-output tail" with exact invocation semantics. The current `corpus_census` graph requires `source`, `rubric`, and `output_path` and ends at `reduce_ledger` (examples/demos/corpus_census/README.md:7-14; examples/demos/corpus_census/graph.yaml:18-30, 87-102). FR-895 must state the new required variables/files, including brief output path, synthesis prompt or prompt artifact, model/provider pin, input artifact path or state key, and whether every existing proof command is updated to pass them. If a `--brief` wrapper mode is the activation surface, define what it calls and what it refuses when required inputs are absent.

### R-4: Add bounded-input and run-provenance acceptance criteria

Add a hard ceiling for synthesis input size and a deterministic selection or compaction rule before the single model call. The reference cost contract requires hard ceilings for source size, calls, per-partition input size, and timeout, and requires provider/model/run identity to be recorded (reference/patterns/corpus-map-reduce.md:223-246). FR-895 names scales from a 3-row proof ledger to a 1700-label diary aggregation (feature-requests/FR-895-census-synthesize-tail.md:61-66), but does not state what happens when the aggregate exceeds the chosen model context. Freeze the maximum rows/chars/tokens, timeout, model/provider, and metadata fields that must appear in proof artifacts.

### R-5: Make public-safe validation mechanically testable

Strengthen AC-06 so it tests the boundary where raw evidence could leak. FR-895 says committed briefs consume only aggregated public-safe artifacts and never raw evidence spans (feature-requests/FR-895-census-synthesize-tail.md:84-87, 98), while FR-893's public-safe contract intentionally kept raw diary spans out of committed census artifacts (feature-requests/FR-893-diary-trap-census.md:128-134). The revised criterion must assert the synthesis input fixture contains only allowed columns/fields and that the brief renderer has no access to raw span text when producing committed output.

### R-6: Constrain graph and prompt artifact changes to the named surfaces

List the exact graph/prompt surfaces authorized for authoring-route modification. FR-895 correctly says the graph change must use the sole authoring route (feature-requests/FR-895-census-synthesize-tail.md:76-77), and repo doctrine requires that any `graph.yaml` or `prompts/*.yaml` authoring go through `scripts/author.sh` with `tmp/draft-authoring-report.md` evidence (.github/copilot-instructions.md:15). Freeze that this FR may modify only `examples/demos/corpus_census/graph.yaml` and its prompt files for the synthesize tail, plus code-side citation/brief helpers and wrappers. Any generic graph templating, prompt override mechanism, or non-census summary framework remains outside this FR.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/demos/corpus_census/graph.yaml` synthesize/render tail, authored through the graph-authoring route, with lint and smoke evidence recorded in `tmp/draft-authoring-report.md` |
| D-2 | Corpus-census prompt/config artifacts needed for one pinned synthesis call over the reduced or aggregated artifact, not over raw fan-out results |
| D-3 | LLM-free citation boundary that validates structured claim citations against ledger/reduced rows before any human brief is accepted |
| D-4 | Deterministic summary head or deterministic-only fallback with unambiguous fail-closed semantics from R-2 |
| D-5 | Diary census wrapper `--brief` mode or equivalent exact invocation surface that produces `docs/diary/census/brief-<date>.md` |
| D-6 | Regenerated PDF-library and git-timeline proof briefs committed alongside their source ledgers, with model/provider/run provenance |
| D-7 | Deterministic tests for citation validation, public-safe input, fallback/fail behavior, and bounded synthesis input |
| D-8 | Changelog fragment, requirement tagging, FR implementation update, and diary reflection |

Not authorized: summaries for non-census graphs; a general narrative-generation framework; external LedgerMind dependency; any LLM in citation validation, grouping, thresholding, or public-safety checks; raw evidence spans in committed briefs; regeneration of historical briefs beyond the named proof and current diary-census artifacts; graph template inheritance, prompt/schema override machinery, or unrelated corpus-census skeleton rewrites; changes to hooks, CI, judge/review doctrine, or Chaplain runtime behavior without explicit human review.

## Revised acceptance criteria

- [ ] AC-01: RED first — failing tests cover citation-boundary behavior before implementation: fabricated row citation rejected, fabricated label citation rejected, claim block without citation rejected, citation to a row outside the source artifact rejected, and no accepted narrative artifact emitted on validation failure under the R-2 contract.
- [ ] AC-02: The brief output contract is structured enough for LLM-free validation: every narrative claim is represented as a discrete claim with required citations, and markdown rendering occurs only after the citation boundary accepts the structured claims.
- [ ] AC-03: The corpus-census synthesize tail is authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` records graph lint plus a smoke run; the tail performs exactly one pinned synthesis call over the reduced/aggregated artifact and never fans out over raw corpus items.
- [ ] AC-04: Invocation semantics are documented and tested: the required brief variables/files are named, missing brief inputs fail loudly before synthesis, and the PDF-library, git-timeline, and diary wrapper commands all pass the required inputs.
- [ ] AC-05: Synthesis input is bounded before the model call by a deterministic rows/chars/tokens ceiling and selection/compaction rule; provider, model, prompt/config version, source artifact hash, run identity, call count, timeout, and output path are recorded in proof metadata.
- [ ] AC-06: Proof regeneration commits PDF-library and git-timeline briefs alongside their ledgers; the 3-row proof corpus yields a proportionate brief with verified citations and no dangling references.
- [ ] AC-07: Diary census brief generation produces `docs/diary/census/brief-<date>.md`; the top finding is mechanically checked against the known alias-of-doctrine headline by cited label family/row references rather than exact prose.
- [ ] AC-08: Public-safe tests prove committed briefs are generated only from aggregated/public-safe fields and contain no raw evidence-span text.
- [ ] AC-09: The deterministic summary-head or fallback behavior from R-2 is tested for both accepted and rejected narrative cases.
- [ ] AC-10: Changelog fragment, valid REQ/CAP wiring as needed, `@pytest.mark.req(...)` on new tests, FR status/update notes, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-6 are folded into FR-895. | GATE |
| C-2 | No graph or prompt artifact may be created or materially modified except through the graph-authoring route, with `tmp/draft-authoring-report.md` as the evidence artifact. | GATE |
| C-3 | Citation validation, public-safety checks, deterministic summary generation, input bounding, and artifact acceptance are code-owned and LLM-free. | GATE |
| C-4 | The synthesis call may consume only reduced/aggregated public-safe artifacts; it must not consume raw fan-out outputs or raw evidence spans for committed briefs. | GATE |
| C-5 | If implementation requires a generic prompt/schema override system, graph templating, non-census summary framework, or external LedgerMind dependency, enforcement stops and a separate FR enters the pipeline. | GATE |
| C-6 | Existing corpus-census proof and diary commands must be updated or wrapped so the new brief contract is explicit; silent omission of the human-readable output is not allowed for the named consumers. | GATE |
| C-7 | Any changes to hooks, CI, judge/review doctrine, or other enforcement infrastructure require explicit human review before merge. | GATE |

Authority granted: after the required revisions are folded into FR-895, the enforcer may add the corpus-census synthesis tail, citation-checked brief rendering, diary `--brief` flow, and the named proof briefs within the frozen scope above.

**Prior art:** dispositioned in FR-895 header (corpus-map-reduce.md canonical guide; FR-892/893 lineage).
