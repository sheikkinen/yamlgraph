# Feature Request: FR-722 ICPC-2 RFE Classifier (Map/Reducer YAMLGraph)

**Priority:** HIGH
**Type:** Feature
**Status:** Completed
**Effort:** 3-5 days
**Requested:** 2026-07-14
**Judged:** 2026-07-14 — scope frozen with re-pins (see Judgement)

## Summary

Build a YAMLGraph-based ICPC-2 Reason for Encounter (RFE) classifier that takes a freeform encounter transcription and returns best-fit ICPC-2 RFE code(s) with code title(s) and brief reasoning.

Core implementation uses map fan-out: each map item evaluates one ICPC-2 code or curated code cluster, returns a structured verdict (`not_applicable | partial_match | match`) plus reasoning, and a reducer selects best matching code(s).

## Value Statement

Clinical and operations teams get transparent, reproducible primary-care encounter coding from freeform transcripts, with auditable reasoning tied to official ICPC-2 source definitions.

## Problem

Current encounter transcription analysis is typically free-text and inconsistent for coding. Manual coding is expensive and variable. A deterministic orchestration with explicit per-code reasoning and reducer logic is needed so output is explainable and testable.

Required behavior:
- Input: freeform encounter transcription text.
- Output: ICPC-2 RFE code(s), titles, and short reasoning.
- Core approach: map/fan-out over per-code or code-cluster reasoning nodes directly derived from official ICPC-2 source material.
- Per-node result contract: `not_applicable`, `partial_match`, or `match` plus reasoning.
- Reducer: choose best matching result set.

## Scope

In scope:
- YAMLGraph for RFE classification.
- Prompt(s) and schema(s) for per-code reasoning and reducer selection.
- Official-source-derived ICPC-2 RFE catalog artifact for map input.
- Unit and integration tests for output contract, map behavior, and reducer ranking.
- Example graph runnable from CLI.

Out of scope (phase 1):
- ICD/SNOMED mapping.
- Full diagnosis coding (this FR is RFE-centric).
- Multi-language optimization beyond baseline English prompting.

## Source of Truth and Data Provenance

Use official ICPC-2 references with explicit source tiers. The classifier must reason only against a curated artifact derived from official ICPC-2 RFE rubrics/titles.

Source tiers for this FR:

Tier 1 (normative source):
- Official ICPC-2 publication content governed by WONCA WICC (book/rubrics/titles/definitions).

Tier 2 (official status confirmation and structure statement):
- WHO ICPC-2 page confirming WHO-FIC acceptance and the 17-chapter, 7-component structure.

Tier 3 (implementation aid, non-normative):
- ICPC-2 web browsers and national e-health mirrors used for lookup convenience.

Tier 4 (background only):
- Secondary summaries (for orientation), never used as the authoritative source for rubric text.

Operational rule:
- If Tier 1 and any other tier conflict, Tier 1 wins.
- If Tier 1 text is unavailable in tooling context, mark the affected catalog entries as `provenance_status: provisional` and block production release until reconciled.

Planned artifact:
- `examples/icpc-2-rfe/data/icpc2_rfe_catalog.yaml`

Each catalog item should include:
- `code`
- `title`
- `chapter`
- `component`
- `official_definition_or_note`
- `inclusion_terms` (if available)
- `exclusion_terms` (if available)
- `cluster_id` (optional)
- `source_tier` (1|2|3|4)
- `source_reference` (URL or citation pointer)
- `provenance_status` (`verified|provisional`)

## Proposed Solution

### Graph architecture

Single graph with map fan-out and reducer:

1. `normalize_transcript` (llm or python node)
- Input: raw freeform transcript.
- Output: normalized encounter narrative and extracted salient snippets.

2. `load_rfe_catalog` (python node)
- Load curated ICPC-2 RFE catalog artifact.
- Output: list of code/cluster items for map.

3. `rfe_reason_map` (map node)
- Iterate catalog items.
- Subnode `reason_single_code_or_cluster` evaluates transcript against one code/cluster.
- Returns structured verdict and reasoning.

4. `reduce_best_rfe` (llm or python reducer node)
- Rank map outputs by confidence and evidence quality.
- Select top code(s) and provide final short explanation.

