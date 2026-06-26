# Diary — 2026-06-26 — The distractor that lowered the ceiling

## What happened

FR-607 refuted goal-anchoring with a flat goal LIST (honest lift +0.000). Its autopsy
named the mechanism — the goal label is *downstream* of the close-beat choice — and an
upstream read confirmed L6 already distinguishes the sibling goals via the beat
`enables` chain. FR-609 hypothesized that injecting that chain as a beat-free goal
*causal graph* (the relations the flat list stripped) would let the model pick the
right sibling and finally move the frozen gate.

It did not. On the CLEAN (branching) subset — genres where the referent goals form an
antichain so chain order cannot leak placement — the GT-graph ceiling moved placement by
**+0.000**. And referent binding *fell* to 0.083 from FR-607's 0.143: the richer
structure made the model bind the wrong sibling **more** often.

## The trap: richer_context_as_signal

I assumed more structure = more signal the model would use. The opposite happened. The
inter-goal `enables`/`threatens` edges are genuine information (Open Q3 was right that
they are materially more than a flat list) — but to *this* model on *this* task they are
**distractors**, not disambiguators. The model's referent choice is salience-driven; it
reads the close beat first, then names whatever goal that beat serves. Handing it more
goals-and-relations to read just gives it more surface to misread. **Signal that exists
in the injection is not signal the model uses.** The only way to know which is to measure
the ceiling, not to reason about information content.

## What made the REFUTED interpretable: the Topology Pre-Check

The Judge's correction 1 (order-leak: a total-order goal graph leaks placement even
beat-free) could have made a null uninterpretable — "maybe the graph would help on a
genre where order can't carry it." Deriving the topology of all five fixtures *before*
running (3 branch, 2 linear) pre-registered a CLEAN subset where order carries nothing.
The +0.000 there is unconfoundable: the graph is the only discriminator and it did
nothing. Pre-checking the experimental geometry turned a soft null into a hard close.

## The mechanism number that closed it: close-beat shift

Close-beat shift 0.367 with *identical* placement recall is the J-corr-2 measurement
earning its place. The model reshuffles a third of its close-beat picks between arms as
pure salience noise around an unchanged accuracy. That is the salience→referent arrow,
measured. Without it the +0.000 is a result; with it, it is a mechanism.

## Heuristic

> **measure_the_ceiling_not_the_information.** Before claiming a richer injection will
> help, run the GT-ceiling arm on the order-clean subset. "It contains more signal" is a
> statement about the data; "the model uses it" is a statement about the model, and only
> the ceiling measures the second. A richer injection that lowers the anchoring number is
> proof the added structure is distractor, not discriminator.

## Seed

The whole FR-596→609 arc moved the referent label and never the gate, because the label
rides on the beat choice. **Seed:** what is the cheapest intervention on the
*beat-selection* step itself — not the annotation downstream of it? If the model picks
the close beat by salience, does forcing it to *first* commit to a beat-pair span (open
AND close together, before any goal/affect naming) change the placement, where every
post-hoc relabel has failed?
