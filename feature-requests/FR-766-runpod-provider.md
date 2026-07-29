# Feature Request: FR-766 RunPod Provider via OpenAI-Compatible vLLM Endpoint

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-29
**First consumer / first event:** the operator running an existing
YAMLGraph graph against a RunPod-hosted model (Public API `moonshot-kimi`
endpoint, already configured in the local `.env`), at the moment
`PROVIDER=runpod yamlgraph graph run examples/demos/hello/graph.yaml`
is invoked with `RUNPOD_API_KEY` + `RUNPOD_ENDPOINT` + `RUNPOD_MODEL` set.

## Summary

Add a `runpod` provider to the LLM factory, targeting RunPod serverless
vLLM workers' OpenAI-compatible API via the existing
`ChatOpenAI + base_url` pattern (lmstudio precedent). Zero new
dependencies.

## Value Statement

Graph authors can point any YAMLGraph pipeline at self-hosted
open-weights models on RunPod with three env vars and no code changes.

## Problem

RunPod hosts open-weights models cheaply on serverless GPUs, but
YAMLGraph has no provider entry for it. The official
`langchain-runpod` package is not a viable route: simulated streaming,
skipped structured-output standard tests, no token usage, dormant ~1
year (see `docs/plan-research-runpod.md`). Meanwhile RunPod vLLM
workers already expose an OpenAI-compatible surface
(`https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1`) that our existing
`_create_lmstudio_llm` pattern handles verbatim. The capability is one
factory entry away; leaving it undone forces users to misuse
`LMSTUDIO_BASE_URL` pointed at RunPod — which hides the API-key
requirement (lmstudio hardcodes `api_key="not-needed"`) and lies about
the provider name in traces.

## Ideal Result

`provider: runpod` in any graph YAML (or `PROVIDER=runpod`) routes all
LLM calls through a RunPod OpenAI-compatible endpoint with true SSE
streaming and Pydantic structured output, configured entirely by
`RUNPOD_API_KEY`, `RUNPOD_ENDPOINT`, and `RUNPOD_MODEL` —
indistinguishable at the graph layer from any other provider, with a
fail-fast error naming the missing env var when misconfigured.

## Proposed Solution

Mirror the lmstudio provider (`yamlgraph/utils/llm_providers.py:234`),
which is the established zero-dependency OpenAI-compat route.

1. **`yamlgraph/utils/llm_providers.py`** — new factory + registry entry:

```python
def _create_runpod_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create RunPod LLM via OpenAI-compatible endpoint.

    RUNPOD_ENDPOINT is the full base URL, e.g.
    https://api.runpod.ai/v2/moonshot-kimi/openai/v1 (Public API) or
    https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1 (serverless vLLM).
    """
    from langchain_openai import ChatOpenAI

    base_url = os.getenv("RUNPOD_ENDPOINT")
    if not base_url:
        raise ValueError("RUNPOD_ENDPOINT is required for provider 'runpod'")
    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        raise ValueError("RUNPOD_API_KEY is required for provider 'runpod'")
    if not model:
        raise ValueError("RUNPOD_MODEL is required for provider 'runpod'")
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=base_url,
        api_key=api_key,
        **_bounded(dict(kwargs)),
    )
```

2. **`yamlgraph/utils/llm_factory.py`** — add `"runpod"` to
   `ProviderType` and add `"runpod": ("RUNPOD_API_KEY",
   "RUNPOD_ENDPOINT")` to `_PROVIDER_FINGERPRINT_VARS` (env-fingerprinted
   cache keys, REQ-YG-540). `RUNPOD_MODEL` stays out of the fingerprint —
   the selected model is already part of the cache key. Not added to
   `THINKING_PROVIDERS` (judgement C-5).

3. **`yamlgraph/config.py`** — `"runpod": os.getenv("RUNPOD_MODEL", "")`
   in `DEFAULT_MODELS`. No hard-coded model: unlike lmstudio, a RunPod
   endpoint serves exactly the model it was deployed with; any default
   would be a plausible wrong answer. Empty model fails fast in the
   factory with the env-var name (Commandment 6 — no silent fallback).

