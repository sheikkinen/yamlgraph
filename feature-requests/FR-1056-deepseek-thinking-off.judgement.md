# Judgement: FR-1056 DeepSeek Non-Thinking Mode (`thinking_budget: 0`)

**Verdict:** APPROVED WITH REVISIONS — the provider-boundary fix is narrow and feasible; authority activates only after R-1 through R-3 are folded into the FR.

**Prior art:** [FR-1056-deepseek-thinking-off.md](FR-1056-deepseek-thinking-off.md) — the judged FR itself, not independent prior art; its own prior-art line dispositions FR-071, FR-230, and FR-680.

**Reviewed against:** `feature-requests/FR-1056-deepseek-thinking-off.md`; `feature-requests/FR-071-thinking-budget-graph-level.md`; `feature-requests/FR-230-google-vertex-thinking-budget.md`; `feature-requests/FR-680-provider-dispatch-registry.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `ARCHITECTURE.md`; `capabilities/CAP-272-clean-dirty-main-triage.yaml`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/linter/checks_providers.py`; `reference/graph-yaml.md`; `examples/dungeon_master/chapter_close.yaml`; `tests/integration/test_thinking_budget_integration.py`.

## What is sound

The problem and smallest useful behavior are explicit: DeepSeek currently receives no `thinking_budget` because its factory is outside the dispatch allowlist (`yamlgraph/utils/llm_providers.py:90-102,311-353`), while the shared factory rejects only unsupported budgets at or above 1024 (`yamlgraph/utils/llm_factory.py:147-156`). Mapping only `thinking_budget == 0` to `reasoning_effort="none"` therefore fixes the exact silent no-op without inventing a token-to-effort conversion (`feature-requests/FR-1056-deepseek-thinking-off.md:32-38,71-83,107-117`).

The proposal follows the existing provider registry rather than adding a second dispatch mechanism. Its proposed DeepSeek signature matches the positional forwarding seam established by FR-680 (`yamlgraph/utils/llm_providers.py:311-353`; `feature-requests/FR-680-provider-dispatch-registry.md:39-73,115-127`). The cache already distinguishes `thinking_budget`, so no cache redesign is warranted (`yamlgraph/utils/llm_factory.py:190-208`).

The intended semantics are internally coherent. Omission preserves the provider default, zero disables thinking, 512 remains an intentionally ignored portability value, and 8000 remains a loud unsupported token budget (`feature-requests/FR-1056-deepseek-thinking-off.md:109-127,131-147`). The portability premise has committed precedent in `examples/dungeon_master/chapter_close.yaml:32-37`, and the proposed change does not alter Anthropic, Google, or Vertex semantics established by FR-071 and FR-230.

The acceptance path is directly testable without a network call by inspecting `ChatOpenAI._get_request_payload`, as the committed alternatives record already reports for installed `langchain_openai` 1.4.1 (`feature-requests/FR-1056-deepseek-thinking-off.md:153-159`). This is a provider-boundary unit test, not an integration dependency.

The alternatives record contains five genuine solution classes, preserves the API/SDK distinction, and dispositions prior art including the absence of a rejected DeepSeek-reasoning proposal (`feature-requests/FR-1056-deepseek-thinking-off.md:13-30,149-159`). Effort tuning, stale model defaults, and reasoning-content round-tripping are correctly excluded as separate concerns (`feature-requests/FR-1056-deepseek-thinking-off.md:172-180`).

Under the doctrine's strategic taxonomy this is **Contrib/example**: one provider-specific use case fills a gap in the existing `thinking_budget` and provider-registry abstractions; it does not justify a new framework primitive.

## Required revisions

### R-1: Record the `is_this_a_graph` disposition

Add an explicit research statement that this change is not a graph-authoring or graph-execution workflow: it is a deterministic one-value provider-boundary mapping implemented and tested in Python, so no existing YAMLGraph graph applies. The alternatives table is substantive, but the local research rule requires the `is_this_a_graph` answer (`.github/skills/judge-fr/doctrine.md:82-91`; `.github/copilot-instructions.md:129`).

### R-2: Freeze the traceability artifacts

Replace the combined “capability `CAP-273` added” criterion with explicit deliverables: add `capabilities/CAP-273-deepseek-non-thinking.yaml`, add CAP-273 to the `ARCHITECTURE.md` capability registry, and define `REQ-YG-684` in the capability file and `ARCHITECTURE.md` requirement table. The requirement text must state all four runtime cases: zero emits `reasoning_effort: "none"`; omission and accepted nonzero sub-1024 values omit `reasoning_effort`; budgets at or above 1024 retain the unsupported-provider error. Tag every new test with `@pytest.mark.req("REQ-YG-684")`. This makes the proposed new identifiers mechanically checkable under ADR-001 (`.github/copilot-instructions.md:169-171`); the current registry ends at CAP-272 and the current requirement sequence reaches REQ-YG-683 (`ARCHITECTURE.md:584-590,799-802`).

