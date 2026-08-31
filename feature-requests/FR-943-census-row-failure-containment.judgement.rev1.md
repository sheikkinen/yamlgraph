# Judgement: FR-943 Corpus Census - Row-Level Failure Containment at the Reduce Boundary

**Verdict:** REJECTED - row-level containment is a sound contrib/example boundary correction, but the mandatory committed research/evidence record is absent and the validation-failure, evidence-preservation, count, and delivery contracts are not precise enough to grant implementation authority.

**Reviewed against:** `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.judgement.md`; `feature-requests/FR-936-map-node-hardening.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `feature-requests/FR-940-census-judgement-normalization.md`; `feature-requests/FR-940-census-judgement-normalization.judgement.md`; `capabilities/CAP-250-census-synthesize-tail.yaml`; `examples/demos/corpus_census/tools.py`; `tests/unit/test_fr892_census_reducer.py`; `tests/unit/test_fr940_census_judgement_normalization.py`; `ARCHITECTURE.md`; `CLAUDE.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`. The cited `tmp/spark-full-census.log` and `tmp/sparks-full/quarantine/` records were not consumed because those paths are absent from this worktree and no committed equivalent is referenced.

## What is sound

The defect class is real in committed evidence and code. FR-940 explicitly records that a finding lacking `abstained` or `abstain_reason` poisons the whole batch through the map-error fail-closed path and identifies row preservation as a separate FR candidate (`feature-requests/FR-940-census-judgement-normalization.md:176-180`). The reducer currently raises immediately for every `_error` finding and every judgement containing an `ERROR_STRINGS` marker, then converts every `LedgerRow` `ValidationError` into a batch-fatal `ValueError` (`examples/demos/corpus_census/tools.py:216-260`). Existing tests pin those batch-fatal map-error and error-string contracts (`tests/unit/test_fr892_census_reducer.py:105-108,124-127`). The proposal therefore addresses an observed contract rather than a hypothetical failure.

The chosen boundary is architecturally correct. The map layer already supplies attributable `_error` findings; deciding whether a failed branch invalidates the entire consumer result belongs in the corpus-census reducer. Keeping the change in `examples/demos/corpus_census/tools.py` avoids imposing this demo's row-preservation policy on other map consumers (`feature-requests/FR-943-census-row-failure-containment.md:64-73,171-179`). This follows the repo law to normalize external claims at their entry boundary and the `two_strike_split` rule to reconcile mechanizable model-output failures in code rather than through another prompt patch (`.github/copilot-instructions.md:51-53,116-117`).

The request has one coherent responsibility: reduce the blast radius of attributable model-output failures while preserving batch-fatal handling for impossible map structure. The proposed failed row reuses the existing 11-field `LedgerRow`, so no new persisted schema is needed (`feature-requests/FR-943-census-row-failure-containment.md:97-140`; `tests/unit/test_fr892_census_reducer.py:46-78`). Retry is correctly dispositioned as a composing frequency control rather than a substitute for final-failure containment (`feature-requests/FR-943-census-row-failure-containment.md:32-39`; `feature-requests/FR-936-map-node-hardening.judgement.md:102-115`).

The strategic classification is **Contrib/example**. The behavior serves callers of one existing corpus-census demo and changes no framework primitive, graph, prompt, or provider contract (`feature-requests/FR-943-census-row-failure-containment.md:83-95`). Direct deterministic reducer tests can cover the core row-containment and structural-fatality behavior.

## Required revisions

The eight-criterion disposition is:

| Criterion | Finding |
|---|---|
| Scope | The reducer callsite is minimal, but the "`tools.py` (+ tests)" boundary omits required CAP/REQ, regenerated architecture, README, changelog, diary, demo evidence, FR implementation record, and the specific existing tests whose old fatal assertions must change (`feature-requests/FR-943-census-row-failure-containment.md:92-95,135-169`). Fold R-5. |
| Consistency | The FR promises full failure evidence but preserves only the raw judgement for a malformed envelope; that loses the actual bad field such as `confidence: None`. AC-1 names `counts["failed"]` as though returned by `reduce_ledger`, while the current public result exposes only paths and row count (`feature-requests/FR-943-census-row-failure-containment.md:109-118,146-150`; `examples/demos/corpus_census/tools.py:324-328,341-349`). The prior-art pointer also says the summary amendment is D-3 although it is D-2 (`feature-requests/FR-943-census-row-failure-containment.md:31,127-140`). Fold R-3 and R-4. |
| Measurability | "`sane length`," "`first error summary`," "`valid` int," and "`verbatim raw material`" do not define exact assertions. The live AC accepts either one failed row or no failed row, so it need not exercise the changed branch (`feature-requests/FR-943-census-row-failure-containment.md:102-118,163-167`). Fold R-2, R-3, and R-6. |
| Feasibility | `_rows_by_index` is a workable seam, but catching every `_build_row` `ValidationError` as model misbehavior also catches reducer-owned `item_ref` and provenance validation failures. `LedgerRow` validates `item_ref` and `model` as non-empty alongside model-owned envelope cells, so the proposed failed-row replacement may itself be invalid (`examples/demos/corpus_census/tools.py:49-65,181-213,258-261`). Fold R-2. |
| Architecture alignment | Consumer-specific, deterministic containment in the existing reducer conforms to the three-layer application pattern and avoids an unnecessary framework or graph change (`ARCHITECTURE.md:27-61`; `feature-requests/FR-943-census-row-failure-containment.md:90-95,178-179`). No architectural revision is required beyond the scope fence in R-5. |
| Single responsibility | Attributable row failure, failed-count reporting, and its reducer tests are one contract. Retry, prompt hardening, schema relaxation, and framework-wide map policy are explicitly excluded (`feature-requests/FR-943-census-row-failure-containment.md:171-179`). No split is required. |
| Strategic classification | **Contrib/example**: multiple runs consume one existing demo reducer; the request neither needs nor authorizes a reusable YAMLGraph primitive (`feature-requests/FR-943-census-row-failure-containment.md:83-95`). |
| Testability | `_error`, error-string, summary, and structural-index cases map directly to tests, and existing tests expose the seam. Catch-all `ValidationError`, evidence serialization, truncation, boolean indexes, failed-count observability, and the nondeterministic live witness cannot be tested to one frozen answer until R-2 through R-6 are folded (`tests/unit/test_fr892_census_reducer.py:94-127`; `feature-requests/FR-943-census-row-failure-containment.md:144-169`). |

### R-1: Supply the mandatory committed research and incident evidence

Replace the waiver with `**Research:** [FR-943.research.md](FR-943.research.md)` and commit a substantive record before re-entry. It must contain 4-6 genuine solution classes, precedent/retrieval lines, preserved disagreement, effort/risk, and an explicit `is_this_a_graph` answer, then disposition every retrieved precedent in the FR. FR-940's one-off operator override does not create a reusable waiver: its committed record says the original judgement rejected the absent research and that the operator separately authorized enforcement for FR-940 (`feature-requests/FR-940-census-judgement-normalization.md:8-20`; `feature-requests/FR-940-census-judgement-normalization.judgement.md:3,30-33,84-91`).

Promote sanitized committed evidence for the four witnessed failures. At minimum, commit a fixture containing each attributable map-error finding, its `_map_index`, the source failure class, and the expected failed-row fields. Cite that fixture from the research record and FR. A `tmp/` path that is absent from the judged worktree is not a committed evidence reference. The template and FR-890 require the Research field to point at a committed substantive record; absent, dangling, or strawman evidence receives no authority (`feature-requests/TEMPLATE.md:9-18`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:123-142,162-170`; `.github/skills/judge-fr/doctrine.md:118-130`).

