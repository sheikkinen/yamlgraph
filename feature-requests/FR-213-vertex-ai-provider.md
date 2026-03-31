# FR-213: Add Google Vertex AI Provider

**Status**: Implemented
**Priority**: Medium
**Type**: Feature
**Effort**: 1 hour
**Risk**: Low
**Requested**: 2026-03-31

## Summary

Add `provider: vertex` to the YAMLGraph LLM factory to support Google Vertex AI
(`ChatVertexAI`) as a distinct provider alongside the existing `google` provider
(which uses Gemini via `GOOGLE_API_KEY`). Vertex AI uses GCP project credentials
(Application Default Credentials or a service account), making it the correct
choice for corporate GCP tenants.

## Value Statement

Teams operating inside a GCP organisation (e.g. `scp-tenant-dps-dev`) can run
YAMLGraph against their Vertex AI quota and billing account without managing a
personal `GOOGLE_API_KEY`, using the same authentication they already have.

## Problem

The existing `google` provider uses `ChatGoogleGenerativeAI` from
`langchain-google-genai`, which requires a `GOOGLE_API_KEY` (consumer API key).
In a corporate GCP environment, access is governed by IAM roles and Application
Default Credentials (ADC), not API keys. Vertex AI exposes the same Gemini
models but through the `aiplatform` endpoint authenticated by
`GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` + ADC. The two providers are
not interchangeable — using the wrong one results in authentication errors.

## Proposed Solution

Add a `vertex` provider that delegates to `ChatVertexAI` from
`langchain-google-vertexai` (already a separate PyPI package). Authentication
falls back to ADC so no API-key variable is required in the happy path.

```yaml
# Graph-level provider selection (metadata section)
defaults:
  provider: vertex
  model: gemini-2.0-flash

# Or per-node, via environment
# PROVIDER=vertex GOOGLE_CLOUD_PROJECT=scp-tenant-dps-dev yamlgraph graph run …
```

### Implementation sketch

**1. `pyproject.toml` — add optional extra**

```toml
[project.optional-dependencies]
vertex = ["langchain-google-vertexai>=2.0.0"]
```

**2. `yamlgraph/config.py` — add to DEFAULT_MODELS**

```python
"vertex": os.getenv("VERTEX_MODEL", "gemini-2.0-flash"),
```

**3. `yamlgraph/utils/llm_factory.py` — add ProviderType entry, factory, dispatch**

```python
ProviderType = Literal[
    "anthropic",
    "deepseek",
    "google",
    "inception",
    "lmstudio",
    "mistral",
    "openai",
    "replicate",
    "vertex",    # ← new (alphabetical between replicate and xai)
    "xai",
]

def _create_vertex_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create Google Vertex AI LLM.

    Requires GOOGLE_CLOUD_PROJECT and optionally GOOGLE_CLOUD_LOCATION.
    Authentication is handled by Application Default Credentials (ADC) or a
    service account key file (GOOGLE_APPLICATION_CREDENTIALS).
    """
    from langchain_google_vertexai import ChatVertexAI

    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("VERTEXAI_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    return ChatVertexAI(
        model_name=model,
        temperature=temperature,
        project=project,
        location=location,
        **kwargs,
    )

# In _dispatch_provider (alphabetical, between replicate and xai):
if provider == "vertex":
    return _create_vertex_llm(model, temperature, **kwargs)
```

**4. Environment variables**

