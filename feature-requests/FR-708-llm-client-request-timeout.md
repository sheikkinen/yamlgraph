# FR-708: Bound provider work at the client boundary — request timeout on every create_llm client

**Priority:** HIGH
**Type:** Bug
**Status:** In Progress
**Effort:** 1 day
**Requested:** 2026-07-10
**Judged:** 2026-07-10 — scope frozen. 6 findings resolved (see Judgement section); root cause re-verified at source (zero timeout/max_retries across all 11 provider constructors; both vertex branches use ChatGoogleGenerativeAI so the transport knob plumbs uniformly).
**Spawned by:** ninchat_voice RCA `docs/analysis/rca-20260710-fly-freeze.txt`
(Fly test-VM total freeze under load; sequel to NC-361/FR-706/FR-707)

## Summary

A provider endpoint that hangs (never completes, never errors) currently
hangs **forever**: `create_llm()` constructs clients with no request
timeout, race-loser cancellation kills the asyncio task but not the
underlying transport work, and FR-707's bridge bounds only the verdict
wait. Production evidence: from a Fly VM, **25/25 `ChatGoogleGenerativeAI`
invocations hung indefinitely** (0 success) while the same code completed
100% locally — each race turn leaked a live gRPC channel until the VM
seized entirely (~8 min, even sshd starved). LLM-run census and chain in
the RCA.

FR-707 bounded the WAIT. This FR bounds the WORK — at the boundary where
it enters (`the_one_law`): the provider client.

## Root cause (code-verified)

- `yamlgraph/utils/llm_providers.py` `_create_vertex_llm` (and sibling
  provider constructors): no `timeout` / `max_retries` passed —
  SDK-default unbounded requests, gRPC transport in vertexai mode.
- `race_node.py _invoke_candidate_async`: `create_llm()` **per candidate
  per turn** — fresh channel each time, no close path; `loser.cancel()`
  is cooperative and cannot interrupt transport-level hangs.
- `_run_coro_sync_safe`: `asyncio.run()` exit waits on
  `shutdown_default_executor()` — a hung executor-backed call also strands
  the `race-bridge` daemon thread.

## Proposed Solution

1. **Universal request timeout (the fix):** every provider constructor in
   `llm_providers.py` sets an explicit request timeout and bounded retries
   via a per-wrapper parameter map (F1): `timeout=` for the
   ChatOpenAI/ChatAnthropic/ChatGoogleGenerativeAI/ChatMistralAI families,
   `request_timeout=` for ChatLiteLLM (replicate); `max_retries=2` where
   the wrapper supports it. Any wrapper genuinely lacking a timeout
   parameter is a **documented exception in this FR**, never a silent
   skip. Default `LLM_REQUEST_TIMEOUT=30` s, env-overridable — parsed once
   in a helper; a garbage value **raises** (no silent fallback to the
   default, Commandment 6) (F5). The race deadline and the client timeout
   are independent layers — race bounds the wait, client bounds the work;
   no plumbing connects them (F2). A hung endpoint then FAILS in 30 s:
   per-candidate error surfaces with the provider's name (FR-705), the
   race hedge keeps working, nothing accumulates.
2. **Transport knob for google/vertex:** `VERTEX_TRANSPORT=rest|grpc`
   (default unchanged) passed as `transport=` to **both** the `google` and
   `vertex` constructors (same wrapper, same suspected hanging layer);
   value validated at the boundary, anything else raises (F5). REST rides
   httpx and honors timeouts reliably; gRPC-from-Fly is the suspected
   hanging layer. One env var makes the environment-specific mitigation
   configuration, not code.
3. **Explicitly NOT in scope:** per-turn client caching/reuse, transport
   close on loser cancellation (with bounded requests the leak window is
   ≤ timeout — accumulation impossible), race node changes (FR-707 stands).

## Acceptance Criteria

- [ ] RED: parametrized provider-matrix test asserting every constructed
      client carries an explicit finite request timeout — fails today per
      provider (mock construction, no network) (F3)
- [ ] GREEN: matrix passes with the wrapper-correct parameter per F1;
      documented-exception list empty or justified per wrapper
- [ ] `LLM_REQUEST_TIMEOUT` env override honored; invalid value raises
      (unit test); default 30 s
- [ ] `VERTEX_TRANSPORT=rest` plumbs `transport="rest"` into
      ChatGoogleGenerativeAI in google + vertex constructors (express and
      ADC branches); invalid value raises; unit tests
- [ ] Honesty bound (F4, mock_escape_hatch): no test claims a mocked hang
      validates SDK timeout behavior — the unit gate is the param matrix;
      end-to-end hang verification is the consumer-side Fly probe
      (non-gating, below); thread-accumulation regression stays covered by
      the FR-706/707 witness suite
- [ ] FR-705 contract intact: a failed candidate appears BY NAME in errors
      (existing tests green)
- [ ] New REQ under the capability owning the LLM factory — id verified
      free against origin/main at enforce time (F6); `req_coverage
      --strict` green; changelog fragment + diary entry

## Judgement (2026-07-10)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | "Every provider" hides per-wrapper param drift (`timeout` vs `request_timeout`) | Per-wrapper parameter map; matrix test asserts the wrapper-correct attribute; missing-param wrappers = documented exceptions, never silent skips |
| F2 | "Node-level timeout wins where smaller" implies plumbing that doesn't exist | Struck; race deadline bounds the wait, client timeout bounds the work — independent layers |
| F3 | RED "asserts invocation outlives node call unboundedly" is untestable as stated | RED = provider-matrix finite-timeout assertion (fails today, no network) |
| F4 | A mocked hang cannot validate SDK timeout behavior (mock ignores the param) | Honesty bound: param matrix is the unit gate; e2e verification stays the non-gating consumer probe |
| F5 | Env knobs need boundary parsing | One helper each; garbage raises; VERTEX_TRANSPORT validated rest\|grpc and applied to google + vertex |
| F6 | Traceability unpinned | New REQ under the LLM-factory capability, id verified free against origin at enforce |

**Out of scope (purge list):** client caching/reuse, transport close on
cancellation, race node changes, per-node client-timeout plumbing,
non-google transport knobs.

## Verification hook (consumer side, not gating this FR)

ninchat_voice post-fix probe on the Fly test instance: single call with
`VERTEX_TRANSPORT=rest` vs default — determines whether the gemini
candidate returns to the deployed fleet or stays dropped. Candidate
completion-rate metric tracked separately (ninchat NC-365 candidate).

## Related

- RCA: `projects/ninchat_voice/docs/analysis/rca-20260710-fly-freeze.txt`
- FR-707 (verdict-at-deadline — the wait bound), FR-706 (condemnation),
  FR-705 (pending-candidate naming), NC-361 (incident lineage)
- FR-227 (vertex env masking — same constructor, same boundary lesson)
- Doctrine: `the_one_law` (bound at the transport boundary, not in the
  race that consumes it); Commandment 9 (a hung provider is an
  operational defect and must fail observably, not silently)
