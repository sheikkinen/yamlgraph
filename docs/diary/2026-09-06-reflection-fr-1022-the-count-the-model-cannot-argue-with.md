# Reflection: the count the model cannot argue with — FR-1022

**Arc.** The operator asked whether a judge *prompt* change — "refuse if the
document has been judged before" — would stop sessions spiralling in judge
loops. The answer that shipped is not a prompt change: `scripts/judge.sh`
counts `**Verdict:**` lines in the adjacent judgement and, at two, writes the
operator's sentence itself and exits 77. One brief, one research run, one
judgement round, one fold, RED, GREEN. FR-1022 was judged once.

## What the raw record says

FR-1013's judgement file: four `**Verdict:**` lines. Its diary already named
the mechanism (`rigor_as_surface_area`: findings ∝ text read; folding adds
text) and planted a Seed asking the wrapper to *print* the round number so the
human could say stop sooner. The operator's instruction went one step past
the Seed: not print — *stop*. "Third judgement is always following, no LLM."

The judge's own round-1 finding on this FR was instructive: I had invented a
fifth verdict token (`REWRITE`). The taxonomy is closed; the judge said use
`REJECTED`. That is exactly the shape the sentinel enforces on everyone else —
a fixed vocabulary is a fixed vocabulary — and I had drifted out of it in the
FR that installs the fixed vocabulary. Folded, one round.

## The trap

**`prompt_as_mechanism`.** When the failure is "the model always produces a
plausible answer", the reflex is to give the model a better instruction. But
an instruction to refuse is consumed by the same component whose consumption
is the problem. The judge prompt is a thin pointer by invariant (NC-412), and
the re-entry guard already showed the working pattern: doctrine *states*,
wrapper *enforces* (NC-414's `JUDGE_EXECUTION`). A termination condition
belongs where the model cannot read it as a suggestion — in the shell, as an
integer.

Sub-trap, from the research run: four personas agreed on the class (wrapper
boundary enforcement) and split on the threshold (block at 2 vs block at 1).
My first research-record header wrote "convergent" over the split. The judge
caught it (R-4). Convergence on *where* is not convergence on *how much*;
the record must carry the disagreement or it is a shape-check.

## Heuristic

For any loop whose body is a model call, ask: what is the terminating
predicate, and can the model influence it? If the predicate is the model's own
verdict, the loop has no fixed point. Move the predicate to a count the model
cannot alter — file lines, invocations, bytes — and make the cap's message the
human's words, so the agent hears the operator, not another reviewer.

Second: the judge's round-1 finding against my own drift out of the closed
taxonomy is the cheapest possible test of the design — the sentinel's message
is `REJECTED` because the judge refused `REWRITE`. When a gate you are
installing fires on the FR that installs it, that is the gate working.

**Seed:** the sentinel counts *judge* rounds. FR-1013 also had three *review*
rounds, and the review→judge ping-pong (a review finding of scope creep
triggering a re-judge) is the other half of the loop. Does `scripts/review.sh`
need the same integer — and what is its fixed sentence?
