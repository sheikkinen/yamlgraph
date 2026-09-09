# Strategy: the oracle that arrives late

**Date:** 2026-09-09
**Series:** metamodelling, part 7
**Trigger:** series continuation; the bottom rung, where the only oracle
is reality and reality is years away.
**Context:** strategic and business decisions have no compiler, no
catalogue, no second source that settles anything. The outcome arrives
late, confounded by everything that happened in between, and the field's
own name for the resulting error is *resulting*: judging the decision by
the outcome. This is the field where part 1's corollary predicts the
least delegation, so it is where the prediction is tested.

## The field's harness

| Field practice | Framework triple | Note |
|---|---|---|
| Decision journal | **RED for decisions**: the prediction, its probability, and its reasoning written before the outcome | the only way to score a decision independently of its result |
| Pre-mortem | imagined failure, written before commitment | "it is two years on and this failed; why?" |
| Base rates, reference class | reference oracle, the outside view | what happened to the last hundred plans of this shape |
| Red team, devil's advocate | adversarial outsider | assigned, not volunteered |
| Assumption register | traceability | decision → assumptions → the evidence for each |
| Post-mortem, after-action review | diary | frequently written; rarely reread against the journal |
| Outcome | reality oracle, delayed and confounded | arrives after the decision-maker has moved on |

## When the oracle is late, independence is temporal

Every previous part found independence in a *different party*: a
checker, a database, a second source. Here there is none available at
decision time. The only independence left is between the decision-maker
now and the world later, and the only way to make that independence
useful is to pre-commit the prediction so the later outcome can score
something specific.

A decision journal entry is therefore exactly a RED test: a falsifiable
statement, dated, written before the output exists, that the future can
mark pass or fail. Without it the future outcome scores nothing, because
any outcome can be rationalised against an unwritten expectation. With
it, the harness learns even though the decision-maker will have
forgotten why they decided.

## Where the generator fails in this field

- **Unfalsifiable strategy.** Fluent, structured, every option sounds
  right, no sentence could be embarrassed by any outcome. The generator's
  training distribution is heavy with strategy prose that was written to
  sound wise, and it reproduces the register.
- **The generic plan.** Regression to the mean of the corpus. The output
  is the strategy that every comparable organisation already has, which
  is by construction not a strategic advantage.
- **Confidence without base rate.** "This will capture the market" with
  no reference class. Reference oracle exists (what fraction of entrants
  of this shape did); the generator does not consult it unless the
  boundary demands it.
- **Consensus as evidence.** "Industry experts agree." The journalism
  trap (part 5) in a suit.

## The corollary, tested

Part 1: *the delegable surface equals the verifiable surface.* Here the
verifiable surface at decision time is: the assumptions are listed; each
has a stated evidence rung; the base rate is cited; a dated, falsifiable
prediction exists; the pre-mortem is written. All of that is
verifiable *now*, mechanically or by a reader. The decision itself is
not.

So the prediction holds: the generator may produce the option list, the
assumption register, the pre-mortem draft, the reference-class search,
and the journal entry skeleton, and every one of those is checkable at
the boundary. It may not produce the decision, because there is no oracle
for it at any price until the world reports back. Delegation stops
exactly where verification stops, and this field makes the line visible
because nothing blurs it.

## Table for the field

| Boundary | Oracle | Action |
|---|---|---|
| option drafted | assumption register present, each assumption with a rung | deny without |
| claim of outcome | base rate cited from a named reference class | flag |
| decision proposed | dated falsifiable prediction with probability | deny commitment without |
| before commitment | pre-mortem written; red team read | block until |
| commitment | human | the decision; not delegable |
| scheduled reread (6, 12, 24 months) | journal entry against outcome | score; amend the harness |

The last row is the one most fields skip. A journal never reread is a
diary never graduated: the harness recorded but did not learn.

## What the field returns to the framework

1. **Where no external oracle exists, pre-commit the prediction.**
   Temporal independence substitutes for party independence. The
   prediction must be dated, specific, and able to embarrass.
2. **Schedule the reread.** Rule 7 (route failures to the harness)
   assumes the failure is noticed. Late oracles are not noticed unless a
   calendar fires. The scheduled reread is the hook for the late oracle.
3. **Delegation stops at the draft.** Where verification stops, the
   generator's output changes category from deliverable to draft, and the
   harness should label it so. A draft presented as a deliverable is
   `type_costume` (part 4) at the level of the whole artifact.
4. **Resulting is the harness's own bias.** Scoring the decision by the
   outcome trains the harness on noise. The journal is what lets the
   harness score the *reasoning* against the outcome instead.

## Traps

**`unfalsifiable_strategy`.** Output no outcome could contradict. Passes
every reader; teaches nothing; is what the generator produces by default
in this register.

**`journal_without_reread`.** The prediction was written and never
scored. The RED test that was never run.

## Heuristic

No strategic claim without a dated prediction that could embarrass it,
and no prediction without a scheduled reread. Where the oracle is late,
the harness is the calendar.

**Seed:** every FR in this repository states an Ideal Result before its
Proposed Solution (FR-746). That is a decision-journal entry. Is there a
scheduled reread that scores the Ideal Result against what shipped, or
does the harness write the prediction and never run it? The recap graph
(FR-1027) reads the week's PRs; a rung above it would read the quarter's
Ideal Results.
