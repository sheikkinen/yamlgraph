# The Invariant Made True by Construction

**Date:** 2026-08-24
**Context:** FR-884 (deviant-daily) — strip-not-drop name redaction; 1,499 prompts recovered

## What happened

The judge demanded a mechanical invariant: `kept == 5893 +
name_recovered_rows`. Written naively — process entries in log order,
count a stripped row as recovered when kept — the invariant is only
*approximately* true: a stripped prompt can collide with a baseline
prompt in dedup, and whichever comes first in log order wins the slot.
The count would drift by exactly the number of collisions, and the AC
would fail for a reason that is neither a bug nor a leak.

The fix was not to weaken the invariant ("kept rises from 5,893") nor
to measure and explain the drift. It was to **reorder the computation**:
admit all baseline rows first, then all stripped candidates. A recovered
row can now never displace a baseline row; the invariant holds exactly,
and FR-883's v1-preservation guarantee becomes trivially true instead of
accidentally true. 495 candidates did collide — the data confirmed the
batch-variant hypothesis (same prompt ± name segment) — and the
invariant survived untouched because the order made collisions land in
`duplicates`, never in the baseline.

## The trap and the cure

Trap: when a demanded invariant is only approximately true of your
implementation, the reflex is to negotiate the invariant down (a floor,
a tolerance, an "approximately"). That is `threshold_encodes_forecast`
wearing an accounting costume.

Cure: **check whether a different evaluation ORDER makes the invariant
exact.** Equality constraints on pipeline outputs are often order-
dependent claims; the implementation, not the claim, should move.
Two-pass admission cost four lines. A tolerance would have cost the
invariant its meaning — and the judge its teeth.

Also confirmed twice today: `junk_drawer_cap`'s demote-never-drop
generalizes to redaction. Whole-row exclusion for one-token
contamination threw away 25% of the corpus; stripping the token
(segment) kept the payload and the guarantee — enforced not by the
strip but by an atomic scan-before-finalize write that leaves zero
artifacts on a seeded leak.

**Seed:** when adding any salvage/recovery path to a deduplicating
pipeline, is "legacy first, salvage second" a universal ordering — so
the delta is exactly attributable and the legacy set provably
undisturbed? Where else do we interleave when we should stage?
