# The Premise the Judge Killed Before the Harness Was Built

*2026-06-21 — FR-553, DM v2 turn-director prompt salience*

## What happened

The chain ran: roll back the World Codex (FR-550), check the post-rollback run (10035-BC,
continuity 1/5), read the LangSmith traces, and ask the honest question — *are we doing too
complicated LLM ops for the small model?* That question became FR-553. I wrote it as an
investigation: build a harness to measure turn-director prompt mass and correlate it with the
continuity failures, then a follow-up FR would fix whatever the harness found.

Then I judged my own FR. And judging it — recomputing `running_scene` offline, splitting the
LangSmith trace by child call — falsified its headline premise *before any harness existed*. The
"~12.3k-token director prompt" was never the director's. It was the whole turn graph's five-call
sum, dominated by three intent sub-calls (7,575 tok). The director's actual scene was ~1.6k. The
premise that the small model was drowning in an over-large director prompt was simply false, and
the cheapest possible measurement — one I had to do anyway to write the judgement — proved it.

The conditions (C1–C5) then reframed the whole investigation: measure three *separate* quantities
(never attribute the 12k to the director), source the mass deterministically (not from optional
LangSmith), and — the decisive turn — replace the weak "mass dilutes salience" hypothesis with a
sharp one: **was the governing fact's subject present in the scene at the failing turn?** When the
harness ran on real data, both Arnulf breaks came back *present-but-ignored* — zero presence gaps.
The fact was in front of the model and got ignored. So the fix is not bounded-prompt or re-ranking
(the FR's own deferred fix); it is wording or the recap/narrator dropping a fact it was handed.

## The trap

**`research_as_inventory`'s cousin: the investigation that pre-commits to its own fix.** I framed
FR-553 around a remedy ("the next FR will pin a priority block") before measuring whether the
defect it remedies exists. That is the FR-548 mistake wearing a lab coat: FR-548 *added* grounding
on an unmeasured premise; FR-553 nearly *built a harness* on an unmeasured premise, with the fix
already named. The discipline that saved it was treating the FR as a junior PR and judging it
against live code — which, for an investigation FR, means *doing the cheap measurement during the
judgement*. The judge step is not paperwork; it is the first and cheapest run of the experiment.

## The heuristic

**Judge an investigation FR by running its cheapest measurement, not by reviewing its plan.** An
investigation's premise is a hypothesis; the judgement is the first place to test it. If the
quantity is recomputable offline in one Python snippet, recompute it before granting authority — the
spec-kill (Commandment: the cheapest bug is the one killed in the spec) applies doubly to FRs whose
entire deliverable is measurement. A harness built to confirm a falsified premise is dead code
shipped green.

Corollary, already folded into C5: an investigation must name *both* outcomes mechanically before it
runs (presence-gap → fix A; present-but-ignored → fix B), so the result redirects effort instead of
rationalizing the pre-chosen fix.

## Seed

The harness now emits `present_but_ignored_count` as a target FR-545 must drive toward zero. But
"ignored" is inferred from *subject token presence* in the opening scene — a necessary, not
sufficient, condition for salience. **What is the deterministic signal for a fact that is present
*and* salient yet still contradicted downstream — i.e. how do we measure the gap between what the
director was told and what the `recap`/narrator actually wrote, without an LLM in the witness?**
