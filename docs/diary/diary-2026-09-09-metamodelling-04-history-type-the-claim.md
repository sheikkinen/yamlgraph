# History: type the claim

**Date:** 2026-09-09
**Series:** metamodelling, part 4
**Trigger:** the operator's own example: "how would the framework look
like in history".
**Context:** history has a reference oracle (the sources) but no reality
re-run: the past cannot be executed. It also produces artifacts in which
three different kinds of claim share one grammar, which is the property
that makes it the best case for *normalising at the boundary*.

## The field's harness

| Field practice | Framework triple | Note |
|---|---|---|
| Footnote | traceability, claim → source | the humanities' requirement traceability matrix, older than the term |
| Archive, edition, catalogue | reference oracle | the source exists and says what is claimed; two checks, not one |
| Peer review | independent human, weak input closure | reads with the author's framing in view |
| Historiography | the diary | the field's record of how its own conclusions changed and why |
| Errata, revised edition | harness learning | slow; decades |
| Source criticism | oracle on the oracle | who wrote this, for whom, with what to gain: provenance as a check on the reference |

The field has run this harness for centuries. What it does not have is
any of it firing at the moment of composition. Everything fires at
publication or after.

## Three claims in one grammar

"The treaty was signed in March." "The treaty was a mistake." "Had the
treaty failed, the war would have come earlier." Same sentence shape,
three epistemic types, three different oracles, and the failure the field
cannot forgive is one type wearing another's costume: an interpretation
stated as a fact, a counterfactual stated as an interpretation.

The generator does this by default. Trained on prose that mixes the
three, it produces the mix, and its fluency is highest exactly where the
type is most ambiguous. So the first move is `the_one_law`: normalise at
the boundary where the claim enters, by typing it.

| Type | Oracle | Boundary action |
|---|---|---|
| **fact** (date, name, number, quotation) | 1. source resolves in a catalogue (mechanical). 2. source says that, page-level (reference) | deny any untyped or unanchored fact |
| **interpretation** | none for truth. Substitute: whose reading, against which alternative (`forced_opposite`); independent LLM given the *sources only* writes its own conclusion; divergence is the signal | flag if either the attribution or the alternative is missing |
| **counterfactual** | none | must be labelled; entropy cap on density per section |

An untyped claim gets the strictest oracle. That is the safe default and
it forces the generator to declare.

## Where the generator fails in this field

- **Confabulated citation.** Same class as law's; the catalogue check
  kills it at the same cost.
- **Narrative completion.** Where sources are silent, the generator
  fills. Continuation bias in its purest form: the story wants a next
  sentence, and the archive's silence is not a token the model can
  emit. The field's name for the discipline of *not* filling is source
  criticism; the harness's version is a hook that denies a fact-typed
  claim with no anchor, so the only legal way to bridge a gap is to type
  the bridge as interpretation and attribute it.
- **Anachronism.** A concept used before it existed: "nationalism" in
  1400, "the economy" in Rome. The field has no verifier for this today;
  it relies on the reviewer's ear. One is constructible: stamp concepts
  with attestation dates and flag any use before its date. A type check
  over time; mechanical, cheap, and absent.
- **Interpretation dressed as consensus.** "Historians agree" with no
  historian named. Reference oracle: name two, or retype as the author's
  own interpretation.

## Traceability both ways

Claim → source, else drift. Source → claim, else padding: a bibliography
inflates exactly the way an uncited test suite does, and for the same
reason. The generator produces long bibliographies because long
bibliographies are what scholarly prose looks like.

## Entropy without correctness

Confidence-word density ("clearly", "undoubtedly", "it is well known")
not adjacent to a citation. Cheap, mechanical, and it catches rot before
wrongness can be caught. A fact claim that needs "undoubtedly" is one the
author could not anchor.

## Table for the field

| Boundary | Oracle | Action |
|---|---|---|
| claim composed | type declared (fact / interpretation / counterfactual) | deny untyped |
| fact typed | catalogue resolves; page-level match | deny unanchored |
| interpretation typed | attribution + alternative present | flag |
| concept used | attestation date ≤ date of context | flag |
| section complete | counterfactual density, confidence-word density | flag |
| draft complete | independent reader given sources only | advisory |
| publication | peer review | advisory, late |

## What the field returns to the framework

1. **Type the claim at entry; the type selects the oracle.** One grammar
   hiding three epistemic classes is not specific to history; FRs do it
   ("this will reduce latency" is a forecast; "the test fails" is a
   fact), and so does every research record.
2. **Silence is a legal output.** The harness must make "the record does
   not say" cheaper to emit than a plausible bridge. In this repository
   that is Commandment 6's "when a filter yields nothing, raise".
3. **Some missing oracles are constructible.** Anachronism has no
   verifier only because nobody built the date-stamped concept table.
   Before accepting that a field's claim class is unverifiable, ask
   whether the oracle is absent or merely unbuilt.

## Traps

**`type_costume`.** An interpretation or forecast wearing the grammar of
a fact. Passes every shape gate; fails the one that was never applied
because the type was never declared.

**`narrative_completion`.** Filling an evidential gap with the most
probable next sentence. The output is fluent, coherent, and unsupported.

## Heuristic

Type every claim at the boundary; give each type its own oracle; treat
an untyped claim as the strictest type. Where a source is silent, emit
the silence.

**Seed:** a claim-typing graph. Corpus-map-reduce over any draft (FR,
research record, diary): map each sentence to fact / interpretation /
forecast; reduce to the untyped and the unanchored. The outsider reads
the PR body for private language; this would read it for costume.
