# Diary — The perfect vocabulary that bought nothing

**2026-06-25 · FR-591 follow-up · L5 encoder recall analysis**

## What happened

Continuing from the FR-591 enforcement, I ran the full corpus through the new
perspective→L5 graph and analysed the worst offender, `scifi-hybrid-the-loom`
(world recall 0.17, precision 0.06). The diagnosis named two failure modes:
a standing-fact **flood** (`alive[The Swarm]` stamped 15×, the corpus-wide
`at`-flood) destroying precision, and **vocabulary drift** (`Vantari Labs`→`lab`,
`shutdown_key`→`airgapped USB drive`, invented `home`/`apartment`) destroying
recall.

Fix #1 (an anti-flood "change-only / never assert `alive` as a standing fact"
encode rule) was a clean, single-variable win: precision 0.06→0.12 (2×), the
`alive` flood 15→2, **zero** recall loss. The flood was pure noise.

Then the user sharpened fix #2 into a real hypothesis: *story analysis should
begin by identifying the story-specific vocabulary, and that vocabulary should be
bound into downstream L5 encoding.* Architecturally exactly right — normalize at
the boundary. So I tested it.

## The experiment that mattered: grant the fix perfection first

Instead of building a vocabulary-extraction step and then measuring, I built an
**oracle**: I extracted the controlled vocabulary directly from the ground truth
(the exact tokens the evaluator scores on) and injected it into the encode
prompt, reusing the already-generated viewpoints so *only* the encode step
varied. This measures the **upper bound** of the hypothesis — if the encoder had
a literally perfect vocabulary, how much recall could it possibly recover?

Answer: **none.** Invented `at`/`holds` tokens dropped 7→0 (the encoder obeyed the
vocab perfectly), but world recall went 4/23 → 3/23. Perfect words, no recall.
The hypothesis was refuted in one ~90-second run, before a single line of
extraction code was written.

## The cognitive trap

**`correlation_named_as_cause`.** Two facts were true at once — the tokens were
wrong *and* the recall was low — and I let their co-occurrence imply causation.
The token drift was real and visible, so it *felt* like the cause. The oracle
severed the correlation: hand the encoder the right tokens and the misses don't
move, because the misses were never lexical.

The beat-level evidence showed the real bottleneck is the encoder's **transition
model**, not its dictionary:
- It never emits departures/losses (`value: false`). GT encodes movement as
  leave-old(false)+arrive-new(true); the encoder only emits arrivals.
- It inverts `pre_world` direction — destination as precondition, where GT uses
  the origin.
- My own anti-flood rule ("emit once, never restate") actively *fights* GT's
  `pre_world` convention, which restates the standing precondition at each
  consuming beat. Precision and pre-recall are in direct tension.
- Handing the model a `rel`-*label* vocabulary *induced* relationship
  hallucination — it stamped `colleagues`/`lovers` where none existed. The fix
  for one slice damaged another.

## The methodological win

The cheapest way to refute a proposed feature is to give it perfect inputs and
watch the metric stay flat. An oracle test is a spike that costs one prompt and
buys a go/no-go on an entire workstream. Had I built the extraction pipeline
first, I'd have shipped a correct, well-engineered solution to a problem that
wasn't the bottleneck — and blamed the extractor's imperfection for the flat
recall, hiding the real cause behind a plausible scapegoat.

## Heuristic

Before building machinery to supply *X* better, first supply **perfect *X*** (an
oracle drawn from ground truth) and measure. If the target metric does not move,
*X* was never the bottleneck — stop, and look elsewhere. Vocabulary was a
precision/cleanliness lever (invented tokens 7→0), never the recall lever.

## Seed

The recall ceiling is set by transition semantics — `value:false` departures and
origin-as-precondition — which a single-character, single-beat view may be
structurally unable to express (you can't assert "Jonas left the City" from
Jonas's arrival narration without a before/after frame). **Is per-beat pre/eff
encoding the wrong unit entirely — should the encoder see adjacent beats as a
delta (state[t-1] → state[t]) so that "leaving" becomes derivable rather than
something the model must remember to assert?**
