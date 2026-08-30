# The Witness That Was Never Interrogated

**Date:** 2026-08-30
**FR:** FR-922 (recap bare-repo latency investigation)

## What happened

FR-922 opened with a number: 282.98s, one test, 34% of the sequential suite.
The number was true. It was measured, logged, and cited. The FR was filed at
HIGH priority with an explicit operator directive — *skip it now* — and a
carefully reasoned investigation-first structure quoting `investigation_before_fix`.

I ran the test three times. 46.59s. 41.44s. 12.95s.

Then inside the full integration lane, where contention is real: 78.35s. Four
controlled witnesses, none within 200s of the premise.

## The trap

The FR itself named the trap it fell into. Under Unknowns it wrote: *"whether
the 283s is stable or was a one-off degraded-API sample (single witness so far
— are_the_witnesses_one_phenomenon)."*

It named the doubt, then filed at HIGH priority with a skip directive anyway.
Naming a risk is not discharging it. The FR's structure — mitigate first,
investigate second — put the irreversible action (suspending the only live
witness for REQ-YG-531) *before* the cheap action that would have shown the
mitigation was unnecessary. Three reruns cost 100 seconds. The skip would have
cost a requirement's live coverage for as long as nobody revisited it.

The ordering felt like prudence. It was the opposite: it spent the expensive
resource to protect the cheap one.

## What the trace showed

`read_raw_output_first` paid again, one level down. The child runs said:
deterministic nodes 0.25s total, `synthesize` 44.66s. The graph runtime was
never a suspect worth naming. And 499 prompt tokens produced **1206 completion
tokens** for a final answer of two strings and an empty list — roughly 40 tokens
of signal. The same shape as FR-598's "haiku returned a 658-token novel."

That is the only latency lever actually inside our control, and it was invisible
from the wall clock. Fourteen minutes of suite timing produced one number;
one trace read produced the causal chain.

## The heuristic

**`mitigation_before_reproduction`** — when a fix FR pairs an immediate
mitigation with a deferred investigation, check which one is reversible. If the
mitigation removes coverage, evidence, or a witness, it is not mitigation; it is
an unbudgeted deletion executed under time pressure. Reproduce first when
reproduction is cheaper than the mitigation's cost. `investigation_before_fix`
governs *expensive* causal chains — a 100-second rerun is not one, and invoking
the doctrine does not exempt you from asking whether it applies.

Corollary: **a single witness cannot license an irreversible act.** The FR
knew this — it cited `are_the_witnesses_one_phenomenon` by name. Citation is not
compliance. A gate that checks whether the trap is *mentioned* is
`gate_checks_shape_not_substance`; what matters is whether the count went up.

## The awkward part

The disposition reverses a written operator directive. That is uncomfortable in
exactly the way it should be: the directive was sound *given its premise*, and
the premise did not survive contact with a second sample. The honest move is to
report the collapse and let the human re-decide, not to execute the letter of an
instruction whose reason has evaporated — and not to quietly substitute my own
judgement either. Reversal on evidence, surfaced for sign-off.

## Seed

The 283s outlier is still unexplained. Four witnesses cluster at 12–78s; one
sits at 283s under full suite **with coverage instrumentation on**, and FR-923
independently measured coverage at +107%. If a coverage tracer can quadruple an
API-bound test, then every latency number this repo has ever recorded under
`addopts` coverage is a composite we have been reading as a measurement.

**Seed:** which of our performance beliefs are artifacts of the instrument?
Before FR-923 splits the lanes, is there value in one deliberate A/B — the same
integration lane with and without coverage — so the split is justified by a
measured multiplier rather than an inherited assumption?
