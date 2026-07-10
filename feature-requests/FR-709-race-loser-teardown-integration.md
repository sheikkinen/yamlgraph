# FR-709: Real-provider race loser-teardown integration test

**Priority:** MEDIUM
**Type:** Test (real-phenomenon witness)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-07-10
**Parent arc:** FR-705/706/707/708 (NC-361 layer stack: message → witness → wait → work) — every witness so far is mocked; this FR exercises the real transport
**Doctrine driver:** `mock_escape_hatch` — cancellation of live TLS/gRPC work is a physical phenomenon; a mocked loser is a unit test with extra steps

## Summary

An API-key-guarded integration test racing **two live providers** (e.g. anthropic haiku vs vertex/google gemini) with a **3 s race timeout**, asserting the FR-707 teardown contract against real transports: verdict at the deadline, loser drained or abandoned-with-WARNING within `CLEANUP_GRACE`, thread population back to baseline, no lingering work. The FR-706/707/708 witnesses proved the design against mocks; this test proves it against the phenomenon the whole arc exists for — real provider connections under cancellation.

## Problem

The NC-361 arc shipped four fixes whose end-to-end composition has never run against a live SDK inside the framework's own test suite:

- FR-707's drain cancels real asyncio tasks wrapping real HTTP/gRPC work — mocks cannot tell us whether live `ainvoke` tasks acknowledge cancellation within `CLEANUP_GRACE` or routinely trip the abandon-WARNING.
- FR-708's client timeout is asserted only as a constructor parameter (Judgement F4 honesty bound); whether the SDK honors it on a cancelled-then-drained loser is unobserved.
- The consumer-side Fly probe verifies the *deployment*, not the framework: a framework regression in loser teardown would next surface as a production incident, not a test failure.

## Design

### The outcome-agnostic invariant (assert_path_not_destination)

"Assuming vertex will lose" is an environment-dependent hope, not a test contract. The test must **not** depend on who wins. Whatever happens in the 3 s window, exactly one of three shapes occurs, and each has a teardown invariant:

| Outcome | Assertion |
|---------|-----------|
| One provider wins, other in-flight | `_race_winner` names the winner; loser cancelled; teardown invariants below |
| Both complete < 3 s | winner named; loser (completed) leaves nothing behind; same invariants |
| Neither completes | `AllCandidatesFailedError` naming BOTH (FR-705); same invariants |

**Teardown invariants (the actual subject), asserted in all three shapes:**
1. Node returns/raises within `3 + CLEANUP_GRACE + margin` wall-clock (FR-707 verdict budget honored on real transport).
2. Within `CLEANUP_GRACE + margin` after return: `threading.enumerate()` back to pre-race baseline (no `race-bridge` thread, no SDK transport threads surviving).
3. Log discipline: either a clean drain (no abandon-WARNING) **or** the WARNING naming the abandoned candidate by task name — both recorded to the test log; anything else (anonymous WARNING, unnamed exception) fails.
4. Repeatability: 3 consecutive races in one process show no monotonic thread growth (the Fly-freeze accumulation signature, now against real channels).

### Mechanics

- `tests/integration/test_race_loser_teardown.py`, guarded by presence of BOTH providers' keys (skip with reason naming the missing key); `@pytest.mark.slow`; total budget ≤ ~30 s.
- Candidates biased toward the desired shape without depending on it: anthropic `claude-3-5-haiku` vs google `gemini-2.5-pro` (heavier model more likely to lose a 3 s race) — bias documented as bias, not contract.
- `LLM_REQUEST_TIMEOUT=10` for the test (env fixture) so FR-708 bounds any pathological hang inside the test budget.
- Graph: reuse [examples/demos/race](../examples/demos/race/) graph with `--var`-style overrides if its shape fits; otherwise a minimal inline node_config through `create_race_node` (decision at enforce — prefer reuse per Commandment 4).
- Prompt: trivial fixed question; output irrelevant to every assertion (this test is about teardown, not content — one job).

### Explicitly NOT this FR

- No mocked variants (they exist: FR-706/707 witnesses).
- No hang injection against live providers (cannot force a real endpoint to hang on demand; the pathological path stays covered by mocks + the consumer Fly probe).
- No CI-gating: integration layer, key-guarded, excluded from the PR-required `test` job as all integration tests already are.

## Acceptance Criteria

- [ ] Test skips cleanly (reason names the missing key) without either API key; runs with both
- [ ] All four teardown invariants asserted in whichever outcome shape occurs; the shape taken is printed to the test log (observability of the path, not just the verdict)
- [ ] Repeatability loop (3 races) shows zero net thread growth
- [ ] Wall-clock bound: full test ≤ 30 s including drains (bounded-witness rule from FR-706: un-hangable by construction)
- [ ] Runs recorded: at least one local run pasted into this FR's Implementation section with the observed shape, timings, and drain/WARNING result (read_raw_output_first — the first artifact of a real-transport test is its own log)
- [ ] Tagged with the appropriate existing REQ (REQ-YG-269 lineage — race must not block on slow losers) or new REQ under CAP-91; id verified against origin at enforce
- [ ] `req_coverage --strict` green; changelog fragment (test scope) + diary entry

## Alternatives Considered

1. **Demo in examples/demos/ instead of a test** — demos prove an abstraction is worth having; this proves a constraint holds. Constraint → test (demo_vs_test doctrine). The existing race demo already demonstrates the feature.
2. **Force vertex to lose via an unroutable endpoint** — that tests connection-refused, not cancellation of live work; refused connections fail fast and never exercise the drain. Rejected.
3. **Assert gRPC channel count via SDK internals** — brittle private-API coupling; the thread-population proxy plus repeatability loop covers the accumulation signature without it. Rejected.

## Related

- FR-707 (drain + verdict budget — the contract under test), FR-708 (client bounds active during the test), FR-706 (witness pattern: bounded, un-hangable), FR-705 (naming contract asserted in the neither-completes shape)
- ninchat_voice NC-361 / Fly freeze RCA (the accumulation signature the repeatability loop guards)
- CAP-91 (race node type, REQ-YG-269)
- Doctrine: `mock_escape_hatch`, `assert_path_not_destination`, `name_the_seam` (file name says loser-teardown, not "race e2e")
