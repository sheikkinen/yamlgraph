# The Timer Nobody Cancelled

**Date:** 2026-08-30
**FR:** FR-921 (network-sniff test window and xdist safety)

## What happened

FR-921 filed a real symptom: the FR-784 sniff tests each consumed their full
`--timeout` window, and six of them failed under `-n auto`. The FR's diagnosis
named settle detection — `waitUntil: "networkidle"` presumably not firing — and
proposed shrinking the windows plus adding an `xdist_group` to serialise them.
Two mitigations, one hypothesis, no failing test.

The judge falsified a load-bearing premise before I wrote a line: the FR claimed
the cost hit the fast loop. It does not. The tests are already `slow`-marked
(9/15 collected, 6 deselected), and CI has no `npm ci` step, so all six *skip*
in CI. The entire cost lands in exactly one place — the operator's local
full-suite run. Priority went HIGH → MEDIUM and the fast-loop claims were
deleted rather than fixed.

Then I read the file instead of theorising about it:

```js
await Promise.race([
  Promise.allSettled(pending),
  new Promise((resolve) => setTimeout(resolve, remaining())),
]);
```

`Promise.race` settles on the fast path, but the loser's `setTimeout` is never
cleared. `main()` ends with a `process.stdout.write` and no `process.exit()`, so
Node's event loop stayed alive until the orphaned timer fired — at the deadline.
Settle detection was never broken. Only the *exit* was late.

One `clearTimeout` and the module went 82.20s → 13.26s; per-sniff 15.4s → 1.2s.

## The traps

**`symptom_patch` in the FR's own proposal.** Both proposed mitigations —
shorter windows and `xdist_group` — would have worked. Shrinking the timeout
would have shortened the floor; serialising would have hidden the parallel
failures. Neither touches the timer. The suite would have gone green with the
defect intact, and every future timeout value would have silently been a
duration rather than a bound.

**The tell was in the data and I nearly walked past it.** The 4-second
hanging-fixture witness took 4.43s before and 4.41s after — *unchanged*, while
everything else collapsed by 12×. A settle-detection bug would have moved that
number too. An exit bug leaves genuinely-slow work exactly where it was. The
test that did **not** change was the strongest evidence about what did.

**The xdist failures were assumed, then verified.** I did not add `xdist_group`.
Three `-n auto` runs after the timer fix: 16 passed in 14.22s, 12.29s, 12.70s —
previously six failures every time. The parallel failures were the same defect
wearing a concurrency costume. Adding the group would have been a second cure
for an already-cured disease, permanently taxing the parallel lane.

## The heuristic

**`configured_bound_is_a_floor`** — when a timeout, budget, or limit is observed
being *consumed* rather than *bounding*, the defect is in teardown, not in
detection. Something the fast path created is still alive. Look for the loser of
the race — the uncleared timer, the unclosed handle, the unjoined thread — before
you touch the thing the bound was supposed to measure. A ceiling that is always
reached is not a slow operation; it is a leak with a schedule.

Corollary, now twice-proven in one session: **read the artifact before
modelling it.** `read_raw_output_first` is filed under LLM prose, but it
generalises — for a latency bug the "raw output" is the source of the thing
being timed. One read of 40 lines of JavaScript ended a hunt that a
timeout-tuning FR had already committed to.

## Seed

The fix was invisible to the test suite for as long as the tests were skipped in
CI and slow-marked locally — a defect can only be found where it is executed.
FR-784's sniffer has never once run in CI, because Playwright is installed
nowhere but this machine.

**Seed:** how many other capabilities does this repo believe it has tested that
have never executed outside one laptop? `req_coverage.py` counts tests that
*exist*; it cannot see which ones *skip everywhere*. Is a skip-rate-by-requirement
report the honest companion to the coverage number — and would it have flagged
REQ-YG-590 as an uncovered claim months ago?