### R-2: Freeze the model-owned versus structural validation taxonomy

Replace catch-all "`_build_row` raises `ValidationError`" with an exact ownership rule based on `ValidationError.errors()` locations. Only errors rooted in model-owned envelope fields may become failed rows: `judgement`, `confidence`, `evidence_span`, `abstained`, and `abstain_reason`, including their abstention cross-validation. Errors rooted in reducer-owned fields (`item_ref`, `model`, `prompt_version`, `disagreement`, `raw_judgement`, or `repaired`) remain batch-fatal. If one `ValidationError` contains both classes, it is structural and batch-fatal. A failed row must itself pass `LedgerRow` validation; failure to construct it remains batch-fatal.

Define a usable index as `type(index) is int`, `0 <= index < len(items)`, and unseen; booleans are not valid indexes. For `_error` findings, use `_map_index` only and treat missing, boolean, conflicting/invalid, duplicate, and out-of-range attribution as structural. Freeze `ERROR_STRINGS` matching to the current case-sensitive substring semantics unless the FR explicitly authorizes another rule. Add direct witnesses for every boundary.

### R-3: Freeze reason truncation and full failure-evidence preservation

Define `MAX_FAILURE_REASON_CHARS = 240`. Build the untruncated reason first; if it exceeds 240 characters, emit its first 237 characters plus `...`. For a contained Pydantic error, define the first summary as the first entry from `ValidationError.errors()` in emitted order, formatted exactly as `<dot-joined loc>: <msg> [<type>]`. Tests must cover exact-boundary and over-boundary reasons.

