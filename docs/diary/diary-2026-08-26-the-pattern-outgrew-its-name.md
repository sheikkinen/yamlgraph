# Diary — The Pattern Outgrew Its Name

**Date:** 2026-08-26
**Context:** Operator reflection mid-study: "it doesn't sound just
map-reduce-mercury anymore — this is discover-extract-map-mercury-reduce
that should be codified: prebaked analysis pipeline, user-supplied
discovery and extraction tools, which implies tool passing to yamlgraph."

## The insight

The study named the pattern by its *expensive-to-learn* stages (cheap map,
fail-closed reduce) and ignored its *expensive-to-author* stages. Eleven
rounds of ideation kept producing "products" that are all the same
pipeline with two sockets swapped — and the naming blindness meant the
codification opportunity (one skeleton, injected adapters) surfaced from
the operator, not from the convergence analysis. Third operator-supplied
insight in two days (FR-888 chmod, site-mapper canary, now this): the
pattern-completion instinct names what was hard to DEBUG, but the product
instinct must name what is hard to REUSE. A pattern's true anatomy is
found by asking "what varies between instances?" — the strategy-pattern
question — not "what did we suffer for?"

## The grounding that made it an FR in one hour

`ask_before_generate` paid off: before writing anything, one grep found
FR-768 tool manifests — the injection FORMAT already shipped, unconsumed
for this purpose. The gap collapsed from "design a plugin system" to
"bind existing manifests at invocation time." The research route then
CONVERGED 4-of-5 personas on the operator's sketch (canary precommitted
and recalled), with a genuine os-infra dissent (Unix process pipeline)
preserved as fallback and Hydra as external precedent. FR-892 filed with
research reference — the FR-890 lifecycle's third real consumption today,
and the first where the canary was the operator's own idea being tested
for independent rediscovery. It was rediscovered; the sketch is validated
by fresh contexts, not by deference.

## Trap witnessed (own): heading-consumption edits

Twice today a `replace_string_in_file` anchored on a section heading
consumed it, silently corrupting document structure (duplicate/lost
"## Sources", lost "### Deprioritized", lost "## Status"). Cure applied
going forward: never use a heading as the oldString terminus — anchor
INSIDE the section being extended, and grep heading counts after every
structural edit.

## Seed

**Seed:** FR-768 manifests + invocation binding makes tools data, not
code. Does the same move apply to the RUBRIC (the map-stage prompt) and
the REDUCE SCHEMA — i.e., is the endgame a census run defined entirely by
four data artifacts (two manifests, one prompt, one schema) with zero
YAML, and if so, is that a CLI subcommand (`yamlgraph census run`) rather
than a graph at all?
