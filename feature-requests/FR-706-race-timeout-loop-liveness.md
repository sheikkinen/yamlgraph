# FR-706: Race node timeout path must not block the host event loop (condemn-or-absolve witness)

**Priority:** HIGH
**Type:** Bug investigation / witness test
**Status:** Judged
**Effort:** 0.5 day
**Requested:** 2026-07-10
**Judged:** 2026-07-10 — scope frozen. 6 findings resolved (see Judgement section); source read predicts CONDEMNED (blocking `t.join()` on the loop thread at `_run_coro_sync_safe`, running-loop branch).
**Spawned by:** ninchat_voice NC-361 (PAR-02 run-5 hard stall, evidence
`projects/ninchat_voice/logs/nc361-timeline.txt`)
**Companion:** FR-705 (race timeout error fidelity — same incident, error
*message*; this FR is the error *behavior*)

## Summary

Production evidence (NC-361, deployed yamlgraph in ninchat_voice v86) shows
that after a race node timeout (`AllCandidatesFailedError`, both candidates
pending), the **host process's event loop hard-stalled for 320–340 s** — zero
event processing, zero log flushes — and was unblocked only by external
teardown (WS close), which then flushed ~5 minutes of queued events in <2 s.
The <2 s flush proves CPU was available: the loop was *blocked*, not starved.
The traceback runs through `race_node.py` `_run_coro_sync_safe` — **which
still exists on current main** (`race_node.py:169`, called at `:267`).

Whether current main still has this behavior is unknown. This FR settles it
with one witness test, in either direction:

- **Test FAILS on main** → it is the condemning test (Commandment 7); a fix
  FR follows referencing it.
- **Test PASSES on main** → it lands as the regression witness (absolution),
  and the NC-361 redeploy recommendation ("main fixes the silent-stall link")
  gets its proof instead of remaining a hypothesis.

Either outcome is a deliverable. A fix without this test is a hypothesis; a
redeploy without it is the same hypothesis wearing an ops costume.

## The witness test (name_the_seam: sync-bridge-called-on-loop-thread)

Reconstruct the production composition, minimally (pins from Judgement):

1. Graph with a `race` node, 2 mock candidates whose `ainvoke` is
   `await asyncio.to_thread(time.sleep, HANG)` with `HANG ≈ 5 s` (F2) —
   uncancellable-but-bounded, mirroring provider HTTP threads pending at the
   deadline. **Not** `threading.Event().wait()` inside `ainvoke`: that blocks
   the background loop before its own timeout can fire and the test hangs
   forever instead of failing.
2. Call the sync `node_fn(state)` **directly inside a coroutine on the host
   loop** (F1) — the NC-361 traceback proves the running-loop branch of
   `_run_coro_sync_safe` was taken, so the faithful seam is
   node-on-loop-thread, no LangGraph `ainvoke` machinery.
3. A concurrent heartbeat task on the host loop ticking every 100 ms,
   recording timestamps.
4. Assert (F3 — order-of-magnitude thresholds, race `timeout=0.5s`):
   - the race node returns/raises within 2.5 s (blocked behavior ≈ 5 s);
   - max heartbeat gap < 2 s during and after the timeout (blocked ≈ 5 s);
   - thread accounting: `threading.enumerate()` delta returns to baseline
     within grace ≤ HANG after the node call (F4).

Termination is guaranteed by the bounded mock, not by a loop-side watchdog —
an on-loop `wait_for` cannot fire while the loop is blocked (F4).

## Acceptance Criteria

- [ ] Witness test exists (`tests/unit/test_fr706_race_timeout_loop_liveness.py`),
      tagged `@pytest.mark.req("REQ-YG-269")` (F5: "race must not block on
      slow losers" — liveness is its statement); exercises the
      node-on-loop-thread seam per F1, not just direct sync invocation
- [ ] Test run against current main; outcome recorded in this FR
      (CONDEMNED → fix FR reference | ABSOLVED → regression pin merged)
- [ ] If condemned: test lands with `@pytest.mark.xfail(strict=True,
      reason="FR-7xx")` (F6) — mechanically documents the defect and errors
      the moment a fix makes it pass; the fix FR removes the marker as its
      RED→GREEN
- [ ] Thread accounting asserted: `threading.enumerate()` delta returns to
      baseline within grace ≤ HANG post-timeout (F4)
- [ ] Suite-safety: the test terminates in bounded time in BOTH verdicts
      (bounded mock hang; no on-loop watchdog reliance)
- [ ] `req_coverage.py --strict` green; changelog fragment (fix or test
      scope) + diary entry
- [ ] NC-361 (ninchat_voice) updated with the verdict — its H2/R-3 AC closes
      on this test's result plus the timeline evidence

## Judgement (2026-07-10)

Scope frozen. The source already indicts: the running-loop branch of
`_run_coro_sync_safe` ends in a blocking `t.join()` on the calling thread;
when the caller is the loop thread, the loop stalls for as long as the
background `asyncio.run` takes — whose `finally: await gather(…)` waits for
uncancellable loser work. That is the 320–340 s shape (provider socket
timeouts), not the 10 s race timeout. Findings:

| # | Finding | Resolution |
|---|---------|------------|
| F1 | "Under ainvoke" ambiguous; LangGraph may shield sync nodes via executor threads | Pin: call `node_fn` directly on the loop thread — the traceback proves that branch was taken in production |
| F2 | `threading.Event().wait()` mock blocks the bg loop before its timeout fires → test hangs instead of failing | Pin: `await asyncio.to_thread(time.sleep, HANG)`, HANG ≈ 5 s — uncancellable but bounded |
| F3 | 500 ms gap threshold is CI-flaky | Pin: timeout 0.5 s / hang 5 s / gap threshold 2 s / return threshold 2.5 s — order-of-magnitude separation |
| F4 | On-loop watchdog cannot fire while the loop is blocked | Termination guaranteed by bounded mock; thread delta with grace ≤ HANG |
| F5 | REQ unpinned | REQ-YG-269 |
| F6 | A committed always-failing test breaks every commit | xfail(strict=True) on condemnation; fix FR removes the marker |

**Out of scope (purge list):** the fix itself (separate FR), LangGraph-`ainvoke` executor-shielding variant, v86-pinned reproduction, load rigs / py-spy observation (NC-361 H2 fallback), changes to `_run_coro_sync_safe`.

## Relationship to NC-361 R-3

NC-361's judged H2 fallback (live PAR-02 + py-spy under load) discriminates
CPU-vs-loop starvation *observationally*. This test discriminates it
*mechanically and deterministically* — no load rig, no phone calls — because
the timeline evidence already eliminated CPU starvation (the <2 s flush).
Load's only proven role was making the 10 s timeout fire; the stall itself is
reproducible (or not) from the timeout alone. If this test ABSOLVES main and
the v86 stall needs positive confirmation, the optional v86-pinned
reproduction remains available but is no longer on the critical path.

## Related

- NC-361 evidence: `projects/ninchat_voice/logs/nc361-timeline.txt`,
  `nc361-langsmith-detail.txt` (traceback through `_run_coro_sync_safe`)
- FR-705 (error message must enumerate pending candidates)
- FR-267/270/271 (race timeout / pool shutdown / asyncio rewrite lineage)
- User-level known behavior: race loser HTTP threads as non-daemons delay
  interpreter exit (pytest observation) — same thread population, different
  symptom
- Doctrine: Commandment 7 (witness test for every production branch),
  `investigation_before_fix`, `assert_path_not_destination` (heartbeat
  continuity during the timeout, not just the final return value)
