# Diary — The half of every change the model forgot to say

**2026-06-25 · FR-591 follow-up · transition-semantics recall lever**

## What happened

Yesterday's oracle test refuted the vocabulary hypothesis and left a Seed: is
per-beat pre/eff the wrong unit, since a single-beat view can't express "leaving"?
Today I tested the narrower repair instead of the architectural one — and it
worked. I added one rule to the encode prompt: **transitions come in pairs.** When
a character moves, emit BOTH the departure (`at[origin] value: false`) and the
arrival (`at[destination] value: true`); when they give away or use a possession,
emit the `holds value: false` half too. `pre_world` restates the origin, not the
destination.

On the same oracle-vocab harness (token confound held constant), scifi world
recall went 3/23 → 7/23 (0.13 → 0.30); `eff_world` recall doubled, 0.20 → 0.50.
The mechanical proof is a single number: `value: false` fluents went from ~0 to
13. F3 now carries `at[Jonas, City]=false` + `at[Jonas, Seoul lab]=true`, the exact
GT pair that was absent before. Precision stayed flat — the new fluents are
legitimate transition halves, not noise.

## The cognitive trap (the model's, and mine)

**`salience_asymmetry_of_change`.** Ask an LLM "what changed in this beat?" and it
reports the *arrival*, the *gain*, the *new* thing — and silently drops the
*departure*, the *loss*, the *vacated* state. Narration foregrounds where you went,
not where you no longer are; "they fly to Seoul" makes Seoul vivid and the empty
lab invisible. The encoder inherited that asymmetry. Every missing `value: false`
was the unspoken half of a change the prose had only half-told.

My own version of the trap: I read the low `eff_world` recall as "the encoder
misses effects" — a quantity problem — when it was a *symmetry* problem. The
encoder wasn't missing effects at random; it was missing exactly the negative
pole of each transition, every time. The fix wasn't "try harder to find effects,"
it was "name the second half explicitly so it cannot be omitted."

## What made the test trustworthy

The same harness that *refuted* the vocabulary hypothesis *confirmed* this one,
and that's not luck — it's the confound isolation. Oracle vocab removes the token
variable, so a recall move can only come from the rule under test. A spike that
can deliver a clean NO (yesterday) is the only kind whose YES (today) means
anything. If the harness had been noisy enough to let vocab look like it helped,
today's +133% would be unreadable.

## The Seed, partly answered

Yesterday I asked whether per-beat encoding was the wrong unit and the model
should see a `state[t-1] → state[t]` delta so "leaving" becomes derivable. Today
says: you don't need to change the unit to recover the negative pole — you can
*name* it and the model will produce it. But the residue argues the Seed still
stands. `pre_world` barely moved (0.08 → 0.15); Mara's origin is still confused
(`City` vs the true `Vantari Labs → Seoul lab`), because her *viewpoint prose*
never fixed an origin to leave from. That's an upstream `summarize` defect a
prompt rule on `encode` cannot reach.

## Heuristic

When a metric misses a *systematic* subset rather than a random fraction —
always the `false` half, always the precondition, always the same predicate —
the cure is not "more effort" but a rule that makes the missing pole impossible to
omit. Diagnose the *shape* of the gap before prescribing its size.

## Seed

If departures are the unspoken half of arrivals, what other dualities does the
pipeline silently drop? Does `summarize` itself need to assert an origin for every
journey — a "from where?" obligation per movement beat — so the negative pole is
present in the prose before `encode` is ever asked to type it?
