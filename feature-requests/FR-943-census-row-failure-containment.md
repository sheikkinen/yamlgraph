# Feature Request: Corpus Census — Row-Level Failure Containment at the Reduce Boundary

**Priority:** MEDIUM
**Type:** Bug
**Status:** PROPOSED — rev 2
Judgement: APPROVED WITH REVISIONS
(`FR-943-census-row-failure-containment.judgement.md`, 2026-08-31);
R-1–R-6 folded below. Enforcement authorized by operator
("write fr. judge. enforce").
**Effort:** 0.5 day
**Requested:** 2026-08-31
**First consumer / first event:** the 1,003-item spark-full census of
2026-08-31 — four of six 200-item batches died in `reduce_ledger` with
`finding contains map error` AFTER all ~200 LLM calls per batch had
completed and been paid for (~800 wasted calls). Each batch was killed
by exactly ONE item whose model output omitted the `abstained`
envelope field. The cure today is a hand-written post-hoc quarantine
script plus a full batch rerun — one more wasted batch per newly
discovered bad item.
**Research:** [FR-943.research.md](FR-943.research.md) — six solution
classes, precedent disposition, preserved disagreement,
`is_this_a_graph`, effort/risk. Incident evidence committed:
[tests/fixtures/fr943_incident_map_errors.json](../tests/fixtures/fr943_incident_map_errors.json)
— all four witnessed map-error findings with `_map_index`, verbatim
error text, failure class, and expected failed-row fields
(`read_raw_output_first` satisfied; surprising details recorded in the
research record: partial abstention envelope at index 178; item shell
content echoed into the judgement field at indexes 3, 131, 88).
**Prior art:** dispositioned below —
- **FR-892** built the fail-closed reducer; its batch-fatal contract is
  PRESERVED for structural impossibilities and AMENDED for the
  model-misbehavior class. FR-892's JSONL key-set contract (exactly 11
  keys) is unchanged.
- **FR-940** taught the ledger to distrust the model's *label*; this FR
  extends the same discipline to the model's *envelope*. FR-940's
  frozen summary line is amended (one added count — D-2 below).
- **FR-936 judgement D-4** (native RetryPolicy, unauthored): COMPOSES —
  retry cuts frequency at the framework layer; this FR caps blast
  radius at the demo reduce boundary. Exhausted retries still surface
  as `_error` findings; containment stays necessary. No shared
  deliverable.
- **FR-027/FR-069**: origin of the `_error`/`_map_index` finding
  taxonomy that makes containment attributable.
- Scripture `junk_drawer_cap` / `two_strike_split`: model output is a
  CLAIM reconciled in code; demote-never-drop, evidence preserved.
- REJECTED-FR sweep: no rejected FR touches the census reducer
  contract.

## Summary

`_rows_by_index` in `examples/demos/corpus_census/tools.py` raises for
the whole batch on ANY per-item anomaly. Split its failure taxonomy:
**attributable model-owned failures** (map-error findings,
error-string judgements, envelope `ValidationError`s wholly rooted in
model-owned fields) become contained, fail-closed **rows** — abstained,
zero-confidence, frozen-format reason, full causal evidence preserved
in `raw_judgement` — while **structural impossibilities** remain
batch-fatal exactly as FR-892 specified.

## Ideal Result

A 200-item census batch in which k items draw malformed model output
yields a 200-row ledger — 200−k judged rows and k row-failed rows with
their full failure evidence — and one item's misbehavior never
forfeits another item's spend. Batch abort survives only for states
the map machinery cannot legally produce.

## Value Statement

Every census caller stops paying an O(batch) rerun tax per bad item;
failures become visible, auditable ledger rows instead of dead runs;
the post-hoc quarantine workflow is retired.

## Proposed Solution

`is_this_a_graph`: no — deterministic Python contract fix inside an
existing demo graph's reduce tool (see research record).

### D-1: Contained row-failure class

**Non-error index selection (frozen, R-3):** read `source_index`; only
when its value is `None`, fall back to `_map_index`; then require
`type(selected_index) is int` (booleans excluded), range validity, and
uniqueness. A present but boolean, non-integer, out-of-range, or
duplicate `source_index` is structural and MUST NOT fall through to a
valid `_map_index`. When both are present, `source_index` is selected
and `_map_index` is not a second attribution input. `_error` findings
attribute via `_map_index` ONLY (same int/range/uniqueness rule);
missing or invalid `_map_index` on an `_error` finding is structural.

**Contained (model-owned) → one failed row, no raise:**

