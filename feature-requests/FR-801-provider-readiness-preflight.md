# Feature Request: Provider Readiness Preflight for Live Integration Tests

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced — 2026-08-15 (see Implementation Record)
**Effort:** 1 day
**Requested:** 2026-08-15
**First consumer / first event:** the next enforcer running `tests/integration/` with any unhealthy live credential — the first event is today's reality: `OPENAI_API_KEY` is present but exhausted (HTTP 429 `insufficient_quota`), so `test_execute_prompt_with_openai_provider` and the three `test_multi_turn_streaming.py` tests run and fail as if the product were broken, costing a full FR-798-scale classification effort to prove otherwise.

**Prior art:** FR-798 (Class C/D investigation — owns the evidence and this disposition: "readiness preflight recommended — the only option that also fixes local runs"; C is folded into this FR: the multi-turn reds are downstream of readiness, no product defect), FR-761 (environment reproducibility precedent — this FR is its provider-credential analogue), FR-756 (test classification — no marker policy change here). Dispositioned keyword hits: FR-785 (api-discovery endpoint probe — probes an A2A server's discovery endpoint inside a graph node at runtime, a production graph concern; this FR probes LLM credential health inside pytest fixtures, test-infrastructure only — different boundary, no overlap), FR-254 (diary-index graph — keyword-incidental match on "provider/readiness" prose; no shared surface).

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

- `tests/integration/conftest.py` (new): session-scoped, lazily-evaluated
  readiness cache. Probe = one minimal `create_llm(provider=...).invoke()`;
  result memoized per provider for the session (one probe, not one per test).
- **Fixture-only precondition (judgement R-1):** provider-specific readiness
  fixtures (e.g. `openai_ready`), consumed via a test parameter or
  `pytest.mark.usefixtures(...)`. NO new custom pytest marker; NO
  `pyproject.toml` marker registration. The skip happens during fixture
  setup, before any product invocation in the test body — a helper called
  from inside the test body does not satisfy AC-05.
- **Probe timeout and cache isolation (judgement R-3):** the probe bounds the
  request via the existing `LLM_REQUEST_TIMEOUT` construction path: the
  fixture saves the current value, sets `os.environ["LLM_REQUEST_TIMEOUT"] = "15"`,
  calls `yamlgraph.utils.llm_factory.clear_cache()`, runs the probe, then
  restores the prior value (or removes it) and calls `clear_cache()` again —
  so the probe's bounded client never leaks into live-test client
  construction and live tests execute with unchanged provider behavior. No
  `create_llm` API change, provider-factory change, or global timeout-policy
  change.
- **Covered provider/test inventory (judgement R-2, frozen):** the helper may
  be provider-generic, but enforcement under FR-801 wires ONLY the tests in
  this table; adjacent integration suites are not authorized.

  | Test | Provider | Credential env | Readiness fixture |
  |---|---|---|---|
  | `tests/integration/test_multi_turn_streaming.py::test_multi_turn_resume_with_command` | openai | `OPENAI_API_KEY` | `openai_ready` |
  | `tests/integration/test_multi_turn_streaming.py::test_guard_classification_separate_call` | openai | `OPENAI_API_KEY` | `openai_ready` |
  | `tests/integration/test_multi_turn_streaming.py::test_checkpointer_persists_across_turns` | openai | `OPENAI_API_KEY` | `openai_ready` |
  | `tests/integration/test_providers.py::TestProviderIntegration::test_execute_prompt_with_openai_provider` | openai | `OPENAI_API_KEY` | `openai_ready` |

- Skip reason format: `provider openai not ready: <error class>/<HTTP status>`
  (redaction per FR-798 AC-13 — no bodies, no account/request IDs).
- Dotenv-aware: the preflight reads effective credentials *after*
  `yamlgraph.config` import (the resurrection boundary), so "absent" means
  absent-after-dotenv.
- Assertions unchanged (FR-798: do not weaken the provider integration
  assertion). Secondary improvement licensed by the C disposition: the
  multi-turn assertion messages include `result["errors"]` so any residual
  failure is legible at the assert site.
- **Requirement traceability (judgement R-4):** every new test for the
  readiness helper carries `@pytest.mark.req("REQ-YG-591")`; a new
  `capabilities/CAP-230-provider-readiness-preflight.yaml` declaring
  REQ-YG-591 is added under this FR.
- Scope: `tests/integration/` only. No unit-lane, marker-policy, CI
  workflow, or hook changes. Probe spend: one minimal completion per
  configured provider per session, only when live tests are selected.

## Acceptance Criteria

(Revised per judgement — supersedes the proposed set.)

- [x] AC-01: With an exhausted OpenAI readiness probe mocked to raise a
  provider exception, each named OpenAI live test skips during fixture setup
  before the test body invokes product code; the skip reason includes
  provider, error class, and HTTP status.
- [x] AC-02: With credentials absent after `yamlgraph.config` dotenv loading,
  each named OpenAI live test skips during fixture setup with an
  absent-credential reason; the dotenv resurrection path is covered without
  committing or exposing secrets.
- [x] AC-03: With a healthy mocked probe, each named test executes its
  original product invocation and assertions unchanged except for optional
  failure-message additions.
- [x] AC-04: Readiness is memoized at most once per provider per pytest
  session; a regression test witnesses the call count.
- [x] AC-05: No provider error is converted to skip after product execution
  begins; fixture-before-body behavior is mechanically tested with a
  sentinel proving the body did not run.
- [x] AC-06: Skip reasons and committed artifacts contain no key material,
  provider response body, account identifier, request identifier, or
  credential value.
- [x] AC-07: The exact tests listed in the frozen provider/test inventory
  consume the readiness fixture; no unlisted integration tests are modified.
- [x] AC-08: The three named `test_multi_turn_streaming.py` tests and
  `test_execute_prompt_with_openai_provider` keep their content/intent
  assertions semantically intact; any assertion edit only adds
  `result["errors"]` to the failure message.
- [x] AC-09: The readiness probe timeout/cache behavior follows the exact
  mechanism above (`LLM_REQUEST_TIMEOUT` set/restore + `clear_cache()`
  bracketing) and does not require production API or provider-factory
  changes.
- [x] AC-10: Unit lane, pytest marker policy, CI workflows, hooks, graph
  artifacts, prompt artifacts, and production code remain unchanged.
- [x] AC-11: All new tests are requirement-tagged with `REQ-YG-591`;
  `capabilities/CAP-230-provider-readiness-preflight.yaml` is added under
  this FR.

## Implementation Record (2026-08-15)

- New `tests/integration/conftest.py`: `probe_provider` (dotenv-boundary
  credential read, one minimal `create_llm(provider).invoke("ping")`,
  `LLM_REQUEST_TIMEOUT=15` set/restore bracketed by `clear_cache()`,
  redacted reason = exception class + HTTP status only),
  `provider_readiness` (session memoization), `require_provider_ready`,
  and the `openai_ready` fixture (skip in setup, C-2).
- Wired the four frozen-inventory tests; multi-turn failure messages now
  include `result["errors"]` (D-4); assertions otherwise unchanged.
- Witnesses: `tests/integration/test_fr801_readiness_preflight.py` — 7
  mocked-probe tests (absent-after-dotenv, exhausted class+status,
  message-body redaction, healthy, timeout/cache restore, memoization
  call-count, and a pytester sentinel proving setup-time skip with the
  body never running), all `@pytest.mark.req("REQ-YG-591")` (C-4).
- `capabilities/CAP-230-provider-readiness-preflight.yaml` added;
  ARCHITECTURE.md capabilities section regenerated;
  `req_coverage.py --strict` passes.
- Live verification against the real exhausted credential: one probe,
  then all four named tests skip with
  `provider openai not ready: RateLimitError/429` — the FR-798 Class C/D
  failure shape is now one legible skip line.
- No production, marker-policy, CI, or hook changes (C-3). No deviations.

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
