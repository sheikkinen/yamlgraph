# Feature Request: CAP journey census — customer journey, blast, disposition, value per capability

**Priority:** MEDIUM
**Type:** Enhancement (measurement instrument)
**Status:** Proposed — pilot complete (3 runs × 30 rows read); Raw Output Read filled; ready for judgement. Authority requested for the remaining code/catalog fixes and the full run.
**Effort:** 2 days (instrument exists; pilot, raw read, full run, artifact)
**Requested:** 2026-09-05
**First consumer / first event:** the operator, at the next retirement-proposal pass — the `retire` rows of the ledger are the proposal queue he expects unprompted (FR-466 lifecycle); second consumer: the judge's incident/consumer question, which today has no per-CAP evidence to check against.
**Research:** [docs/2026-09-05-research-plan-cap-journey-census.md](../docs/2026-09-05-research-plan-cap-journey-census.md) — committed, operator-reviewed research plan (questions, closed journey catalog, six canaries with expected answers written before any run, prior verdicts imported, forced opposite). Alternatives are dispositioned in-body below (FR-889 style).
**Prior art:** [FR-893 diary trap census](FR-893-diary-trap-census.md) — open-vocabulary confession count over diary; this FR uses a closed catalog over CAPs. [FR-962 person-profile census](FR-962-person-profile-census-authored-prs.md) — reducer precedent (`row_failed`, enum vocabulary, evidence substring); reused, not re-implemented. [FR-892 corpus census](FR-892-corpus-census-pipeline-injected-adapters.md) — skeleton shape; this graph has one corpus so uses plain tools, not slots. [FR-466](FR-466-cap-retirement-support.md) — retirement lifecycle; this FR produces candidates, never retires. [docs/node-type-census-2026-08.md](../docs/node-type-census-2026-08.md) — dispositioned `map` RETIRE with "no committed consumer"; canary C5 tests that this census reads the current tree instead. [FR-722/725/727/730/734 ICPC-2 arc] — closed-catalog + off-catalog + junk-drawer discipline, inherited.

## Summary

A per-CAP census (242 capability files) adding the four columns the traceability chain cannot carry: customer journey (closed 10-entry catalog), blast kind, keep/retire/extend disposition anchored to mechanically discovered consumers, and a for-whom/pain/versus value proposition. Cheap map on haiku, LLM-free reduce with fail-closed anchors and a hidden-canary gate. Output: journey × CAP matrix, disposition table, value table, per-journey blast diagrams.

## Value Statement

The operator gets a retirement queue and a journey map derived from evidence rather than recall; the judge gets per-CAP consumer facts to check "is the pain real" against.

## Problem

The chain proves every link is present (411/411 REQs covered) and cannot say whether any link is used, needed, or valuable. The registry knows who declares a capability, not who calls it ([diary 2026-08-30](../docs/diary/diary-2026-08-30-the-generator-nobody-fed.md)). Split FRs are abstract by construction — a SPLIT slices by concern, not beneficiary — so the "why" is not recoverable from the FR corpus. Nothing ranks 242 CAPs by consumer, incident, journey, or value.

## Raw Output Read (measurement / metric-tooling FRs only)

