# Research: LangGraph / YAMLGraph × RunPod Support

**Date:** 2026-07-29
**Status:** Research (pre-plan). Sources verified 2026-07-29.

## Question

Can YAMLGraph pipelines (LangGraph-based) use LLMs hosted on RunPod, and
what is the right integration route?

## Findings

### 1. LangGraph itself needs nothing

LangGraph is provider-agnostic — any `BaseChatModel` works. "RunPod
support" reduces entirely to the chat-model layer, i.e. our
`create_llm()` factory. (Deploying a YAMLGraph app *onto* RunPod
serverless is a container/deployment concern, out of framework scope —
same verdict as URL-based prompt loading in
`reference/prompt-deployment.md`.)

### 2. `langchain-runpod` (official package) — reject

RunPod publishes `langchain-runpod` (`RunPod` + `ChatRunPod` classes)
wrapping the native async `/run` → `/status/{job_id}` polling API.
Verified state (github.com/runpod/langchain-runpod, PyPI):

| Feature | Status |
|---|---|
| Invoke / async invoke | Works |
| Streaming | **Simulated** — full response fetched, then chunked |
| Tool calling | Endpoint-dependent, no standard support; standard tests **skipped** |
| Structured output | Endpoint-dependent; standard tests **skipped** |
| Token usage / logprobs | Not available |
| Maintenance | 1 contributor, 3 stars, 0 releases, dormant ~1 year, ~210 dl/mo |

Structured output is YAMLGraph's core contract (Commandment 5: all LLM
output through Pydantic). A provider whose structured-output tests are
skipped and whose streaming is fake fails two boundary contracts at
once. **Do not adopt.**

### 3. RunPod vLLM workers' OpenAI-compatible API — the viable route

RunPod serverless vLLM workers expose an OpenAI-compatible surface
(docs.runpod.io/serverless/vllm/openai-compatibility):

```
base_url = https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1
api_key  = <RUNPOD_API_KEY>
```

- `/chat/completions` with **true SSE streaming** (`RAW_OPENAI_OUTPUT=1`
  default), `/completions`, `/models`.
- Standard OpenAI params + vLLM extras (`top_k`, `min_p`,
  `repetition_penalty`, …).
- Tool calling and JSON mode: **model- and vLLM-version-dependent**, not
  guaranteed by the API layer. Structured output via
  `with_structured_output` rides the OpenAI function/JSON path into
  vLLM guided decoding — must be verified per deployed model.
- Token counting may differ from OpenAI (different tokenizers).

LangChain's own docs endorse exactly this: use `ChatOpenAI` with a
custom `base_url` for OpenAI-compatible providers (with the caveat that
non-standard fields like `reasoning_content` are dropped).

### 4. YAMLGraph already owns this pattern

`yamlgraph/utils/llm_providers.py:_create_lmstudio_llm` is the
precedent: `ChatOpenAI` + `base_url` from env, zero new dependencies.
A `runpod` provider is the same ~15 lines:

```python
def _create_runpod_llm(model, temperature, **kwargs):
    from langchain_openai import ChatOpenAI
    endpoint = os.getenv("RUNPOD_ENDPOINT_ID")  # or RUNPOD_BASE_URL override
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=f"https://api.runpod.ai/v2/{endpoint}/openai/v1",
        api_key=os.getenv("RUNPOD_API_KEY"),
        **_bounded(dict(kwargs)),
    )
```

Env contract: `RUNPOD_API_KEY` + `RUNPOD_ENDPOINT_ID` (mirrors the
`lmstudio` row in `_PROVIDER_ENV_VARS`).

## Distilled constraints (for the FR, if planned)

1. **No `langchain-runpod` dependency** — unmaintained; breaks the
   structured-output and streaming contracts.
2. **OpenAI-compat route only**, via the existing `ChatOpenAI` +
   `base_url` factory pattern (lmstudio precedent, zero new deps).
3. **Normalize at the provider boundary**: RunPod's OpenAI surface is a
   type lie in known places — token usage, model-dependent tool
   calling. Structured-output support must be *witnessed* against a
   live endpoint, not assumed from the API shape.
4. **Cold starts are real**: serverless flex workers can take tens of
   seconds to spin up — per-node `timeout` and `on_error: retry`
   guidance belongs in the provider docs row.
5. **Verification needs a live endpoint + credits**: if unavailable at
   enforce time, acceptance must record the exact blocked command
   (blocked-validation honesty), not simulate success.

## Recommendation

Smallest sufficient change: add a `runpod` provider to the factory
(lmstudio-shaped) + env-var table row + one integration test gated on
`RUNPOD_API_KEY`/`RUNPOD_ENDPOINT_ID`. Alternative (cheaper, FR-747
precedent): document the pattern only — `provider: lmstudio` is
already abusable by pointing `LMSTUDIO_BASE_URL` at a RunPod endpoint,
but that misuses a named provider and hides the API-key requirement, so
the named provider is the honest form.

## Sources

- https://github.com/runpod/langchain-runpod (README, feature table)
- https://docs.runpod.io/serverless/vllm/openai-compatibility
- https://docs.langchain.com/oss/python/integrations/chat (ChatRunPod
  row: no stream/tool/structured checkmarks; Chat Completions API
  guidance for OpenAI-compatible endpoints)
- `yamlgraph/utils/llm_providers.py` (`_create_lmstudio_llm` precedent)
