# Feature Request: Provider Readiness Preflight for Live Integration Tests

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-15
**First consumer / first event:** the next enforcer running `tests/integration/` with any unhealthy live credential — the first event is today's reality: `OPENAI_API_KEY` is present but exhausted (HTTP 429 `insufficient_quota`), so `test_execute_prompt_with_openai_provider` and the three `test_multi_turn_streaming.py` tests run and fail as if the product were broken, costing a full FR-798-scale classification effort to prove otherwise.

**Prior art:** FR-798 (Class C/D investigation — owns the evidence and this disposition: "readiness preflight recommended — the only option that also fixes local runs"; C is folded into this FR: the multi-turn reds are downstream of readiness, no product defect), FR-761 (environment reproducibility precedent — this FR is its provider-credential analogue), FR-756 (test classification — no marker policy change here).

## Summary

Live-provider integration tests gate on `skipif(not KEY)` — key *presence*.
FR-798 proved presence ≠ readiness: an exhausted key passes the gate, then
fails mid-test. Add a session-scoped readiness preflight: one cheap probe
per provider per pytest session; tests requiring that provider skip
*before execution begins* with an explicit
`provider not ready: <error class>/<HTTP status>` reason.

## Value Statement

Provider outages and exhausted credentials become one legible skip line
instead of N misleading product-failure reds — locally and in any future
CI credential lane.

## Problem

Evidence from FR-798 (`docs/investigations/fr798-full-suite-failures.md`):

- Exhausted key: 429 `insufficient_quota` surfaces as a typed
  `PipelineError` in graph state; tests asserting only the destination
  field (`response`) misreport it as a product/checkpoint defect.
- Absent key is unreachable via `env -u`: `yamlgraph.config`'s
  `load_dotenv()` resurrects the key from `.env`. Only an empty-string
  override survives.
- The three readiness states (absent / exhausted / healthy) are cleanly
  separable by one `invoke` probe (`logs/fr798-classD-ready.log`).

FR-798's constraint carries over: converting arbitrary provider errors to
skips *after* execution begins is forbidden — the gate must run before the
test body.

## Ideal Result

A red integration lane means the product is broken. Provider trouble is
visible as `SKIPPED [provider openai not ready: RateLimitError/429]`, the
readiness probe result is computed once per session, and a healthy-key run
executes every live test unchanged.

## Proposed Solution

- `tests/integration/conftest.py`: session-scoped, lazily-evaluated
  readiness cache. Probe = one minimal `create_llm(provider=...).invoke()`
  wrapped with a short timeout; result memoized per provider for the
  session (one probe, not one per test).
- A `requires_provider("openai")` marker/fixture consumed by the live tests
  (`test_providers.py`, `test_multi_turn_streaming.py`, other live-provider
  suites): skip before the test body when the probe failed, with error
  class + HTTP status in the skip reason (redaction per FR-798 AC-13 —
  no bodies, no account/request IDs).
- Dotenv-aware: the preflight reads effective credentials *after*
  `yamlgraph.config` import (the resurrection boundary), so "absent" means
  absent-after-dotenv.
- Assertions unchanged (FR-798: do not weaken the provider integration
  assertion). Secondary improvement licensed by the C disposition: the
  multi-turn assertion messages include `result["errors"]` so any residual
  failure is legible at the assert site.
- Scope: `tests/integration/` only. No unit-lane, marker-policy, CI
  workflow, or hook changes. Probe spend: one minimal completion per
  configured provider per session, only when live tests are selected.

## Acceptance Criteria

- [ ] AC-01: With an exhausted key (mocked probe), live OpenAI tests skip
  before execution with a reason naming error class and HTTP status.
- [ ] AC-02: With an absent-after-dotenv key, tests skip with an
  absent-credential reason; the dotenv resurrection path is covered by a test.
- [ ] AC-03: With a healthy probe (mocked), tests execute; no behavior change.
- [ ] AC-04: The probe runs at most once per provider per session (memoization
  witnessed).
- [ ] AC-05: No error-to-skip conversion after a test body starts; the gate is
  a precondition, mechanically distinct from in-test exception handling.
- [ ] AC-06: Skip reasons contain no key material, account, or request
  identifiers.
- [ ] AC-07: The three `test_multi_turn_streaming.py` tests and
  `test_execute_prompt_with_openai_provider` consume the gate; their
  assertions are not weakened.
- [ ] AC-08: Unit lane, markers policy, CI workflows, and hooks unchanged.

## Alternatives Considered

- **Dedicated CI credential lane:** solves CI only; local enforcers still
  burn time on unhealthy keys — FR-798 evaluated and recommended preflight.
- **Explicit operator selection (env flag per run):** manual, forgettable;
  doesn't encode the absent/exhausted distinction.
- **Retry-on-429 in tests:** an exhausted account never recovers within a
  run; retries mask the state FR-798 exists to make legible.

## Related

- `docs/investigations/fr798-full-suite-failures.md` (Classes C, D)
- `docs/diary/diary-2026-08-15-fr798-failure-classification.md`
  (`dotenv_resurrects_the_key`, `key_presence_is_not_readiness`)
- Operations note (outside this FR): the OpenAI credit itself is an
  operator decision; this FR makes its absence legible, not survivable.
