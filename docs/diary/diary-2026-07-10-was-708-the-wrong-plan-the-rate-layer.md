# Was 708 the Wrong Plan? — The Rate Layer (reflection)

**Date:** 2026-07-10
**Context:** Post-FR-709-judgement reflection, prompted by the question: should FR-708 have been replanned as a persistent client pool?

## The verdict

No — and yes. 708 stands regardless of client lifecycle: a pooled client
still needs a request timeout; one hung request inside a persistent client
hangs that call without it. Boundary invariants don't become obsolete when
the architecture above them changes. And it was the smallest sufficient
change against an active production failure.

But the FR-709 judgement's F1 finding (SDKs spawn persistent pools/pollers
on first use — test baselines must be post-warm-up) is testimony about
design intent: **clients are built to be long-lived, and yamlgraph builds
one per candidate per turn**. 708's purge-list justification — "with bounded
requests, accumulation impossible" — was overstated: accumulation is
bounded, not impossible. 708 capped the leak's LIFETIME (≤ timeout); nothing
caps the RATE (channels per second under load). Lifetime × rate is the
resource envelope; we fixed one factor and declared the product safe.

## The non-obvious blocker

"Just pool the clients" collides with the bridge: `_run_coro_sync_safe`
runs `asyncio.run()` — a fresh event loop per race turn — and async SDK
clients bind to their first loop. Naive pooling breaks. The coherent fifth
layer is the conjunction of two seeds already in the diary:

- FR-707's seed: ONE persistent bridge loop thread (the deadline-aware
  primitive) instead of a loop per call;
- a client registry keyed by (provider, model, temperature,
  env-fingerprint) — with invalidation answering the FR-227 lesson that
  construction is env-sensitive.

Neither seed is sufficient alone; the pool requires the persistent loop.

## The trap named

`bounded_is_not_small`: proving a resource's lifetime is bounded and
concluding accumulation is solved ignores the rate dimension. Every
"leak window ≤ X" claim should be accompanied by the worst-case
population estimate: rate × window, at design load. If that number was
never computed, the claim is shape, not substance.

## The gate

Measure before architecting: FR-709's repeatability loop and the
consumer-side Fly probe are the instruments that decide whether the fifth
layer is real pain or speculative complexity. If post-708 churn under
PAR-02 load is negligible, the pool FR should not exist. If it is visible,
the FR arrives with field numbers instead of theory.

**Seed:** FR-710 candidate — persistent bridge loop + provider client
registry — gated on FR-709/Fly-probe measurements showing per-turn channel
churn is a real cost post-708. The layer stack becomes: message → witness →
wait → work → **rate**.