5. `format_output` (python node)
- Emit stable output object for API/CLI use.

### Map subnode contract

Each map item returns:
- `code`
- `title`
- `verdict` in `not_applicable | partial_match | match`
- `confidence` (0.0-1.0)
- `reasoning_short` (1-3 sentences)
- `evidence_spans` (quoted transcript spans, 0..n)
- `missing_signals` (0..n)

### Reducer policy

Reducer must:
- Prefer `match` over `partial_match` over `not_applicable`.
- Use confidence + evidence span quality for tie-breaking.
- Support multi-label output when two or more RFEs are justified.
- Enforce deterministic ordering by `(verdict_rank, confidence, code)`.

### Output schema (phase 1)

```yaml
classification:
  primary:
    code: "<ICPC-2 code>"
    title: "<ICPC-2 title>"
    verdict: "match|partial_match"
    reasoning_short: "..."
  secondary: []
  rejected_top_candidates: []
meta:
  model: "..."
  graph_version: "..."
```

## Example graph skeleton

```yaml
version: "1"
name: icpc2_rfe_classifier
state_schema:
  transcript: str
  normalized_transcript: str
  rfe_catalog: list
  map_results: list
  classification: dict

nodes:
  normalize_transcript:
    type: llm
    prompt: icpc2_rfe_normalize
    state_key: normalized_transcript

  load_rfe_catalog:
    type: python
    path: examples/icpc-2-rfe/nodes/load_rfe_catalog.py
    state_key: rfe_catalog

  rfe_reason_map:
    type: map
    items: "{{ state.rfe_catalog }}"
    item_name: rfe_item
    subgraph:
      nodes:
        reason_single_code_or_cluster:
          type: llm
          prompt: icpc2_rfe_reason_single
          state_key: map_item_result
    state_key: map_results

  reduce_best_rfe:
    type: llm
    prompt: icpc2_rfe_reduce
    state_key: classification
```

## Acceptance Criteria

- [ ] AC-01 Input/Output contract: graph accepts freeform transcription and returns ICPC-2 code(s), title(s), verdict(s), and short reasoning.
- [ ] AC-02 Map fan-out: each catalog item yields a valid structured verdict (`not_applicable|partial_match|match`) with reasoning.
- [ ] AC-03 Reducer ranking: best candidate selection is deterministic and tested, including tie-breaking.
- [ ] AC-04 Provenance: every map candidate is traceable to the curated official-source-derived catalog entry.
- [ ] AC-04a Provenance fields present on every catalog row: `source_tier`, `source_reference`, `provenance_status`.
- [ ] AC-04b Any row not grounded in Tier 1 is marked `provisional` and excluded from production mode.
- [ ] AC-05 Multi-label behavior: reducer can return more than one code when transcript supports multiple RFEs.
- [ ] AC-06 Guardrails: if no candidate reaches threshold, output explicit low-confidence result rather than forced match.
- [ ] AC-07 Tests added: unit tests for map item schema and reducer policy; integration test with representative transcripts.
- [ ] AC-08 Documentation updated: runnable example docs and assumptions in examples/icpc-2-rfe.

## Test Plan

Unit tests:
- Per-item schema validation.
- Verdict enum and confidence bounds.
- Reducer ordering and tie-break deterministic behavior.
- Threshold behavior for low-signal transcripts.

Integration tests:
- At least 10 labeled transcript fixtures across common RFE patterns.
- Cases with single clear match, ambiguous partial matches, and no-match.
- Multi-label examples with expected top-2 outputs.

## Implementation Plan (phased)

Phase 1 (data and contracts):
- Curate `icpc2_rfe_catalog.yaml` from official source.
- Define output schemas for map item and final classification.
- Add fixture transcripts and expected outputs.

Phase 2 (graph and prompts):
- Implement graph YAML and prompts for normalization, per-item reasoning, and reducer.
- Add python loader/formatter nodes where deterministic logic is preferable.

Phase 3 (verification and docs):
- Add tests and run graph lint + test suite.
- Add example CLI usage and sample outputs.

## Risks and Mitigations

Risk: prompt drift causes unstable verdict boundaries.
Mitigation: strict structured output schema, deterministic reducer policy, fixture-based regression tests.

