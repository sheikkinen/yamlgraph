# Judgement: FR-766 RunPod Provider via OpenAI-Compatible vLLM Endpoint

**Prior art:** `FR-766-runpod-provider.md` [Proposed] — self-hit: this
artifact is the judgement OF that FR, not a competing proposal. No
other FR touches the `runpod` noun; the rejected `langchain-runpod`
route is dispositioned inside the FR's Alternatives Considered.

**Verdict:** APPROVED WITH REVISIONS — the OpenAI-compatible RunPod provider is a minimal, pattern-aligned provider addition, but authority activates only after the FR folds in the required auth, cache-fingerprint, streaming, and provider-count/documentation revisions below.

**Reviewed against:** `feature-requests/FR-766-runpod-provider.md`; `docs/plan-research-runpod.md`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/config.py`; `tests/unit/test_lmstudio_provider.py`; `tests/integration/test_providers.py`; `tests/unit/test_fr680_provider_registry.py`; `tests/unit/test_architecture_provider_count.py`; `ARCHITECTURE.md`; `capabilities/CAP-03-node-execution.yaml`; `.env.sample`; `CLAUDE.md`; `feature-requests/FR-213-vertex-ai-provider.md`; `feature-requests/FR-263-azure-openai-provider.md`; `feature-requests/TEMPLATE.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is real and narrow: the first consumer/event is concrete (`PROVIDER=runpod yamlgraph graph run ...` with three RunPod env vars, `feature-requests/FR-766-runpod-provider.md:8-12`), and the research shows LangGraph itself is provider-agnostic so the integration belongs at `create_llm()` rather than graph orchestration (`docs/plan-research-runpod.md:13-20`).

The route is architecture-aligned: the FR rejects `langchain-runpod` because streaming is simulated and structured-output tests are skipped (`feature-requests/FR-766-runpod-provider.md:28-35`; `docs/plan-research-runpod.md:22-40`), then selects the existing `ChatOpenAI + base_url` shape already used by LM Studio (`feature-requests/FR-766-runpod-provider.md:52-53`; `yamlgraph/utils/llm_providers.py:234-247`). That satisfies the doctrine to conform before extending (`.github/copilot-instructions.md:214`) and keeps the change inside the existing provider capability (`ARCHITECTURE.md:563-575`; `capabilities/CAP-03-node-execution.yaml:20-23`).

The proposal is a framework primitive, not pattern documentation: the documented LM Studio workaround would hardcode `api_key="not-needed"` (`yamlgraph/utils/llm_providers.py:240-246`) while the FR's problem statement correctly says RunPod requires a real key and would otherwise be mislabeled in traces (`feature-requests/FR-766-runpod-provider.md:36-39`). The change is a single provider concern and explicitly rejects endpoint-ID composition in favor of passing a full RunPod base URL (`feature-requests/FR-766-runpod-provider.md:151-157`).

## Required revisions

### R-1: Require `RUNPOD_API_KEY` at the provider boundary

Amend the Proposed Solution and AC-02 so `_create_runpod_llm()` reads `RUNPOD_API_KEY` into a local variable and raises `ValueError("RUNPOD_API_KEY is required for provider 'runpod'")` when blank before constructing `ChatOpenAI`. The FR currently promises configuration by `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT`, and `RUNPOD_MODEL` with fail-fast misconfiguration (`feature-requests/FR-766-runpod-provider.md:43-48`), but the implementation sketch only validates endpoint and model while passing `api_key=os.getenv("RUNPOD_API_KEY")` (`feature-requests/FR-766-runpod-provider.md:69-79`). That violates the error-boundary doctrine (`.github/copilot-instructions.md:216-218`) and repeats the very hidden-auth problem the FR uses to reject LM Studio (`feature-requests/FR-766-runpod-provider.md:36-39`).

### R-2: Replace the stale env-var mapping instruction with cache fingerprinting

