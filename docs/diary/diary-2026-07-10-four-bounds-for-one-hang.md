# Four Bounds for One Hang (FR-708)

**Date:** 2026-07-10
**Context:** FR-708 closes the NC-361 chain — the fourth FR spawned by one production incident, each bounding a different layer of the same hang.

## The chain, seen whole

One incident (a voice worker going silent under load) decomposed into four
defects at four boundaries, each invisible until the previous fix exposed it:

1. **FR-705 (message):** the error miscounted its own evidence — `All 1 …
   ?/?` for a fleet of two.
2. **FR-706 (witness):** the loop-stall was reproduced deterministically —
   5.01 s block for a 0.5 s timeout.
3. **FR-707 (wait):** the verdict was held hostage by loser cleanup and the
   runtime's own shutdown — fixed by Future handoff.
4. **FR-708 (work):** the losers themselves were unbounded — no client
   timeout anywhere in 11 provider constructors, so a hung gRPC channel
   lived forever and accumulated until the VM seized.

The pattern worth keeping: **a timeout is not one setting but a stack of
them** — message fidelity, deadline authority, wait bounds, work bounds —
and each layer's absence hides behind the layer above. NC-361 looked
"fixed" after FR-707 (the loop stayed alive), yet the Fly freeze RCA showed
the work still accumulating underneath. `assert_path_not_destination` at
system scale: verifying the caller returns is not verifying the work ended.

## Enforce notes

- The matrix RED (30 condemned across 11 providers, zero network) was the
  Judgement's F3 replacing an untestable "outlives unboundedly" criterion —
  the cheapest possible condemnation of a concurrency bug is often a
  *configuration* assertion, not a timing assertion.
- The `mock_escape_hatch` honesty bound (F4) held: no test here claims to
  validate SDK timeout behavior; the param matrix proves what WE pass, the
  consumer-side Fly probe proves the phenomenon.
- One environment lesson: optional-SDK providers (replicate/litellm) must
  `importorskip`, not fail — a skip with a reason is honest; a matrix that
  fails on missing optional deps punishes the wrong party.

## Heuristic

When an incident chain produces N fixes at the same seam, write the layer
stack down explicitly (message → witness → wait → work) and check each
layer has its own witness before declaring the chain closed. The next hang
should be caught by layer 4 in 30 s and reported by layer 1 with names —
if it isn't, a fifth layer exists.

**Seed:** the four layers generalize beyond races — map nodes, agent tool
calls, and subgraph invocations all wrap provider work. Should the
capability registry carry a "bounded-work audit" listing every seam where
external work enters without an explicit timeout, the way confessions list
every noqa?