Freeze `raw_judgement` by failure class:

- `_error`: exact `str(finding["_error"])`;
- error-string judgement: the original judgement string before stripping or normalization;
- model-owned envelope `ValidationError`: deterministic JSON for the complete original finding using `json.dumps(finding, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`.

If the malformed finding is not JSON-serializable, keep the batch-fatal contract; do not silently stringify unknown objects. This preserves the actual failing value, such as `confidence: null`, rather than merely preserving an unrelated judgement label. The failed row's `abstain_reason` records the bounded summary while `raw_judgement` carries the full causal input.

### R-4: Align count observability with the existing public result

Keep the current `reduce_ledger` result shape unchanged: `ledger` continues to expose `markdown_path`, `jsonl_path`, and `rows` only (`examples/demos/corpus_census/tools.py:324-328,341-349`). Remove the implication in AC-1 that `counts` is a public return value. Public tests must assert the exact JSONL row and exact markdown summary:

`Normalization: N repaired, M demoted, K model-abstained, F row-failed of T rows.`

An internal `_rows_by_index` unit test may additionally assert `counts == {"repaired": N, "demoted": M, "model_abstained": K, "failed": F}`. Keep the JSONL row key set at exactly 11. Correct the prior-art reference from D-3 to D-2.

### R-5: Name every authorized surface and legacy-test amendment

Replace "`tools.py` (+ tests)" with this exact delivery surface:

- `examples/demos/corpus_census/tools.py`;
- `examples/demos/corpus_census/README.md`;
- new `tests/unit/test_fr943_census_row_failure_containment.py`;
- `tests/unit/test_fr892_census_reducer.py`, specifically replacing the old map-error and error-string batch-fatal witnesses while preserving its missing, duplicate, invalid-cell, and 11-key witnesses;
- `tests/unit/test_fr940_census_judgement_normalization.py`, only for the frozen summary-line amendment;
- `capabilities/CAP-250-census-synthesize-tail.yaml`, adding FR-943 and REQ-YG-634;
- regenerated `ARCHITECTURE.md`;
- the FR-943 changelog fragment, demo evidence, FR implementation record, and diary reflection.

No `graph.yaml`, prompt, schema-file, YAMLGraph core, map compiler, retry policy, synthesis-tail, hook, CI, judge/review doctrine, or Chaplain runtime change is authorized. No material graph artifact is needed for this reducer-only correction.

### R-6: Replace the nondeterministic live gate with a deterministic replay

Make the four sanitized incident findings from R-1 a deterministic replay fixture. For each fixture, combine the failed finding with valid peer findings and assert: all input indexes produce ledger rows; exactly the attributable row is failed; peer rows are unchanged; failed count is exact; the full causal evidence is preserved; and no batch abort occurs. Regenerate `demo-output.log` using the bounded committed demo fixture and assert the amended summary line. Move the 200-item live LLM rerun to optional operational evidence: an outcome that permits zero row failures cannot serve as the witness for the new containment branch, and external model behavior must not determine acceptance.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-0 | No implementation deliverable is authorized by this rejected judgement. |
| D-1 | Revised FR-943 and committed `FR-943.research.md` with committed sanitized incident fixtures, for re-entry into judgement. |

Not authorized: production or test changes under FR-943 before a revised FR receives a fresh judgement; `graph.yaml` or prompt changes; `CorpusCensusFinding` schema relaxation; YAMLGraph core or `map_compiler` changes; native retry work; synthesis-tail behavior; new ledger columns or changes to the 11-key JSONL shape; hooks, CI, judge/review doctrine, or Chaplain runtime changes; a mandatory 200-item paid live rerun.

