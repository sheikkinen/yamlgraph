# The cure that was wider than its false positive

**FR-1057** — three review rounds, two self-inflicted defects, and a deletion
that ended the argument.

## The shape of it

The FR's real work was small: decide the template dialect **per message**, so a
Jinja `system` could no longer vouch for a `str.format` `user` the renderer
would reject. That landed, and it was right.

The trouble started with a side effect. Making validation honest meant lint
started reporting braces it had never reported before — including
`{pred: alive, args: []}`, which is prose documenting an output shape, not a
variable. One advisory false positive. So I built a discriminator: if the
field's tail looks like documentation rather than a format spec, exempt it.

Round 1 of review: the discriminator keyed on "has a tail", which swallowed
`{score:.2f}` along with the prose. A real variable went unvalidated and the
render raised `KeyError`. Fixed by narrowing the rule to a format-spec regex.

Round 2: the regex is closed, but Python's format-spec grammar is **open** —
the spec is handed to the value's own `__format__`, so `{when:%Y-%m-%d}` is
perfectly valid for a `datetime` and my regex said otherwise. Same class of
defect, one layer deeper. Fixed by splitting the rule by dialect: strict on
the `str.format` side, permissive on the Jinja side where the guess is only
advisory.

Round 3: the permissive side was still suppressing E014 for valid fields —
the exact failure the acceptance criterion existed to catch.

## Naming it

**A cure must be no wider than the false positive it treats.** Mine kept being
wider, and each narrowing was itself a guess about a grammar I did not control.

But the deeper error is upstream of all three rounds:

**I was inferring intent the author could simply have declared.** Jinja ships
`{% raw %}`. The author knows whether a brace is prose; no amount of regex
archaeology recovers that knowledge from the text. Every round was an attempt
to make the machine guess something a human already knew and had a syntax for
saying.

The census settles it. Across the whole prompt corpus, exactly **two** braces
relied on the guess:

| prompt | field |
|---|---|
| `examples/plot_modeller/prompts/extract_goals.yaml` | `pred` |
| `examples/yamlgraph_gen/prompts/assemble_graph.yaml` | `positive` |

Twenty-five lines of heuristic, three review rounds and two shipped-and-caught
defects, to silence an advisory warning about two braces. The corrected version
is a deletion plus four words of YAML in two files.

## The review loop's actual score

Worth recording honestly, because I had started to resent the rounds. Rounds 1
and 2 each caught a defect that would have shipped. Round 3 caught the third
instance of the same one. **All three were mine, and all three were introduced
in response to the previous round.** The reviewer was not nitpicking; it was
performing the RED step I kept skipping.

The cheap move I never made: after round 1, ask *"what else is a valid format
spec?"* and write the failing test for the **whole class**, not the cited
instance. That one question collapses rounds 2 and 3 into nothing.
`partial_remediation` already names this — I fixed the occurrence, not the
class, three times running.

## Heuristics

- When a guard fires on legitimate input, the first question is not "how do I
  narrow the guard" but **"is there an existing way for the author to declare
  this?"** A language feature beats an inference every time, because the author
  holds information the text does not carry.
- A heuristic that infers author intent is a design smell wherever a
  declaration is available. Prefer the explicit escape; accept the migration
  cost — here it was two lines.
- When a review finding lands, fix the **class**. Ask what else satisfies the
  predicate that fooled you, and write that test before touching the code.
- Deleting the machinery is a legitimate response to its third defect. I spent
  two rounds defending an artifact whose entire justification was two braces,
  because I had written it and it "worked".

**Seed:** Every guard I've written that guesses at intent has an author who
knows the answer. Which of the remaining lint rules are inferring something a
declaration could carry — and what would the corpus census cost for each?
