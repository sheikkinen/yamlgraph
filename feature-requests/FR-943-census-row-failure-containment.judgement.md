# Judgement: FR-943 Corpus Census — Row-Level Failure Containment at the Reduce Boundary

**Prior art:** FR-892 (fail-closed reducer — amended for the model-owned class), FR-940 (label boundary — summary line superseded), FR-936 judgement D-4 (native retry — composes, no overlap), FR-027/FR-069 (origin of the `_error`/`_map_index` finding taxonomy); full dispositions in the body and in `FR-943.research.md`.

**Verdict:** APPROVED WITH REVISIONS — the demo-scoped containment boundary is sound, but authority activates only after R-1–R-6 correct provenance, traceability, index selection, validation-error classification, return-shape wording, and the module-size delivery surface.

**Reviewed against:** `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/FR-943.research.md`; `tests/fixtures/fr943_incident_map_errors.json`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `feature-requests/FR-940-census-judgement-normalization.md`; `feature-requests/FR-940-census-judgement-normalization.judgement.md`; `examples/demos/corpus_census/tools.py`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/corpus_census/prompts/judge_item.yaml`; `examples/demos/corpus_census/README.md`; `examples/demos/corpus_census/demo-output.log`; `tests/unit/test_fr892_census_reducer.py`; `tests/unit/test_fr940_census_judgement_normalization.py`; `capabilities/CAP-249-tool-slot-binding.yaml`; `capabilities/CAP-250-census-synthesize-tail.yaml`; `ARCHITECTURE.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect is real and economically material. The committed incident record contains four separate 200-item batch failures, each attributable through `_map_index` to one malformed model envelope after the fan-out had completed (`feature-requests/FR-943.research.md:6-27`; `tests/fixtures/fr943_incident_map_errors.json:1-43`). The record also satisfies the repo's raw-output discipline: it preserves the partial abstention envelope and three distinct item-content fragments echoed into judgement output, rather than reporting only an aggregate failure count (`.github/copilot-instructions.md:116-118`).

The proposed correction sits at the existing durable boundary. `_rows_by_index` already owns index attribution, model-label normalization, `LedgerRow` construction, and batch completeness checks; today it aborts on map errors, error strings, and row validation errors (`examples/demos/corpus_census/tools.py:220-268`). Containing only attributable model-owned failures there follows the repo rule to reconcile model claims in deterministic code and preserves the FR-892 fail-closed behavior for structural states (`feature-requests/FR-943-census-row-failure-containment.md:46-55,74-125`; `.github/copilot-instructions.md:117-118`).

The research is substantive: it compares six genuine solution classes, rejects schema relaxation and prompt-only repair for stated reasons, preserves framework-level containment as the future answer after a second consumer, and explains why native retry composes rather than substitutes (`feature-requests/FR-943.research.md:31-97`). The scope has one responsibility and one current consumer. Its strategic classification is **Contrib/example**, not a framework primitive: the change is confined to the corpus-census reducer and explicitly excludes graph, prompt, map compiler, retry, and core changes (`feature-requests/FR-943-census-row-failure-containment.md:153-175,234-242`).

| Criterion | Finding |
|---|---|
| Scope | The model-owned-versus-structural split is the smallest complete correction for the stated spend-loss objective; framework policy and retry are explicitly excluded (`feature-requests/FR-943-census-row-failure-containment.md:57-69,153-175`). |
| Consistency | The failure-row contract is internally coherent, but the status cites an absent judgement, non-error index precedence is not frozen, model-level Pydantic locations have no exact rendered name, and D-3 misstates the outer return shape. Fold R-1, R-3, R-4, and R-5 (`feature-requests/FR-943-census-row-failure-containment.md:5-6,78-82,94-102,144-150`; `examples/demos/corpus_census/tools.py:231-235,311-315`). |
| Measurability | The fixture replay, exact row cells, exact counts, exact summary text, and structural raises are directly assertable. The index and location ambiguities prevent complete tests until R-3 and R-4 are folded (`feature-requests/FR-943-census-row-failure-containment.md:177-232`). |
| Feasibility | Pydantic `ValidationError`, the row-construction seam, and deterministic artifact writers already exist. The implementation is feasible, but `tools.py` is already 424 lines against the 450-line maximum, so the exact one-file production surface is not feasible without a focused split (`examples/demos/corpus_census/tools.py:17-26,148-214,220-315`; `CLAUDE.md:331-336`). Fold R-6. |
| Architecture alignment | Deterministic normalization at the demo reduce boundary conforms to the existing census architecture; no graph or prompt change is needed (`examples/demos/corpus_census/graph.yaml:88-109`; `examples/demos/corpus_census/prompts/judge_item.yaml:20-46`). |
| Single responsibility | Map errors, error-string findings, and model-owned row-validation failures are three representations of one concern: an attributable per-item model failure crossing the reducer boundary. No split is required (`feature-requests/FR-943-census-row-failure-containment.md:84-125`). |
| Strategic classification | **Contrib/example**: one named demo consumer, existing reducer abstraction, no reusable framework surface (`feature-requests/FR-943.research.md:31-56,81-97`). |
| Testability | RED tests can be written directly at `_rows_by_index`/`reduce_ledger`, and the four incidents are replayable without a live model. Traceability currently contradicts the new behavior because REQ-YG-624 still requires error-string rejection. Fold R-2 (`tests/unit/test_fr892_census_reducer.py:73-128`; `capabilities/CAP-249-tool-slot-binding.yaml:21-29`). |

