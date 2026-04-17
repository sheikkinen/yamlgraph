# Feature Request: Mask GOOGLE_CLOUD_PROJECT/LOCATION During Vertex Express Construction

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-04-17

## Summary

When `VERTEX_API_KEY` is set (Express mode), the google-genai SDK ignores the explicitly-passed `google_api_key` and falls back to ADC auth if `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` are also present in the environment. Temporarily masking those env vars during `ChatGoogleGenerativeAI` construction—under a threading lock—makes Express mode work reliably in all environments.

## Value Statement

Developers using Vertex AI Express mode (`VERTEX_API_KEY`) whose environment also contains `GOOGLE_CLOUD_PROJECT`/`GOOGLE_CLOUD_LOCATION` (e.g. multi-provider `.env` files or shared CI environments) get a working LLM instead of a silent ADC auth failure.

## Problem

`BaseApiClient.__init__` (lines 84–97 of `google/genai/_api_client.py`) reads `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` from `os.environ` directly after constructor arguments are parsed. Its internal precedence rule — *"explicit project/location from env > implicit api_key"* — causes the SDK to log "project/location will take precedence", set `api_key=None`, and attempt ADC authentication, which fails when GCP credentials are absent.

FR-226 introduced the `VERTEX_API_KEY` branch in `_create_vertex_llm` and deliberately passes no `project`/`location` kwargs. However, the SDK still reads those values from the environment, so the Express mode fix is incomplete when both env vars coexist with `VERTEX_API_KEY`.

The env vars to mask are those that trigger the SDK's ADC precedence rule:
- `GOOGLE_CLOUD_PROJECT` — read by the SDK's `BaseApiClient`
- `GOOGLE_CLOUD_LOCATION` — read by the SDK's `BaseApiClient`
- `VERTEXAI_PROJECT` — aliased by the SDK; confirmed read at `llm_factory.py` line 389

`VERTEXAI_LOCATION` is **not** included in the mask: it is not read by the SDK's ADC path (verified against `_api_client.py`) and is not referenced anywhere in `llm_factory.py`.

Because `os.environ` is a process-global dict, concurrent calls to `_create_vertex_llm` (e.g. parallel graph compilations at FastAPI startup) could race: one thread removes vars while another reads them, or the `finally`-block restores vars after a second caller has entered construction without masking. A module-level `threading.Lock` scopes the mask atomically.

## Proposed Solution

Introduce a module-level `_VERTEX_CONSTRUCT_LOCK` and a `_masked_env` context manager in `llm_factory.py`. Apply both around the Express-mode `ChatGoogleGenerativeAI(...)` call only.

```python
import contextlib
import threading
from typing import Iterator

_VERTEX_CONSTRUCT_LOCK = threading.Lock()


@contextlib.contextmanager
def _masked_env(*keys: str) -> Iterator[None]:
    """Temporarily remove environment variables, restoring them on exit."""
    saved = {k: os.environ.pop(k) for k in keys if k in os.environ}
    try:
        yield
    finally:
        os.environ.update(saved)


def _create_vertex_llm(model: str, temperature: float, **kwargs: object) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("VERTEX_API_KEY")
    if api_key:
        with _VERTEX_CONSTRUCT_LOCK, _masked_env(
            "GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "VERTEXAI_PROJECT"
        ):
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                vertexai=True,
                google_api_key=api_key,
                **kwargs,
            )

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

The lock is module-level and wraps only the Express branch; the ADC branch is unaffected. The mask is scoped strictly to the constructor call.

## Acceptance Criteria

- [ ] When `VERTEX_API_KEY` **and** `GOOGLE_CLOUD_PROJECT`/`GOOGLE_CLOUD_LOCATION` are all set, `_create_vertex_llm` constructs `ChatGoogleGenerativeAI` while those env vars are absent from `os.environ`
- [ ] `VERTEXAI_PROJECT` is also absent from `os.environ` during Express construction (SDK aliased read)
- [ ] `VERTEXAI_LOCATION` is **not** added to the mask (not read by SDK ADC path; mask must only contain the three keys above)
- [ ] After construction, all masked env vars are restored to their original values in `os.environ`
- [ ] If an exception is raised inside `ChatGoogleGenerativeAI(...)`, env vars are still restored (context manager `finally`-block)
- [ ] When `VERTEX_API_KEY` is absent (ADC mode), `GOOGLE_CLOUD_PROJECT`/`GOOGLE_CLOUD_LOCATION` are never removed from `os.environ`
- [ ] A module-level `threading.Lock` (`_VERTEX_CONSTRUCT_LOCK`) wraps the masked construction block
- [ ] Unit test: mock `ChatGoogleGenerativeAI`; assert env vars absent during construction and restored after
- [ ] Unit test: verify exception during construction still restores env vars
- [ ] Existing FR-226 tests remain green
- [ ] No change to public `create_llm` signature

## Alternatives Considered

- **Pass `project=None, location=None` explicitly**: `ChatGoogleGenerativeAI` does not accept `None` for these kwargs; the SDK still reads env vars regardless.
- **Patch `os.environ` at module level on import**: too broad; would affect unrelated code in the same process.
- **Use `unittest.mock.patch.dict` inside production code**: test-only API; inappropriate in production path.
- **Option B (document single-threaded constraint)**: Rejected — `_create_vertex_llm` is already called from async graph compilation paths and FastAPI startup; documenting a threading constraint instead of enforcing it is a detection-without-enforcement anti-pattern per doctrine.

## Limitations

None known. The lock serialises Express-mode LLM construction, which is an infrequent operation (typically once per graph compile, not per inference call).

## Related

- `yamlgraph/utils/llm_factory.py` — `_create_vertex_llm` (line 368)
- `feature-requests/FR-226-vertex-express-api-key-auth.md` — original Express mode FR (Implemented)
- `google/genai/_api_client.py` lines 84–97 — root cause in SDK
- `tests/unit/test_llm_factory.py` — existing Vertex tests to extend