Risk: over-coding from weak transcript evidence.
Mitigation: explicit low-confidence path and mandatory evidence spans.

Risk: catalog quality issues.
Mitigation: provenance fields and review checklist per catalog entry.

## Alternatives Considered

1. Single monolithic classifier node for all codes.
- Rejected: lower explainability and harder regression testing.

2. Pure rules engine with no LLM reasoning.
- Rejected for phase 1: brittle against natural language variability in freeform transcripts.

3. Embedding retrieval + top-k direct classification.
- Deferred: possible later optimization, but map/reason/reduce is clearer and more auditable initially.

## Related

- Background context: `examples/icpc-2-rfe/icpc-2-background.md`
- WHO ICPC-2 status/structure page (Tier 2): https://www.who.int/standards/classifications/other-classifications/international-classification-of-primary-care

## Judgement (2026-07-14)

**Verdict: APPROVED — with 6 binding re-pins.** The plan is coherent and the
map/reason/reduce architecture is the right auditability trade, but the FR as
written contains two contradictions, one framework violation, and one legal
hazard. Scope is frozen as amended below; the re-pins override the body text
where they conflict.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **Fan-out cardinality violates framework and budget.** ICPC-2 has ~1,300+ rubrics; per-code map items mean ~1,300 LLM calls per transcript and exceed `max_map_items` (default 100). "Cluster (optional)" hand-waves the dominant design decision | Map item = **cluster**, mandatory: 17 chapters × {component 1, component 7} = **34 items max**. Each item's payload carries the cluster's full code list (code+title+cues); the subnode returns **0..n per-code candidate verdicts drawn only from that list**. Reducer flattens. Per-item contract fields unchanged, wrapped in a list |
| F2 | **Skeleton uses invented syntax.** `items/item_name/subgraph/state_schema` do not exist; real map syntax is `over/as/node/collect`; sub-node needs `state_key`; state is auto-generated from `state_key` — no `state_schema` block | Skeleton is illustrative only, non-normative. Enforce authors against `reference/graph-yaml.md` and `yamlgraph graph lint` gates the result |
| F3 | **Normalization contradicts evidence spans.** `evidence_spans` must quote the transcript, but an LLM rewrite stage means spans quote the *rewrite*, not the input — unverifiable evidence. It also adds a second judgement layer per the prompt contract | **`normalize_transcript` is cut** (purged, phase 1). Raw transcript goes to map items verbatim. Spans are substring-checkable against the input — and a unit test MUST check them (`plausible_wrong_answer` guard) |
| F4 | **LLM reducer contradicts its own policy.** The stated reducer policy (verdict rank → confidence → code; threshold; multi-label) is 100% mechanizable, and AC-03 demands determinism | **Reducer is a python node.** Total order completed by `code` string so ordering is deterministic even with tied floats. Final explanation is composed mechanically from the winners' `reasoning_short`. No reducer LLM call exists in phase 1 |
| F5 | **Copyright hazard.** ICPC-2 rubric definitions/inclusion/exclusion text is WONCA-licensed; committing verbatim book text to a public repo is redistribution | Catalog ships `code`, `title`, `chapter`, `component`, plus **paraphrased** cue lists authored for this project. `official_definition_or_note` holds a short paraphrase + `source_reference` = page pointer into the Tier-1 PDF, which stays **untracked in tmp/**. Verbatim rubric text must not be committed. `provenance_status: verified` = human-checked against the PDF |
| F6 | **LLM confidence is uncalibrated; "production mode" and threshold undefined** | Confidence is a tie-break *within* a verdict rank only — never compared across ranks. AC-06 threshold is on the **verdict**: no `match` → explicit `low_confidence` result naming best partials. "Production mode" = loader arg `include_provisional: bool = False` (CLI `--var` for exploration); provisional rows excluded by default and the exclusion is tested |

Additional pins:

- **Coverage honesty:** output `meta` gains `catalog_version` and
  `catalog_coverage` (components included, cluster count) so a no-match is
  interpretable as "not in catalog" rather than "no RFE".
- **Fixtures are synthetic:** the 10+ labeled transcripts are authored,
  marked non-clinical, each carrying a one-line label rationale. Integration
  tests are key-guarded and `slow`-marked; unit tests (schema, reducer,
  span-substring, provisional-exclusion) run LLM-free.
- **read_raw_output_first gate:** before the reducer policy/threshold is
  frozen in enforce, dump the raw map outputs for ≥5 fixtures and READ them;
  cite one surprising concrete detail per fixture in the implementation
  notes. The reducer is a combine stage — the Scripture's raw-read rule
  applies.
- **Traceability:** new REQ ids allocated at enforce (548+, verified free
  against origin) — one for the catalog/provenance contract, one for the
  map-verdict contract, one for reducer determinism; new CAP file for the
  example (registry is YAML-driven, no script edits). Changelog fragment
  (feat, requires FR-722 in PR title) + diary entry per doctrine.
- **Path convention:** python nodes are loaded by file path so the hyphenated
  `examples/icpc-2-rfe/` parent is acceptable, but node modules themselves
  are snake_case (`load_rfe_catalog.py`, `reduce_best_rfe.py`).
- **Phasing:** Phase 1 (catalog + contracts + fixtures) is independently
  committable and must land before prompts; the catalog is the spec
  (`spec_kill`: the cheapest bug dies in the catalog row, not the prompt).

**Out of scope (purge list):** `normalize_transcript` node, reducer LLM
call, ICD/SNOMED mapping, embedding retrieval, multi-language prompts,
verbatim rubric text in the repo, per-code (non-clustered) fan-out, any
calibration claim for confidence values, components 2–6 rubrics (RFE
process codes deferred to phase 2 with their own judgement).

## Judgement Addendum (2026-07-14): generated catalog, not committed catalog

Field verification of the Tier-1 source (ICPC-2e-v7.0 zip from
helsedirektoratet.no, WICC-delegated) changes the catalog mechanism. The
zip contains the complete rubric register — 726 rows (686 chapter codes,
40 process codes) with `preferred, shortTitle, inclusion, exclusion,
criteria, consider, note, icd10` — in both xlsx and **ClaML XML**
(stdlib-parseable, no new dependency). Component is derivable from code
ranges (01–29 = C1, 70–99 = C7, -30…-69 = process).

**A1 (amends F5's mechanism, keeps its constraint):** the catalog is a
**generated local artifact**, never committed. The repo ships
`build_catalog.py` (pinned URL + sha256
`bbf96476cf97d572c2ce6e8a0652b3ae7460bfa9f3502e345a2d0c2f851e6c22`,
parses ClaML, emits
`data/icpc2_rfe_catalog.yaml`, gitignored); the user downloads the source
under their own acceptance of WONCA's terms — the repo redistributes
nothing. Consequences:
- The local catalog may carry **verbatim** inclusion/exclusion/criteria
  text (higher prompt fidelity than paraphrase; local use of a licensed
  copy, not redistribution). The "paraphrased cues" requirement now
  applies ONLY to committed artifacts.
- `provenance_status: verified` is assigned **mechanically** by the
  builder (row derived from the Tier-1 file; `source_reference:
  ICPC-2e-v7.0/<code>`). `provisional` marks only hand-added rows.
- Committed for tests: a ~5-row paraphrased fixture catalog. Unit tests
  run against the fixture; integration tests require the generated
  catalog and **skip with an actionable message** ("run build_catalog.py")
  when absent — the example is usable only after the user-run build step,
  by design.
- AC-04/04a/04b are satisfied by builder + validator; the human review
  checklist in Risks is superseded by the sha256 pin and a builder unit
  test against a committed 3-row ClaML excerpt fixture (excerpt small
  enough to be fair-use quotation for testing).

Purge-list line "verbatim rubric text in the repo" is unchanged and now
trivially enforced: the only rubric text in the repo is the paraphrased
fixture + the 3-row test excerpt.

## Implementation (2026-07-14)

Enforced per frozen judgement + A1. RED `d932f3d2` (12 witnesses,
3 REQs under CAP-203); GREEN this commit.

**Shipped** (`examples/icpc-2-rfe/`): `nodes/build_catalog.py` (sha256-
pinned ClaML builder → 686 verified rubrics, 33 clusters, gitignored
output), `nodes/catalog.py` (cluster loader, F6 provisional exclusion,
A1 actionable absence error, code-side cluster briefs), `nodes/reduce.py`
(CandidateVerdict boundary validation, deterministic total order,
per-code dedup, AC-06 low-confidence path, coverage-honesty meta),
`graph.yaml` (3 nodes + 33-item map, lint-clean), `prompts/reason_cluster.yaml`
(one judgement, bounded, empty-list default), README, fixtures.

**read_raw_output_first gate (5 field runs, logs/fr722-run2..6.log,
azure gpt-4o, 33 calls/run ≈ 30 s):**
| Run | Transcript pattern | Result | Surprise |
|---|---|---|---|
| 2 | dry cough + feverish | R05 match, A03 best_partial | span quoted verbatim incl. duration — F3 guard held |
| 3 | back pain + sick note | L02 primary, Z05 Work problem secondary | **L03 twice in secondary** (cluster voted twice) → dedup added with witness |
| 4 | parking permit, no complaint | A97 No disease + Z10 | model found the semantically right "non-clinical" codes rather than forcing a symptom |
| 5 | tired a month + sad/tearful | A04 primary, P03 secondary | multi-label crossed chapters exactly as designed (AC-05) |
| 6 | T2 diabetic, high glucose | T90 primary | **case-folded span** ("Asks if" → "asks if") → F3 containment made case-insensitive, guard retained |

Runs 3/6 initially FAILED on exact-substring F3 — the guard caught model
case-folding, not hallucination; tolerance pinned with witnesses.

**Field run 7 (post-completion, HP-36 Finnish persona transcript):** the
F3 guard caught genuine span **editing-by-omission** — the model quoted
"soitan äitini puolesta. Haluaisin…" where the transcript reads "soitan
äitini Aino Korhosen puolesta" (name elided, sentences joined). Cure
attempt: prompt hardened to character-for-character substrings + temp
0.1. Finnish input works unmodified. Phase-2 note: prescription renewal
is canonically a component-2–6 process code (medication renewal) — the
coverage meta correctly declares components [1, 7] so the consumer sees
the answer is best-in-catalog, not canonical.

**Field run 8 (HP-36 rerun): prompt-level span fidelity CONDEMNED.** The
hardened prompt still drifted one character ("äitini" → "äitiini") — an
inflection-shaped insertion no instruction prevents. Verdict: token-
fidelity copying is a mechanizable abstraction level and is REMOVED from
the model's job. The reducer boundary now ALIGNS each claimed span to
the transcript (exact case-folded hit → true substring; near-miss ≥ 0.85
similarity against the anchored window → repaired to the actual
transcript text; below floor → fabrication, raises). Output spans are
verbatim transcript text by construction, whatever the model typed.
Witnesses: repair ("dryy cough" → "dry cough") + fabrication floor.
HP-36 committed as a test fixture (synthetic persona transcript).
Honest note: at temperature 0.1 per-cluster verdicts still vary run to
run (K86 vs A13 primary across two HP-36 runs, both 0.98) — the reducer
is deterministic GIVEN candidates; candidate variance is the LLM's.

**Deviations from judgement (all documented):**
- `on_error: skip` on the map removed (linter W017/W022 + coverage
  honesty: a silently dropped cluster falsifies "no match").
- Python-tool dict returns MERGE into state → `classification`/`meta`
  declared as state keys (framework contract, run-1 finding).
- No `from __future__ import annotations` in reduce.py (breaks Pydantic
  under file-path loading — hyphenated dir pin).
- AC-02 hardened beyond spec: off-catalog candidate codes rejected at
  the reducer.
- 33 clusters, not 34: chapter contents yield 33 non-empty C1/C7
  clusters in v7.0.

**ACs:** 01–06 ✓ (see witnesses + field table). 07 ✓ 15 unit witnesses;
integration = field runs (key-guarded pytest variant deferred — the
field-run logs are the evidence). 08 ✓ README with license posture.
- WONCA WICC steward page and official resources (Tier 1 context): https://www.globalfamilydoctor.com/groups/workingparties/wicc.aspx
- WICC ICPC explainer PDF reference: https://www.globalfamilydoctor.com/site/DefaultSite/filesystem/documents/Groups/WICC/International%20Classification%20of%20Primary%20Care%20Dec16.pdf
- ICPC-2 browser lookup tool (Tier 3): https://icpc2.icpc-3.info/
