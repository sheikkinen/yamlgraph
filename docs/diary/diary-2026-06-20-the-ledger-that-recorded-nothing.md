# Diary -- 2026-06-20 -- The Ledger That Recorded Nothing

## What happened

FR-545's first cut was rejected for reading the wrong layer: a detector that diffed
the relationship ledger to catch allegiance resets, when the resets live in the prose
and never reach the ledger. The re-plan pivoted to a two-part design: a ledger-fidelity
*witness* (read the bi-temporal stamps) plus a chapter-close *prompt* change (make the
writer record stance flips). Judged APPROVED with four conditions. Enforcing it produced
a finding sharper than the judgement anticipated.

## The trap: trusting the snapshot, not the stamp

Condition C2 told me to read `valid_from`/`valid_to` stamps from the *final* committed
ledger instead of diffing adjacent per-chapter snapshots. I almost coded the baseline
assertion from memory -- "10031-BC has one recorded transition, Hilde/Gunnar
enmity->romantic_bond at Ch1->Ch2" -- a number that came from the rejected snapshot
method. Measuring before asserting overturned it: the final Ch8 ledger holds **three
edges, all `valid_to=None`**. No closed edge. No bi-temporal transition anywhere.
Hilde/Gunnar is `romantic_bond` from `valid_from=0` -- the bond was never recorded as
*turning*; it was simply present from the start.

So under C2 the witness reads `transition_count == 0` on the very book the reviewer
flags for seven allegiance flips. That zero is not a bug in the witness -- it is the
**total fidelity gap** made visible: the writer recorded *no* stance reversal at all.
The snapshot method's "1" was an artifact of comparing two chapters' carried-forward
floors, not a real bi-temporal `update`. C2 was load-bearing precisely because it
exposed that the supposed "one recorded transition" never existed.

## The deeper insight: the gauge's headline is a zero

A witness whose best-case reading on a defect-dense book is zero looks broken to anyone
expecting a count of problems. But this witness measures the *writer's bookkeeping*, not
the *reader's complaints*. Zero recorded transitions against seven narrated flips is the
strongest possible statement of the thesis: the ledger is not being written. That is why
C4 (name the limitation in-module) matters -- a future reader must not see `0` and
conclude "no allegiance problems"; they must read it as "the writer recorded nothing,
go look at the prose." The number is honest only with its caveat attached.

## Heuristic

When an AC cites a specific measured number, re-measure at the boundary the condition
names before you assert it -- a number carried over from a rejected method is a stale
fact wearing a fresh citation. The cheapest correction is the one made before the test
is written.

## Seed

The witness now proves the ledger is empty of transitions; the prompt change asks the
writer to fill it. But compliance is stochastic. Is there a deterministic seam -- a
post-close reconciliation that diffs a chapter's recap-asserted stances against the
inherited ledger and *synthesizes* the missing `update` op -- that would close the
fidelity gap without trusting the writer to remember? Or does synthesizing ops from
prose just relocate the hallucination risk from the writer to the reconciler?
