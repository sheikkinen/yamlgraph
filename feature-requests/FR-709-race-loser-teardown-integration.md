# FR-709: Real-provider race loser-teardown integration test

**Priority:** MEDIUM
**Type:** Test (real-phenomenon witness)
**Status:** Completed
**Effort:** 0.5 day
**Requested:** 2026-07-10
**Judged:** 2026-07-10 — scope frozen. 6 findings resolved (see Judgement section); the draft's own thread-baseline invariant was flaky by construction (F1) and its teardown window mixed layers of the very stack the parent arc documented (F2).
**Completed:** 2026-07-10 — PASSED on live transport; two field findings below.

## Implementation (2026-07-10)

**Run log (local, both keys present, verbatim):**

```
FR-709 shapes: race1: winner=anthropic loser=google verdict=0.74s;
race2: winner=anthropic loser=google verdict=1.22s;
race3: winner=anthropic loser=google verdict=1.95s | abandon-warnings: 0
1 passed, 4 warnings in 9.66s
```

- All four invariants held in the `winner+in-flight-loser` shape ×3: verdicts far under the 9 s budget; threads settled to the post-warm-up baseline after every race; no `race-bridge` survivors; **zero net growth over 3 races** — the Fly-freeze accumulation signature is absent on live channels post-FR-707/708. First datapoint for the rate-layer gate (diary 2026-07-10): local evidence says FR-710 is NOT needed; the Fly probe remains the deployed-environment check.
- Clean drain every race (0 abandon-WARNINGs): real cancelled gemini tasks acknowledged cancellation within `CLEANUP_GRACE` — the abandon path stayed cold on healthy endpoints, as designed.

**Field finding 1 (F2 fixture corrected by reality):** google rejects client
deadlines below its floor — `400 INVALID_ARGUMENT: "Manually set deadline 5s
is too short. Minimum allowed deadline is 10s."` The judged
`LLM_REQUEST_TIMEOUT=5` fixture was invalid for google; the test runs at the
floor (10 s). **Consumer implication for FR-708:** any deployment setting
`LLM_REQUEST_TIMEOUT < 10` breaks the google provider outright — surfaced
loudly (400 at request time), but worth knowing before the Fly probe.

**Field finding 2:** the stale `claude-3-5-haiku-latest` id 404s; current id
`claude-haiku-4-5` used. Model ids in tests rot; the census lives in the
repo's own usage (83 occurrences), not memory.

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
2. **After a per-provider warm-up call** (F1: SDKs spawn persistent pool/poller threads on first use — baseline is taken post-warm-up, never pre-race): zero net thread growth from the post-warm-up baseline, measured within `LLM_REQUEST_TIMEOUT + margin` after return (F2: an abandoned loser legally lives until the CLIENT timeout, not CLEANUP_GRACE — the layers must not be mixed), plus name-based absence of any `race-bridge` thread.
3. Log discipline: either a clean drain (no abandon-WARNING) **or** the WARNING naming the abandoned candidate by task name — both recorded to the test log; anything else (anonymous WARNING, unnamed exception) fails.
4. Repeatability: 3 consecutive races in one process show no monotonic thread growth from the post-warm-up baseline (the Fly-freeze accumulation signature, now against real channels).

Shape dispatch is explicit (F4): an if/elif over the three outcomes with the
taken shape recorded; an unrecognized shape fails the test rather than
falling through.

### Mechanics

- `tests/integration/test_race_loser_teardown.py`, guarded by presence of BOTH `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` (F3: the two keys the integration suite already guards on; providers `anthropic` + `google` — "vertex loses" becomes "gemini loses", same transport family; `VERTEX_TRANSPORT` is out of scope, covered by FR-708 units); skip reason names the missing key; `@pytest.mark.slow`; total budget ≤ 60 s (F2 recomputation: worst case 3 races × verdict + final settle ≤ LLM_REQUEST_TIMEOUT).
- Candidates biased toward the desired shape without depending on it: anthropic `claude-3-5-haiku` vs google `gemini-2.5-pro` (heavier model more likely to lose a 3 s race) — bias documented as bias, not contract.
- `LLM_REQUEST_TIMEOUT=5` for the test (env fixture, F2) so FR-708 bounds any pathological residue inside the test budget.
- Graph: minimal `create_race_node` node_config with a **test-local fixture prompt** resolved via `prompts_dir` (F6) — no coupling to the demo graph; the unit of interest is the node factory against real transports.
- Prompt: trivial fixed question; output irrelevant to every assertion (this test is about teardown, not content — one job).

