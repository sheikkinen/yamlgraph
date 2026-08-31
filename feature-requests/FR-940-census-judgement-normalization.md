# Feature Request: Corpus Census — Judgement Label Normalization at the Ledger Boundary

**Priority:** MEDIUM
**Type:** Bug / Enhancement
**Status:** Rev 2 — judge R-2–R-5 folded
(`FR-940-census-judgement-normalization.judgement.md`, REJECTED 2026-08-31).
R-1 (committed research record) **waived by operator** 2026-08-31
("research skipped — we know the issue by now"); evidence promoted to a
committed witness fixture instead. Enforcement authorized by operator.
**Effort:** 1 day
**Requested:** 2026-08-31
**First consumer / first event:** the spark-census runs of 2026-08-31 —
19/106 rows of the opener census carried the model's free-form answer in
`judgement` (silent aggregation corruption); the follow-up 1,007-item
run needed a hand-tightened rubric to reach 0/1003 non-conforming. The
fix removes that rubric tax for every census caller.
**Research:** waived (operator decision, see Status). Witness evidence:
[tests/fixtures/fr940_witnessed_judgements.json](../tests/fixtures/fr940_witnessed_judgements.json)
— the 19 witnessed shapes with expected normalized outcomes.
**Prior art:** FR-892 built the census pipeline; FR-895 is the in-repo
precedent — LLM-free code boundary (`adapters/census_brief.py`)
validating model claims before rendering; this FR applies the same
discipline one stage earlier, at `reduce_ledger`. Scripture
`two_strike_split` (from FR-722/727/730): model output shape is a CLAIM
reconciled in code, never cured by prompt rewording — third strike, new
component. FR-936/FR-939 harden the map layer below — no overlap.
REJECTED-FR sweep: FR-940 rev 1 itself (this file's predecessor) is the
only prior proposal; its judgement's revisions are folded here.

## Summary

`reduce_ledger` accepts any non-empty, non-error string as the ledger
category — presence, not substance. Add a deterministic, LLM-free
normalization stage at that boundary (frozen algorithm below), an
optional caller-supplied `labels` vocabulary, and audit fields
(`raw_judgement`, `repaired`) plus frozen counts. Additionally wire an
optional `model` graph variable (default `claude-haiku-4-5`) so census
runs can select the judge/synthesis model (mercury-2, deepseek, …)
without editing the graph; ledger/brief provenance carries the
effective model.

## Ideal Result

Without a vocabulary, every `judgement` value in a census ledger is
**syntactically clean**: it satisfies the frozen label grammar or is
`abstain` — nothing structurally compound can occupy the label column.
With `labels` supplied, the guarantee is **semantic**: every value is
an exact canonical member of the caller's vocabulary or `abstain`.
Nothing is silently dropped: every demotion or repair preserves the
original model text in `raw_judgement`. Model choice is a run-time
variable, not a graph edit.

## Value Statement

Census callers (spark census, diary recurrence, repo census) get
aggregation-safe ledgers without defensive rubric engineering, an audit
trail of every reconciliation, and per-run model selection for cost
control.

## Problem

Witnessed 2026-08-31 (spark census, 106 items): rubric asked for
"(a) type; (b) theme; (c) spark"; the model returned the full triple in
`judgement` for 19/106 rows. `reduce_ledger`
(`examples/demos/corpus_census/tools.py`) checks only `min_length=1`
and error-string markers, so all 19 reached the JSONL unchanged and
splintered every downstream aggregation. The 19 shapes are committed in
the witness fixture. Separately, the model pin (`claude-haiku-4-5` in
graph defaults, map sub-node, and synthesize node) is hardcoded, so the
operator's cost-control choice (mercury-2 et al.) requires a graph edit.

## Frozen Normalization Algorithm (R-2)

Applied per finding in `reduce_ledger`, after existing structural
validation (map-error / missing / duplicate handling is UNCHANGED and
stays fail-closed). All steps deterministic and LLM-free (C-3).

Definitions:
- `raw` := the original judgement string; `J` := NFC-normalized,
  whitespace-stripped `raw`.
- SEPARATORS := `|`, `;`, newline (first occurrence of any cuts).
- PREFIX strips, applied in order, each at most once, case-insensitive,
  anchored: (1) enumeration marker `^\([a-z]\)\s*`; (2) tag
  `^type\s*:\s*`.
- QUOTES: after separator cut, strip one surrounding pair of `"` if
  present.
- GRAMMAR (checked on the lowercased candidate): length 1–64; matches
  `^[a-z0-9][a-z0-9 _/&-]*$`; no trailing space; at most 4
  space-separated words.

Steps:
1. **Model abstention**: if `abstained` is true, `judgement` :=
   `abstain`; if `J != "abstain"` (casefold), record `raw_judgement :=
   raw`. Not counted as demotion. Existing abstention cell validation
   (reason required, evidence empty) unchanged.
2. **Candidate extraction**: apply PREFIX strips to `J`; cut at first
   SEPARATOR; strip whitespace and QUOTES; lowercase → candidate `L`.
3. **Grammar gate**: if `L` fails GRAMMAR → **shape demotion**:
   `judgement := "abstain"`, `abstained := true`, `confidence := 0.0`,
   `evidence_span := ""`, `abstain_reason := "unparseable judgement
   shape"`, `raw_judgement := raw`, `repaired := false`;
   `demoted_count += 1`.
4. **Vocabulary gate** (only when `labels` supplied): validated at
   entry — non-empty list of non-empty strings, unique under casefold,
   must not contain `abstain` (violation raises, fail-closed). Every
   non-abstained candidate is matched case-insensitively; on match,
   emit the caller's exact canonical spelling; on miss → **vocabulary
   demotion**: as step 3 but `abstain_reason := "label not in
   vocabulary"`.
5. **Audit fields**: `raw_judgement := raw` whenever the emitted value
   differs from stripped `raw` in any way, else `""`. `repaired :=
   true` iff the emitted label differs from stripped `raw` under
   casefold (content change, not mere case/whitespace canonicalization)
   and the row was not demoted; `repaired_count += 1`.

Row-state transitions (R-3), complete:

| input class | judgement | abstained | raw_judgement | repaired | counted |
|---|---|---|---|---|---|
| untouched valid label | unchanged (lowercased/canonical) | false | "" (or raw if case differed) | false | — |
| repaired label | extracted label | false | raw | true | repaired_count |
| shape-unparseable | abstain | true | raw | false | demoted_count |
| vocabulary miss | abstain | true | raw | false | demoted_count |
| model abstention | abstain | true | raw if not literal | false | model_abstained_count |

`raw_judgement: str = ""` and `repaired: bool = False` are
reducer-owned `LedgerRow` fields with those defaults; the LLM schema
(`judge_item.yaml`) is NOT asked to produce them. Markdown ledger gains
one frozen line after the title:
`Normalization: {repaired} repaired, {demoted} demoted, {model_abstained} model-abstained of {total} rows.`

## Model Variable

- New optional graph state var `model` (str, default
  `claude-haiku-4-5`), applied to the map judge node and the synthesize
  node; `reduce_ledger` and brief provenance report the effective model
  (replacing the hardcoded `MODEL`/`SYNTHESIS_MODEL` constants as row
  values; constants remain as defaults).

## Authorized Surfaces (R-4)

- `examples/demos/corpus_census/tools.py` — normalization, audit
  fields, counts, effective-model plumbing.
- `examples/demos/corpus_census/graph.yaml` — `labels` + `model` state
  wiring; **material graph change: produced via the sole
  graph-authoring route with lint/smoke evidence** (C-4).
- `examples/demos/corpus_census/README.md` — invocation contract
  (`labels`, `model`), JSONL schema, normalization semantics.
- `tests/fixtures/fr940_witnessed_judgements.json` — witness fixture.
- `tests/unit/test_fr940_census_judgement_normalization.py` — new
  tests; `tests/unit/test_fr892_census_reducer.py` stays green.
- `capabilities/CAP-250-census-synthesize-tail.yaml` — REQ-YG-633 +
  FR-940 in `fr:`; ARCHITECTURE.md regenerated.
- Changelog fragment, diary reflection, demo evidence (demo gate).

Not in scope: YAMLGraph core, map-node policy, brief-citation logic,
generic normalization APIs, prompt rewording as mechanism. The
missing-fields defect (a finding lacking `abstained`/`abstain_reason`
poisons the whole batch via map-error fail-closed, witnessed 4× on
2026-08-31) is RECORDED but out of scope — fail-closed behavior is
pinned by AC-11; a row-preserving policy for malformed findings is a
separate FR candidate.

## Acceptance Criteria

- AC-1: RED first — parameterized tests over the committed 19-row
  fixture fail against the current reducer; committed separately
  (SKIP=pytest), GREEN follows.
- AC-2: All 19 fixture rows normalize to their expected
  `judgement`/`raw_judgement`/`repaired` values (all 19 repair to a
  valid four-word-vocabulary label; zero demotions).
- AC-3: Boundary fixtures: >64 chars, >4 words, forbidden separators,
  enum/tag prefixes, quoted heads, ambiguous prose (demotes), empty /
  duplicate-under-casefold / abstain-containing vocabularies (raise),
  valid-but-out-of-vocabulary (demotes), case-colliding input emits
  canonical vocabulary spelling, model-declared abstention (canonical,
  not demotion-counted).
- AC-4: Without `labels`, every emitted judgement satisfies the full
  GRAMMAR or is `abstain`; with `labels`, every emitted judgement is an
  exact vocabulary member or `abstain`.
- AC-5: Markdown contains the exact frozen summary line; JSONL rows
  carry the revised key set including `raw_judgement`/`repaired`;
  untouched, repaired, demoted, and model-abstained schemas asserted.
- AC-6: FR-892 behavior preserved: missing, duplicate, map-error, and
  invalid abstention-cell rows still fail closed — those assertions in
  `test_fr892_census_reducer.py` stay unmodified; its frozen-column
  key-set assertion is extended to the revised schema (explicit schema
  revision, in scope per R-4).
- AC-7: `labels` and `model` wired as graph state via the authoring
  route (lint + smoke report); README documents JSON-list invocation;
  a CLI smoke proves `--var labels='[...]'` reaches `reduce_ledger`
  and `--var model=...` reaches provenance.
- AC-8: Every new test carries `@pytest.mark.req("REQ-YG-633")`;
  changelog fragment references REQ-YG-633; demo evidence refreshed;
  diary reflection included.