## Revised acceptance criteria

- [ ] AC-01: `**Research:**` references committed `FR-943.research.md` containing 4-6 substantive solution classes, precedent/retrieval lines, preserved disagreement, effort/risk, and `is_this_a_graph`; the FR dispositions every retrieved precedent and cites committed sanitized fixtures for all four incident failures.
- [ ] AC-02: RED first - a valid `_error` finding with `type(_map_index) is int`, an in-range unseen index, and valid peer findings fails against the current reducer; GREEN emits one failed row without aborting or changing peer rows.
- [ ] AC-03: A judgement containing a current case-sensitive `ERROR_STRINGS` substring becomes one failed row; the original judgement is preserved exactly in `raw_judgement`.
- [ ] AC-04: A `LedgerRow` validation error rooted only in model-owned envelope fields becomes one failed row; deterministic tests cover at least `confidence: None`, invalid confidence range, missing evidence on a judged row, and inconsistent abstention cells.
- [ ] AC-05: A validation error involving any reducer-owned field, or mixed model-owned and reducer-owned locations, remains batch-fatal; construction failure of the replacement failed row remains batch-fatal.
- [ ] AC-06: Structural cases remain batch-fatal: non-dict finding; `_error` without `_map_index`; boolean, duplicate, out-of-range, or otherwise invalid index; conflicting/unattributable index; non-error finding without a usable source index; and any missing finding.
- [ ] AC-07: Every failed row has exactly `judgement="abstain"`, `abstained=true`, `confidence=0.0`, `evidence_span=""`, `repaired=false`, and a `row failed: ` reason using the frozen first-error format and 240-character truncation rule.
- [ ] AC-08: `raw_judgement` follows the exact per-class contract: `_error` string, original error judgement, or deterministic complete-finding JSON for model-owned envelope validation; a non-JSON-serializable malformed finding remains batch-fatal.
- [ ] AC-09: Markdown contains exactly `Normalization: N repaired, M demoted, K model-abstained, F row-failed of T rows.`; internal counts carry exactly the four named keys; the public `reduce_ledger` result shape remains unchanged.
- [ ] AC-10: JSONL retains exactly the existing 11 `LedgerRow` keys, and failed rows render through the existing markdown table without a schema addition.
- [ ] AC-11: The four committed incident fixtures replay deterministically with all rows retained and exact failed counts; bounded `demo-output.log` is regenerated. A paid live 200-item run is optional evidence, not an acceptance gate.
- [ ] AC-12: Existing missing, duplicate, invalid-cell, normalization, and key-set behavior remains green; the old FR-892 map-error and error-string fatal witnesses are replaced by FR-943 containment witnesses rather than left contradictory.
- [ ] AC-13: CAP-250 adds FR-943 and REQ-YG-634; every new or materially changed test carries `@pytest.mark.req("REQ-YG-634")` where it witnesses the new contract; requirement coverage passes.
- [ ] AC-14: README documentation, fix changelog fragment for REQ-YG-634, FR implementation record, refreshed demo evidence, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Enforcement must not begin until R-1 through R-6 are folded into FR-943 and a fresh independent judgement grants authority. | GATE |
| C-2 | Only attributable model-owned failures may become failed rows; structural, reducer-owned, mixed-location, unserializable, and replacement-row-construction failures remain batch-fatal. | GATE |
| C-3 | Failure evidence must remain complete in `raw_judgement`; reason truncation must never truncate the only copy of the causal input. | GATE |
| C-4 | The JSONL contract remains exactly 11 keys and the public `reduce_ledger` result shape remains unchanged. | GATE |
| C-5 | No graph, prompt, schema-file, framework, map compiler, retry, synthesis-tail, or enforcement-infrastructure change may enter this FR. | GATE |
| C-6 | Acceptance must use committed deterministic replay fixtures; paid live LLM behavior is not a merge gate. | GATE |
| C-7 | RED and GREEN must remain separate commits, and every implementation decision or deviation must be folded into the FR before completion. | GATE |

Authority granted: none. FR-943 must add committed research and incident evidence, fold R-1 through R-6, and re-enter independent judgement before implementation.