- **Samples read:** 30 rows × 3 pilot runs (90 rows), all read end-to-end. All three runs committed under [docs/census/](../docs/census/): `cap-journey-pilot-2026-09-05-run{1,2,3}.{jsonl,md,run.json}` (run 3 at SHA a110a103 is the current instrument; runs 1–2 are the pre-fix rows the findings below cite).
- **What I saw:**
  - Run 1: two rows (CAP-221, CAP-233) put `example_only` — a *blast_kind* enum value — into `journeys`. The model leaked one enum into another. Reducer now demotes to off-catalog instead of failing the row.
  - Run 1: CAP-203 (ICPC-2) evidence span was a paraphrase (`Core implementation uses map fan-out` vs yaml `Cluster fan-out (17 chapters…)`) while CAP-108's span matched exactly only after whitespace squashing — YAML folded scalars join lines with spaces. Two distinct evidence failure modes: formatting (fixed in code, `_squash`) and paraphrase (tolerant match: exact/prefix/ngram, kind recorded per row).
  - Run 2: **every example CAP came back `keep`** because its own directory was its consumer (novel_fandom cites `examples/novel_fandom/close.yaml`). Self-consumption satisfied the anchor. Fixed in `extract.py` by excluding the CAP's own example directory — the `builders_never_call` question is "does anything *outside* use it".
  - Run 2: **`author_graph` was the junk drawer** — 8/28 rows, 7 of them examples (ICPC-2, novel_fandom ×2, api-discovery, image pipeline, fi_domain_crawl). "A graph author could study this" is true of every example. Run 3, after the prompt said not to: example rows dropped to 3 but `author_graph` moved onto process/tooling CAPs (CAP-108 changelog gate, CAP-84 import-linter, CAP-153 questionnaire, CAP-209 package seams). Rewording relocated the junk drawer; it did not remove it. **Two strikes → the cap belongs in code** (FR-725/727/730 precedent), and the bare-id catalog is under-specified: the model never sees the `who` line, so `census_classify` was not recognised as covering ICPC-2 coding — run 3 answered `off_catalog:clinical_encounter_coding`, an honest and informative miss.
  - Run 2: value column `stated` 28/28 — unfalsifiable as designed. Reading `versus`: ~60% were "manual X" (CAP-79 "Manual review or skipping enforcement", CAP-84 "Convention-only enforcement"). Run 3 with a `value_generic` regex: 10/30 generic, 1 unstated, 19 stated. The column is a paraphrase of the CAP description; it is context, not a ranking input.
  - Run 2→3: **journeys are unstable at temperature 0** for cross-cutting runtime CAPs: CAP-131 prompt caching went `run_operate` → `serve_embed` → `serve_embed`; CAP-11 map node `run_operate` → `run_operate` → `author_graph`. A capability every LLM node uses has no single journey; the question is a category error for `core_runtime` rows.
  - Run 3: **consumer anchor caught three invented citations** — CAP-153 cited `yamlgraph/tools/questionnaire.py`, CAP-77 (image pipeline example) cited `yamlgraph/compile/map_compiler.py`, CAP-150 cited its own graph — none in the mechanical list → `contested`. This is `plausible_wrong_answer` made visible per row.
  - Run 3: **two genuine `retire` candidates surfaced** once self-consumption was excluded: CAP-184 (novel_fandom duplicate-entity guard; zero external consumers) and CAP-78 (fi_domain_crawl demo; `contested` because 2 consumers remain — both `.chaplain` demo logs, which the exclude list should have caught). CAP-81 (A2A, retired) still cites `yamlgraph/discovery.py` — a comment mention, not a call; the substance check (AC-5) is still open.
  - Run 3: 30/30 judged, 0 `row_failed`, evidence matched 24 exact / 6 prefix. The shape anchors are done; the *journey* column is the unfinished part.
- **Pilot verdict (research plan §8 exit criterion):** canaries still miss on `journeys` after one rubric revision → exit the prompt loop. Remaining fixes are code and catalog inputs, listed in Proposed Solution.

## Ideal Result

Every CAP row carries a journey, a disposition with a cited consumer or an honest `contested`, and a value sentence or `value_unstated`; the `retire` rows are a proposal queue the operator can act on; the journey matrix shows which journeys are thick and which are one CAP wide; the result is stamped with git SHA and rerunnable in minutes.

## Proposed Solution

Instrument already authored (this branch): `examples/demos/cap_journey_census/` — `graph.yaml` + `prompts/judge_cap.yaml` via `scripts/author.sh` (brief: `feature-requests/authoring-briefs/cap-journey-census-brief.md`); `extract.py` (discover, evidence bundle with mechanical consumers by id and import needle, doc mentions, incidents, tagged tests); `tools.py` (reducer); `journeys.yaml`; `canaries.yaml`.

Sequence (research plan §8): pilot N=30 with canaries → read all 30 raw rows → fill Raw Output Read → judge → full run over 242 → commit artifact under `docs/census/` with SHA → separate FR-466 FRs for each `retire` row.

