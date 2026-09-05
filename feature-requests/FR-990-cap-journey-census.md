# Feature Request: CAP journey census — customer journey, blast, disposition, value per capability

**Priority:** MEDIUM
**Type:** Enhancement (measurement instrument)
**Status:** Proposed — authority withheld until the Raw Output Read below is filled from the N=30 pilot
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

- **Samples read:** PENDING — `tmp/cap-census/pilot.jsonl` (N=30 including the six canaries) to be read end-to-end before this section is filled and before any matrix or ranking is quoted anywhere.
- **What I saw:** PENDING. Smoke (N=3, `examples/demos/cap_journey_census/demo-output.log`): CAP-81's row cited `yamlgraph/discovery.py` as consumer of a retired A2A server — the grep found a comment mention, not a call; the anchor accepted it because the path is in the mechanical list. Substance check needed on `consumer_cited`, not just presence.

## Ideal Result

Every CAP row carries a journey, a disposition with a cited consumer or an honest `contested`, and a value sentence or `value_unstated`; the `retire` rows are a proposal queue the operator can act on; the journey matrix shows which journeys are thick and which are one CAP wide; the result is stamped with git SHA and rerunnable in minutes.

## Proposed Solution

Instrument already authored (this branch): `examples/demos/cap_journey_census/` — `graph.yaml` + `prompts/judge_cap.yaml` via `scripts/author.sh` (brief: `feature-requests/authoring-briefs/cap-journey-census-brief.md`); `extract.py` (discover, evidence bundle with mechanical consumers by id and import needle, doc mentions, incidents, tagged tests); `tools.py` (reducer); `journeys.yaml`; `canaries.yaml`.

Sequence (research plan §8): pilot N=30 with canaries → read all 30 raw rows → fill Raw Output Read → judge → full run over 242 → commit artifact under `docs/census/` with SHA → separate FR-466 FRs for each `retire` row.

## Acceptance Criteria

- [ ] AC-1: Pilot N=30 including all six canaries runs; canary gate passes (or every miss is explained by a code fix, not a prompt reword — two-strike rule).
- [ ] AC-2: Raw Output Read lists ≥ 30 rows read with one concrete surprising detail each.
- [ ] AC-3: Full run over all `capabilities/CAP-*.yaml` completes; `row_failed + abstained ≤ 20%`.
- [ ] AC-4: Artifact committed under `docs/census/cap-journey-<date>.md` + `.jsonl` + `.run.json` with git SHA; contains matrix, disposition table, value table with `value_unstated` count, off-catalog list, canary report.
- [ ] AC-5: `consumer_cited` substance check: reducer distinguishes call/import hits from comment/doc mentions (smoke finding above) — implemented in `extract.py` before the full run.
- [ ] AC-6: No `retire` is applied by this FR; each candidate is listed with its evidence for a separate FR-466 FR.
- [ ] AC-7: Tests: reducer unit tests for catalog anchor, consumer anchor, evidence normalization, canary gate, `already_retired` consistency — each tagged `@pytest.mark.req` under a new CAP.

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