1. **Map-error finding**: `"_error" in finding` with a usable
   `_map_index`. Reason source: `str(finding["_error"])`.
   `raw_judgement` = exact `str(finding["_error"])`.
2. **Error-string judgement**: judgement contains an `ERROR_STRINGS`
   member under the existing case-sensitive substring semantics
   (frozen, unchanged). Reason source:
   `"judgement is an error string"`. `raw_judgement` = the original
   judgement string before any stripping or normalization.
3. **Model-owned envelope `ValidationError`** (closed rule, R-4):
   `_build_row` raises `ValidationError` and EVERY `exc.errors()`
   entry has either `loc == ()` (the model-level abstention validator
   — model-owned) or a non-empty `loc` whose FIRST component is one of
   `judgement`, `confidence`, `evidence_span`, `abstained`,
   `abstain_reason`. Every other location — unknown roots, reducer
   fields, or any mixture with a non-model-owned location — is
   batch-fatal. Reason source: the FIRST entry of `exc.errors()` in
   emitted order, location text
   `".".join(str(part) for part in loc) or "<model>"`, formatted
   exactly `<location>: <msg> [<type>]`. `raw_judgement` =
   deterministic JSON of the complete original finding via
   `json.dumps(finding, sort_keys=True, ensure_ascii=False,
   separators=(",", ":"))`. If the finding is not JSON-serializable,
   batch-fatal (no silent stringification).

**Failed row (frozen shape):** `judgement="abstain"`,
`abstained=True`, `confidence=0.0`, `evidence_span=""`,
`repaired=False`, `abstain_reason = "row failed: " + reason`
(truncation in D-2), `raw_judgement` per class above. The failed row
must itself pass `LedgerRow` validation; construction failure of the
replacement row is batch-fatal.

**Batch-fatal (structural, preserved from FR-892):**
- finding is not a dict
- `_error` finding without a usable `_map_index`
- non-error finding whose frozen index selection fails
- out-of-range or duplicate index (any finding class)
- `ValidationError` failing the closed model-owned rule
- non-JSON-serializable malformed finding (class 3)
- missing findings for any item index

### D-2: Reason truncation and frozen summary line

`MAX_FAILURE_REASON_CHARS = 240`: build the untruncated
`"row failed: " + reason`; if it exceeds 240 characters, emit its
first 237 characters plus `...`. Truncation never touches
`raw_judgement` — the full causal input always survives there.

