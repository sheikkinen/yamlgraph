# Judgement: FR-981 Module-History Demo — YAMLGraph Witness for the Phased Summary Pattern

**Verdict:** APPROVED WITH REVISIONS — the contrib/example direction is sound, but authority activates only after R-1 through R-7 are folded into the committed FR and its required pre-authority evidence.

**Reviewed against:** `feature-requests/FR-981-module-history-phased-summary-demo.md`; `feature-requests/FR-981.research.md`; `feature-requests/research-briefs/fr981-phased-summary-witness-brief.md`; `feature-requests/research-runs.jsonl` line 29; CLIN-SUMM at `https://www.medrxiv.org/content/10.64898/2025.11.28.25341233v3.full`; `feature-requests/FR-775-book-summary-loop-redesign.md`; `feature-requests/FR-962-person-profile-census-authored-prs.md`; `examples/demos/book-summary/README.md`; `reference/patterns/corpus-map-reduce.md`; `reference/getting-started.md`; `ARCHITECTURE.md`; `feature-requests/TEMPLATE.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem has a named consumer and event, and the research record contains six genuine solution classes, preserved dissent, external precedent, and an explicit `is_this_a_graph` answer (`FR-981.research.md:36-78`). The source confirms that CLIN-SUMM incrementally constructs reusable, structured, date-partitioned summaries and reports roughly 70% token reduction with clinician-rated quality; the FR correctly limits that evidence to an external preprint rather than treating it as proof of YAMLGraph composition (`FR-981.research.md:80-108`).

The minimal architecture is feasible with existing YAMLGraph facilities: Python owns enumeration, identity, persistence, and arithmetic; a map node owns per-record LLM work; and an LLM node owns reduction (`FR-981-module-history-phased-summary-demo.md:193-256`). Existing map compilation and reduction requirements are already registered as REQ-YG-040 and REQ-YG-041 (`ARCHITECTURE.md:710-718`), and `book-summary` demonstrates the adjacent per-item map plus final reduction shape. This is therefore strategically classified as a **contrib/example with pattern documentation**, not a framework primitive and not a new capability.

The FR also correctly fences out framework changes, recognizes the store as derived data rather than graph state, requires deterministic ownership of identity and counts, and routes governed graph artifacts through the authoring contract (`FR-981-module-history-phased-summary-demo.md:228-265`). These constraints make the proposal one responsibility: publish the phased-summary pattern together with the executable witness required to support its YAMLGraph-composition claim.

The strongest case against authority is that the committed repository currently has no phased-summary document to repair: the FR itself records `reference/patterns/phased-summary.md` as an uncommitted draft (`FR-981-module-history-phased-summary-demo.md:109-121`). The research nevertheless supports adding the document and witness together. The FR must state that truth directly rather than describe an uncommitted draft as an existing repository claim.

## Required revisions

### R-1: State the actual documentation scope

Rewrite the Summary, Problem, and documentation acceptance criterion to say that enforcement **creates** `reference/patterns/phased-summary.md` and adds it to `reference/README.md`; do not say an existing committed document is being upgraded. Define the document's evidence grades before enforcement: external shape evidence remains explicitly preprint-grade, while YAMLGraph composition stays UNEXERCISED until the demo witness passes. Cite the new pattern document and index as deliverables. This resolves the contradiction between the acknowledged uncommitted draft (`FR-981-module-history-phased-summary-demo.md:109-121`) and the current “has its grade moved” criterion (`FR-981-module-history-phased-summary-demo.md:292-295`).

### R-2: Preserve one selected record to one brief

Delete the near-duplicate dropping behavior at `FR-981-module-history-phased-summary-demo.md:235-241`. It contradicts “every commit ... to one durable typed brief” (`:64-68`), breaks coverage and provenance, and makes the required N+1 run produce zero brief calls for some valid new commits (`:273-275`). Redundancy filtering is not needed to witness this pattern and is not authorized in this demo. Every selected commit, including merge or empty-diff touches, must produce exactly one typed brief; uncertainty remains represented by `confidence: low`.

### R-3: Freeze a truthful single-subject corpus and ceiling policy

Specify one tracked path per invocation. Replace “every commit touching a source module” with “every commit in the frozen selected history window.” Define deterministic ordering, `--follow` rename behavior, the default and maximum `max_commits` value (maximum 60), and how the run record exposes total discovered, selected, and omitted-older counts plus the selected date/SHA range. Remove the unexplained three-module and 200-call ceilings at `FR-981-module-history-phased-summary-demo.md:258-260`; for one module the static maximum is 60 brief calls plus one rollup call. Separate preflight ceilings from runtime behavior: item, diff-byte, and planned-call limits fail before the first model call; an elapsed-time limit cannot truthfully do so and must either be removed or described as a runtime abort. Add tests for zero commits, a renamed path, over-window history, oversized diff truncation, and preflight rejection.

### R-4: Define and validate the durable-store and citation contracts

Replace `<path-slug>` with a collision-resistant deterministic subject key that includes a normalized repo-relative path and hash. Freeze a Pydantic-validated stored-brief envelope containing the collector-owned identity/date, model-authored fields, `brief_schema_version`, `prompt_version`, resolved provider/model, truncation metadata, and source path. A malformed or corrupt stored brief must fail loudly; it must never be treated as a hit or silently discarded. Freeze the typed rollup output as a list of claims, each carrying one or more stored-brief references. Deterministic render code must reject unknown references and prove each accepted reference resolves to a brief whose collector-owned commit SHA is present. This makes the current prose-only provenance criterion (`FR-981-module-history-phased-summary-demo.md:281-282`) directly testable.

### R-5: Make call arithmetic and invalidation exact

Define “brief call” separately from “total LLM call.” For a first run over N selected commits, assert N brief calls and one rollup call. For a second run after one distinct new commit, assert one brief call, N reused briefs, and one rollup call. For an unchanged third run, assert zero brief calls, N+1 reused briefs, and one rollup call. Invalidation must be tested independently for each frozen key: schema version, prompt version, and resolved provider/model. Planned and actual counts must come from deterministic instrumentation around the LLM seams, not model output or README arithmetic.

### R-6: Supply the raw-read evidence and freeze the cost/loss protocol before authority

The FR proposes a measurement of token saving and question loss (`FR-981-module-history-phased-summary-demo.md:283-289`) but defers its first raw read until enforcement (`:297-299`). Fold a committed pre-authority evidence record into the FR: at least three source-diff/brief pairs from a pilot, each naming one concrete detail retained and one concrete detail dropped or stating that none was found. Then freeze a small committed question fixture, source-backed expected answers, tokenizer/counting method, source-path prompt, brief-path prompt, and deterministic answer-scoring rule. Report at least source-input tokens, brief-input tokens, correctly answered questions on each path, and the raw answers; do not collapse unlike units into the FR's current “one named currency” wording, and set no quality threshold not supported by the samples. The witnessed run must reuse this frozen protocol. Without this revision, the cost/loss criterion cannot yield a failing acceptance test and violates `read_raw_output_first`.

### R-7: Close the authoring and requirement contracts

Add and cite a committed task brief at `feature-requests/authoring-briefs/fr-981-module-history-phased-summary-brief.md` before invoking `scripts/author.sh`, as required by `.github/skills/graph-authoring/doctrine.md`. State that the demo adds no CAP/REQ identifier: it exercises existing graph loading/linting, LLM, map, and Python-node requirements, including REQ-YG-040/041. Every new test must carry the applicable existing `@pytest.mark.req` marker. If enforcement discovers that a framework change or new capability is required, stop and return to Plan through a separate FR; do not allocate an ID or broaden FR-981.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-981-module-history-phased-summary-demo.md` and committed pre-authority raw-read evidence |
| D-2 | `feature-requests/authoring-briefs/fr-981-module-history-phased-summary-brief.md` |
| D-3 | `examples/demos/module-history/graph.yaml`, `prompts/*.yaml`, `tools.py`, and `README.md` |
| D-4 | `tests/unit/test_fr981_module_history.py` covering the frozen deterministic, store, prompt-boundary, and call-count contracts |
| D-5 | A committed demo-local real-model witness log plus the frozen question fixture and raw comparison answers |
| D-6 | New `reference/patterns/phased-summary.md` and its `reference/README.md` index entry |
| D-7 | One FR-981 changelog fragment and one diary entry with a Seed |

