# The Carve-Out Measured in Milliseconds

**Date:** 2026-07-11
**FR:** FR-713 Part B reframe (F13)
**Trap encountered:** pricing a purity change in the currency of performance

## What happened

After Part A shipped, I evaluated Part B by asking what the
`_UNCACHED_PROVIDERS` revert would *buy* — measured it at ~60 ms per
google call, declared it a near-no-op, and recommended parking it behind
the deployed-google incident. The operator's correction was five words in
spirit: special faulty code is against the Scripture. The question was
never what the deletion buys. `_UNCACHED_PROVIDERS` is a provider
carve-out whose justifying cause (fresh loop per call) Part A removed;
code whose justification has been deleted is entropy regardless of its
runtime cost (Commandment 8). And the purity audit I skipped found the
real payload: the vertex Express `_masked_env` window mutates global
`os.environ` on every uncached call, on concurrent caller threads,
unguarded against any non-vertex env reader — a correctness surface that
scales with call rate, invisible to a latency instrument by construction.

## The insight

Deletion decisions and feature decisions have different currencies. A
feature is priced in value delivered; a deletion is priced in entropy
removed. Measuring a deletion with a latency instrument answers the wrong
question with high precision — the 60 ms figure was correct and
irrelevant. The tell: when the strongest argument against removing a
special case is "the numbers say it doesn't matter," the numbers are
measuring the wrong axis. The special case's cost is not in its hot path;
it is in every future reader who must learn why it exists, every witness
that must encode it, and every window where its side effects race.

## Heuristic

When evaluating whether to remove a special case, do not ask what removal
buys — ask what keeping it costs in causes: does its justifying condition
still hold? If the cause is gone, the code is dead even while executing.
Run the purity audit (what global state does it touch, what uniformity
does it break) BEFORE the performance measurement, because the instrument
you reach for determines the conclusion you reach (evaluation boundary,
`inventory_by_visibility`'s sibling).

**Seed:** `_UNCACHED_PROVIDERS`, `_masked_env`, `_VERTEX_CONSTRUCT_LOCK`
— each is a downstream guard for an SDK that reads process-global state
at construction. Should the provider boundary own a single
`construction_context` seam (env snapshot in, client out, no global
mutation) so the next env-sensitive SDK adds a parameter instead of a
lock?