## Required revisions

### R-1: Correct the judgement provenance claim

Replace the two-line status at `feature-requests/FR-943-census-row-failure-containment.md:5-6` with exactly `**Status:** PROPOSED — rev 2`. Remove the claims that rev 1 was rejected, that R-1–R-6 were folded, and that `FR-943-census-row-failure-containment.judgement.md` records that decision: no such committed judgement exists in the reviewed tree or its history. The present draft must not manufacture authority for an unavailable prior artifact.

### R-2: Reconcile the superseded REQ-YG-624 contract

Add `capabilities/CAP-249-tool-slot-binding.yaml` to the delivery surface. Add FR-943 to its `fr:` field and amend REQ-YG-624 so it no longer promises error-string rejection. Freeze its census clause as: `the corpus-census reducer preserves abstention rows and rejects structural index/completeness failures and invalid ledger cells`. Keep the surviving FR-892 structural and invalid-cell witnesses tagged REQ-YG-624.

Add FR-943 and REQ-YG-634 to CAP-250 as proposed, with REQ-YG-634 owning attributable model-failure row containment, exact failed-row cells, full `raw_judgement` evidence, the four-key count, and the revised normalization summary. Tag containment and superseded error-string/map-error witnesses REQ-YG-634. Regenerate `ARCHITECTURE.md` from both capability edits.

### R-3: Freeze non-error index selection

In D-1 and AC-06, specify the existing non-error selection algorithm exactly: read `source_index`; only when its value is `None`, fall back to `_map_index`; then require `type(selected_index) is int`, range validity, and uniqueness. A present but boolean, non-integer, out-of-range, or duplicate `source_index` is structural and MUST NOT fall through to a valid `_map_index`. When both are present, `source_index` is selected and `_map_index` is not a second attribution input. Add direct tests for fallback, boolean rejection, invalid-present-source rejection despite a valid `_map_index`, and the both-present case. `_error` findings continue to use `_map_index` only.

### R-4: Make ValidationError classification closed and root rendering exact

Replace the open-ended "location root" language with this complete rule: a `ValidationError` is containable iff every `exc.errors()` entry has either `loc == ()` or a non-empty `loc` whose first component is one of `judgement`, `confidence`, `evidence_span`, `abstained`, or `abstain_reason`. `loc == ()` is the model-level abstention validator and is model-owned. Every other location, including an unknown root or any mixture with a non-model-owned location, is batch-fatal.

Define the first-error location text as `".".join(str(part) for part in loc) or "<model>"`, then format the reason exactly `<location>: <msg> [<type>]`. Add direct witnesses for a field location, the empty model location, mixed model/reducer locations, and an unknown location defaulting to fatal.

### R-5: State the public result shape accurately

Replace D-3's result-shape sentence with: `reduce_ledger returns exactly {"ledger": ledger_result}; ledger_result keeps exactly markdown_path, jsonl_path, rows`. Amend AC-09 to assert both the one-key outer shape and the three-key nested shape. `counts` remains internal and MUST NOT appear at either public level (`examples/demos/corpus_census/tools.py:303-315`).

### R-6: Add a focused helper surface to obey the module limit

