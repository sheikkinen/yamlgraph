# Feature Request: FR-766 RunPod Provider via OpenAI-Compatible vLLM Endpoint

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-29
**First consumer / first event:** the operator running an existing
YAMLGraph graph against a self-hosted open-weights model on a RunPod
serverless vLLM endpoint, at the moment
`PROVIDER=runpod yamlgraph graph run examples/demos/hello/graph.yaml`
is invoked with `RUNPOD_API_KEY` + `RUNPOD_ENDPOINT_ID` set.

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
LLM calls through a RunPod vLLM endpoint with true SSE streaming and
Pydantic structured output, configured entirely by `RUNPOD_API_KEY`,
`RUNPOD_ENDPOINT_ID`, and `RUNPOD_MODEL` — indistinguishable at the
graph layer from any other provider, with a fail-fast error naming the
missing env var when misconfigured.

## Proposed Solution

Mirror the lmstudio provider (`yamlgraph/utils/llm_providers.py:234`),
which is the established zero-dependency OpenAI-compat route.

1. **`yamlgraph/utils/llm_providers.py`** — new factory + registry entry:

```python
def _create_runpod_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create RunPod serverless vLLM LLM (OpenAI-compatible API)."""
    from langchain_openai import ChatOpenAI

    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
    if not endpoint_id:
        raise ValueError("RUNPOD_ENDPOINT_ID is required for provider 'runpod'")
    if not model:
        raise ValueError("RUNPOD_MODEL is required for provider 'runpod'")
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=f"https://api.runpod.ai/v2/{endpoint_id}/openai/v1",
        api_key=os.getenv("RUNPOD_API_KEY"),
        **_bounded(dict(kwargs)),
    )
```

2. **`yamlgraph/utils/llm_factory.py`** — add `"runpod"` to the valid
   provider list and `"runpod": ("RUNPOD_API_KEY", "RUNPOD_ENDPOINT_ID")`
   to the env-var mapping.

3. **`yamlgraph/config.py`** — `"runpod": os.getenv("RUNPOD_MODEL", "")`
   in `DEFAULT_MODELS`. No hard-coded model: unlike lmstudio, a RunPod
   endpoint serves exactly the model it was deployed with; any default
   would be a plausible wrong answer. Empty model fails fast in the
   factory with the env-var name (Commandment 6 — no silent fallback).

4. **Tests** — `tests/unit/test_runpod_provider.py` mirroring
   `test_lmstudio_provider.py` (`@pytest.mark.req("REQ-YG-010")`,
   mocked `ChatOpenAI`): provider valid, base_url composed from
   `RUNPOD_ENDPOINT_ID`, api_key from `RUNPOD_API_KEY`, fail-fast on
   missing endpoint/model. One integration test in
   `tests/integration/`, skipped unless `RUNPOD_API_KEY` +
   `RUNPOD_ENDPOINT_ID` + `RUNPOD_MODEL` are set, that runs a real
   `create_llm(provider="runpod").invoke(...)` and a
   `with_structured_output` round-trip (constraint 3 below: structured
   output must be witnessed, not assumed).

5. **Docs** — `CLAUDE.md` env-var table rows (`RUNPOD_API_KEY`,
   `RUNPOD_ENDPOINT_ID`, `RUNPOD_MODEL`) + `runpod` in the `PROVIDER`
   row; changelog fragment (`req: REQ-YG-010`).

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

- [ ] AC-01: `create_llm(provider="runpod")` returns a `ChatOpenAI`
      with `base_url == "https://api.runpod.ai/v2/<RUNPOD_ENDPOINT_ID>/openai/v1"`
      and `api_key` from `RUNPOD_API_KEY` (mocked unit test).
- [ ] AC-02: Missing `RUNPOD_ENDPOINT_ID` or empty model raises
      `ValueError` naming the missing env var (unit test).
- [ ] AC-03: `runpod` appears in the factory's valid provider list and
      `DEFAULT_MODELS`; existing provider-registry tests pass unchanged.
- [ ] AC-04: Gated integration test exercises real `invoke()` and
      `with_structured_output()` against a live endpoint, OR the FR
      records the exact blocked command and skip reason.
- [ ] AC-05: `CLAUDE.md` env-var table updated; changelog fragment
      present (`req: REQ-YG-010`).
- [ ] AC-06: Unit tests tagged `@pytest.mark.req("REQ-YG-010")`;
      `python scripts/req_coverage.py --strict` passes.

## Alternatives Considered

- **`langchain-runpod` package** — rejected: simulated streaming,
  structured-output standard tests skipped, no token usage, dormant
  (see research doc). Violates Commandment 5.
- **Document-only** (point `LMSTUDIO_BASE_URL` at RunPod, FR-747-style
  doc): works today by accident but lmstudio hardcodes
  `api_key="not-needed"` — RunPod requires a real key, so this route
  is actually broken, not merely dishonest. Killed by mechanism, not
  taste.
- **`RUNPOD_BASE_URL` override** (for dedicated pods with direct URLs):
  purged as speculative — no first consumer. A dedicated-pod user can
  file the follow-up when the moment exists.
- **New CAP file**: not needed — provider additions live under the
  existing provider capability (REQ-YG-010), per lmstudio precedent
  (`tests/unit/test_lmstudio_provider.py`).

## Related

- `docs/plan-research-runpod.md` — research and sources (2026-07-29)
- `yamlgraph/utils/llm_providers.py` `_create_lmstudio_llm` — pattern precedent
- https://docs.runpod.io/serverless/vllm/openai-compatibility

## Judgement (pending)

**Verdict:** —
