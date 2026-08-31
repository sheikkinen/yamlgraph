# Judgement: FR-940 Corpus Census — Judgement Label Normalization at the Ledger Boundary

**Verdict:** REJECTED — the reducer-boundary correction is sound, but the mandatory committed research record is absent and the proposed label grammar, vocabulary canonicalization, abstention transition, and authorized surfaces are not yet precise enough to grant implementation authority.

**Reviewed against:** feature-requests/FR-940-census-judgement-normalization.md; feature-requests/TEMPLATE.md; feature-requests/FR-890-research-sole-route-closed-input-alternatives.md; feature-requests/FR-895.research.md; feature-requests/FR-895-census-synthesize-tail.md; feature-requests/FR-895-census-synthesize-tail.judgement.md; examples/demos/corpus_census/tools.py; examples/demos/corpus_census/graph.yaml; examples/demos/corpus_census/prompts/judge_item.yaml; examples/demos/corpus_census/README.md; tests/unit/test_fr892_census_reducer.py; .github/skills/judge-fr/doctrine.md; .github/skills/judge-fr/judgement.template.md; .github/copilot-instructions.md. The cited `tmp/spark-census-ledger.jsonl` was not consumed because it is not a committed evidence artifact.

## What is sound

The defect class is real in the committed implementation: `LedgerRow.judgement` enforces only non-emptiness, and `_rows_by_index` rejects only known error-string markers before accepting the model text as the ledger category (`examples/demos/corpus_census/tools.py:23-33,78-91`). That permits structurally compound model output to reach the JSONL artifact unchanged (`examples/demos/corpus_census/tools.py:145-149`), exactly the presence-without-substance failure identified by the Scripture (`.github/copilot-instructions.md:89`).

The proposed correction is at the right architectural boundary. The FR places deterministic reconciliation in `reduce_ledger`, where model claims become durable ledger rows (`feature-requests/FR-940-census-judgement-normalization.md:27-34,70-94`), matching the repo's law to normalize external data at entry and its `two_strike_split` rule that model verdict shape must be reconciled in code rather than repaired through prompt wording (`.github/copilot-instructions.md:51-53,117`). It also preserves rows rather than dropping them, consistent with the existing first-class abstention contract and reducer tests (`examples/demos/corpus_census/tools.py:44-55`; `tests/unit/test_fr892_census_reducer.py:62-72`).

The request has one cohesive responsibility: make the corpus-census reducer's judgement dimension aggregation-safe and expose the reducer's reconciliation decisions. Its strategic classification is **Contrib/example**, not a framework primitive: all proposed behavior belongs to the existing corpus-census demo and explicitly excludes YAMLGraph core and map-node changes (`feature-requests/FR-940-census-judgement-normalization.md:70-74,115-120`).

## Required revisions

The eight-criterion disposition is:

| Criterion | Finding |
|---|---|
| Scope | The reducer boundary is minimal, but "all changes" in `tools.py` plus the finding schema conflicts with a new graph variable and README/schema output changes (`feature-requests/FR-940-census-judgement-normalization.md:70-74,88-94,110`). Fold R-4. |
| Consistency | The Ideal Result promises that no prose can enter the label column regardless of rubric, while an absent vocabulary permits any separator-free string up to 64 characters; case-insensitive membership also does not say whether output is canonicalized, so `A` and `a` may still split aggregation (`feature-requests/FR-940-census-judgement-normalization.md:36-41,76-90`). Fold R-2. |
| Measurability | AC-1 is directly assertable, but "unrecoverable prose," "repair floor," and repaired/demoted counts have no frozen rules; AC-4 depends on 19 rows that are not committed in the closed input (`feature-requests/FR-940-census-judgement-normalization.md:79-93,98-112`). Fold R-1, R-2, R-3, and R-5. |
| Feasibility | A Pydantic reducer boundary already exists and is the workable implementation point (`examples/demos/corpus_census/tools.py:23-55,78-106`), but `labels` is absent from graph state and the invocation contract (`examples/demos/corpus_census/graph.yaml:18-36`; `examples/demos/corpus_census/README.md:7-16`). Fold R-4 and prove CLI list parsing in R-5. |
| Architecture alignment | LLM-free normalization at `reduce_ledger` conforms to repo doctrine and the census tail's existing code-owned validation pattern (`.github/copilot-instructions.md:51-53,117`; `examples/demos/corpus_census/README.md:18-28`). Any material `graph.yaml` or prompt edit must nevertheless use the graph-authoring route (`.github/copilot-instructions.md:13-16`). Fold R-4. |
| Single responsibility | Normalization, audit fields, and normalization counts are one reducer-contract concern; no split is required (`feature-requests/FR-940-census-judgement-normalization.md:27-34,70-94`). |
| Strategic classification | **Contrib/example**: the named consumers share one existing demo, and the FR neither needs nor authorizes a reusable core primitive (`feature-requests/FR-940-census-judgement-normalization.md:44-48,70-74,115-120`). |
| Testability | Direct reducer tests can cover the behavior using the existing FR-892 test seam, but failing tests cannot be derived for prose detection, case output, model-declared abstentions, or count semantics until those rules and fixtures are frozen (`tests/unit/test_fr892_census_reducer.py:26-88`; `feature-requests/FR-940-census-judgement-normalization.md:96-112`). Fold R-2, R-3, and R-5. |

