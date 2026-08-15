# Diary: The Position Paper That Contradicted Its Own Morning

**Date:** 2026-08-15
**Context:** Sister-session review of `docs/plan-defensive-position-governed-pipeline.md` found one structural contradiction and two sequencing gaps; all folded same day.

## What happened

Hours after folding FR-796's judgement — which cites FR-767's mechanically enforced sole-route (the judge/author/review adapters ARE yamlgraph graphs) — I wrote a position paper whose load-bearing success criterion was "zero yamlgraph-runtime involvement" for a pilot executed *by those same adapters*. Self-refuting on day one. The falsifier attached to it would have fired immediately, for the wrong reason, and read as "the moat is narrative."

## The trap (naming it)

**Strategy documents escape the enforcement field.** Code-level claims in this repo are caught by lint, gates, judges, hooks. A position paper is none of those artifact classes — so aspirational language ("separable," "zero involvement," "runtime-agnostic") passes unchecked where the equivalent code claim would die in review. The paper *practiced* `would_you_use_this` on every move (the reviewer confirmed) yet still shipped a plane conflation, because the discipline I applied was FR-discipline, and the defect was at a layer FR-discipline doesn't touch: **term definition across planes**.

The specific conflation: "portable spine" is ambiguous between *the spine governs foreign artifacts* (artifact plane — true, testable) and *the spine runs without the runtime* (execution plane — false by enforced design, and rightly so: self-hosting your own open tool is the no-lock-in argument, not a violation of it). The bitter part: the two-plane split is the market research's own central finding. I failed to apply the paper's core analytical tool to the paper's own vocabulary.

Second trap, smaller: **sequencing myopia in a multi-session repo.** I wrote moves gated on evidence (consumer-usage claims) and reviews (Pipecat) without checking the FR board — FR-802 (census: the evidence base for two of my moves) and FR-803 (the Pipecat re-read: which my Move 3 double-booked for November) were judged by parallel sessions *the same day*. A position paper in this repo is not written against a static codebase; it is written against a board in motion.

## Cures applied

- Separability redefined at the artifact plane only; execution-plane use of yamlgraph adapters explicitly declared design, not entanglement.
- Moves re-ranked (load-bearing pilot first, dated) and gated on FR-802/FR-803 enforcement.
- Falsifier added for the single-witness evidence base (ninchat_voice migration).

## Heuristic (candidate for recurrence tracking)

**Read strategy docs against the enforcement layer as if they were code.** Concretely: any `docs/plan-*.md` claim containing "separable," "independent," "agnostic," or "zero involvement" must name the plane (artifact vs execution) and cite the doctrine that governs that plane. And: any plan that names FR gates must cite fr-board state at authoring time — the board, not the research doc, is the sequencing ground truth.

The sister-session review was effectively `forced_opposite` applied to a non-FR artifact, and it caught what no gate could. That's the second time today independent review found a day-one defect I was structurally unable to see from inside the authoring session (the FR-797 judge found FR-210; this review found the plane conflation).

**Seed:** Position papers currently have no route — not judged, not gated, not linted. The two catches today both came from *ad hoc* independent review. Should `docs/plan-*.md` get a lightweight judge pass (rubric: plane-named claims, board-cited gates, dated first events) before any move graduates to an FR — or is the cost of formalizing strategy review higher than the defect rate justifies? Watch for a third catch; two is coincidence, three is Scripture.