Change the `yamlgraph/utils/llm_factory.py` instruction from adding `"runpod": ("RUNPOD_API_KEY", "RUNPOD_ENDPOINT")` to an unspecified "env-var mapping" (`feature-requests/FR-766-runpod-provider.md:83-85`) to adding `runpod` to `_PROVIDER_FINGERPRINT_VARS` with `("RUNPOD_API_KEY", "RUNPOD_ENDPOINT")`. The current factory has `_PROVIDER_FINGERPRINT_VARS`, not a generic provider-env validation map (`yamlgraph/utils/llm_factory.py:57-83`), and REQ-YG-540 requires env-fingerprinted cache keys for provider construction state (`ARCHITECTURE.md:574-575`; `capabilities/CAP-03-node-execution.yaml:61-79`). Do not include `RUNPOD_MODEL` in that fingerprint unless the implementation also changes the model-resolution mechanism; the selected model is already part of the cache key (`yamlgraph/utils/llm_factory.py:175-197`).

### R-3: Add a streaming witness acceptance criterion

Add an AC requiring the gated RunPod integration test to exercise `create_llm(provider="runpod").stream(...)` against the live endpoint and assert at least one streamed chunk, or record the exact blocked command and skip reason in the FR. The FR's Ideal Result promises "true SSE streaming" (`feature-requests/FR-766-runpod-provider.md:43-45`) and the research rejects `langchain-runpod` specifically because it simulates streaming (`docs/plan-research-runpod.md:28-40`), but the current integration AC only witnesses `invoke()` and `with_structured_output()` (`feature-requests/FR-766-runpod-provider.md:132-135`). This is a measurability gap under the judge rubric (`.github/skills/judge-fr/doctrine.md:43-44`) and the demo/test doctrine (`.github/copilot-instructions.md:208-218`).

### R-4: Freeze all provider-count and sample-env surfaces

