# Journalism: two sources under a clock

**Date:** 2026-09-09
**Series:** metamodelling, part 5
**Trigger:** series continuation; the rung where the oracle is another
witness and the boundary is a deadline.
**Context:** journalism's oracle is not a text and not a checker; it is a
second, independent origin for the same claim. The field also runs its
harness under a clock, which is where every harness reveals what it does
when it is expensive.

## The field's harness

| Field practice | Framework triple | Note |
|---|---|---|
| Two-source rule | independence of oracles | two origins, not two mentions |
| Fact-checker | outsider with partial input closure | works from the extracted claims, not the narrative |
| Editor | judge | reads for the story; a different question than the checker's |
| On-the-record / anonymous | provenance typing | the source's type selects how much weight the claim may carry |
| Corrections column | diary | public, dated, and rarely graduated into the style guide |
| Style guide | Scripture | slow to change; the field's graduation pipeline is informal |
| Publish | irreversible boundary | on the network, the retraction never catches the original |

## Independence is traced, not counted

The rule says two sources. The failure the rule exists to catch is the
one where two outlets report the same claim because both copied one press
release, one wire story, one tweet. Two mentions, one origin. Counting
gives two; tracing gives one.

This is the field's version of `are_the_witnesses_one_phenomenon`, and it
transfers directly to LLM harnesses. Two runs of the same model on the
same prompt are one witness. A judge and a reviewer on the same model
family with the same doctrine in context share an origin more than their
separate names suggest; part 1 called the substitute *separation of
context* and this field says how partial that is. The independence of a
verifier is a claim to be traced back to its origin, not a property
conferred by giving it a different role name.

## Where the generator fails in this field

- **Fluency read as credibility.** Well-formed prose in the register of
  reporting is what a report looks like. The reader's shape gate passes.
- **Single-source amplification.** One claim, restated three ways in
  three paragraphs, reads as corroborated. Entropy proxy: distinct-origin
  count per claim, not sentence count.
- **The quote that does not exist.** Quotation is fact-typed (part 4);
  the generator produces plausible quotes for real people. Oracle: the
  quote resolves to a recording, transcript, or document, or it is not a
  quote.
- **Anonymous by default.** "Sources say" is the generator's cheapest
  bridge; the field permits anonymity only with editor sign-off and a
  known identity. Provenance typing at the boundary: every source claim
  carries on-record / background / anonymous, and anonymous requires a
  named approver.

## The clock

Every field's harness is a set of checks that cost time. Journalism is
the field that has made the trade-off explicit: the deadline is the
boundary and the checks that survive it are the ones that were made
cheap. Under the clock, the harness collapses toward the mechanical rungs
(does the quote resolve, does the name spell, does the number match the
document) and away from the expensive ones (is the framing fair, is the
second source really independent).

This is the honest description of what any harness does under pressure.
The lesson is not to remove the clock; it is to know in advance which
checks are load-bearing and make *those* the cheap ones. A harness whose
load-bearing check is the expensive one will drop it first.

## Table for the field

| Boundary | Oracle | Action |
|---|---|---|
| claim drafted | origin recorded (who, when, how obtained) | deny unrecorded |
| second source added | origin differs from first, traced | reject if same origin |
| quote inserted | resolves to recording/document | deny |
| anonymous source | approver named | deny without |
| draft complete | fact-checker, claims only | block on unresolved |
| deadline | editor | publish / hold |
| post-publication | corrections; reader letters | amend, and the diary entry |

## What the field returns to the framework

1. **Independence must be traced to origin.** Counting confirmations is
   counting mentions. For LLM verifiers: name what the judge shares with
   the author (model, doctrine, prompt lineage) and treat the shared part
   as one witness.
2. **Under pressure the harness keeps its cheap checks.** Design so the
   load-bearing checks are the cheap ones. If a check is both essential
   and expensive, it will be the first one skipped, and the harness's
   real behaviour is the behaviour under deadline.
3. **Provenance is a type.** Where a claim came from selects how much it
   may carry. Untyped provenance is the strictest type, as in part 4.

## Traps

**`counted_not_independent`.** N confirmations from one origin. The
harness reports N; the world has 1.

**`load_bearing_and_expensive`.** The check that matters most is the one
that costs most, so under the clock it is the one dropped. The harness's
published shape and its deadline shape differ exactly there.

## Heuristic

Before accepting N confirmations, trace each to its origin and collapse
duplicates; the count is the number of origins. Before trusting a
harness, list which checks it keeps at deadline; those are the harness.

**Seed:** the judge, reviewer, and outsider in this repository are three
roles. How many origins are they? Same model family, same Scripture in
context, prompts descended from one template. A one-time trace of what
each shares with the author's session would give the real witness count.
