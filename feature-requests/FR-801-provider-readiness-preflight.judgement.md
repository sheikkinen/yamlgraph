# Judgement: FR-801 Provider Readiness Preflight for Live Integration Tests

**Verdict:** APPROVED WITH REVISIONS — the provider-readiness boundary is real and the preflight direction is sound, but authority activates only after the FR resolves its marker/fixture contradiction, freezes the covered provider/test inventory, and specifies timeout/cache mechanics without product-code scope creep.

**Prior art:** dispositioned in the parent FR's Prior art line (FR-798 owns the C/D evidence and preflight disposition; FR-761 is the reproducibility analogue; FR-756 confirms no marker change; FR-785 probes an A2A discovery endpoint in a production graph node — different boundary, no overlap; FR-254 is a keyword-incidental hit) and re-verified against the cited artifacts in the Reviewed-against record below — no undispositioned overlap found.

**Reviewed against:** `feature-requests/FR-801-provider-readiness-preflight.md`; cited evidence `docs/investigations/fr798-full-suite-failures.md`, `docs/diary/diary-2026-08-15-fr798-failure-classification.md`; prior art `feature-requests/FR-798-full-suite-failure-classification-investigation.md`, `feature-requests/FR-798-full-suite-failure-classification-investigation.judgement.md`, `feature-requests/FR-761-reproducible-dependency-governance.md`, `feature-requests/FR-761-reproducible-dependency-governance.judgement.md`, `feature-requests/FR-756-core-test-isolation.md`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`; implementation surfaces inspected for feasibility: `tests/integration/test_providers.py`, `tests/integration/test_multi_turn_streaming.py`, `tests/conftest.py`, `yamlgraph/config.py`, `yamlgraph/utils/llm_factory.py`, `yamlgraph/utils/llm_providers.py`, `pyproject.toml`; attempted surface `tests/integration/conftest.py` (absent).

## What is sound

The problem is real and directly evidenced. FR-798 records the exact downstream failure shape: the multi-turn tests reached a legal checkpoint with a typed `PipelineError(type=llm_error, node=respond, retryable=true, exception_type=RateLimitError, HTTP 429 insufficient_quota/credit_balance_exhausted)` while `response`/`intent` stayed empty (`docs/investigations/fr798-full-suite-failures.md:117-151`). The same report proves key presence is not readiness: absent key, exhausted OpenAI key, and healthy Anthropic credential were separable by one probe (`docs/investigations/fr798-full-suite-failures.md:172-204`). The diary records the same two boundary lessons as `dotenv_resurrects_the_key` and `key_presence_is_not_readiness` (`docs/diary/diary-2026-08-15-fr798-failure-classification.md:31-44`).

The FR correctly preserves the key FR-798 constraint: arbitrary provider errors must not be converted to skips after execution begins (`feature-requests/FR-801-provider-readiness-preflight.md:40-42`). That aligns with the repo's boundary doctrine: normalize where external state enters, not downstream where it manifests (`.github/copilot-instructions.md:49-58`, `.github/copilot-instructions.md:246-249`). The implementation target is also test-local: FR-801 confines scope to `tests/integration/` and explicitly excludes unit-lane, marker-policy, CI workflow, and hook changes (`feature-requests/FR-801-provider-readiness-preflight.md:69-71`, `:89`).

Feasibility is plausible. `yamlgraph.config` loads `.env` at import time (`yamlgraph/config.py:41-44`), which supports the FR's "effective credentials after dotenv" boundary (`feature-requests/FR-801-provider-readiness-preflight.md:62-64`). Provider construction already has bounded request support through `LLM_REQUEST_TIMEOUT` and provider factory `_bounded(...)` (`yamlgraph/utils/llm_providers.py:21-25`, `:41-92`), and the LLM cache fingerprints that env var (`yamlgraph/utils/llm_factory.py:47-58`, `:190-199`). The existing failing tests are exactly shaped as the FR says: OpenAI is selected by env-key presence only in `test_execute_prompt_with_openai_provider` (`tests/integration/test_providers.py:69-81`), and the three multi-turn assertions currently hide `errors` in at least two failure messages (`tests/integration/test_multi_turn_streaming.py:34-38`, `:82-89`).

Strategic classification: **test-infrastructure pattern**, not a framework primitive. This should produce a reusable integration-test precondition and mocked tests for that precondition, not a new runtime provider-readiness API.

## Required revisions

### R-1: Replace the marker/fixture ambiguity with a fixture-only precondition

Amend the Proposed Solution to remove the `requires_provider("openai")` marker wording (`feature-requests/FR-801-provider-readiness-preflight.md:57-59`) and require a fixture-based precondition that runs before the test body, for example provider-specific fixtures consumed via a test parameter or `pytest.mark.usefixtures(...)`. Do not add a new custom pytest marker and do not modify `pyproject.toml` marker registration; the FR already excludes marker-policy changes (`feature-requests/FR-801-provider-readiness-preflight.md:69-70`, `:89`), while registered markers currently live in `pyproject.toml:223-228`.

The fixture contract must state that the skip happens during fixture setup, before any product invocation in the test body. Calling a helper from inside the test body does not satisfy AC-05.

### R-2: Freeze the provider/test coverage inventory

Add a table naming every test that must consume the gate in this FR: `path::test`, provider, credential env vars, and readiness fixture. At minimum, include the three OpenAI-backed multi-turn tests and `TestProviderIntegration::test_execute_prompt_with_openai_provider` (`feature-requests/FR-801-provider-readiness-preflight.md:86-88`; `tests/integration/test_multi_turn_streaming.py:17-92`; `tests/integration/test_providers.py:69-81`).

Do not leave "other live-provider suites" as open scope (`feature-requests/FR-801-provider-readiness-preflight.md:57-59`). If additional existing live-provider tests are included, they must appear in the table and in AC-07; if they are not included, state that the helper may be provider-generic but enforcement under FR-801 wires only the named tests. Adjacent integration suites not named in the table are not authorized.

### R-3: Specify readiness probe timeout and cache isolation mechanics

Replace "wrapped with a short timeout" (`feature-requests/FR-801-provider-readiness-preflight.md:53-56`) with one exact test-local mechanism. The existing public `create_llm(...)` signature does not accept arbitrary timeout kwargs (`yamlgraph/utils/llm_factory.py:88-94`); provider timeouts are currently supplied through `LLM_REQUEST_TIMEOUT` at construction (`yamlgraph/utils/llm_providers.py:41-92`). Fold in the exact timeout value, how the fixture temporarily sets or avoids setting `LLM_REQUEST_TIMEOUT`, how `clear_cache()` is used if env changes affect client construction, and how the environment/cache are restored so the actual live test executes with unchanged provider behavior.

No production `create_llm` API change, provider factory change, or global timeout policy change is authorized by this FR.

### R-4: Add requirement-traceability coverage for the new preflight tests

Amend the acceptance criteria to require every new test for the readiness helper to carry `@pytest.mark.req(...)`, and either name the existing REQ that governs this test-infrastructure behavior or add a new CAP/REQ entry. Repo doctrine requires every test function to link to a requirement and new capabilities to add a CAP file (`.github/copilot-instructions.md:173-176`); the current FR's ACs require mocked probe tests but do not specify traceability (`feature-requests/FR-801-provider-readiness-preflight.md:75-89`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tests/integration/conftest.py` or an equivalent integration-test-local helper module providing the session-scoped provider-readiness cache and fixture preconditions |
| D-2 | Revisions to the exact live-provider tests named in the revised FR inventory |
| D-3 | Unit/integration tests for absent-after-dotenv, exhausted probe, healthy probe, memoization, redaction, and fixture-before-body behavior |
| D-4 | Optional assertion-message-only edits in the named multi-turn tests so residual failures print `result["errors"]` without weakening assertions |
| D-5 | FR-801 implementation-status note after enforcement |