4. **Tests** — `tests/unit/test_runpod_provider.py` mirroring
   `test_lmstudio_provider.py` (`@pytest.mark.req("REQ-YG-010")`,
   mocked `ChatOpenAI`): provider valid, base_url taken verbatim from
   `RUNPOD_ENDPOINT`, api_key from `RUNPOD_API_KEY`, fail-fast on
   missing api-key/endpoint/model, cache-fingerprint distinctness when
   either fingerprint env var changes. One integration test in
   `tests/integration/`, skipped unless `RUNPOD_API_KEY` +
   `RUNPOD_ENDPOINT` + `RUNPOD_MODEL` are set, that runs a real
   `create_llm(provider="runpod").invoke(...)`, a `stream(...)`
   asserting at least one streamed chunk (R-3: the streaming claim is
   the reason langchain-runpod was rejected — it must be witnessed
   too), and a `with_structured_output` round-trip (constraint 3
   below: structured output must be witnessed, not assumed).

5. **Docs & provider-count surfaces (R-4)** — every hard-coded provider
   surface updates together: `tests/unit/test_fr680_provider_registry.py`
   and `tests/unit/test_architecture_provider_count.py` (both hard-code
   the eleven-provider set), `ARCHITECTURE.md` provider count/list,
   `CLAUDE.md` env-var table rows (`RUNPOD_API_KEY`, `RUNPOD_ENDPOINT`,
   `RUNPOD_MODEL`) + `runpod` in the `PROVIDER` row, `.env.sample`
   RunPod rows; changelog fragment (`req: REQ-YG-010`).

### Distilled constraints (from `docs/plan-research-runpod.md`)

1. No `langchain-runpod` dependency — unmaintained; breaks streaming
   and structured-output contracts.
2. OpenAI-compat route only, via existing `ChatOpenAI + base_url`
   pattern; zero new dependencies.
3. Structured output and tool calling are model- and
   vLLM-version-dependent on RunPod: the integration test is the
   witness. If no live endpoint is available at enforce time, record
   the exact blocked command in this FR (blocked-validation honesty) —
   do not simulate success.
4. Serverless cold starts (tens of seconds) are a documented caveat in
   the env-var table row, resolved by existing per-node `timeout` /
   `on_error: retry` — no new framework mechanism.

## Acceptance Criteria

Revised by judgement (2026-07-29) — these supersede the original six:

- [ ] AC-01: `create_llm(provider="runpod")` accepts `runpod` as a valid
      provider and dispatches through `_PROVIDER_FACTORIES["runpod"]`.
- [ ] AC-02: `DEFAULT_MODELS["runpod"]` reads `RUNPOD_MODEL` with no
      hard-coded fallback; an empty selected model raises `ValueError`
      naming `RUNPOD_MODEL`.
- [ ] AC-03: Missing or blank `RUNPOD_API_KEY` raises `ValueError`
      naming `RUNPOD_API_KEY` before `ChatOpenAI` is constructed.
- [ ] AC-04: Missing or blank `RUNPOD_ENDPOINT` raises `ValueError`
      naming `RUNPOD_ENDPOINT` before `ChatOpenAI` is constructed.
- [ ] AC-05: Mocked unit test proves `ChatOpenAI` receives `model`,
      `temperature`, `base_url` exactly from `RUNPOD_ENDPOINT`,
      `api_key` exactly from `RUNPOD_API_KEY`, and the existing bounded
      timeout/retry kwargs.
- [ ] AC-06: `_PROVIDER_FINGERPRINT_VARS["runpod"]` includes
      `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT`; a targeted unit test
      proves changing either env var yields a distinct cached client.
- [ ] AC-07: `runpod` appears in `ProviderType`, `_PROVIDER_FACTORIES`,
      `DEFAULT_MODELS`, provider registry tests, architecture
      provider-count tests, ARCHITECTURE.md provider count/list,
      CLAUDE.md provider/env table, and `.env.sample`.
- [ ] AC-08: Gated integration test is skipped unless `RUNPOD_API_KEY`,
      `RUNPOD_ENDPOINT`, and `RUNPOD_MODEL` are all present; when
      present, it runs real `invoke()`, `stream()` (asserting at least
      one streamed chunk), and `with_structured_output()` against the
      configured endpoint.
- [ ] AC-09: If the live RunPod endpoint is unavailable during
      enforcement, the FR records the exact skipped/blocked command and
      reason; mocked tests must not be presented as live validation.
