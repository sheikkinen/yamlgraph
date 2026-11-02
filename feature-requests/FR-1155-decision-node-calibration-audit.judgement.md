# Judgement: FR-1155 Decision-node primitive with calibration audit and hello demo

**Verdict:** APPROVED WITH REVISIONS — the framework direction is sound, but authority activates only after the FR supplies the mandatory raw-output evidence, closes the backend/schema decisions, and turns the calibration claim into a mechanically testable contract.

**Prior art:** `FR-1155-decision-node-calibration-audit.md` — the FR under judgement (mechanical self-hit, no disposition owed); FR-588/FR-589 dispositioned in the FR body and affirmed here; FR-532, FR-722, FR-995, FR-1001 retrieved by the research record and ordered dispositioned by R-5 before authority.

**Reviewed against:** `feature-requests/FR-1155-decision-node-calibration-audit.md`; `feature-requests/FR-1155.research.md`; `feature-requests/research-briefs/fr1155-decision-node-calibration-brief.md`; `docs/2026-11-02-research-typesafe-system-one-jev.md`; `feature-requests/FR-588-llm-scored-prompt-abstraction-span.md`; `feature-requests/FR-589-abstraction-span-standalone-example.md`; `feature-requests/FR-761-reproducible-dependency-governance.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.md`; `capabilities/CAP-03-node-execution.yaml`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is concrete rather than vendor-led: the FR identifies routing, guard, census, verdict, and game-loop consumers (`FR-1155` L30-L48), while the committed census distinguishes pure decision shapes from hybrids instead of claiming universal fit (`docs/2026-11-02-research-typesafe-system-one-jev.md` L147-L175). That supports **framework primitive** classification: there are more than three distinct use cases, and the `state` + named-questions call shape is materially different from the existing chat structured-output surface (`FR-1155` L136-L141).

The proposed architecture follows repo law: one factory boundary, Pydantic normalization at ingress, no provider imports in node code, network-free mock tests, sync/async parity, and graph-native demonstrations (`FR-1155` L94-L108, L136-L152). The calibration audit and smart-if graph are witnesses for the same responsibility—safe consumption of decision-provider confidence—rather than unrelated product features. FR-588's rejected Python-orchestration path and FR-589's graph-native correction are correctly recognized (`FR-1155` L183-L195).

The research record preserves genuine disagreement and answers `is_this_a_graph` rather than merely listing one preferred design (`FR-1155.research.md` L15-L21). The ideal result is also appropriately narrower than replacing generative nodes: the evidence explicitly says hybrids dominate and free-text rationale remains on the LLM path (`docs/2026-11-02-research-typesafe-system-one-jev.md` L152-L175, L203-L210).

## Required revisions

### R-1: Commit and cite the mandatory raw-output read

Before authority, add a committed, sanitized artifact containing the 10 raw responses already promised by the plan (`FR-1155` L62-L67) from the selected non-mock backend. Read them before designing the reducer. Amend the FR with a table that cites each sample and records at least one concrete, sample-specific surprise or boundary observation per response. The current evidence expressly says vendor claims were not independently measured (`docs/2026-11-02-research-typesafe-system-one-jev.md` L5-L9), so planned future reading does not satisfy the measurement-FR gate in `.github/skills/judge-fr/doctrine.md` L114-L117 or `.github/copilot-instructions.md` L210.

### R-2: Close the backend and response-contract branches before enforcement

Replace the unresolved “optional dependency or thin internal client” branch (`FR-1155` L63-L70, L167-L169) with one selected implementation. Record the FR-761 governance result if `system-one-adapter` is selected; otherwise specify the exact public request/response contract the internal client implements and why adding that client is smaller than the governed dependency.

Add a per-question-kind contract table for `choice`, `score`, and `noul`: required YAML fields, answer type, probability shape, confidence presence/type, and validation failures. Base it on the committed raw samples and SDK/source evidence. The current plan acknowledges that a question type may lack confidence (`FR-1155` L69-L70) while the node contract and acceptance criteria promise confidence uniformly (`FR-1155` L16-L19, L163-L164); that contradiction must be removed.

### R-3: Specify the calibration algorithm and its condemning fixture

Define the audit input schema, sample count, confidence buckets, bucket-boundary rule, empty-bucket behavior, expected calibration error formula, and serialized reliability-table shape. Define a deterministic planted-miscalibration fixture with a hand-computed expected table and ECE, plus an explicit configured threshold that the fixture exceeds. Require tests for both a flagged fixture and a non-flagged calibrated fixture. “N labeled items” and “must flag it” (`FR-1155` L145-L149, L170-L172) are not sufficient to derive failing tests.

### R-4: Narrow “mandatory gate” to the surface actually proposed

Amend the Summary, Ideal Result, and first-consumer language so the calibration audit is a documented operator gate for onboarding a provider, not a runtime prohibition. The proposed implementation contains a demo and reducer but no provider-certification store or execution guard (`FR-1155` L7-L11, L50-L57, L143-L152). This FR does not authorize such enforcement machinery. The README must state that confidence-based production routing is unsupported until the operator runs the audit against representative labeled data and records the result.

