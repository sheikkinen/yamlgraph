# Judgement: FR-803 Pipecat Flows Architecture-Level Re-Assessment (DRAFT)

**Prior art:** FR-803-pipecat-flows-architecture-reassessment.md — the governing FR of this judgement (self-pair); FR-359 dispositioned in the verdict body.

**Verdict:** APPROVED WITH REVISIONS — the no-code research question is real, minimal, and strategically timed, but authority activates only after the FR pins reproducible source inputs and makes the paper-translation acceptance checks mechanically auditable.

**Reviewed against:** `feature-requests/FR-803-pipecat-flows-architecture-reassessment.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/diary/pipecat-assessment-2026-04.md`; `docs/diary/2026-08-15-market-research.md`; `feature-requests/FR-359-pipecat-frame-processor-integration.md`.

## What is sound

The proposal asks the right-level question. The April assessment explicitly concluded Pipecat and YAMLGraph do not compete because they occupy media and reasoning planes (`docs/diary/pipecat-assessment-2026-04.md:96-143`), while the later market research reframed production reality as a deterministic control plane plus stochastic reasoning plane and named Pipecat Flows as the strongest merged-plane challenger (`docs/diary/2026-08-15-market-research.md:61-84`). That is a valid `evaluation`-boundary correction under repo doctrine (`.github/copilot-instructions.md:65`).

Scope is minimal and single-purpose: a one-day, no-code research report plus an update to the existing kill-risk record (`feature-requests/FR-803-pipecat-flows-architecture-reassessment.md:24-33`, `:41-42`). A smaller change would only restate the April verdict, which the cited evidence shows answered a different question (`docs/diary/2026-08-15-market-research.md:69-70`, `:84-90`).

The approach aligns with doctrine. It front-loads raw source/examples before docs prose (`feature-requests/FR-803-pipecat-flows-architecture-reassessment.md:28`), matching `read_raw_output_first` (`.github/copilot-instructions.md:115`) and the research mandate (`.github/copilot-instructions.md:230`). It also names the first consumer and event (`feature-requests/FR-803-pipecat-flows-architecture-reassessment.md:7-8`), satisfying the `would_you_use_this` discipline (`.github/copilot-instructions.md:125`).

Prior art is acknowledged rather than buried. FR-359 positioned Pipecat as a distribution channel for YAMLGraph reasoning (`feature-requests/FR-359-pipecat-frame-processor-integration.md:9-15`, `:169-188`); FR-803 requires the report to decide whether that position composes with or conflicts against a Flows-as-control-plane threat (`feature-requests/FR-803-pipecat-flows-architecture-reassessment.md:32`, `:39-40`). That satisfies the repo's prior-art disposition rule in direction, though it needs one mechanical acceptance criterion below.

Strategic classification: **Pattern documentation / research**. This is not a framework primitive or implementation FR; it produces a decision artifact governing whether a foreign runtime threatens or composes with the current governed-pipeline architecture.

## Required revisions

### R-1: Pin the research corpus and source versions

Amend the FR to require the final report to record the exact Pipecat Flows source provenance used for judgement: repository URL, commit SHA or immutable release/tag, and the three example file paths/URLs read end-to-end. The current criterion permits mutable URLs and therefore cannot be rechecked later (`feature-requests/FR-803-pipecat-flows-architecture-reassessment.md:37`).

### R-2: Identify the ninchat_voice mode-switch evidence before translation

Amend the FR to name the exact source artifact for the "mode-switch cluster" or, if the source is outside this repository, require the report to reproduce a bounded transition table extracted from that artifact before attempting the Flows translation. The current phrase "one real ninchat_voice FSM fragment (the mode-switch cluster, ~10 states)" is not enough for an enforcer to know which states/transitions are in scope (`feature-requests/FR-803-pipecat-flows-architecture-reassessment.md:29`). Missing context belongs in the FR, not in the author's chat narrative (`.github/skills/judge-fr/doctrine.md:16-24`).

### R-3: Replace "attempted" with an auditable translation artifact

Amend the paper-translation acceptance criterion so the report must include: source state/transition table, proposed Flows representation or pseudocode, a construct-by-construct mapping table, and an explicit PASS/PARTIAL/FAIL for each required property: static diffable transitions, deterministic non-LLM dispatch, guard/action semantics, and self-hosted execution. "Attempted" is too weak to distinguish analysis from inventory (`feature-requests/FR-803-pipecat-flows-architecture-reassessment.md:38`; `.github/copilot-instructions.md:92`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `docs/diary/2026-08-XX-pipecat-flows-architecture-assessment.md` |
| D-2 | In-place update to kill-risk #3 in `docs/diary/2026-08-15-market-research.md` |
| D-3 | FR-803 status/implementation notes only if the enforcement process normally updates the governing FR |

Not authorized: changes under `yamlgraph/`; changes to `pyproject.toml` or dependencies; new Pipecat integration/demo code; graph or prompt authoring; Pipecat Cloud account/deployment work; CI, hook, judge/review doctrine, or other enforcement-infrastructure changes; re-opening FR-359 implementation scope.

## Revised acceptance criteria

- [ ] AC-01: The assessment report cites the Pipecat Flows repository URL plus immutable commit SHA/tag used for the research.
- [ ] AC-02: The report names at least three real Flows example files/URLs, states that each was read end-to-end before docs prose, and records one concrete surprising detail from each example.
- [ ] AC-03: The report identifies the ninchat_voice mode-switch source artifact or includes a bounded source transition table with approximately 10 states before any Flows translation.
- [ ] AC-04: The report includes a paper translation artifact with source transition table, Flows representation/pseudocode, construct mapping table, and PASS/PARTIAL/FAIL rows for static diffable transitions, deterministic non-LLM dispatch, guard/action semantics, and self-hosted execution.
- [ ] AC-05: The report renders exactly one of THREAT-LIVE, THREAT-DORMANT, or NOT-A-THREAT and cites the specific source/example evidence line or construct mapping row that decides the verdict.
- [ ] AC-06: The report explicitly dispositions FR-359 as COMPOSES, CONFLICTS, or SUPERSEDES, with one paragraph explaining the relation to the `YAMLGraphProcessor` distribution-channel position.
- [ ] AC-07: `docs/diary/2026-08-15-market-research.md` kill-risk #3 is updated with the verdict and a concrete re-check trigger.
- [ ] AC-08: The diff contains zero code, dependency, graph, prompt, CI, hook, or judge/review doctrine changes.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is conditional on R-1 through R-3 being folded into FR-803 before research execution is treated as approved. | GATE |
| C-2 | The enforcer must not use mutable marketing pages as deciding evidence when source/examples are available; decisions must cite source, examples, or immutable docs. | GATE |
| C-3 | If the research cannot access Pipecat Flows source/examples or the ninchat_voice source fragment, enforcement must stop and update the FR as blocked rather than substituting a generic framework comparison. | GATE |
| C-4 | Any conclusion that requires code, prototype integration, vendor deployment, or enforcement-infrastructure change must be parked as a separate FR. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may produce only the no-code architecture assessment and kill-risk update described above.
