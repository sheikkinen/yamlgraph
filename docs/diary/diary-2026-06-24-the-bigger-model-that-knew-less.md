# The Bigger Model That Knew Less

*2026-06-24 — FR-578 L7 assign-affects spike*

## What happened

L7 assigns the emotional skeleton: per beat, an `eff_affect` list of
`AffectDelta` objects (`op` open/close, `char`, `kind` from a closed 6-enum,
optional relational `toward`). The gate was affect recall ≥ 0.70.

The first spike, on `claude-haiku-4-5`, returned **4/33 (0.12)** — a deep miss.
The reflex was obvious: haiku is the cheap model, scale up. So I re-ran the exact
same graph on `claude-sonnet-4-6`, a far stronger model.

It scored **3/33 (0.09)**. Slightly *worse*. Precision dropped too (0.10 → 0.07).

Both `Creating LLM: anthropic/...` log lines were verified — the swap genuinely
took effect. A 6×-stronger model moved the gate by nothing.

## The trap I almost fell into

The default response to a bad LLM result is *continuation bias toward scale*:
"the output is poor → use a bigger model." It feels like progress because it's
one command and it sometimes works. But it answers a question I hadn't yet
asked: **is this a capability bottleneck at all?**

Had haiku scored 0.12 and I'd stopped there, I would have recorded "L7 needs a
stronger model" as the revision hypothesis — and FR-579 would have inherited a
false lead, burning opus-tier budget chasing a gap that scale cannot close.

## The probe that paid off

Running the second model was not "trying again harder" — it was a **controlled
capability probe**. The two runs are identical except for the one variable that
matters (model strength). When the gap is *invariant* across a large capability
jump, the bottleneck is provably **upstream of the model**: in the task framing,
the prompt, or the input richness.

The confusion analysis confirmed it — the failure axis was identical under both
models:

- `char` almost always correct (knows *who* feels);
- `op` roughly correct (knows *when* an arc opens/closes);
- `kind` systematically wrong (over-emits generic `hope`/`loss`, misses the
  moral-relational `guilt`/`betrayal`);
- `toward` mis-targeted (Jonas ↔ ARIA swapped).

Both models recover *who* and *roughly when*, neither recovers the authors'
specific emotional *kind*. That stability across a capability jump is the signal:
the kind/relational discrimination isn't sitting in the model's weights waiting
for more parameters — it's missing from the task as posed.

## The heuristic

> When an LLM result is poor, do not reach for a bigger model first. Run a
> **controlled capability probe**: re-run with a model from a different
> capability tier, changing nothing else. If the metric is invariant across the
> jump, the bottleneck is upstream of the model — stop scaling, start
> reframing. Model-invariance is the cheapest proof that the fix is in the
> prompt, the decomposition, or the input, not the weights.

This is the inverse witness to FR-577's lesson. There, decomposing a composite
*metric* (agent vs goal) revealed where the model was actually succeeding. Here,
holding the task fixed and varying the *model* reveals where it cannot succeed by
scale at all. Both are seam-finding moves: split the thing you're measuring, or
split the thing you're measuring *with*.

## What carried the verdict

The gate (0.70) was not met, so by the raw number this prints KILL. But J:N2
says the threshold triggers and the *confusion* carries the verdict — and the
confusion is coherent, model-invariant, and prompt-addressable (decompose
detect-vs-name, ground the relational kinds, track open/close pairing). A
coherent, fixable failure cluster is a **REVISE**, not a KILL. The exact-enum
`kind` match (C4) stays — it is precisely *what exposed* the kind-axis confusion;
fuzzy matching would have buried the signal that made the diagnosis possible.

L7 does not pass to the FR-579 merge node until a revised spike clears 0.70.

**Seed:** If model-invariance proves a bottleneck is upstream of the weights,
can we make the probe *cheap and automatic* — a two-tier spike harness that runs
every new layer on a weak and a strong model by default, and flags
"model-invariant gap → reframe, don't scale" before a human ever reads the
number?
