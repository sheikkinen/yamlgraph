# Feature Request: FR-229 Mask GOOGLE_API_KEY During Vertex Express Construction

**Priority:** HIGH
**Type:** Bug
**Status:** Approved — implement unit tests
**Effort:** 0.5 days
**Requested:** 2026-04-17

## Summary

When `VERTEX_API_KEY` is set (Vertex AI Express mode) and `GOOGLE_API_KEY` is also present
in the environment, LangChain's `ChatGoogleGenerativeAI.validate_environment` reads
`GOOGLE_API_KEY` from `os.environ` and silently overrides the explicitly passed
`google_api_key=VERTEX_API_KEY`, causing a `401 UNAUTHENTICATED` error.

The production fix — adding `"GOOGLE_API_KEY"` to `_masked_env(...)` in the Express branch
of `_create_vertex_llm` — is already present (commit `557b108`, FR-227). This FR tracks
the missing unit tests that condemn the root cause and verify the fix.

## Value Statement

Developers using Vertex AI Express mode (`VERTEX_API_KEY`) whose `.env` file also contains
`GOOGLE_API_KEY` (Gemini developer key) get a working LLM call instead of a silent
`401 UNAUTHENTICATED` failure with no actionable error message.

## Problem

`ChatGoogleGenerativeAI.validate_environment` (LangChain) checks `os.getenv("GOOGLE_API_KEY")`
after constructor kwargs are applied. Its precedence rule treats a present `GOOGLE_API_KEY`
env var as authoritative, replacing the explicitly passed `google_api_key` argument with the
Gemini developer key. The google-genai SDK then authenticates against the Gemini developer
endpoint rather than the Vertex Express endpoint, producing `401 UNAUTHENTICATED`.

FR-227 solved the symmetric problem for the google-genai SDK's `BaseApiClient` reading
`GOOGLE_CLOUD_PROJECT`/`GOOGLE_CLOUD_LOCATION`/`VERTEXAI_PROJECT`. The LangChain wrapper
layer introduces a second env-var read that FR-227's test suite did not cover.

**Root cause location:**
- `langchain_google_genai/chat_models.py` — `validate_environment` reads `GOOGLE_API_KEY`
- `yamlgraph/utils/llm_factory.py` line ~401 — Express branch `_masked_env(...)` call
  (fix already present; tests missing)

**Production code (already correct):**
```python
if api_key:
    with (
        _VERTEX_CONSTRUCT_LOCK,
        _masked_env(
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_LOCATION",
            "VERTEXAI_PROJECT",
            "GOOGLE_API_KEY",   # present since commit 557b108
        ),
    ):
        return ChatGoogleGenerativeAI(...)
```

## Proposed Solution

Add four unit tests to `tests/unit/test_llm_factory.py` inside the existing
`TestVertexProvider` class, following the FR-227 test pattern. Write RED first (committed
with `SKIP=pytest`), then verify GREEN against the already-present production code.

