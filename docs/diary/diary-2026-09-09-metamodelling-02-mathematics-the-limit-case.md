# Mathematics: the limit case

**Date:** 2026-09-09
**Series:** metamodelling, part 2
**Trigger:** operator: "construct a series of case studies one field at a
time"; the candidate list was ordered by oracle strength and this is the
strongest.
**Context:** part 1 claimed *the delegable surface of a task equals its
verifiable surface*. Mathematics with a proof assistant is the field where
the verifier is complete, so it is where the claim is tested at its edge.

## The field's harness

| Field practice | Framework triple | Note |
|---|---|---|
| Proof assistant (Lean, Coq, Isabelle) | mechanical oracle, complete, at every step | the only domain outside code where the oracle is *total*: a checked proof is correct, full stop |
| Referee | independent human, sees the paper not the author | informal mathematics still runs on this; the assistant is a minority practice |
| Counterexample | reality oracle, instant | one witness kills a universal claim |
| Formal statement | the RED artifact | written before the proof, and the thing the checker actually verifies |

## What the complete oracle does to the generator

When verification is total and cheap, the generator's error rate stops
mattering. Generate a thousand candidates, check them all, keep one. That
is the AlphaProof shape and it is the engineering answer to a generator
without a feedback loop: buy the loop with compute at the oracle, not
with quality at the generator. Part 1's asymmetry does not disappear; it
is priced and paid.

Two things survive the oracle.

**The statement.** Lean checks that the proof proves the *stated*
theorem. Whether the statement is the theorem meant is unverifiable by
construction; the checker has no access to intent. Every formalisation
project reports the same incident: a lemma proved with a quantifier in the
wrong place, a definition subtly weaker than the textbook's, a `sorry`
left in a dependency. The bug surface moves entirely into the
specification. This is `spec_kill` at its purest: the cheapest bug is
the one in the spec because in this field it is the *only* bug left.

**Insight.** A checked proof is correct and may be unreadable. The
oracle certifies truth, not understanding; the diary analog, "why does
this work", is not produced by the verifier and the generator has no
incentive to produce it either. Correctness at scale can arrive without
any human learning anything, which is a new failure class rather than a
solved one.

## Informal mathematics: the referee's gap

Most mathematics is not formalised. The referee reads the paper and the
failure mode is the step marked "obviously" or "it is easy to see". The
generator's fluency is strongest exactly there: a plausible bridging
sentence between two true statements. The referee is an independent
human but reads with the author's framing in the window; input closure
is weak. The field's remedy is slow (errata, retraction, the occasional
decade-long gap before a hole is found). The assistant is the harness
moved to the generation boundary, and its adoption curve is the cost of
formalising the statement, which is again the specification.

## Table for the field

| Boundary | Oracle | Action |
|---|---|---|
| statement written | human review of intent; comparison with informal source | reject before any proof is attempted |
| each proof step | kernel check | fail |
| `sorry` / axiom introduced | grep, mechanical | deny at commit |
| paper submitted | referee, independent, weak closure | advisory |
| claim of novelty | literature search, reference oracle | advisory |

## What the field returns to the framework

1. When the oracle is complete, spend the saved verification budget on
   the specification. Rule 1 of the procedure ("write the falsifiable
   claim") is not a preliminary here; it is the whole job.
2. A total oracle makes generation free and understanding optional. The
   harness must ask for the explanation separately or it will not exist.
3. Compute at the oracle substitutes for quality at the generator. Where
   an oracle is cheap and complete, the correct architecture is
   many-candidates-one-check, not one-careful-candidate.

## Traps

**`verified_but_not_meant`.** The proof checks; the statement was not the
theorem. The oracle was total and the output was still wrong, because the
oracle's input was the wrong claim.

**`correctness_without_residue`.** A verified artifact that leaves no
understanding behind. The next generator starts from zero; the harness
learned nothing.

## Heuristic

If the oracle is complete, review the specification with the care the
proof no longer needs, and require the explanation as a separate
deliverable with its own reader.

**Seed:** this repository's judge checks that acceptance criteria are
testable. Does anything check that they are *the criteria meant*, that
the RED test condemns the bug described in the FR and not a neighbour?
The FR's Ideal Result is the informal statement; the test is the formal
one; the gap between them is where `verified_but_not_meant` lives.