Amend the file list and acceptance criteria to update every hard-coded provider surface: `ProviderType`, `DEFAULT_MODELS`, `_PROVIDER_FACTORIES`, `_PROVIDER_FINGERPRINT_VARS`, `tests/unit/test_fr680_provider_registry.py`, `tests/unit/test_architecture_provider_count.py`, `ARCHITECTURE.md` provider count/list rows, `CLAUDE.md`, `.env.sample`, and the changelog fragment. The FR currently says "existing provider-registry tests pass unchanged" (`feature-requests/FR-766-runpod-provider.md:130-131`), but the registry test hard-codes the eleven-provider set (`tests/unit/test_fr680_provider_registry.py:21-36`), the architecture guard hard-codes the provider set and compares provider count (`tests/unit/test_architecture_provider_count.py:23-64`), and ARCHITECTURE.md says 11 providers in both the diagram and module table (`ARCHITECTURE.md:269-280`; `ARCHITECTURE.md:3299`). `.env.sample` is also the repo-level provider env contract and currently lacks RunPod rows (`.env.sample:1-46`), while prior provider FRs updated equivalent documentation and provider-count guards (`feature-requests/FR-213-vertex-ai-provider.md:137-156`; `feature-requests/FR-263-azure-openai-provider.md:91-119`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/llm_providers.py`: add `_create_runpod_llm()` using existing `ChatOpenAI(base_url=..., api_key=...)` plus `_bounded(dict(kwargs))`; register it in `_PROVIDER_FACTORIES`. |
| D-2 | `yamlgraph/utils/llm_factory.py`: add `"runpod"` to `ProviderType`; add `runpod` to `_PROVIDER_FINGERPRINT_VARS`; do not add it to `THINKING_PROVIDERS`. |
| D-3 | `yamlgraph/config.py`: add `DEFAULT_MODELS["runpod"] = os.getenv("RUNPOD_MODEL", "")` so missing model fails loudly in the provider factory. |
| D-4 | Unit tests covering provider registration, constructor kwargs, env fingerprint behavior, model override, temperature passthrough, and fail-fast errors for missing `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT`, and model. |
| D-5 | Gated integration test for real RunPod `invoke()`, `stream()`, and `with_structured_output()`, skipped unless `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT`, and `RUNPOD_MODEL` are all set; if not run during enforcement, record the exact blocked command and skip reason in the FR. |
| D-6 | Provider-count and documentation updates: `tests/unit/test_fr680_provider_registry.py`, `tests/unit/test_architecture_provider_count.py`, `ARCHITECTURE.md`, `CLAUDE.md`, `.env.sample`, and one `changelog/unreleased/` fragment with `req: REQ-YG-010`. |
| D-7 | Update `feature-requests/FR-766-runpod-provider.md` with implementation status, any blocked live-validation command, and deviations from the frozen judgement. |

Not authorized: adding `langchain-runpod`; adding any new dependency; composing URLs from `RUNPOD_ENDPOINT_ID`; adding RunPod deployment/orchestration support; adding thinking-budget support; adding provider-specific retry/cold-start framework mechanisms beyond existing timeout/retry configuration; changing judge/review/CI/hook doctrine; storing or committing real RunPod credentials.

## Revised acceptance criteria

- [ ] AC-01: `create_llm(provider="runpod")` accepts `runpod` as a valid provider and dispatches through `_PROVIDER_FACTORIES["runpod"]`.
- [ ] AC-02: `DEFAULT_MODELS["runpod"]` reads `RUNPOD_MODEL` with no hard-coded fallback; an empty selected model raises `ValueError` naming `RUNPOD_MODEL`.
- [ ] AC-03: Missing or blank `RUNPOD_API_KEY` raises `ValueError` naming `RUNPOD_API_KEY` before `ChatOpenAI` is constructed.
- [ ] AC-04: Missing or blank `RUNPOD_ENDPOINT` raises `ValueError` naming `RUNPOD_ENDPOINT` before `ChatOpenAI` is constructed.
- [ ] AC-05: Mocked unit test proves `ChatOpenAI` receives `model`, `temperature`, `base_url` exactly from `RUNPOD_ENDPOINT`, `api_key` exactly from `RUNPOD_API_KEY`, and the existing bounded timeout/retry kwargs.
- [ ] AC-06: `_PROVIDER_FINGERPRINT_VARS["runpod"]` includes `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT`; a targeted unit test proves changing either env var yields a distinct cached client.
- [ ] AC-07: `runpod` appears in `ProviderType`, `_PROVIDER_FACTORIES`, `DEFAULT_MODELS`, provider registry tests, architecture provider-count tests, ARCHITECTURE.md provider count/list, CLAUDE.md provider/env table, and `.env.sample`.
- [ ] AC-08: Gated integration test is skipped unless `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT`, and `RUNPOD_MODEL` are all present; when present, it runs real `invoke()`, `stream()`, and `with_structured_output()` against the configured endpoint.
- [ ] AC-09: If the live RunPod endpoint is unavailable during enforcement, the FR records the exact skipped/blocked command and reason; mocked tests must not be presented as live validation.
- [ ] AC-10: No new dependency is added; no import or use of `langchain-runpod` appears.
- [ ] AC-11: All new tests are tagged `@pytest.mark.req("REQ-YG-010")`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-12: A changelog fragment exists under `changelog/unreleased/` with front matter `req: REQ-YG-010`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into `feature-requests/FR-766-runpod-provider.md` before implementation authority is active. | GATE |
| C-2 | Use only the OpenAI-compatible `ChatOpenAI + base_url` implementation path; `langchain-runpod` and new dependencies are forbidden. | GATE |
| C-3 | Validate RunPod auth, endpoint, and model at the provider boundary with explicit `ValueError`s; do not rely on downstream SDK authentication errors or `OPENAI_API_KEY` fallback behavior. | GATE |
| C-4 | Do not claim live RunPod validation unless the gated integration test actually ran; otherwise record the exact blocked command and skip reason in the FR. | GATE |
| C-5 | Keep the provider out of `THINKING_PROVIDERS`; thinking/tool-calling semantics are not authorized by this FR. | GATE |

Authority granted after R-1 through R-4 are folded into the FR: implement one `runpod` LLM provider entry via the existing OpenAI-compatible factory pattern, with the tests and documentation listed above.
