# Feature Request: FR-803 Pipecat Flows Architecture-Level Re-Assessment

**Priority:** MEDIUM
**Type:** Research (no code)
**Status:** Enforced 2026-08-15 - THREAT-DORMANT; AC-01..AC-08 delivered
**Effort:** 1 day
**Requested:** 2026-08-15
**Prior art:** FR-803-pipecat-flows-architecture-reassessment.judgement.md — this FR's own judgement (self-pair). FR-359-pipecat-frame-processor-integration.md — substantive prior art, dispositioned in Proposed Solution step 5 (COMPOSES/CONFLICTS/SUPERSEDES verdict required by AC-06). docs/diary/pipecat-assessment-2026-04.md — superseded at architecture level by this FR's output.
**First consumer / first event:** the 2026-Q4 kill-risk review (docs/diary/2026-08-15-market-research.md, kill-risk #3), at the moment it decides whether the voice-vertical control plane remains statemachine-engine or the foreign-runtime governance strategy is promoted from side bet to primary.

## Summary

Re-assess Pipecat at the *architecture* level — specifically whether Pipecat Flows can express an auditable, deterministic conversation FSM of ninchat_voice's class (≈50 states, 100+ transitions, regulated domain) — superseding the framework-level April 2026 verdict.

## Value Statement

The operator gets a decided (not assumed) answer to kill-risk #3 before committing the next arc of voice-vertical work to the statemachine-engine + yamlgraph pair.

## Problem

The April 2026 assessment (docs/diary/pipecat-assessment-2026-04.md) concluded "Pipecat does not compete — different planes (media vs reasoning)." That comparison was framework-vs-framework: Pipecat vs yamlgraph. The 2026-08-15 market research showed the production unit of analysis is the *pair* (deterministic FSM control plane + yamlgraph reasoning plane), and at that level **Pipecat Flows is a conversation FSM** — it challenges the control plane, statemachine-engine's seat, and would absorb the ~2.8K LOC audio/telephony services with it. The April verdict is an instance of the `evaluation` boundary trap: the method (framework comparison) determined the conclusion (no competition). The question was never actually asked at the right level.

## Ideal Result

A one-day research report answers, with evidence from Pipecat Flows' actual source and docs (not marketing): can Flows express a 50-state/100-transition FSM with (a) transitions as diffable, lintable, judgeable artifacts, (b) deterministic dispatch with no LLM in the control path, (c) self-hosted operation with no Pipecat Cloud dependency? A three-way verdict follows: THREAT-LIVE (Flows can; plan response), THREAT-DORMANT (Flows cannot yet; cite the specific missing property and a re-check trigger), or NOT-A-THREAT (structural mismatch; cite why it cannot converge). The market-research kill-risk #3 is updated in place.

## Proposed Solution

1. **Read the raw artifact first** (`read_raw_output_first` applied to research): clone/fetch Pipecat Flows source; read ≥3 real Flows configurations from their examples end-to-end before reading any docs prose. Record one surprising concrete detail per example. **R-1 (pinned corpus):** the report must record exact provenance — repository URL, immutable commit SHA or release tag, and the three example file paths/URLs — so the research is recheckable; mutable marketing pages must not be deciding evidence (C-2).
2. **Expressiveness probe (R-2, R-3):** name the exact ninchat_voice source artifact for the mode-switch cluster, or — if the source lives outside this repo — reproduce a bounded transition table (~10 states) extracted from it in the report *before* translation. The translation must be an auditable artifact: source state/transition table, proposed Flows representation or pseudocode, a construct-by-construct mapping table, and an explicit PASS/PARTIAL/FAIL per required property — static diffable transitions, deterministic non-LLM dispatch, guard/action semantics, self-hosted execution.
3. **Auditability check:** are Flows definitions static data (lintable, diffable) or Python callbacks (code)? Where does the LLM sit relative to transition decisions?
4. **Platform-commitment check:** what degrades without Pipecat Cloud (deploy, observability, SDK features)? Maps to the open-source/no-commercial-platform differentiator.
5. **Disposition of FR-359** (prior art, approved 2026-05-09: yamlgraph as a Pipecat FrameProcessor): render exactly one of COMPOSES / CONFLICTS / SUPERSEDES with one paragraph relating it to the `YAMLGraphProcessor` distribution-channel position.
6. Deliverable: `docs/diary/2026-08-XX-pipecat-flows-architecture-assessment.md` + kill-risk #3 updated in the market-research doc. No code. If Flows source/examples or the ninchat_voice fragment are inaccessible, stop and mark this FR blocked — do not substitute a generic framework comparison (C-3).

## Acceptance Criteria (revised per judgement)

- [x] AC-01: report cites the Pipecat Flows repository URL plus immutable commit SHA/tag used
- [x] AC-02: ≥3 real Flows example files/URLs named, each read end-to-end before docs prose, one concrete surprising detail each
- [x] AC-03: ninchat_voice mode-switch source artifact identified, or a bounded ~10-state transition table reproduced in the report before translation
- [x] AC-04: paper-translation artifact includes source transition table, Flows representation/pseudocode, construct mapping table, and PASS/PARTIAL/FAIL rows for: static diffable transitions, deterministic non-LLM dispatch, guard/action semantics, self-hosted execution
- [x] AC-05: exactly one of THREAT-LIVE / THREAT-DORMANT / NOT-A-THREAT rendered, citing the specific evidence line or mapping row that decides it
- [x] AC-06: FR-359 dispositioned as COMPOSES / CONFLICTS / SUPERSEDES with one explanatory paragraph
- [x] AC-07: kill-risk #3 in docs/diary/2026-08-15-market-research.md updated with verdict + concrete re-check trigger
- [x] AC-08: diff contains zero code, dependency, graph, prompt, CI, hook, or doctrine changes

## Alternatives Considered

- **Wait for the quarterly review to do it inline:** the review is a decision moment, not a research slot; unresearched kill-risks get rolled forward indefinitely (`audit_as_ritual`).
- **Full prototype integration:** premature — the April assessment already banked ecosystem facts; only the architecture question is open. Paper translation is the cheapest falsifier.
- **Dismiss on the April verdict:** the verdict answered a different question (framework vs framework); reusing it here is the `evaluation` trap twice.

## Related

- docs/diary/pipecat-assessment-2026-04.md — superseded at architecture level by this FR's output
- docs/diary/2026-08-15-market-research.md — kill-risk #3, alternative-implementations section
- FR-359 — Pipecat FrameProcessor integration (prior art; dispositioned in step 5)
- Scripture: `evaluation` boundary, `read_raw_output_first`, `does_the_platform_already_do_this`

## Judgement (2026-08-15)

**Verdict:** APPROVED WITH REVISIONS — see [FR-803-pipecat-flows-architecture-reassessment.judgement.md](FR-803-pipecat-flows-architecture-reassessment.judgement.md). R-1..R-3 folded above. Gates: C-1 fold-first (done), C-2 no mutable marketing pages as deciding evidence, C-3 stop-and-block rather than substitute a generic comparison, C-4 any code/prototype/vendor conclusion parks as a separate FR.

## Implementation Notes (2026-08-15)

- Assessed the live integrated Pipecat Flows source at `pipecat-ai/pipecat` commit `a5bb7867e1a08595dac1a778948bbdb49e0549b2`; recorded the frozen predecessor and v1.0 static-flow removal provenance.
- Read `food_ordering.py`, `patient_intake.py`, and `multi_worker_handoff.py` end-to-end before relying on documentation prose.
- Translated a bounded 10-state cluster from `projects/ninchat_voice/config/voice_coordinator_navigator.yaml` and rendered construct/property matrices.
- Verdict: **THREAT-DORMANT**. Static diffable transitions and deterministic non-LLM dispatch fail; guard/action semantics are partial; self-hosted execution passes.
- FR-359 disposition: **COMPOSES**. The no-code assessment is in `docs/diary/2026-08-15-pipecat-flows-architecture-assessment.md`; kill-risk #3 now carries the concrete recheck trigger.
