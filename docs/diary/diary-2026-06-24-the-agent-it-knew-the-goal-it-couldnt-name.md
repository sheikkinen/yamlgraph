# The Agent It Knew, The Goal It Couldn't Name

*2026-06-24 — FR-577 L6 assign-causality spike*

## What happened

L6 assigns causal structure to classified beats: `enables` (the causal
backbone), `motivation` and `threatens` ({agent, goal} pairs). The gate was
`enables` recall ≥ 0.75. The spike returned **0.96** — a clean GO on the first
run, with precision 0.93 (only 3 invented edges). The forward-only validator
(J:C2) and the prompt's "FORWARD ONLY" rule held: no backward links survived.

The interesting result was in the *informational* slices, the ones J:C3 said
must not carry the verdict:

| slice | agent+goal recall | agent-only recall |
|---|---|---|
| motivation | 0.26 | 0.83 |
| threatens | 0.00 | 0.81 |

The model knew *who* almost every time. It could not name *what they wanted* in
the corpus's words — and for `threatens`, never once cleared the 0.34 Jaccard
bar.

## The trap I almost fell into

The naive read of `threatens_recall: 0/26 (0.00)` is "the model can't do
threatens — KILL the slice." That reading conflates two failures that live at
different boundaries:

1. **comprehension failure** — the model doesn't understand who is threatened;
2. **vocabulary failure** — the model understands perfectly but phrases the
   goal differently than the ground-truth author did.

A single recall number cannot tell them apart. The *agent-only* recall is the
disambiguator: 0.81 says comprehension is intact; the 0.00 full-match says the
goal *tokens* diverge. Had I reported only the combined recall, I'd have
mislabelled a wording problem as a reasoning problem — and possibly "fixed" a
prompt that wasn't broken.

## The heuristic

> When a composite metric (agent **+** goal) collapses, decompose it before you
> diagnose. Report the cheapest sub-signal separately. A high agent-recall under
> a zero goal-recall is not "the model failed" — it is "the model succeeded in a
> vocabulary you didn't score it in." The confusion lives in the denominator you
> didn't split.

This is the same boundary FR-583 already named: goal phrases are free-form, so
exact equality is a category error (J:C1). L6 confirms it with a second witness —
the agent attribution is a *referential* match (exact, like beat IDs), the goal
is a *generative* match (tolerant, like invented predicates). Scoring them with
one number erases the seam between them.

## What carried the verdict, and what didn't

The gate was `enables` — a referential match on canonical beat IDs, no tolerance
needed, and it scored 0.96. The informational slices flagged a real but
out-of-scope gap and pointed forward without blocking. J:N2 (threshold triggers,
confusion carries the verdict) did exactly its job: GO on the backbone, a logged
forward-signal on the vocabulary.

## Seed

The agent-only recall worked here because "agent" is a closed, referential set.
What is the analogous *cheapest referential sub-signal* for the goal itself —
could we ground goals against the L2 goal-extraction output (a per-story closed
vocabulary) instead of free Jaccard, turning the generative match back into a
referential one? If L2 goals become the lexicon L6 must draw from, does
`threatens_recall` jump from 0.00 the same way `enables` did — and at what cost
to the model's expressive freedom?