Not authorized: changes under `yamlgraph/`; changes to shared `corpus_census`, `book-summary`, compaction, research, judge, review, hook, CI, or requirement-reservation infrastructure; a reusable brief-store primitive; multi-module invocation; clinical or customer data; near-duplicate record dropping; cumulative rollup mutation; new CAP/REQ IDs; committed derived brief-store contents; or claims that the external preprint proves YAMLGraph behavior.

## Revised acceptance criteria

- [ ] AC-01: R-1 through R-7 are folded into the committed FR, including a cited committed record with at least three pilot source-diff/brief pairs and concrete retained/dropped-detail observations.
- [ ] AC-02: The committed FR cites `feature-requests/authoring-briefs/fr-981-module-history-phased-summary-brief.md`, and governed graph/prompt artifacts are produced only by `scripts/author.sh`; `tmp/draft-authoring-report.md` names the artifacts, precedent, lint, smoke, repairs, and blocked validation.
- [ ] AC-03: `examples/demos/module-history/` contains the frozen graph, prompt, Python-tool, README, question-fixture, raw-answer, and witnessed-run surfaces.
- [ ] AC-04: `yamlgraph graph lint examples/demos/module-history/graph.yaml` passes, and a recorded real-model smoke run over one small frozen module window completes with the resolved provider/model recorded.
- [ ] AC-05: Enumeration accepts exactly one normalized repo-relative tracked path, follows renames, freezes at most 60 date-ordered commits, and records discovered, selected, omitted, first/last date, and first/last SHA before any model call.
- [ ] AC-06: Tests prove zero-history rejection, renamed-path identity, over-window disclosure, 20 kB per-diff truncation with omission metadata, and preflight rejection before any LLM call when an item, byte, or planned-call ceiling is exceeded.
- [ ] AC-07: Every selected commit produces exactly one validated brief; merge and empty-diff touches produce `confidence: low` briefs rather than disappearing; no near-duplicate filter exists.
- [ ] AC-08: For N selected commits, the first run records N brief calls, zero reused briefs, and one rollup call; after one distinct new commit the second records one brief call, N reused briefs, and one rollup call; an unchanged third records zero brief calls, N+1 reused briefs, and one rollup call.
- [ ] AC-09: Independent tests prove that changing each of `brief_schema_version`, `prompt_version`, and resolved provider/model invalidates all applicable cached briefs, while unchanged valid envelopes are reused.
- [ ] AC-10: Store tests prove collision-resistant subject keys, Pydantic validation on write and read, explicit failure on corrupt envelopes, and no source diff text in any stored brief or rollup prompt input.
- [ ] AC-11: Rollup output is typed as claims with brief references; deterministic rendering rejects missing or unknown references and proves every rendered claim reaches one or more valid briefs and then collector-owned commit SHAs.
- [ ] AC-12: The frozen comparison protocol runs the same committed question set through source and brief paths and records tokenizer/method, source-input tokens, brief-input tokens, raw answers, deterministic correct-answer counts, and concrete omissions without claiming an unevidenced pass threshold.
- [ ] AC-13: The run record prints the normalized subject, selected range, truncations, planned/actual brief calls, rollup calls, reused briefs, invalidated briefs, resolved provider/model, prompt/schema versions, and store path; deterministic values are never supplied by the model.
- [ ] AC-14: `reference/patterns/phased-summary.md` is created and indexed. It labels external shape evidence as preprint-grade, names the demo for YAMLGraph composition only after AC-04 and AC-08 pass, lists the exercised and unexercised invariants, and states that the store is derived data outside graph state.
- [ ] AC-15: The README names subject, record, selected-window semantics, store location, graph/store boundary, rebuild procedure, cost ceilings, and the regenerate-not-cumulative trade-off.
- [ ] AC-16: New tests use applicable existing requirement markers, and `python scripts/req_coverage.py --strict` passes without a new CAP/REQ allocation or any change under `yamlgraph/`.
- [ ] AC-17: A changelog fragment and diary entry with a Seed are committed, and the FR records implementation status, validation commands, witness paths, and deviations.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Human review must confirm R-1 through R-7 are folded into committed planning artifacts before implementation begins; this draft is advisory. | GATE |
| C-2 | Governed graph and prompt files must be authored through the committed-brief `scripts/author.sh` route and evidenced by `tmp/draft-authoring-report.md`. | GATE |
| C-3 | The selected-record-to-brief relation is exactly one-to-one; no similarity filter or other optimization may remove a selected record. | GATE |
| C-4 | Deterministic code owns record identity, store keys, dates, truncation, citations, call counts, ceilings, and scoring arithmetic; model output is treated as a claim. | GATE |
| C-5 | Rollup input contains validated briefs only and no source diff text; every rendered claim must resolve through a brief to a collector-owned commit SHA. | GATE |
| C-6 | No framework, shared-pipeline, research-route, enforcement-infrastructure, CAP, or REQ change may ride in FR-981. | GATE |
| C-7 | No clinical/customer data or derived brief-store contents may be committed; only the bounded repo-history witness inputs/outputs authorized above may be retained. | GATE |
| C-8 | If the default small-model smoke or the frozen cost/loss protocol cannot be completed honestly, the composition grade remains UNEXERCISED and the FR returns to Plan rather than weakening the witness. | GATE |

Authority granted: after C-1 activates, implement the single-module contrib demo, its deterministic local brief store, its bounded tests and witness artifacts, and the accurately graded phased-summary documentation on only the frozen surfaces above.
