# Diary — Cheap-Map, Code-Reduce: The Mercury Pattern Names Itself

**Date:** 2026-08-26
**Context:** Reflection requested on the map-reduce-mercury pattern, after
finding it independently reinvented on a concurrent device (philosopher
rework, unpushed) while already committed three times: prompt_theme_analyzer
(FR-402), diary_digest (FR-046), research-route (FR-890).

## The shape

Three moves, always the same:

1. **Map** — fan out one-judgement-per-call LLM nodes on the *cheapest
   adequate* model. Mercury-2 (diffusion, near-instant) when the per-item
   judgement is shallow classification/scoring; haiku-class when it is a
   paragraph of reasoning (research-route personas). `on_error: skip` per
   item — one bad element never kills the corpus.
2. **Reduce** — deterministic, LLM-free code at the boundary: counting,
   thresholding, schema validation, fail-closed rejection of error strings
   and missing citations. Disagreement preserved as rows, never voted away.
3. **Tail (optional)** — at most ONE synthesis judgement on a single call,
   where the expensive model earns its cost — or no tail at all when the
   reduced table IS the artifact (FR-890).

## Why it keeps winning

It is `prompt-as-subagent-contract` made structural. The alternative it
displaces — one monolithic prompt over a concatenated corpus (the
philosopher's old `analyze` copilot node) — fuses comprehension, salience,
aggregation, and serialization into one validator-uncovered call. The
pattern splits those levels the way the contract demands: comprehension to
the model (one judgement, closed input, one item), aggregation and
validation to code, salience to the single tail call. Reword moves load
between levels; only split removes a level — and map/reduce IS the split.

Second force: **model tier follows the abstraction-span of the per-call
judgement, not the importance of the pipeline.** The pipeline can be
doctrine-critical (research-route gates FR authority) and still run on
haiku, because each call carries one small judgement. Mercury for label,
haiku for paragraph, opus never in the fan-out. The economics are the
adoption mechanism: pennies-per-run is what turns instruments from
`builders_never_call` shelfware into one-command routes that actually fire.

Third force: the reduce step is where "normalize at the boundary" lives.
The model's outputs are CLAIMS; the LLM-free reducer reconciles them
against schema and evidence (FR-890's librarian: a URL or the run dies).
A monolithic prompt has no such boundary — its aggregation happens inside
the same opaque call that generated the items.

## The trap it cures

**monolithic_analyze:** per-item judgement over a corpus routed through
one large expensive call. Symptoms: context dilution as the corpus grows,
validator coverage collapsing to shape-checks, cost high enough that the
instrument is fired rarely (and thus never trusted). The philosopher
exhibited all three; its rework converged on this pattern independently,
on another device, without seeing this reflection — the strongest kind of
recurrence evidence.

## Heuristic

> Per-item judgement over a corpus ⇒ cheap-map, code-reduce,
> one-judgement-tail. Pick the map model by the abstraction-span of a
> single call; validate claims in the LLM-free reduce; spend the expensive
> model only on the lone synthesis — or nowhere.

Recurrence count: FR-402, FR-046, FR-890, philosopher WIP = four
instances. The graduation bar (twice → FR; confirmed → Scripture) is met
twice over. `is_this_a_graph` already points at map as the native shape;
this heuristic is its model-economics and boundary-validation completion.

## Seed

Should `is_this_a_graph` in Scripture gain the model-tier clause — "the
map model is chosen by per-call abstraction-span, the reduce is LLM-free" —
or does this warrant its own knowledge-graph cure entry
(`cheap_map_code_reduce`)? Candidate for a .chaplain/inbox proposal once
the philosopher commit lands and makes the fourth witness citable.
