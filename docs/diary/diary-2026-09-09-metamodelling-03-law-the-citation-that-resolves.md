# Law: the citation that resolves

**Date:** 2026-09-09
**Series:** metamodelling, part 3
**Trigger:** series continuation; second rung down from the complete
oracle.
**Context:** law has the strongest *reference* oracle of any prose field
(statute, precedent, the filed record) and, less noticed, a mechanical one
that was available the whole time. The field also produced the canonical
LLM incident, which makes it the cleanest test of where a harness fails.

## The field's harness

| Field practice | Framework triple | Note |
|---|---|---|
| Citation to statute or case | reference oracle | the claim is checkable against a fixed external text |
| Citation resolves in a reporter/database | **mechanical oracle** | exists or does not; cheap; no judgement required |
| Defined terms ("Company", "Effective Date") | linter | every capitalised term defined once, used consistently: a type checker for contracts |
| Opposing counsel | adversarial outsider, by profession | reads only the filing, motivated to find the gap |
| Jurisdiction | platform boundary | the same words carry different meanings across systems; the OS-difference class |
| Judge | human oracle, final | expensive, late, and the one who found the incident |
| Malpractice, sanctions | harness learning at institutional scale | slow, punitive, effective |

## The incident

*Mata v. Avianca* (S.D.N.Y. 2023). A brief cited six cases that did not
exist. The generator produced them with real judges' names, plausible
reporter volumes, and internally consistent quotations. When the drafter
grew suspicious he asked the same generator whether the cases were real;
it affirmed they were. The court found the fabrication after filing.

Read against the table, three things stand out.

**The mechanical oracle existed.** Every one of those citations could
have been resolved in a database in seconds. The cheapest rung was
available and unused.

**It fired at the wrong boundary.** The check that eventually ran was the
judge's, after filing, at the most expensive and least reversible point.
The harness was a post-mortem.

**The self-check was not a check.** Asking the generator to verify its
own output is a verifier with the same weights *and* the same context,
including the fabrication as an anchor. It is part 1's asymmetry restated
as a dialogue. This is the failure mode a future user of any LLM is most
likely to repeat, because it feels like diligence.

## Where the generator fails in this field

- Fabricated authority with correct form: the signature failure. The
  shape gate (looks like a citation) passes; the substance gate (resolves)
  was never run.
- Jurisdiction drift: a correct rule from the wrong system. Reference
  oracle exists; the generator does not know which jurisdiction it is in
  unless told at the boundary.
- Defined-term drift in long contracts: "Services" in clause 3,
  "the services" in clause 41. Mechanical, and the field already lints
  it in commercial drafting tools.
- Quotation drift: a real case, a paraphrase presented as a quote. Needs
  the page-level reference oracle, not the existence check.

## Table for the field

| Boundary | Oracle | Action |
|---|---|---|
| citation typed | resolves in database (mechanical) | **deny** the draft until resolved |
| citation quoted | page-level text match (reference) | flag |
| defined term used | defined-once, consistent-case (linter) | block at draft save |
| jurisdiction stated | required field at draft start | deny start without it |
| draft complete | opposing-counsel read, input closure | advisory |
| filing | court | irreversible; should never be the first oracle that fires |

## What the field returns to the framework

1. **The cheapest available rung must fire at the earliest boundary.**
   A harness whose first firing oracle is the most expensive one is not a
   harness; it is an incident report waiting for its incident.
2. **The generator is never its own oracle.** Same weights, same
   context, same anchor. Any "are you sure?" protocol is theatre unless
   the second pass has different inputs.
3. **Form is the attack surface.** A generator that has learned the form
   of authority produces authoritative-looking output by default.
   Substance checks must be mechanical where they can be, because the
   human eye is tuned to form.

## Traps

**`generator_as_own_oracle`.** Re-asking the model that produced the
claim. Feels like diligence; adds no independence.

**`last_boundary_first_oracle`.** The only verifier that runs is the one
at the irreversible boundary. The harness's existence is proven by its
failures.

## Heuristic

Enumerate the oracle rungs available for the artifact; for each, name
the earliest boundary it could fire at; then check whether it actually
fires there. Every rung that exists but fires only at the end is a
scheduled incident.

**Seed:** this repository resolves FR numbers, REQ IDs, and CAP files as
cross-references. Which of those checks fire at pre-commit, which only at
CI, and which only when a reader notices? The *Mata* table applied to our
own references would show the rungs that exist but fire late.