### R-3: Witness the promised observability and public contract

Add acceptance criteria that a nonzero accepted DeepSeek budget (use 512) emits the proposed DEBUG message and that `create_llm`'s `thinking_budget` parameter documentation names the DeepSeek zero/omitted/other-value semantics. The implementation promises DEBUG observability (`feature-requests/FR-1056-deepseek-thinking-off.md:109-111`), but the current criteria test only payload omission and non-raising (`feature-requests/FR-1056-deepseek-thinking-off.md:136-137`). The current public docstring still says only Anthropic/Google/Vertex support the field (`yamlgraph/utils/llm_factory.py:101-119`), so leaving it unchanged would contradict the newly supported zero-value behavior.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/llm_providers.py`: route `thinking_budget` to the DeepSeek factory; emit `reasoning_effort="none"` only for zero; DEBUG-log ignored nonzero accepted values |
| D-2 | Provider-focused unit tests exercising payloads, error preservation, DEBUG observability, and unchanged existing-provider behavior |
| D-3 | `yamlgraph/utils/llm_factory.py` parameter documentation and `reference/graph-yaml.md` DeepSeek semantics |
| D-4 | `capabilities/CAP-273-deepseek-non-thinking.yaml` and CAP-273 / REQ-YG-684 entries in `ARCHITECTURE.md` |
| D-5 | One providers-scoped fix changelog fragment and the FR implementation-status update |

Not authorized: a new `reasoning_effort` YAML field; mapping positive token budgets to DeepSeek effort levels; changing the `>= 1024` unsupported-provider guard; adding DeepSeek to `llm_factory.THINKING_PROVIDERS`; changing linter warnings; changing Anthropic, Google, or Vertex construction; changing DeepSeek default model names; handling `reasoning_content`; editing graph or prompt artifacts; or introducing a live-API acceptance dependency.

## Revised acceptance criteria

- [ ] AC-01: With the LLM cache isolated, `create_llm(provider="deepseek", model="deepseek-v4-pro", thinking_budget=0)` returns `ChatOpenAI` and `_get_request_payload(...)` contains `reasoning_effort == "none"`.
- [ ] AC-02: With the cache isolated, the same call with `thinking_budget` omitted produces a request payload with no `reasoning_effort` key.
- [ ] AC-03: With the cache isolated, the same call with `thinking_budget=512` does not raise, produces a request payload with no `reasoning_effort` key, and emits the specified DEBUG record naming the ignored value and provider.
- [ ] AC-04: `create_llm(provider="deepseek", model="deepseek-v4-pro", thinking_budget=8000)` raises `ValueError` naming the supported token-budget providers; no DeepSeek client is constructed.
- [ ] AC-05: Existing Anthropic, Google, and Vertex thinking-budget tests pass unchanged in asserted behavior.
- [ ] AC-06: Distinct DeepSeek calls with omitted, zero, and 512 budgets do not alias in the client cache.
- [ ] AC-07: Every new test carries `@pytest.mark.req("REQ-YG-684")`, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-08: `capabilities/CAP-273-deepseek-non-thinking.yaml` exists and defines REQ-YG-684; `ARCHITECTURE.md` registers CAP-273 and REQ-YG-684 with the frozen four-case contract.
- [ ] AC-09: `reference/graph-yaml.md` and the `create_llm` `thinking_budget` parameter documentation state: DeepSeek zero disables thinking, omission preserves the API default, accepted other values are ignored, and effort tuning is unsupported.
- [ ] AC-10: A `changelog/unreleased/` fragment has `type: fix`, `scope: providers`, and identifies FR-1056 / REQ-YG-684.
- [ ] AC-11: Git history contains a failing RED test commit before the GREEN implementation commit.
- [ ] AC-12: The FR records the explicit `is_this_a_graph` disposition and, after enforcement, records implementation status and deviations.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 and the revised acceptance criteria into FR-1056 before production-code implementation begins. | GATE |
| C-2 | Preserve the asymmetric registries: DeepSeek enters only dispatch-side `_THINKING_PROVIDERS`; it must remain outside `llm_factory.THINKING_PROVIDERS` so budgets at or above 1024 still fail. | GATE |
| C-3 | Set `reasoning_effort` only when `thinking_budget == 0`; omission, `-1`, and positive accepted values must not put a reasoning-effort field into the request. | GATE |
| C-4 | Keep the change keyless and deterministic; tests may inspect SDK request payloads but must not require the DeepSeek API. | GATE |
| C-5 | Do not alter linter behavior or any graph/prompt artifact under this authority. | GATE |

Authority granted: after R-1 through R-3 are folded into the FR, implement only the frozen DeepSeek zero-value mapping, its observability, traceability, documentation, and keyless regression tests.
