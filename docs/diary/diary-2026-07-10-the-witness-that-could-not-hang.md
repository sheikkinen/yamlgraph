# The Witness That Could Not Hang (FR-706)

**Date:** 2026-07-10
**Context:** FR-706 — condemn-or-absolve witness for the NC-361 production stall; verdict CONDEMNED in one deterministic run.

## What happened

A production incident (320–340 s process silence) had two candidate
explanations and a judged fallback plan involving load rigs and py-spy under
live phone calls. Instead, one unit test settled it in 5.7 seconds: the race
node's sync bridge blocks its caller — measured 5.01 s for a 0.5 s timeout —
because `_race_async`'s finally-gather awaits uncancellable losers and
`t.join()` hands that wait to the loop thread. The observational plan is now
unnecessary; the mechanism is pinned, reproducible, and xfail(strict) keeps
it pinned until FR-707 removes it.

## The trap the Judgement caught

The proposed fixture — `threading.Event().wait()` inside the candidate's
`ainvoke` — would have blocked the *background* loop before its own timeout
could fire. The witness would have hung forever: a test that cannot fail is
useless, but a test that cannot *finish* is worse — it condemns nothing and
blocks CI. The fix was fixture physics: `asyncio.to_thread(time.sleep, 5)` is
uncancellable (faithful to provider HTTP threads) but bounded (the test
always terminates, in both verdicts).

Naming it: **the witness must be un-hangable by construction**. When testing
"does X block?", the hazard is that the test itself inherits X's blocking.
Every liveness test needs an escape guaranteed by something *outside* the
mechanism under test — here, the bounded mock; never an on-loop watchdog,
which dies with the loop it watches.

## The second insight

`investigation_before_fix`, quantified: the investigation FR cost half a day
and replaced a multi-day live-load observation plan. The discriminating fact
(CPU available vs loop blocked) was already in the incident timeline (<2 s
flush after teardown); the witness only had to reconstruct the seam
mechanically. When the evidence already eliminates one hypothesis, build the
deterministic reconstruction, not the observation rig.

**Seed:** `_run_coro_sync_safe` is a generic bridge — every sync node that
wraps async work under a running loop has this shape. Should the framework
have ONE deadline-aware bridge primitive (join with timeout + abandon +
telemetry) that race, map, and future async-wrapping nodes all use, instead
of each node type rediscovering the stall?