### Explicitly NOT this FR

- No mocked variants (they exist: FR-706/707 witnesses).
- No hang injection against live providers (cannot force a real endpoint to hang on demand; the pathological path stays covered by mocks + the consumer Fly probe).
- No CI-gating: integration layer, key-guarded, excluded from the PR-required `test` job as all integration tests already are.

## Acceptance Criteria

- [ ] Test skips cleanly (reason names the missing key) without either API key; runs with both
- [ ] Per-provider warm-up precedes the baseline; all four teardown invariants asserted in whichever outcome shape occurs; the shape taken is printed to the test log; unrecognized shape fails (F1/F4)
- [ ] Repeatability loop (3 races) shows zero net thread growth from the post-warm-up baseline
- [ ] Wall-clock bound: full test ≤ 60 s including settle windows (bounded-witness rule from FR-706: un-hangable by construction) (F2)
- [ ] Runs recorded: at least one local run pasted into this FR's Implementation section with the observed shape, timings, and drain/WARNING result (read_raw_output_first — the first artifact of a real-transport test is its own log)
- [ ] Tagged `@pytest.mark.req("REQ-YG-269")` (F5 — race must not block on slow losers; no new REQ)
- [ ] `req_coverage --strict` green; changelog fragment (test scope) + diary entry

## Judgement (2026-07-10)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | Pre-race thread baseline is flaky by construction — SDKs spawn persistent pool/poller threads on first use | Warm-up call per provider; baseline post-warm-up; name-based race-bridge absence + zero net growth |
| F2 | "Baseline within CLEANUP_GRACE" mixes layers — an abandoned loser legally lives until the CLIENT timeout (FR-708 bound) | LLM_REQUEST_TIMEOUT=5 fixture; settle window = client timeout + margin; total budget ≤ 60 s |
| F3 | "vertex/google" key ambiguity | Pinned: anthropic + google (keys the suite already guards on); VERTEX_TRANSPORT out of scope |
| F4 | Shape variance across runs could silently skip assertions | Explicit three-branch dispatch; unrecognized shape fails |
| F5 | REQ unpinned | REQ-YG-269 under CAP-91; no new REQ |
| F6 | Demo-graph reuse couples the constraint test to demo maintenance | Test-local fixture prompt via prompts_dir; direct create_race_node config |

**Out of scope (purge list):** mocked variants, hang injection against live endpoints, VERTEX_TRANSPORT dimension, gRPC-internal channel assertions, CI-gating, demo changes.

## Alternatives Considered

1. **Demo in examples/demos/ instead of a test** — demos prove an abstraction is worth having; this proves a constraint holds. Constraint → test (demo_vs_test doctrine). The existing race demo already demonstrates the feature.
2. **Force vertex to lose via an unroutable endpoint** — that tests connection-refused, not cancellation of live work; refused connections fail fast and never exercise the drain. Rejected.
3. **Assert gRPC channel count via SDK internals** — brittle private-API coupling; the thread-population proxy plus repeatability loop covers the accumulation signature without it. Rejected.

## Related

- FR-707 (drain + verdict budget — the contract under test), FR-708 (client bounds active during the test), FR-706 (witness pattern: bounded, un-hangable), FR-705 (naming contract asserted in the neither-completes shape)
- ninchat_voice NC-361 / Fly freeze RCA (the accumulation signature the repeatability loop guards)
- CAP-91 (race node type, REQ-YG-269)
- Doctrine: `mock_escape_hatch`, `assert_path_not_destination`, `name_the_seam` (file name says loser-teardown, not "race e2e")