**Done in the pilot (this branch):** whitespace-normalized + tolerant evidence match; enum-leak demotion; own-example-directory exclusion; node-type consumer needles (`type: map`); `extend_to` derived from `journeys.yaml` wedges instead of asked; `value_generic` flag; one prompt revision (end-user journeys). Canary and catalog changes recorded inline with reasons.

**Remaining before the full run (code and inputs, not prompt — two-strike rule):**
1. Pass the catalog *definitions* (`id: who`) to the model, not bare ids — a closed catalog is a rubric with inclusion terms (ICPC-2 lesson, FR-722); bare ids produced `off_catalog:clinical_encounter_coding` for an ICPC-2 example.
2. Code cap for `author_graph`: allowed only when `blast_kind ∈ {cli_surface, tooling_integration}` and a module path is under `yamlgraph/compile|lint|schema|skills` or `.github/skills`; otherwise demote to `contested` with reason. Generalises the example-only cap that pilot 3 showed was too narrow.
3. `core_runtime` rows: journey recorded but excluded from the journey × CAP matrix as `cross_cutting` (category error observed on CAP-131/CAP-11); disposition and consumers still apply.
4. Consumer substance (AC-5): classify each mechanical hit as `import`/`call`/`graph_ref`/`mention` by line content; `keep` requires a non-`mention` hit. Fixes the CAP-81 `discovery.py` comment and the `.chaplain` demo-log leak on CAP-78.
5. Fix own-directory exclusion for module spellings without the `examples/` prefix (CAP-226/232/233 still cited own steps).

## Acceptance Criteria

- [x] AC-1: Pilot N=30 including all six canaries runs; canary gate passes (or every miss is explained by a code fix, not a prompt reword — two-strike rule). *Result: 3 runs; shape anchors pass 30/30; journey canaries still miss after one prompt revision → exited the prompt loop; remaining fixes are code/catalog (Proposed Solution 1–5).*
- [x] AC-2: Raw Output Read lists ≥ 30 rows read with one concrete surprising detail each. *Filled above; rows committed under docs/census/.*
- [ ] AC-3: Full run over all `capabilities/CAP-*.yaml` completes after fixes 1–5; `row_failed + abstained ≤ 20%`; canary gate passes.
- [ ] AC-4: Artifact committed under `docs/census/cap-journey-<date>.md` + `.jsonl` + `.run.json` with git SHA; contains matrix (with `cross_cutting` row), disposition table, value table with `value_generic`/`value_unstated` counts, off-catalog list, canary report.
- [ ] AC-5: `consumer_cited` substance check: reducer distinguishes import/call/graph-ref hits from comment/doc mentions; `keep` requires a non-mention hit.
- [ ] AC-6: No `retire` is applied by this FR; each candidate is listed with its evidence for a separate FR-466 FR.
- [ ] AC-7: Tests: reducer unit tests for catalog anchor, consumer anchor, evidence normalization + tolerant match kinds, enum-leak demotion, junk-drawer cap, wedge derivation, canary gate, `already_retired` consistency — each tagged `@pytest.mark.req` under a new CAP.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| 1 | Manual review of 242 CAPs in chat | REJECTED — an LLM judgement anyway, unlogged, unreproducible, primed by the session, no reducer validating claims (`monolithic_analyze`). |
| 2 | Extend `req_coverage.py` with a consumer-count column (no LLM) | PARTIAL — the mechanical consumer facts are exactly this and live in `extract.py`; journey and value need reading, so the LLM column is justified only for those. |
| 3 | Mercury-2 for all fields | DEFERRED to cadence reruns — enum columns fit its abstraction span; value/blast need a paragraph of reading. Pilot on haiku. |
| 4 | Census over FRs instead of CAPs | REJECTED for this question — split FRs are abstract; the CAP is the unit that joins REQ, tests, modules, FR. FR-level incident-citation census is a separate instrument. |

## Related

- Diary: [the-judge-that-never-says-no](../docs/diary/diary-2026-09-04-the-judge-that-never-says-no.md), [the-opening-frame-set-the-prior](../docs/diary/diary-2026-09-04-the-opening-frame-set-the-prior.md) (PR #589)
- Business ranking: [docs/2026-09-02-brainstorm-business-use-cases.md](../docs/2026-09-02-brainstorm-business-use-cases.md)
