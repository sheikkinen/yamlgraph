# Deterministic precision on one noisy draw

**FR-603 — L7 hope-emission discrimination (CLOSED, cue refuted)**

## What happened

The FR-599 decomposition pointed the next L7 lever at `hope` (8 of 14 ABSENT). I extended
the deterministic `--absent` probe to split each hope miss into `cap_blocked` (the one-op
cap forbids the second delta on a multi-affect beat) vs `hope_open_missed` (the model never
named the hope) vs `irreducible` (open+close of the same kind on one beat — excluded). The
split came back a clean **3–3 near-tie**, exactly as the Judge predicted, so the
pre-committed tie rule chose the hope-open cue. I wrote it — an OPEN mirror of FR-601's
close-op cue — ran the spike, and the aggregate recall **did not move** (6/28 → 6/28).

That flat number was the whole lesson, but it took two more rounds to see it.

## The trap: a precise ruler on a trembling object

Every probe mode prints exact integer counts and ties out to the frozen gate. That precision
is real — and it seduced the entire L7 arc into believing the *object* was as stable as the
*ruler*. It is not. The classifier runs at temp 0.7, and the whole corpus is 28 deltas. When
I finally ran the spike three times with the cue and three times without, the no-cue `(c)`
count alone swung **3 → 6 with no change whatsoever to the prompt**. The "FR-601 (c)=3 gain"
I had treated as a fixed baseline was a single lucky low draw from a distribution that spans
3–6.

I had been making 1-delta lever decisions on top of a ±2-delta noise floor. The deterministic
decomposition gives exact counts *on one stochastic sample* — and exactness about a sample is
not knowledge about the population. The committed evidence file ("8 hope absent, (c)=3") reads
like a fact; it is one roll of the dice rendered in a monospace table.

## The second insight: the cue's failure was coherent, not noise

The distributions still said something true. With the cue, hope-recoverable dropped
consistently (4.5 → 2.3 mean) **and** `(c)` rose consistently (4.0 → 5.7). The cue makes the
model paint hope onto more beats: ~2 land on real hope (recall up), ~1.7 land on wrong-kind
beats (kind-wrong up). That is textbook **over-emission** — the precision guard's reason to
exist — and it is a *mechanism*, visible across draws, even though each individual count is
noisy. Noise hides the size of an effect; it does not necessarily hide its sign or its shape.

So the cue genuinely fails the hard (c) AC, *and* the corpus is too small to adjudicate a
gentler refinement. Both are true. Killing it was the boring, correct outcome.

## The cure that graduates the lever

The deeper read reframes the whole approach. Hope loses because the single-pass classifier
forces six kinds to share **one op per beat** — hope, the soft forward-looking feeling, is
always out-shouted by a concrete loss-close or betrayal-close. No amount of prompt text fixes
a budget problem; the cue just bought over-emission. The fix is **structural**: map over
*kinds*, not just characters — give each kind its own pass and its own budget — guarded
against the FR-598 invention engine that the single-pass collapse was built to kill. And
before any of that, measure the noise floor: at 28 deltas and temp 0.7, a 1–2 delta lever is
unmeasurable. Enlarge the corpus or drop the temperature first, or keep mistaking dice for
data.

## Heuristic

**Measure the noise floor before pulling a sub-noise lever.** When a deterministic metric
reads off a single stochastic generation, run the generator N times *with no change* first.
If the metric's own run-to-run variance exceeds the effect you're chasing, the exact count is
theater — refine the experiment (more samples, lower temperature, bigger corpus) before
refining the thing under test. A precise ruler on a trembling object reports the tremble.

## Seed

The probe modes assert a tie-out to the frozen gate on *one* prediction file. What if the
forced-observation discipline (`read_raw_output_first`) had a sibling for stochastic stages —
a forced *N-sample* discipline that withholds any single-draw decomposition until the
generator has been rolled K times and the metric's variance is reported alongside its value?
Could the gate itself refuse to print a count without printing its noise band?
