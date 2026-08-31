# Feature Request: Corpus Census — Row-Level Failure Containment at the Reduce Boundary

**Priority:** MEDIUM
**Type:** Bug
**Status:** PROPOSED — rev 2 (judge R-1–R-6 folded); rev 1 REJECTED
2026-08-31 (`FR-943-census-row-failure-containment.judgement.md`)
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
**Prior art (dispositioned):**
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
  contract. FR-943 rev 1's rejection revisions are folded here.

## Summary

`_rows_by_index` in `examples/demos/corpus_census/tools.py` raises for
the whole batch on ANY per-item anomaly. Split its failure taxonomy:
**attributable model-owned failures** (map-error findings,
error-string judgements, envelope `ValidationError`s rooted only in
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

### D-1: Contained row-failure class in `_rows_by_index`

**Index validity (frozen):** a usable index satisfies
`type(index) is int` (booleans excluded), `0 <= index < len(items)`,
and is unseen. For `_error` findings, attribution uses `_map_index`
ONLY; missing, boolean, out-of-range, or duplicate `_map_index` is
structural → batch-fatal.

**Contained (model-owned) → one failed row, no raise:**

1. **Map-error finding**: `"_error" in finding` with a usable
   `_map_index`. Reason source: `str(finding["_error"])`.
   `raw_judgement` = exact `str(finding["_error"])`.
2. **Error-string judgement**: judgement contains an `ERROR_STRINGS`
   member under the existing case-sensitive substring semantics
   (frozen, unchanged). Reason source:
   `"judgement is an error string"`. `raw_judgement` = the original
   judgement string before any stripping or normalization.
3. **Model-owned envelope `ValidationError`**: `_build_row` raises
   `ValidationError` and EVERY entry of `exc.errors()` has its
   location root in a model-owned field:
   `{judgement, confidence, evidence_span, abstained, abstain_reason}`
   (including their abstention cross-validation, whose Pydantic
   location root is the model itself — treated as model-owned).
   Reason source: the FIRST entry of `exc.errors()` in emitted order,
   formatted exactly `<dot-joined loc>: <msg> [<type>]`.
   `raw_judgement` = deterministic JSON of the complete original
   finding via `json.dumps(finding, sort_keys=True,
   ensure_ascii=False, separators=(",", ":"))`. If the finding is not
   JSON-serializable, batch-fatal (no silent stringification).

**Failed row (frozen shape):** `judgement="abstain"`,
`abstained=True`, `confidence=0.0`, `evidence_span=""`,
`repaired=False`, `abstain_reason = "row failed: " + reason`
(truncation rule in D-2), `raw_judgement` per class above. The failed
row must itself pass `LedgerRow` validation; construction failure of
the replacement row is batch-fatal.

**Batch-fatal (structural, preserved from FR-892):**
- finding is not a dict
- `_error` finding without a usable `_map_index` (as frozen above)
- non-error finding without a usable `source_index`/`_map_index`
- out-of-range or duplicate index (any finding class)
- `ValidationError` with ANY entry rooted in a reducer-owned field
  (`item_ref`, `model`, `prompt_version`, `disagreement`,
  `raw_judgement`, `repaired`) or mixing model- and reducer-owned
  locations
- non-JSON-serializable malformed finding (class 3)
- missing findings for any item index

### D-2: Reason truncation and frozen summary line

`MAX_FAILURE_REASON_CHARS = 240`: build the untruncated
`"row failed: " + reason`; if it exceeds 240 characters, emit its
first 237 characters plus `...`. Truncation never touches
`raw_judgement` — the full causal input always survives there.

`counts` (internal) gains `"failed"`. The FR-940 frozen summary line
becomes (superseding FR-940's format):

```
Normalization: N repaired, M demoted, K model-abstained, F row-failed of T rows.
```

The `"row failed: "` reason prefix distinguishes contained rows from
FR-940 demotions (`unparseable judgement shape`,
`label not in vocabulary`).

### D-3: Public result shape and JSONL unchanged

`reduce_ledger`'s public result keeps exactly `markdown_path`,
`jsonl_path`, `rows`. `counts` is internal to `_rows_by_index` /
`_write_artifacts`; an internal unit test may assert
`counts == {"repaired": N, "demoted": M, "model_abstained": K,
"failed": F}`. JSONL rows keep exactly the existing 11 `LedgerRow`
keys; failed rows render through the existing markdown table.

## Delivery surface (exact, per judgement R-5)

- `examples/demos/corpus_census/tools.py`
- `examples/demos/corpus_census/README.md`
- new `tests/unit/test_fr943_census_row_failure_containment.py`
- `tests/unit/test_fr892_census_reducer.py` — replace the old
  map-error and error-string batch-fatal witnesses with FR-943
  containment witnesses; preserve missing/duplicate/invalid-cell and
  11-key witnesses
- `tests/unit/test_fr940_census_judgement_normalization.py` — frozen
  summary-line amendment only
- `capabilities/CAP-250-census-synthesize-tail.yaml` — add FR-943 and
  REQ-YG-634
- `tests/fixtures/fr943_incident_map_errors.json` (committed incident
  fixture, already authored)
- regenerated `ARCHITECTURE.md` (requirement registry)
- changelog fragment (`fix`, req REQ-YG-634), demo evidence
  (`demo-output.log` regenerated from the bounded committed demo
  fixture), FR implementation record, diary reflection

Not touched: `graph.yaml`, prompts, `CorpusCensusFinding` schema,
YAMLGraph core, `map_compiler`, retry policy, synthesis tail, hooks,
CI, doctrine.

## Acceptance Criteria

- [ ] AC-01: `**Research:**` references committed `FR-943.research.md`
      (six solution classes, precedent disposition, preserved
      disagreement, effort/risk, `is_this_a_graph`); the FR
      dispositions every retrieved precedent and cites the committed
      incident fixture for all four failures.
- [ ] AC-02: RED first — a valid `_error` finding with
      `type(_map_index) is int`, in-range, unseen, plus valid peers
      fails against the current reducer; GREEN emits one failed row
      without aborting or changing peer rows.
- [ ] AC-03: a judgement containing a case-sensitive `ERROR_STRINGS`
      substring becomes one failed row; the original judgement is
      preserved exactly in `raw_judgement`.
- [ ] AC-04: a `ValidationError` rooted only in model-owned envelope
      fields becomes one failed row; deterministic tests cover
      `confidence: None`, out-of-range confidence, missing evidence on
      a judged row, and inconsistent abstention cells.
- [ ] AC-05: a validation error involving any reducer-owned field, or
      mixed locations, remains batch-fatal; replacement-row
      construction failure remains batch-fatal.
- [ ] AC-06: structural cases remain batch-fatal: non-dict finding;
      `_error` without `_map_index`; boolean, duplicate, out-of-range
      or otherwise invalid index; non-error finding without a usable
      index; missing findings; non-JSON-serializable malformed
      finding.
- [ ] AC-07: every failed row has exactly `judgement="abstain"`,
      `abstained=true`, `confidence=0.0`, `evidence_span=""`,
      `repaired=false`, and a `row failed: ` reason using the frozen
      first-error format and 240-char rule; tests cover exact-boundary
      (240) and over-boundary (241+) reasons.
- [ ] AC-08: `raw_judgement` follows the exact per-class contract
      (`_error` string / original judgement / deterministic
      complete-finding JSON); non-serializable finding stays
      batch-fatal.
- [ ] AC-09: markdown contains exactly
      `Normalization: N repaired, M demoted, K model-abstained, F row-failed of T rows.`;
      internal counts carry exactly the four named keys; public
      `reduce_ledger` result shape unchanged.
- [ ] AC-10: JSONL retains exactly the existing 11 keys; failed rows
      render through the existing markdown table.
- [ ] AC-11: the four committed incident fixtures replay
      deterministically — all indexes produce rows, exactly the
      attributable row fails, peers unchanged, counts exact, evidence
      complete, no abort; bounded `demo-output.log` regenerated. Paid
      live runs are optional evidence, not a gate.
- [ ] AC-12: existing missing/duplicate/invalid-cell/normalization/
      key-set behavior stays green; old FR-892 map-error and
      error-string fatal witnesses are replaced by FR-943 containment
      witnesses.
- [ ] AC-13: CAP-250 adds FR-943 and REQ-YG-634; new/changed tests
      carry `@pytest.mark.req("REQ-YG-634")` where they witness the
      new contract; requirement coverage passes.
- [ ] AC-14: README documentation, `fix` changelog fragment
      (REQ-YG-634), FR implementation record, refreshed demo evidence,
      diary reflection.

## Alternatives Considered

Dispositioned in [FR-943.research.md](FR-943.research.md): framework
map-level error-row policy (S-2, rejected — consumer semantics; one
consumer today), native RetryPolicy (S-3, composes), schema relaxation
(S-4, rejected — `plausible_wrong_answer`), prompt hardening (S-5,
rejected — `two_strike_split`), quarantine status quo (S-6, rejected —
O(batch) rerun tax).

## Related

- FR-892, FR-940, FR-936 judgement D-4, FR-027, FR-069, CAP-250
- `tests/fixtures/fr943_incident_map_errors.json` — committed incident
  record (source: `tmp/spark-full-census.log`, 2026-08-31)
