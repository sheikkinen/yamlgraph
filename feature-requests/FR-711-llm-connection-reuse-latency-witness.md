# Feature Request: FR-711 LLM Connection-Reuse Latency Witness (condemn-or-absolve the client pool)

**Priority:** MEDIUM
**Type:** Investigation (measurement; FR-706-shaped — the deliverable is a verdict with numbers, not architecture)
**Status:** Judged
**Effort:** 0.5–1 day
**Requested:** 2026-07-10
**Judged:** 2026-07-10 — scope frozen. 6 findings resolved (see Judgement section); cache and bridge claims re-verified at source.
**Related:** FR-708 (request timeout + `VERTEX_TRANSPORT`), FR-709 (pool-for-safety absolved), FR-710 (deadline floors), rate-layer diary 2026-07-10; field site: projects/ninchat_voice

## Summary

Measure what one LLM call costs at the **connection layer** when the client
object is warm but the event loop is fresh — the actual production topology
of every race-node turn. Verdict rule fixed up front: below the threshold,
the pooling seed is closed for good; above it, the numbers write the
architecture FRs (FR-A persistent bridge loop / FR-B cache loop-affinity).

## Value Statement

The pool is currently a plausible architecture with one absolving datapoint
(FR-709: zero thread growth — pool-for-safety dead) and zero condemning
ones. One afternoon of measurement either kills the idea permanently or
funds it with field numbers — either way, no more re-litigating.

## Problem — the boundary is loop-affinity, not construction

Prior framing ("are clients reconstructed constantly?") measures the wrong
boundary. Verified 2026-07-10:

- **Object layer: cached.** `yamlgraph/utils/llm_factory.py` `_llm_cache`
  (keyed provider/model/temperature/max_tokens/thinking_budget,
  thread-locked). Race-node `create_llm()` per candidate is a cache hit
  after first use.
- **Connection layer: cannot survive the bridge.**
  `race_node.py::_run_coro_sync_safe` runs `asyncio.run()` in a fresh
  daemon thread on BOTH entry paths — every race execution gets a new
  event loop. httpx pools and gRPC aio channels are loop-bound; the cached
  object silently opens fresh connections in each new loop.
- **Field arithmetic (ninchat_voice):** `flex_navigator` is race-heavy
  (classify_intents, extract_fields, classify_recap, classify_more,
  answer_recap_question — NC-345/NC-346). A caller turn = 1–3 race
  executions × 2 candidates (NC-339 fleet: vertex/gemini-2.5-flash +
  azure/aaa-gpt-5.4-mini) = **2–6 TLS/gRPC handshakes per spoken turn**,
  doubled on an NC-352 retry. Voice latency is the currency that matters
  most there.
- gRPC channel setup is the prime suspect: the 2026-07-10 fly freeze RCA
  (ninchat_voice `rca-20260710-fly-freeze.txt`, 25/25 unbounded gemini
  gRPC hangs) already shows this layer is where ninchat's production pain
  lives.

## Raw Output Read

- **Samples read:** ninchat_voice `rca-20260710-fly-freeze.txt` (25/25
  hung calls, all gemini gRPC, no deadline); `llm_factory.py` L150–187
  (cache present — "reconstruction" premise false as stated);
  `race_node.py` L175–215 (fresh loop per execution — the real recurring
  cost is not visible in any existing metric, only in the topology).
- **What I saw:** the freeze RCA's hangs are all in channel/transport
  territory, not inference; and the factory logs `Creating LLM` only once
  per key per process — meaning no existing log line records the per-loop
  reconnect at all. The cost this FR measures is currently **invisible in
  every artifact we emit**.

## Proposed Solution

**Instrument 1 — local micro-witness** (`scripts/fr711_conn_witness.py`):
per provider in the ninchat race fleet (vertex, azure) + anthropic
control, with a warm `_llm_cache`, time a minimal `ainvoke`:

- **Arm A (same loop):** one loop, N sequential calls → per-call latency
  floor with connection reuse.
- **Arm B (fresh loop per call, production topology):** each call under
  `_run_coro_sync_safe` → per-call latency with forced reconnect.
- **Report:** `B − A` = handshake cost per provider; cold construction as
  a secondary column only.

**Instrument 2 — fly probe** (now unblocked: ninchat pins yamlgraph
0.5.10): `VERTEX_TRANSPORT=rest` vs grpc A/B on the deployed box +
LangSmith per-turn latency split (construction/connect vs inference) for
real flex_navigator turns. The deployed network path is where handshakes
hurt; laptop numbers alone do not condemn.