```python
@pytest.mark.req("REQ-YG-010")
def test_vertex_express_masks_google_api_key_during_construction(self, monkeypatch):
    """FR-229: GOOGLE_API_KEY must be absent from os.environ during Express construction."""
    monkeypatch.setenv("VERTEX_API_KEY", "express-key-fr229")
    monkeypatch.setenv("GOOGLE_API_KEY", "gemini-dev-key")
    captured = {}

    def capture_env(**kwargs):
        captured["GOOGLE_API_KEY_present"] = "GOOGLE_API_KEY" in os.environ
        return MagicMock()

    with patch("yamlgraph.utils.llm_factory.ChatGoogleGenerativeAI", side_effect=capture_env):
        create_llm(provider="vertex")

    assert not captured["GOOGLE_API_KEY_present"], (
        "GOOGLE_API_KEY must be absent from os.environ during Express construction"
    )


@pytest.mark.req("REQ-YG-010")
def test_vertex_express_restores_google_api_key_after_construction(self, monkeypatch):
    """FR-229: GOOGLE_API_KEY must be restored after Express construction."""
    monkeypatch.setenv("VERTEX_API_KEY", "express-key-fr229")
    monkeypatch.setenv("GOOGLE_API_KEY", "gemini-dev-key")

    with patch("yamlgraph.utils.llm_factory.ChatGoogleGenerativeAI", return_value=MagicMock()):
        create_llm(provider="vertex")

    assert os.environ.get("GOOGLE_API_KEY") == "gemini-dev-key"


@pytest.mark.req("REQ-YG-010")
def test_vertex_express_restores_google_api_key_on_exception(self, monkeypatch):
    """FR-229: GOOGLE_API_KEY must be restored even when construction raises."""
    monkeypatch.setenv("VERTEX_API_KEY", "express-key-fr229")
    monkeypatch.setenv("GOOGLE_API_KEY", "gemini-dev-key")

    with patch(
        "yamlgraph.utils.llm_factory.ChatGoogleGenerativeAI",
        side_effect=RuntimeError("construction failed"),
    ):
        with pytest.raises(RuntimeError):
            create_llm(provider="vertex")

    assert os.environ.get("GOOGLE_API_KEY") == "gemini-dev-key"


@pytest.mark.req("REQ-YG-010")
def test_vertex_adc_does_not_mask_google_api_key(self, monkeypatch):
    """FR-229: ADC mode (no VERTEX_API_KEY) must not remove GOOGLE_API_KEY."""
    monkeypatch.delenv("VERTEX_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "gemini-dev-key")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    captured = {}

    def capture_env(**kwargs):
        captured["GOOGLE_API_KEY_present"] = "GOOGLE_API_KEY" in os.environ
        return MagicMock()

    with patch("yamlgraph.utils.llm_factory.ChatGoogleGenerativeAI", side_effect=capture_env):
        create_llm(provider="vertex")

    assert captured["GOOGLE_API_KEY_present"], (
        "GOOGLE_API_KEY must NOT be masked in ADC mode"
    )
```

## Acceptance Criteria

- [x] `"GOOGLE_API_KEY"` is included in `_masked_env(...)` in the Express branch of
  `_create_vertex_llm` *(already done — commit 557b108)*
- [ ] Unit test: `GOOGLE_API_KEY` absent from `os.environ` at construction time when both
  `VERTEX_API_KEY` and `GOOGLE_API_KEY` are set
- [ ] Unit test: `GOOGLE_API_KEY` restored to original value after successful Express
  construction
- [ ] Unit test: `GOOGLE_API_KEY` restored after Express construction raises an exception
- [ ] Unit test: ADC mode (no `VERTEX_API_KEY`) does not remove `GOOGLE_API_KEY` from
  `os.environ` during construction
- [ ] All FR-227 tests remain green
- [ ] `pytest tests/unit/test_llm_factory.py -q --no-cov` passes

## Alternatives Considered

- **Pass `google_api_key=None` explicitly**: LangChain's `validate_environment` still reads
  `os.environ` after constructor kwargs; the explicit kwarg is overwritten.
- **Remove `GOOGLE_API_KEY` from `.env` before running Vertex**: Operationally fragile;
  requires users to maintain separate `.env` files per provider. Framework adapters should
  handle provider quirks, not end users.
- **Clear `GOOGLE_API_KEY` at module import time**: Would break the `google` provider which
  legitimately reads it; scope too broad.

## Related

- `yamlgraph/utils/llm_factory.py` — `_create_vertex_llm` Express branch (line ~397–410)
- `tests/unit/test_llm_factory.py` — `TestVertexProvider` class; FR-227 tests to extend
- `feature-requests/FR-227-vertex-express-env-var-masking.md` — parent FR (Implemented)
- `feature-requests/FR-226-vertex-express-api-key-auth.md` — original Express mode FR
- LangChain source: `langchain_google_genai/chat_models.py` — `validate_environment`