`counts` (internal) gains `"failed"` — exactly
`{"repaired": N, "demoted": M, "model_abstained": K, "failed": F}`.
The FR-940 frozen summary line becomes (superseding FR-940's format):

```
Normalization: N repaired, M demoted, K model-abstained, F row-failed of T rows.
```

The `"row failed: "` reason prefix distinguishes contained rows from
FR-940 demotions.

### D-3: Public result shape and JSONL unchanged (R-5)

`reduce_ledger` returns exactly `{"ledger": ledger_result}`;
`ledger_result` keeps exactly `markdown_path`, `jsonl_path`, `rows`.
`counts` remains internal and MUST NOT appear at either public level.
JSONL rows keep exactly the existing 11 `LedgerRow` keys; failed rows
render through the existing markdown table.

### D-4: Focused helper module (R-6)

`tools.py` is 424/450 lines; the FR-943 failure taxonomy lives in a
new `examples/demos/corpus_census/ledger_failures.py` containing ONLY:
closed `ValidationError`-location classification, reason
formatting/truncation, and deterministic raw-finding serialization/
failed-row value assembly. `LedgerRow`, reducer orchestration, index
selection, and artifact writing remain in `tools.py`, which stays at
or below the 450-line hard maximum. The helper exposes no shared
framework API.

## Delivery surface (frozen by judgement)

- D-1 `examples/demos/corpus_census/tools.py` — orchestration, exact
  index selection, failed-row construction, four-key counts, summary
- D-2 `examples/demos/corpus_census/ledger_failures.py` — FR-943-only
  helpers
- D-3 new `tests/unit/test_fr943_census_row_failure_containment.py`
- D-4 `tests/unit/test_fr892_census_reducer.py` +
  `tests/unit/test_fr940_census_judgement_normalization.py` —
  superseded witnesses and exact summary amendment only
- D-5 `examples/demos/corpus_census/README.md` + regenerated
  `examples/demos/corpus_census/demo-output.log`
- D-6 `capabilities/CAP-249-tool-slot-binding.yaml` (add FR-943; amend
  REQ-YG-624 clause to: "the corpus-census reducer preserves
  abstention rows and rejects structural index/completeness failures
  and invalid ledger cells"), `capabilities/CAP-250-census-synthesize-tail.yaml`
  (add FR-943 + REQ-YG-634 owning containment, failed-row cells,
  evidence, four-key count, revised summary), regenerated
  `ARCHITECTURE.md`
- D-7 existing `tests/fixtures/fr943_incident_map_errors.json` replay
  evidence
- D-8 FR implementation record, `fix` changelog fragment
  (REQ-YG-634), diary reflection

Not authorized: `graph.yaml`, prompts, `CorpusCensusFinding` schema,
YAMLGraph core, `map_compiler`, retry, synthesis behavior, hooks, CI,
doctrine, shared failure APIs, public result/JSONL schema expansion.
No live paid run required.

## Acceptance Criteria (judgement AC-01–AC-17, frozen)

- [ ] AC-01: no unavailable prior-judgement claim in Status; research
      record retained with all six classes and the four-record
      incident citation.
- [ ] AC-02: RED committed first — valid `_error` finding with
      exact-int, in-range, unseen `_map_index` plus valid peers aborts
      under current reducer; GREEN emits one failed row, peers
      unchanged.
- [ ] AC-03: case-sensitive `ERROR_STRINGS` judgement → one failed
      row; original judgement exact in `raw_judgement`.
- [ ] AC-04: `ValidationError` contained iff every location is `()` or
      rooted in the frozen model-owned set; tests cover field-root,
      model-root, mixed-root, reducer-root, unknown-root.
- [ ] AC-05: model-owned fixtures cover `confidence: None`,
      out-of-range confidence, missing judged-row evidence,
      inconsistent abstention cells; replacement-row construction
      failure stays batch-fatal.
- [ ] AC-06: structural cases stay batch-fatal (non-dict; `_error`
      without usable `_map_index`; type/range/uniqueness violations;
      invalid-present `source_index` despite valid `_map_index`;
      missing findings; reducer/unknown/mixed locations;
      non-serializable findings).
- [ ] AC-07: non-error index selection follows the frozen
      `source_index`-then-None-fallback algorithm; `_error` uses
      `_map_index` only; both exclude booleans.
- [ ] AC-08: failed rows carry the exact frozen cells and
      `row failed: ` reason; tests cover exactly 240 and ≥241 chars.
- [ ] AC-09: validation reasons use first emitted error, exact
      `<location>: <msg> [<type>]`, `<model>` for `loc == ()`;
      truncation never changes `raw_judgement`.
- [ ] AC-10: `raw_judgement` per class (map-error string / original
      judgement / sorted compact UTF-8 JSON); non-serializable class-3
      aborts.
- [ ] AC-11: counts exactly the four named keys; markdown contains
      exactly the revised Normalization line.
- [ ] AC-12: `reduce_ledger` returns exactly one outer `ledger` key
      with exactly `markdown_path`, `jsonl_path`, `rows`; JSONL keeps
      exactly 11 keys.
- [ ] AC-13: all four committed incidents replay as full-row ledgers
      with exactly one failed target row each, unchanged peers, exact
      counts, complete raw evidence; bounded demo evidence
      regenerated; no paid live run required.
- [ ] AC-14: existing missing/duplicate/invalid-cell/normalization/
      key-set behavior stays green; replaced witnesses carry
      REQ-YG-634; surviving FR-892 witnesses retain REQ-YG-624.
- [ ] AC-15: CAP-249 adds FR-943 and drops the superseded error-string
      promise from REQ-YG-624; CAP-250 adds FR-943 + REQ-YG-634;
      regenerated requirement coverage passes.
- [ ] AC-16: `tools.py` ≤ 450 lines; `ledger_failures.py` FR-943-only,
      no shared framework API.
- [ ] AC-17: README, REQ-YG-634 `fix` changelog fragment, FR
      implementation record, refreshed demo evidence, diary
      reflection committed.

## Alternatives Considered

Dispositioned in [FR-943.research.md](FR-943.research.md): framework
map-level error-row policy (S-2, rejected — consumer semantics; one
consumer today), native RetryPolicy (S-3, composes), schema relaxation
(S-4, rejected — `plausible_wrong_answer`), prompt hardening (S-5,
rejected — `two_strike_split`), quarantine status quo (S-6, rejected —
O(batch) rerun tax).

## Related

- FR-892, FR-940, FR-936 judgement D-4, FR-027, FR-069, CAP-249,
  CAP-250
- `tests/fixtures/fr943_incident_map_errors.json` — committed incident
  record (source: `tmp/spark-full-census.log`, 2026-08-31)