### R-5: Disposition every retrieved precedent

Add explicit relevance/disposition entries for FR-532, FR-722, FR-995, and FR-1001, which the committed research retrieved but the FR omits (`FR-1155.research.md` L8-L13). Retain the existing FR-588/FR-589 disposition. For each record, state what constraint is inherited, what surface is distinct, or why the match is irrelevant. Prior art must be dispositioned before authority under `.github/skills/judge-fr/doctrine.md` L114-L117.

### R-6: Replace the acceptance criteria with the revised criteria below

Fold the exact criteria below into the FR. Remove the current branch-shaped dependency criterion and vague calibration criterion. Record the selected requirement ID instead of `REQ-YG-XXX`, and make the two authoring-route witnesses distinguishable in the implementation record.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Typed `decision` node configuration and per-kind validation for `choice`, `score`, and `noul` |
| D-2 | One decision-client protocol/factory, deterministic mock backend, and exactly one selected non-mock backend |
| D-3 | Pydantic-normalized decision response models and equivalent sync/async execution |
| D-4 | Node registration, lint integration, import-boundary contract, requirement traceability, and unit tests |
| D-5 | `examples/demos/calibration-audit` graph, reducer, deterministic fixtures, README, and recorded smoke |
| D-6 | `examples/demos/smart-if` graph, README, and keyless mock-provider smoke |
| D-7 | Dependency-governance artifacts if required, authoring-route evidence, and changelog fragment |

Not authorized: native Jev integration; migration of existing examples; replacement or modification of FR-998's chat structured-output policy; automatic provider certification or runtime blocking of confidence access; CI, hook, judge, or review-pipeline integration; latency, cost, or calibration claims not measured by this FR; additional decision-provider backends; confidence-ladder, guardrail, census A/B, NPC, or other follow-on demos.

## Revised acceptance criteria

- [ ] AC-01: A committed artifact contains 10 sanitized raw responses from the selected non-mock backend, and the FR cites all 10 with one sample-specific boundary observation each.
- [ ] AC-02: The FR names exactly one non-mock backend and records either its completed FR-761 governance result or the exact thin-client contract and rationale.
- [ ] AC-03: A per-kind contract table defines required fields and typed response fields for `choice`, `score`, and `noul`; unit tests accept every valid kind and reject unknown kinds, missing required fields, and choice cardinality above 255.
- [ ] AC-04: Decision responses cross the provider boundary as Pydantic models with the documented answer, probabilities, and confidence contract; tests prove raw provider dictionaries do not enter graph state.
- [ ] AC-05: The `decision` node registers and executes the same request and normalized result through sync and async paths against the deterministic mock backend.
- [ ] AC-06: A unit test proves a graph condition branches on the documented confidence field, and all decision tests carry the selected `@pytest.mark.req(...)` marker.
- [ ] AC-07: Provider-specific imports exist only in the selected backend/factory boundary; `lint-imports` and any FR-761 direct-import/dependency checks pass.
- [ ] AC-08: The calibration reducer has a documented bucket rule, empty-bucket rule, ECE formula, output schema, and configurable pass threshold; unit tests assert the exact table and ECE for deterministic calibrated and planted-miscalibrated fixtures.
- [ ] AC-09: `examples/demos/calibration-audit/graph.yaml` lints and completes a keyless mock-provider smoke; its output flags the planted fixture and its README records the exact command and observed result.
- [ ] AC-10: `examples/demos/smart-if/graph.yaml` lints and completes a keyless mock-provider smoke that visits both conditional branches across deterministic fixtures; its README contains the exact quickstart.
- [ ] AC-11: Each demo is authored through `scripts/author.sh`; the implementation record identifies the target and verdict from each distinct `tmp/draft-authoring-report.md` run.
- [ ] AC-12: `python scripts/req_coverage.py --strict`, the targeted unit tests, and the non-slow unit suite pass.
- [ ] AC-13: The FR implementation record states that calibration is an operator onboarding gate only and that no runtime certification/enforcement mechanism was added.
- [ ] AC-14: A changelog fragment exists in `changelog/unreleased/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-6 are folded into the FR before production code or governed graph artifacts are authored. | GATE |
| C-2 | The selected non-mock backend and per-kind response contract are fixed from committed evidence; the enforcer must not choose between alternative designs during implementation. | GATE |
| C-3 | The calibration algorithm must be condemned by deterministic exact-value tests before implementation of the passing reducer. | GATE |
| C-4 | Both demo graphs must use the sole graph-authoring route and retain distinct run evidence. | GATE |
| C-5 | No code may claim or enforce provider calibration beyond the exact datasets and threshold exercised by the audit. | GATE |
| C-6 | Any automatic certification, CI/hook gate, judge/review integration, or migration of existing graphs requires a separate judged FR. | GATE |

Authority granted: after the revisions are folded, implementation may add the frozen decision-node primitive, one factory-selected real backend plus mock, and the two graph-native witness demos—nothing beyond the surfaces listed above.