Not authorized: production changes under `yamlgraph/**`; graph or prompt artifact edits; new pytest marker policy or `pyproject.toml` marker registration; CI workflow, hook, branch-protection, or unit-lane changes; provider credential creation, rotation, purchase, or disclosure; changing live-test assertions from "provider produced content" to weaker success-shaped checks; converting provider exceptions to skips from inside product execution; broad rewrites of unrelated integration suites; global timeout-policy changes.

## Revised acceptance criteria

- [ ] AC-01: With an exhausted OpenAI readiness probe mocked to raise a provider exception, each named OpenAI live test skips during fixture setup before the test body invokes product code; the skip reason includes provider, error class, and HTTP status.
- [ ] AC-02: With credentials absent after `yamlgraph.config` dotenv loading, each named OpenAI live test skips during fixture setup with an absent-credential reason; the dotenv resurrection path is covered without committing or exposing secrets.
- [ ] AC-03: With a healthy mocked probe, each named test executes its original product invocation and assertions unchanged except for optional failure-message additions.
- [ ] AC-04: Readiness is memoized at most once per provider per pytest session; a regression test witnesses the call count.
- [ ] AC-05: No provider error is converted to skip after product execution begins; fixture-before-body behavior is mechanically tested with a sentinel proving the body did not run.
- [ ] AC-06: Skip reasons and committed artifacts contain no key material, provider response body, account identifier, request identifier, or credential value.
- [ ] AC-07: The exact tests listed in the revised provider/test inventory consume the readiness fixture; no unlisted integration tests are modified.
- [ ] AC-08: The three `test_multi_turn_streaming.py` tests and `test_execute_prompt_with_openai_provider` keep their content/intent assertions semantically intact; any assertion edit only adds `result["errors"]` to the failure message.
- [ ] AC-09: The readiness probe timeout/cache behavior follows the revised FR's exact mechanism and does not require production API or provider-factory changes.
- [ ] AC-10: Unit lane, pytest marker policy, CI workflows, hooks, graph artifacts, prompt artifacts, and production code remain unchanged.
- [ ] AC-11: All new tests are requirement-tagged with the REQ named in the revised FR or with a new CAP/REQ added under this FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-4 are folded into `feature-requests/FR-801-provider-readiness-preflight.md`. | GATE |
| C-2 | The preflight must run as a pytest precondition before the product test body; a helper called after the body starts fails the judgement. | GATE |
| C-3 | No production `yamlgraph/**`, graph, prompt, CI, hook, or marker-policy surface may change under this authority. | GATE |
| C-4 | The enforcer must use mocked probe outcomes for readiness-state tests; real provider calls are allowed only for the existing live tests when the provider is ready. | GATE |
| C-5 | Credential spend and account readiness remain operator concerns; this FR may report and skip unhealthy credentials, not create, rotate, buy, or expose them. | GATE |

Authority granted: after the required revisions are folded, enforcement may build a test-local provider-readiness preflight for the revised inventory of live integration tests, with session memoization, redacted skip reasons, dotenv-aware absent detection, and unchanged live-test assertions.