Add `examples/demos/corpus_census/ledger_failures.py` to the authorized delivery surface. It may contain only the FR-943 failure taxonomy, closed ValidationError-location classification, reason formatting/truncation, and deterministic raw-finding serialization/value assembly. `LedgerRow`, reducer orchestration, index selection, and artifact writing remain in `tools.py`. Add focused unit coverage through `test_fr943_census_row_failure_containment.py`, and keep `tools.py` at or below the 450-line hard maximum (`CLAUDE.md:333-334`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/demos/corpus_census/tools.py` — reducer orchestration, exact index selection, failed-row construction, four-key counts, and revised summary |
| D-2 | `examples/demos/corpus_census/ledger_failures.py` — FR-943-only classification, reason, truncation, and raw-evidence helpers |
| D-3 | `tests/unit/test_fr943_census_row_failure_containment.py` — new RED/GREEN containment and structural-boundary witnesses |
| D-4 | `tests/unit/test_fr892_census_reducer.py` and `tests/unit/test_fr940_census_judgement_normalization.py` — superseded witnesses and exact summary amendment only |
| D-5 | `examples/demos/corpus_census/README.md` and regenerated `examples/demos/corpus_census/demo-output.log` |
| D-6 | `capabilities/CAP-249-tool-slot-binding.yaml`, `capabilities/CAP-250-census-synthesize-tail.yaml`, and regenerated `ARCHITECTURE.md` |
| D-7 | Existing `tests/fixtures/fr943_incident_map_errors.json` replay evidence |
| D-8 | FR implementation record, `fix` changelog fragment for REQ-YG-634, and diary reflection |

Not authorized: edits to `examples/demos/corpus_census/graph.yaml`, any prompt or `CorpusCensusFinding` schema, YAMLGraph core, `map_compiler`, map error-envelope production, retry policy, synthesis/citation behavior, hooks, CI, judge/review doctrine, shared failure APIs, or any public result/JSONL schema expansion. No live paid run is required.

## Revised acceptance criteria

- [ ] AC-01: The FR status carries no unavailable prior-judgement claim; committed `FR-943.research.md` retains six substantive solution classes, dispositioned precedent, preserved disagreement, effort/risk, `is_this_a_graph`, and the four-record incident citation.
- [ ] AC-02: RED is committed first: a valid `_error` finding with an exact-int, in-range, unseen `_map_index` and valid peers aborts under the current reducer; GREEN emits one failed row without changing peer rows.
- [ ] AC-03: A judgement containing a case-sensitive `ERROR_STRINGS` substring emits one failed row and preserves the original judgement string exactly in `raw_judgement`.
- [ ] AC-04: A `ValidationError` is contained iff every error location is `()` or rooted in the frozen model-owned field set; tests cover field-root, model-root, mixed-root, reducer-root, and unknown-root classifications.
- [ ] AC-05: Model-owned validation fixtures cover `confidence: None`, out-of-range confidence, missing judged-row evidence, and inconsistent abstention cells; replacement-row construction failure remains batch-fatal.
- [ ] AC-06: Structural cases remain batch-fatal: non-dict finding; `_error` without a usable `_map_index`; exact-type, range, and uniqueness violations; invalid-present `source_index` despite a valid `_map_index`; missing findings; reducer/unknown/mixed validation locations; and non-JSON-serializable malformed findings.
- [ ] AC-07: Non-error index selection follows the frozen `source_index`-then-None-fallback algorithm; `_error` attribution uses `_map_index` only; both paths exclude booleans.
- [ ] AC-08: Every failed row has exactly `judgement="abstain"`, `abstained=true`, `confidence=0.0`, `evidence_span=""`, `repaired=false`, and the frozen `row failed: ` reason; tests cover 240 characters exactly and 241 or more.
- [ ] AC-09: Validation-error reasons use the first emitted error and exact `<location>: <msg> [<type>]` format, with `<model>` for `loc == ()`; truncation never changes `raw_judgement`.
- [ ] AC-10: `raw_judgement` is exactly the map-error string, original error judgement, or sorted compact UTF-8-preserving JSON of the complete finding according to class; non-serializable class-3 input aborts.
- [ ] AC-11: Counts equal exactly `{"repaired": N, "demoted": M, "model_abstained": K, "failed": F}` and markdown contains exactly `Normalization: N repaired, M demoted, K model-abstained, F row-failed of T rows.`.
- [ ] AC-12: `reduce_ledger` returns exactly one outer `ledger` key; its nested result retains exactly `markdown_path`, `jsonl_path`, and `rows`; JSONL retains exactly the existing 11 `LedgerRow` keys.
- [ ] AC-13: All four committed incidents replay as 200-row ledgers with exactly one failed target row each, unchanged peers, exact counts, and complete raw error evidence; the bounded committed demo evidence is regenerated without requiring a paid live run.
- [ ] AC-14: Existing missing/duplicate/invalid-cell/normalization/key-set behavior remains green; replaced error-string/map-error witnesses carry REQ-YG-634 while surviving FR-892 contract witnesses retain REQ-YG-624.
- [ ] AC-15: CAP-249 adds FR-943 and removes the superseded error-string-rejection promise from REQ-YG-624; CAP-250 adds FR-943 and REQ-YG-634; regenerated requirement coverage passes.
- [ ] AC-16: `tools.py` remains at or below 450 lines; `ledger_failures.py` contains only the frozen FR-943 helper responsibility and exposes no shared framework API.
- [ ] AC-17: README documentation, REQ-YG-634 `fix` changelog fragment, FR implementation record, refreshed demo evidence, and diary reflection are committed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Contain only findings with usable frozen attribution and an error class proven wholly model-owned; every unclassified, structural, mixed, or replacement-row failure remains batch-fatal. | GATE |
| C-2 | Preserve full causal evidence in `raw_judgement`; only the human-facing `abstain_reason` may be truncated. | GATE |
| C-3 | Do not change graph YAML, prompts, model schema, map machinery, retry behavior, synthesis behavior, YAMLGraph core, hooks, CI, or doctrine. | GATE |
| C-4 | Do not add `counts`, failure metadata, or any twelfth key to the public return or JSONL contracts. | GATE |
| C-5 | Do not implement GREEN before the committed RED witness; all new-contract tests must carry REQ-YG-634 and requirement coverage must pass. | GATE |
| C-6 | Do not exceed the 450-line module maximum or turn the demo helper into a generic framework abstraction. | GATE |
| C-7 | Human review must accept this advisory draft and R-1–R-6 must be folded into the committed FR before implementation authority exists. | GATE |

Authority granted: after human acceptance and mechanical folding of R-1–R-6, implementation is authorized only for the frozen demo reducer containment, focused helper, tests, traceability corrections, documentation, and required evidence listed above.