### R-1: Supply the mandatory committed research evidence

Add `**Research:** [FR-940.research.md](FR-940.research.md)` and commit a substantive research record before the FR re-enters judgement. The record must contain 4-6 genuine solution classes, precedent lines, preserved disagreement, effort/risk, and an explicit `is_this_a_graph` answer, then disposition every retrieved precedent in the FR. Promote the 19 witnessed judgement strings, with sensitive source content removed if necessary, into a committed fixture or equivalent committed evidence cited by the research record. Three examples in the FR and an uncommitted `tmp/` ledger do not satisfy the closed-input evidence gate. This revision is mandatory because newly created FRs without a committed, substantive research reference receive no authority (`.github/skills/judge-fr/doctrine.md:118-130`; `feature-requests/TEMPLATE.md:10-21`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:126-142,164-170`).

### R-2: Freeze the normalization grammar and vocabulary semantics

Replace "single short token/phrase," "enumeration markers," "recoverable label," and "below the repair floor" with a deterministic ordered algorithm. Define exact trimming and Unicode/case handling; the complete accepted character, word, and length grammar; every recognized leading form and separator; whether prefixes such as `(a) type:` are discarded; and the exact condition under which extraction fails.

Apply vocabulary validation to every non-abstained candidate, not only repaired candidates. Require `labels` to be a non-empty list of non-empty strings when supplied, reject vocabulary entries that collide under the chosen case normalization, reserve `abstain`, and emit the exact caller-supplied canonical spelling after a case-insensitive match. Unknown candidates demote.

**Human decision required:** must runs without `labels` guarantee semantic categorical labels, or only syntactic cleanliness? If semantic categorical labels are guaranteed, make `labels` required. If `labels` remains optional, narrow the Ideal Result and Value Statement to the exact syntactic guarantee; a length ceiling and separator blacklist cannot prove that arbitrary separator-free text is not prose.

### R-3: Freeze row-state transitions and audit/count fields

Define the complete output transition for each input class: untouched valid label, repaired label, vocabulary miss, unparseable shape, and model-declared abstention. For demotions, explicitly set `judgement: "abstain"`, `abstained: true`, `confidence: 0`, `evidence_span: ""`, and the exact `abstain_reason`; preserve the original judgement in `raw_judgement`. State whether an already-abstained row whose judgement is not `abstain` is canonicalized and audited.

Freeze `raw_judgement` and `repaired` as reducer-owned `LedgerRow`/JSONL fields, including types and defaults for untouched rows; do not ask the LLM to produce reducer audit fields. Define `repaired_count` and `demoted_count` exactly, exclude model-originated abstentions from `demoted_count`, and specify the exact markdown summary line. Resolve whether clearing `evidence_span` during shape demotion is the intended exception to the "nothing is silently dropped" claim or whether a separate raw evidence field is required.

### R-4: Name every authorized surface and route graph changes correctly

Replace the `tools.py`-only surface claim with an exact deliverable list. At minimum, account for `examples/demos/corpus_census/tools.py`, `examples/demos/corpus_census/graph.yaml` state wiring for `labels`, `examples/demos/corpus_census/README.md`, and `tests/unit/test_fr892_census_reducer.py`, plus required changelog, requirement traceability, FR implementation notes, demo evidence, and diary reflection. State that `raw_judgement` and `repaired` belong to the ledger schema, not `prompts/judge_item.yaml`; a prompt description clarification has no acceptance weight.

Because adding `labels` to `graph.yaml` is a material graph modification, require the sole graph-authoring route and its lint/smoke report. Keep YAMLGraph core, map-node policy, synthesis citation logic, and generic normalization machinery outside this FR.

### R-5: Replace aspirational criteria with exact witnesses

Commit the 19 witnessed judgement strings with expected normalized judgement, `raw_judgement`, `repaired`, `abstained`, and reason values. Add boundary fixtures for maximum length, every allowed and forbidden separator/prefix, ambiguous prose, empty/duplicate/case-colliding vocabularies, canonical case emission, valid-but-out-of-vocabulary input, repaired-but-out-of-vocabulary input, and model-declared abstention. Require assertions over the full grammar or vocabulary membership, not merely absence of structural separators. Pin exact repaired/demoted markdown counts and JSONL keys. Preserve the RED-before-GREEN commit requirement and apply `@pytest.mark.req(...)` to every new test (`.github/copilot-instructions.md:222`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-0 | No implementation deliverable is authorized by this rejected judgement. |

Not authorized: changes to `examples/demos/corpus_census/tools.py`, `graph.yaml`, prompt files, README, tests, proof artifacts, or callers under FR-940 until a revised FR with committed research evidence is judged and receives authority; YAMLGraph core changes; map-node changes; brief-synthesis changes; generic label-normalization APIs; prompt/rubric rewording as the normalization mechanism; hooks, CI, judge/review doctrine, or Chaplain runtime changes.

## Revised acceptance criteria

- [ ] AC-01: `**Research:**` references a committed FR-940 research record containing 4-6 substantive solution classes, precedent, disagreement, effort/risk, and `is_this_a_graph`; the FR dispositions the retrieved prior art and cites a committed sanitized fixture containing all 19 witnessed shapes.
- [ ] AC-02: RED first — parameterized tests fail against the current reducer for all 19 witnessed rows and for the frozen grammar, repair-floor, vocabulary, canonical-case, collision, and model-originated-abstention boundaries.
- [ ] AC-03: The FR states one deterministic ordered normalization algorithm; tests assert every accepted label satisfies the complete frozen grammar when no vocabulary is configured.
- [ ] AC-04: When `labels` is configured, it is validated as a non-empty, case-normalization-unique list; every non-abstained candidate is matched case-insensitively and emitted using the exact canonical vocabulary spelling; non-members demote.
- [ ] AC-05: `"new-spark | theme | spark text"` emits `judgement: "new-spark"`, `raw_judgement` equal to the full original, and `repaired: true`; every other recognized repair form has an exact fixture and expected result.
- [ ] AC-06: Every unrecoverable or out-of-vocabulary non-abstained finding remains a row and emits `judgement: "abstain"`, `abstained: true`, `confidence: 0`, `evidence_span: ""`, the frozen reason, full `raw_judgement`, and `repaired: false` unless the FR explicitly defines a distinct audited repair-then-demote state.
- [ ] AC-07: Model-declared abstentions are canonicalized according to the frozen transition, remain distinguishable from normalization demotions, and do not increment `demoted_count`.
- [ ] AC-08: The committed 19-row fixture produces only exact vocabulary members plus `abstain` when a vocabulary is supplied, and only strings satisfying the complete frozen grammar plus `abstain` otherwise.
- [ ] AC-09: Markdown contains the exact frozen repaired/demoted summary line and JSONL contains the exact revised `LedgerRow` key set; untouched, repaired, demoted, and model-abstained row schemas are asserted.
- [ ] AC-10: `labels` is wired and documented as graph state; a CLI smoke proves the documented JSON-list invocation reaches `reduce_ledger`; the material graph change is produced through the graph-authoring route with lint and smoke evidence.
- [ ] AC-11: Existing FR-892 reducer behavior remains covered: missing, duplicate, map-error, and invalid evidence/abstention rows still fail closed, while normalization demotions alone remain row-preserving.
- [ ] AC-12: Changelog fragment, valid REQ/CAP wiring as applicable, `@pytest.mark.req(...)` on every new test, FR status/decision updates, refreshed demo evidence required by the demo gate, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Enforcement must not begin unless R-1 through R-5 are folded into FR-940 and a fresh judgement grants authority. | GATE |
| C-2 | The committed research record and sanitized 19-row witness fixture must be available to the next judge under input closure. | GATE |
| C-3 | Normalization, vocabulary validation, canonicalization, demotion, and count calculation must remain deterministic and LLM-free at the census reducer boundary. | GATE |
| C-4 | Any material `graph.yaml` or prompt change must use the graph-authoring route and produce the required lint/smoke report. | GATE |
| C-5 | If implementation requires YAMLGraph core, map-node, generic normalization, synthesis-tail, hook, CI, judge/review doctrine, or Chaplain changes, enforcement stops and that concern enters a separate FR. | GATE |

Authority granted: none. FR-940 must return to research and planning, then re-enter independent judgement before any implementation begins.

**Prior art:** FR-940-census-judgement-normalization.md — this is the judgement OF that FR (rev 1 REJECTED; revisions R-1..R-5 folded into rev 2).
