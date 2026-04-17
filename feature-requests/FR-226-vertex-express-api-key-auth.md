# Feature Request: Vertex AI Express Mode via VERTEX_API_KEY

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-17

## Summary

Add Vertex AI Express authentication mode to `_create_vertex_llm`: when `VERTEX_API_KEY` is set, pass `google_api_key` without `project`/`location`. When absent, keep the current ADC path (`GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION`).

## Value Statement

Developers without a GCP project/ADC setup can use Vertex AI models immediately via an API key, matching the ergonomics of other providers (Anthropic, OpenAI, Mistral) that are also key-only.

## Problem

`_create_vertex_llm` unconditionally passes `project` and `location` to `ChatGoogleGenerativeAI(vertexai=True, ...)`. The google-genai SDK raises `ValueError` when both `project`/`location` **and** `api_key` are set simultaneously, so Express mode is currently blocked. `VERTEX_API_KEY` is already defined in `.env` but silently ignored.

## Proposed Solution

Mutually exclusive branch inside `_create_vertex_llm`:

```python
def _create_vertex_llm(model: str, temperature: float, **kwargs: object) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("VERTEX_API_KEY")
    if api_key:
        # Express mode: API key only, no project/location
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            vertexai=True,
            google_api_key=api_key,
            **kwargs,
        )

    # ADC mode: project + location, no api_key
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("VERTEXAI_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        vertexai=True,
        project=project,
        location=location,
        **kwargs,
    )
```

The two branches are mutually exclusive and never mix `api_key` with `project`/`location`.

## Acceptance Criteria

- [ ] When `VERTEX_API_KEY` is set, `_create_vertex_llm` passes `google_api_key=<value>` and does **not** pass `project` or `location`
- [ ] When `VERTEX_API_KEY` is absent, `_create_vertex_llm` passes `project` + `location` and does **not** pass `google_api_key` (existing ADC behaviour unchanged)
- [ ] Both branches tested with mocked `ChatGoogleGenerativeAI` constructor; assertions on kwargs passed
- [ ] `VERTEX_API_KEY` documented in the env-var table in `CLAUDE.md`
- [ ] No change to public `create_llm` signature

## Alternatives Considered

- **Auto-detect from presence of `GOOGLE_CLOUD_PROJECT`**: less explicit than a dedicated `VERTEX_API_KEY` variable; harder to override in CI where both vars might exist.
- **New `provider: vertex-express`**: adds a second provider string that users must remember; unnecessary complexity when a single env var cleanly selects the path.

## Related

- `yamlgraph/utils/llm_factory.py` — `_create_vertex_llm` (line 368)
- `.env` — `VERTEX_API_KEY` already present but unused
- `CLAUDE.md` — env-var table to be updated
- SDK constraint: `google.genai.BaseApiClient.__init__` raises `ValueError` on `project`+`api_key` collision