- [ ] AC-10: No new dependency is added; no import or use of
      `langchain-runpod` appears.
- [ ] AC-11: All new tests are tagged `@pytest.mark.req("REQ-YG-010")`;
      `python scripts/req_coverage.py --strict` passes.
- [ ] AC-12: A changelog fragment exists under `changelog/unreleased/`
      with front matter `req: REQ-YG-010`.

## Alternatives Considered

- **`langchain-runpod` package** — rejected: simulated streaming,
  structured-output standard tests skipped, no token usage, dormant
  (see research doc). Violates Commandment 5.
- **Document-only** (point `LMSTUDIO_BASE_URL` at RunPod, FR-747-style
  doc): works today by accident but lmstudio hardcodes
  `api_key="not-needed"` — RunPod requires a real key, so this route
  is actually broken, not merely dishonest. Killed by mechanism, not
  taste.
- **`RUNPOD_ENDPOINT_ID` + URL composition** (original draft): rejected
  on contact with the first consumer's actual env — the operator's
  live config targets the RunPod **Public API**, whose URL path segment
  is a model slug (`moonshot-kimi`), not an account endpoint ID. A full
  `RUNPOD_ENDPOINT` base URL expresses both Public API and personal
  serverless endpoints with zero composition logic; the value in the
  working `.env` is the witness.
- **New CAP file**: not needed — provider additions live under the
  existing provider capability (REQ-YG-010), per lmstudio precedent
  (`tests/unit/test_lmstudio_provider.py`).

## Related

- `docs/plan-research-runpod.md` — research and sources (2026-07-29)
- `yamlgraph/utils/llm_providers.py` `_create_lmstudio_llm` — pattern precedent
- https://docs.runpod.io/serverless/vllm/openai-compatibility

## Judgement (2026-07-29)

**Verdict:** APPROVED WITH REVISIONS — rendered via the sole-route
judge adapter (`scripts/judge.sh`, model gpt-5.5, session
d1b21243); full artifact archived below from `tmp/draft-judgement.md`.
R-1–R-4 folded into this FR 2026-07-29 (C-1 satisfied); authority
active.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | Sketch validated endpoint+model but passed `api_key=os.getenv(...)` unchecked — repeats the hidden-auth problem used to reject the lmstudio route | Fail-fast `ValueError` naming `RUNPOD_API_KEY` before `ChatOpenAI` construction (folded into Proposed Solution + AC-03) |
| R-2 | "Env-var mapping" instruction was stale — the factory has `_PROVIDER_FINGERPRINT_VARS` (REQ-YG-540 cache fingerprints), not a validation map | Add `runpod: (RUNPOD_API_KEY, RUNPOD_ENDPOINT)` to `_PROVIDER_FINGERPRINT_VARS`; model excluded (already in cache key) (folded + AC-06) |
| R-3 | Ideal Result promises true SSE streaming — the reason langchain-runpod was rejected — but no AC witnessed it | Integration test also exercises `stream()` asserting ≥1 chunk (folded + AC-08) |
| R-4 | "Registry tests pass unchanged" was false — `test_fr680_provider_registry.py` and `test_architecture_provider_count.py` hard-code the eleven-provider set; ARCHITECTURE.md says 11 providers; `.env.sample` lacks RunPod rows | All provider-count and sample-env surfaces frozen into scope (folded + AC-07) |

**Purge list:** `langchain-runpod` and any new dependency;
`RUNPOD_ENDPOINT_ID` URL composition; RunPod deployment/orchestration
support; thinking-budget support (`THINKING_PROVIDERS`);
provider-specific retry/cold-start mechanisms beyond existing
timeout/retry config; committing real credentials.

**Scope frozen:** D-1–D-7 per `tmp/draft-judgement.md` — factory fn +
registry (D-1), ProviderType + fingerprint vars (D-2), DEFAULT_MODELS
(D-3), unit tests (D-4), gated integration test invoke/stream/
structured-output (D-5), provider-count + docs surfaces (D-6), FR
status update (D-7). Conditions C-1–C-5 GATE.

### Questions for the human (as options, or 'none')

None — the live endpoint is configured in the operator's `.env`; no
decision is open that the frozen scope does not answer.