**Verdict rule (frozen before measurement):**
- Jurisdiction (F1): the verdict is rendered on **Instrument 2 (deployed)**
  numbers — neither direction of the local/deployed gap bounds the other
  (Fly's datacenter RTT to google may be lower than a laptop's).
  Instrument 1 is mechanism-proof and per-provider decomposition; wild
  local/deployed disagreement blocks the verdict pending investigation.
- `(B − A) × handshakes-per-turn < 100 ms` on the deployed path →
  **ABSOLVE**: close the pooling seed, record the numbers, no pool ever
  without new evidence.
- `≥ 100 ms` → **CONDEMN**: file FR-A (persistent bridge loop — one
  long-lived loop thread owned by the bridge; independently kills the
  FR-707 shutdown blocker class) and FR-B (loop-stable connections for the
  EXISTING `_llm_cache` + env-fingerprint invalidation per FR-227 — not a
  new registry). Pre-listed judge hazards for FR-B: **fork-safety**
  (ninchat supervisor forks workers — assert `_llm_cache` empty pre-fork),
  shutdown draining, staleness semantics.
- Cross-loop-reuse basis (F2): "cached object silently reconnects per
  loop" is field-verified for anthropic + google by FR-709 (3 races ×
  fresh loops, cached clients, zero errors). If Arm B instead ERRORS for
  any provider, that is itself a recorded finding, not a witness bug.

## Acceptance Criteria

- [ ] AC-01 Micro-witness produces the A/B table (N ≥ 20 calls/arm,
      p50/p95); providers: google-family arm REQUIRED (the gRPC suspect;
      `google` may substitute for `vertex` locally, annotated — same SDK
      transport family), azure desired, anthropic control; missing keys
      skip with a named reason (F3). Raw timings committed to
      `docs/analysis/fr711-conn-witness-2026-07-10.txt` (F5).
- [ ] AC-02 Arm B uses the real `_run_coro_sync_safe`, not a simulated
      loop — the witness exercises the production bridge; default
      `LLM_REQUEST_TIMEOUT` respected (≥ FR-710 floors).
- [ ] AC-03 Fly probe: `VERTEX_TRANSPORT=rest` vs grpc per-turn split from
      LangSmith on ≥ 10 real flex_navigator turns each — **executed from
      the ninchat_voice side** (F4: one session, one repo), results folded
      into this FR.
- [ ] AC-04 Per-turn cost computed for ninchat_voice using measured
      handshake × actual race-execution count per turn (from a suite-run
      trace, not the 1–3 estimate) — ninchat_voice side (F4).
- [ ] AC-05 Verdict recorded against the frozen rule on deployed numbers
      (F1); seed closed OR FR-A/FR-B filed with the numbers embedded. No
      third outcome.
- [ ] No REQ/changelog (investigation script + verdict, no production
      branch changed); diary entry required (F6).

## Judgement (2026-07-10)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | Verdict jurisdiction ambiguous — rule says "deployed path", Instrument 1 is local; neither bounds the other | Verdict on Instrument 2 numbers; Instrument 1 = mechanism proof + decomposition; wild disagreement blocks verdict |
| F2 | "Silently reconnects per loop" could instead ERROR (loop-bound clients) | Field-verified tolerant for anthropic+google by FR-709 (3 races × fresh loops, cached, zero errors); an Arm-B error is a finding, not a bug |
| F3 | Fleet keys locally unknown (azure/vertex creds) | Skip-with-reason per provider; google-family arm required, google↔vertex substitution annotated |
| F4 | AC-03/04 live in another repo/session | Executed from ninchat_voice; this FR lands its local instrument independently; AC-05 waits for both halves |
| F5 | Artifact location unpinned | docs/analysis/fr711-conn-witness-2026-07-10.txt |
| F6 | Traceability for an investigation script | No REQ/changelog (no production branch); diary required |

**Out of scope (purge list):** the pool itself (FR-A/FR-B only on CONDEMN),
bridge changes, cache changes, new metrics infrastructure, provider floors
(FR-710 shipped).

## Alternatives Considered

- Build the pool first, measure later — rejected: plausible architecture
  with zero condemning datapoints; the next artifact must be a measurement
  (rate-layer diary discipline).
- Measure `create_llm()` construction cost — rejected: measures a cache
  hit; the correlate, not the property (the recurring cost is
  loop-crossing reconnect).

## Related

- ninchat_voice consumers: NC-345/346 race nodes, NC-352 retry (doubles
  handshakes on failure), NC-356 campaign (per-turn latency vs baseline is
  an ST-01 metric — this witness's numbers become its baseline
  decomposition).
- FR-709 witness suite guards the bridge contract through any follow-up
  FR-A change.