```bash
# .env or shell
GOOGLE_CLOUD_PROJECT=scp-tenant-dps-dev       # required
GOOGLE_CLOUD_LOCATION=europe-west4            # optional (default: us-central1)
VERTEX_MODEL=gemini-2.0-flash                 # optional model override
# ADC is resolved automatically (gcloud auth application-default login)
# or via GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

**5. Unit test (`tests/unit/test_llm_factory.py`)**

```python
@pytest.mark.req("REQ-YG-010")
def test_create_llm_vertex(monkeypatch):
    """Vertex provider creates ChatVertexAI with project and location."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "europe-west4")

    with patch("yamlgraph.utils.llm_factory.ChatVertexAI") as mock_cls:
        create_llm(provider="vertex", model="gemini-2.0-flash")
        mock_cls.assert_called_once()
        kwargs = mock_cls.call_args[1]
        assert kwargs["project"] == "test-project"
        assert kwargs["location"] == "europe-west4"
        assert kwargs["model_name"] == "gemini-2.0-flash"
```

**6. Architecture consistency**

- Update ARCHITECTURE.md `utils/llm_factory.py` row: `(9 providers)` → `(10 providers)`
- Update `test_provider_type_has_expected_providers` to include `"vertex"`
- Update `CLAUDE.md` env var table with `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`

## Acceptance Criteria

- [x] `create_llm(provider="vertex")` returns a `ChatVertexAI` instance
- [x] `GOOGLE_CLOUD_PROJECT` is forwarded to `ChatVertexAI(project=…)`
- [x] `GOOGLE_CLOUD_LOCATION` is forwarded (default: `"us-central1"`)
- [x] `VERTEX_MODEL` env var overrides default model (`gemini-2.0-flash`)
- [x] A graph with `defaults.provider: vertex` runs end-to-end (integration test, skipped if `GOOGLE_CLOUD_PROJECT` not set)
- [x] Unit test mocks `ChatVertexAI` and verifies all constructor kwargs
- [x] `langchain-google-vertexai` added as optional extra `[vertex]` in `pyproject.toml`
- [x] ARCHITECTURE.md provider count updated to 10
- [x] `test_provider_type_has_expected_providers` updated and passing
- [x] `CLAUDE.md` env var table updated
- [x] Changelog fragment written in `changelog/unreleased/`
- [x] Diary entry written in `docs/diary/`

## Files to Change

| File | Change |
|------|--------|
| `pyproject.toml` | Add `vertex` optional extra with `langchain-google-vertexai>=2.0.0` |
| `yamlgraph/config.py` | Add `"vertex"` to `DEFAULT_MODELS` |
| `yamlgraph/utils/llm_factory.py` | Add `ProviderType` entry, `_create_vertex_llm()`, dispatch case |
| `tests/unit/test_llm_factory.py` | Add `test_create_llm_vertex` unit test |
| `tests/integration/test_providers.py` | Add skippable integration test |
| `tests/unit/test_architecture_provider_count.py` | Add `"vertex"` to expected set |
| `ARCHITECTURE.md` | Bump provider count to 10 |
| `CLAUDE.md` | Add `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` env var rows |
| `.env.sample` | Add `GOOGLE_CLOUD_PROJECT=`, `GOOGLE_CLOUD_LOCATION=`, `VERTEX_MODEL=` |
| `changelog/unreleased/` | New fragment file |
| `docs/diary/` | Metacognitive entry |

## Alternatives Considered

1. **Reuse `google` provider with a `use_vertex=True` flag** — rejected; violates
   single-responsibility and adds a boolean flag that changes authentication
   semantics entirely. Two distinct providers is the established YAMLGraph pattern
   (e.g. `deepseek` and `openai` are separate despite sharing the same backend).

2. **Keep `google` and add `GOOGLE_CLOUD_PROJECT` fallback to it** — rejected;
   `ChatGoogleGenerativeAI` and `ChatVertexAI` have different constructor APIs.
   Normalising at the boundary (this factory) is correct per doctrine.

3. **Require service-account JSON** — rejected; ADC is the standard corporate auth
   mechanism. `GOOGLE_APPLICATION_CREDENTIALS` is already honoured by the GCP SDK
   transparently; no YAMLGraph-specific handling needed.

## Related

- FR-112: Inception provider (pattern reference for OpenAI-compatible APIs)
- FR-121: Architecture provider count consistency test
- `yamlgraph/utils/llm_factory.py` — dispatch pattern
- `yamlgraph/config.py` — DEFAULT_MODELS
- `tests/unit/test_architecture_provider_count.py` — must be updated
- https://python.langchain.com/docs/integrations/chat/google_vertex_ai_palm/
