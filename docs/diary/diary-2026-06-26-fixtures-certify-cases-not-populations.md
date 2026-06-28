# The fixtures certified the judge; reading every member convicted it

*2026-06-26 — FR-599, L7 affect-recall miss decomposition*

## What happened

FR-598 left the affect gate on the floor (recall ~0.06) and REFUTED its own "kill the
novel" hypothesis. The reserved escalation had three candidate levers — model scale,
taxonomy, evaluator tolerance — and one number to choose between them. FR-599 built a
read-only probe to partition every missed GT delta into buckets, each naming a different,
differently-priced lever, and to tie out to the frozen gate's own `recall_hits` so the
decomposition is provably the same misses the gate sees.

The requester's amendment added a fifth bucket I had not seen: **UNLICENSED** — GT deltas
the anchor beat's own words do not license at all (Marren's `loss` anchored to F1, whose
subject is Hagen and which never names Marren; `hidden_blessing` on a beat with no
setback). Deciding (e) needs a judgement, so it entered an otherwise deterministic probe
as the one un-validated surface. The Judgement fenced it with two corrections: **#5**
fixture-pin the licensing pass to hand-adjudicated known answers, and **#6** gate (e)
conservatively and read **every** member, because (e) is the motivated-reasoning bucket —
"the GT is wrong" exonerates both model and taxonomy at zero cost.

## The trap I walked into, and what caught me

My first licensing prompt asked the natural question: *does the anchor text show the
character feeling this kind?* It passed both fixtures (F1 `loss`, F7 `hidden_blessing` —
both `open` ops) and reported (e) at **55%, DOMINANT**. A clean single-cause verdict: the
ground truth is broken, re-annotate it, done. The fixtures were green. I could have
stopped.

Correction #6 made me read all 17 (e) members instead of trusting the two green fixtures.
Seven were `close` ops, and they were all flagged UNLICENSED for the same reason — *"the
beat shows a gain, not the feeling."* But a `close` op is licensed by the feeling's
**resolution**: a recovery, a triumph, an avenging. Asking "does the text show loss?" of a
*close-loss* beat is the wrong question by construction — the beat is supposed to show the
loss being recovered. My judge was open-biased, and the open-op fixtures were structurally
blind to it.

Adding one `close`-op fixture (F5 `close loss` → LICENSED) and an op-branched prompt moved
five misses out of (e). The verdict flipped: (e) 55%→39%, tied with ABSENT, **MULTI-CAUSE**.
The single most expensive decision in the whole escalation — is this a data problem or a
model problem? — turned on a bucket I had certified with two passing fixtures and would
have shipped wrong.

## The heuristic

**A fixture certifies the cases it contains; it cannot certify the population it samples
from.** Two `open`-op fixtures proved the judge correct on `open` ops and said nothing
about `close` ops — yet the aggregate they fed was a verdict over *all* ops. The mandated
full read (correction #6) was not ceremony; it was the only instrument that could see the
half of the population the fixtures didn't span. This is `read_raw_output_first` applied to
a *judge's* output, not a model's: the licensing pass is itself an LLM doing the same
per-beat task the L7 classifier fails at, so its output is exactly as untrustworthy and
exactly as in need of a raw read before its aggregate is believed.

The deeper pattern: when a judge enters a deterministic pipeline, the danger is not that
it is wrong on the cases you checked — you checked those. The danger is that it is
*systematically* wrong on an axis your fixtures happen not to vary. Vary the fixture along
every axis the aggregate sums over (here: op), or read every member along the axes you
couldn't fixture.

## Seed

The op-bias was invisible because both fixtures shared an op value. Could a probe that
builds an LLM-judge gate **auto-audit its own fixture coverage** — refuse to trust the
judge until the fixtures span every categorical axis (op, kind-class, neighbor_licensed)
the buckets are split by — so "your fixtures don't vary `op`; read every `close` member by
hand" is a mechanical warning, not a lesson learned after the verdict already flipped?
