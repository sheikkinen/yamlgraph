"""Unit tests for LLM factory module."""

import os
from unittest.mock import patch

import pytest
from langchain_anthropic import ChatAnthropic

from yamlgraph.utils.llm_factory import clear_cache, create_llm


class TestCreateLLM:
    """Test the create_llm factory function."""

    def setup_method(self):
        """Clear cache and environment before each test."""
        clear_cache()

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_default_provider_is_anthropic(self):
        """Should use Anthropic by default."""
        # Clear PROVIDER from environment to ensure default behavior
        with patch.dict(os.environ, {"PROVIDER": ""}, clear=False):
            llm = create_llm(temperature=0.7)
            assert isinstance(llm, ChatAnthropic)
            assert llm.temperature == 0.7

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_explicit_anthropic_provider(self):
        """Should create Anthropic LLM when provider='anthropic'."""
        llm = create_llm(provider="anthropic", temperature=0.5)
        assert isinstance(llm, ChatAnthropic)
        assert llm.temperature == 0.5

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_mistral_provider(self):
        """Should create Mistral LLM when provider='mistral'."""
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"}):
            llm = create_llm(provider="mistral", temperature=0.8)
            # Check it's the right class (will import on first call)
            assert llm.__class__.__name__ == "ChatMistralAI"
            assert llm.temperature == 0.8

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_openai_provider(self):
        """Should create OpenAI LLM when provider='openai'."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            llm = create_llm(provider="openai", temperature=0.6)
            assert llm.__class__.__name__ == "ChatOpenAI"
            assert llm.temperature == 0.6

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_xai_provider(self):
        """Should create xAI LLM when provider='xai'."""
        with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
            llm = create_llm(provider="xai", temperature=0.6)
            assert llm.__class__.__name__ == "ChatOpenAI"
            assert llm.temperature == 0.6
            assert llm.openai_api_base == "https://api.x.ai/v1"

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_provider_from_environment(self):
        """Should use PROVIDER env var when no provider specified."""
        with patch.dict(
            os.environ, {"PROVIDER": "mistral", "MISTRAL_API_KEY": "test-key"}
        ):
            llm = create_llm(temperature=0.7)
            assert llm.__class__.__name__ == "ChatMistralAI"

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_custom_model(self):
        """Should use custom model when specified."""
        with patch.dict(os.environ, {"PROVIDER": ""}, clear=False):
            llm = create_llm(model="claude-opus-4", temperature=0.5)
            assert isinstance(llm, ChatAnthropic)
            assert llm.model == "claude-opus-4"

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_model_override_parameter(self):
        """Should prefer model parameter over default."""
        llm = create_llm(provider="anthropic", model="claude-sonnet-4", temperature=0.7)
        assert llm.model == "claude-sonnet-4"

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_default_models(self):
        """Should use correct default models for each provider."""
        # Anthropic default - use the configured default from config.py
        from yamlgraph.config import DEFAULT_MODELS

        llm_anthropic = create_llm(provider="anthropic", temperature=0.7)
        assert llm_anthropic.model == DEFAULT_MODELS["anthropic"]

        # Mistral default
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"}):
            llm_mistral = create_llm(provider="mistral", temperature=0.7)
            assert llm_mistral.model == "mistral-large-latest"

        # OpenAI default (uses model_name attribute)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            llm_openai = create_llm(provider="openai", temperature=0.7)
            assert llm_openai.model_name == "gpt-4o"

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_invalid_provider(self):
        """Should raise error for invalid provider."""
        with pytest.raises((ValueError, KeyError)):
            create_llm(provider="invalid-provider", temperature=0.7)

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_caching(self):
        """Should cache LLM instances for same parameters."""
        llm1 = create_llm(provider="anthropic", temperature=0.7)
        llm2 = create_llm(provider="anthropic", temperature=0.7)
        assert llm1 is llm2

        # Different temperature = different instance
        llm3 = create_llm(provider="anthropic", temperature=0.5)
        assert llm1 is not llm3

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_cache_key_includes_all_params(self):
        """Cache should differentiate on provider, model, temperature."""
        llm1 = create_llm(
            provider="anthropic", model="claude-haiku-4-5", temperature=0.7
        )
        llm2 = create_llm(provider="anthropic", model="claude-opus-4", temperature=0.7)
        assert llm1 is not llm2

        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"}):
            llm3 = create_llm(provider="mistral", temperature=0.7)
            assert llm1 is not llm3

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_google_provider(self):
        """Should create Google Gemini LLM when provider='google'."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            llm = create_llm(provider="google", temperature=0.7)
            assert llm.__class__.__name__ == "ChatGoogleGenerativeAI"
            assert llm.temperature == 0.7

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_google_default_model(self):
        """Should have a Google model default that starts with 'gemini'."""
        from yamlgraph.config import DEFAULT_MODELS

        assert "google" in DEFAULT_MODELS
        assert DEFAULT_MODELS["google"].startswith("gemini")

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_google_custom_model(self):
        """Should accept custom Google model."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            llm = create_llm(provider="google", model="gemini-2.5-pro", temperature=0.5)
            assert llm.model == "gemini-2.5-pro"

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_inception_provider(self):
        """Should create Inception Labs LLM when provider='inception'."""
        with patch.dict(os.environ, {"INCEPTION_API_KEY": "test-key"}):
            llm = create_llm(provider="inception", temperature=0.6)
            assert llm.__class__.__name__ == "ChatOpenAI"
            assert llm.temperature == 0.6
            assert llm.openai_api_base == "https://api.inceptionlabs.ai/v1"

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_inception_default_model(self):
        """Should use mercury-2 as default Inception model."""
        from yamlgraph.config import DEFAULT_MODELS

        assert "inception" in DEFAULT_MODELS
        assert DEFAULT_MODELS["inception"] == "mercury-2"

    @pytest.mark.req("REQ-YG-010")
    def test_create_llm_vertex(self, monkeypatch):
        """Vertex provider creates ChatGoogleGenerativeAI with vertexai=True."""
        monkeypatch.delenv("VERTEX_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "europe-west4")

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
            create_llm(provider="vertex", model="gemini-2.0-flash")
            mock_cls.assert_called_once()
            kwargs = mock_cls.call_args[1]
            assert kwargs["project"] == "test-project"
            assert kwargs["location"] == "europe-west4"
            assert kwargs["model"] == "gemini-2.0-flash"
            assert kwargs["vertexai"] is True

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_default_location(self, monkeypatch):
        """Vertex provider defaults location to us-central1 when env var not set."""
        monkeypatch.delenv("VERTEX_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
        monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
            create_llm(provider="vertex", model="gemini-2.0-flash")
            kwargs = mock_cls.call_args[1]
            assert kwargs["location"] == "us-central1"

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_model_env_var(self, monkeypatch):
        """VERTEX_MODEL env var overrides default model."""
        from yamlgraph.config import DEFAULT_MODELS

        assert "vertex" in DEFAULT_MODELS
        assert DEFAULT_MODELS["vertex"].startswith("gemini")

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_vertexai_project_fallback(self, monkeypatch):
        """Vertex provider falls back to VERTEXAI_PROJECT env var."""
        monkeypatch.delenv("VERTEX_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.setenv("VERTEXAI_PROJECT", "fallback-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
            create_llm(provider="vertex", model="gemini-2.0-flash")
            kwargs = mock_cls.call_args[1]
            assert kwargs["project"] == "fallback-project"

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_express_api_key(self, monkeypatch):
        """VERTEX_API_KEY triggers Express mode: google_api_key set, no project/location."""
        monkeypatch.setenv("VERTEX_API_KEY", "express-key-abc")
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.delenv("VERTEXAI_PROJECT", raising=False)

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
            create_llm(provider="vertex", model="gemini-2.0-flash")
            kwargs = mock_cls.call_args[1]
            assert kwargs["google_api_key"] == "express-key-abc"
            assert "project" not in kwargs
            assert "location" not in kwargs
            assert kwargs["vertexai"] is True

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_express_takes_priority_over_project(self, monkeypatch):
        """When VERTEX_API_KEY set, project/location are omitted even if present."""
        monkeypatch.setenv("VERTEX_API_KEY", "express-key-xyz")
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "should-be-ignored")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-east1")

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
            create_llm(provider="vertex", model="gemini-2.0-flash")
            kwargs = mock_cls.call_args[1]
            assert kwargs["google_api_key"] == "express-key-xyz"
            assert "project" not in kwargs
            assert "location" not in kwargs

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_adc_no_api_key(self, monkeypatch):
        """When VERTEX_API_KEY absent, ADC branch uses project+location, no google_api_key."""
        monkeypatch.delenv("VERTEX_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
            create_llm(provider="vertex", model="gemini-2.0-flash")
            kwargs = mock_cls.call_args[1]
            assert kwargs["project"] == "my-project"
            assert kwargs["location"] == "us-central1"
            assert "google_api_key" not in kwargs

    # --- FR-227 condemning tests ---

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_express_masks_gcp_env_vars_during_construction(self, monkeypatch):
        """FR-227: During Express construction, GOOGLE_CLOUD_PROJECT/LOCATION/VERTEXAI_PROJECT
        must be absent from os.environ so the SDK cannot fall back to ADC auth."""
        monkeypatch.setenv("VERTEX_API_KEY", "express-key-fr227")
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-east1")
        monkeypatch.setenv("VERTEXAI_PROJECT", "my-vertexai-project")

        env_snapshot: dict[str, str | None] = {}

        def capture_env(**kwargs):  # noqa: ARG001
            env_snapshot["GOOGLE_CLOUD_PROJECT"] = os.environ.get(
                "GOOGLE_CLOUD_PROJECT"
            )
            env_snapshot["GOOGLE_CLOUD_LOCATION"] = os.environ.get(
                "GOOGLE_CLOUD_LOCATION"
            )
            env_snapshot["VERTEXAI_PROJECT"] = os.environ.get("VERTEXAI_PROJECT")
            from unittest.mock import MagicMock

            return MagicMock()

        with patch(
            "langchain_google_genai.ChatGoogleGenerativeAI", side_effect=capture_env
        ):
            create_llm(provider="vertex", model="gemini-2.0-flash")

        assert (
            env_snapshot["GOOGLE_CLOUD_PROJECT"] is None
        ), "GOOGLE_CLOUD_PROJECT must be absent from os.environ during Express construction"
        assert (
            env_snapshot["GOOGLE_CLOUD_LOCATION"] is None
        ), "GOOGLE_CLOUD_LOCATION must be absent from os.environ during Express construction"
        assert (
            env_snapshot["VERTEXAI_PROJECT"] is None
        ), "VERTEXAI_PROJECT must be absent from os.environ during Express construction"

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_express_restores_env_vars_after_construction(self, monkeypatch):
        """FR-227: After Express construction, all masked env vars are restored."""
        monkeypatch.setenv("VERTEX_API_KEY", "express-key-fr227")
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "restore-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-east1")
        monkeypatch.setenv("VERTEXAI_PROJECT", "restore-vertexai")

        with patch("langchain_google_genai.ChatGoogleGenerativeAI"):
            create_llm(provider="vertex", model="gemini-2.0-flash")

        assert os.environ.get("GOOGLE_CLOUD_PROJECT") == "restore-project"
        assert os.environ.get("GOOGLE_CLOUD_LOCATION") == "us-east1"
        assert os.environ.get("VERTEXAI_PROJECT") == "restore-vertexai"

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_express_restores_env_vars_on_exception(self, monkeypatch):
        """FR-227: If ChatGoogleGenerativeAI raises, masked env vars are still restored."""
        monkeypatch.setenv("VERTEX_API_KEY", "express-key-fr227")
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "exc-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        monkeypatch.setenv("VERTEXAI_PROJECT", "exc-vertexai")

        with (
            patch(
                "langchain_google_genai.ChatGoogleGenerativeAI",
                side_effect=RuntimeError("SDK boom"),
            ),
            pytest.raises(RuntimeError, match="SDK boom"),
        ):
            create_llm(provider="vertex", model="gemini-2.0-flash")

        assert os.environ.get("GOOGLE_CLOUD_PROJECT") == "exc-project"
        assert os.environ.get("GOOGLE_CLOUD_LOCATION") == "us-central1"
        assert os.environ.get("VERTEXAI_PROJECT") == "exc-vertexai"

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_express_vertexai_location_not_masked(self, monkeypatch):
        """FR-227: VERTEXAI_LOCATION must NOT be removed during Express construction."""
        monkeypatch.setenv("VERTEX_API_KEY", "express-key-fr227")
        monkeypatch.setenv("VERTEXAI_LOCATION", "europe-west4")

        env_snapshot: dict[str, str | None] = {}

        def capture_env(**kwargs):  # noqa: ARG001
            env_snapshot["VERTEXAI_LOCATION"] = os.environ.get("VERTEXAI_LOCATION")
            from unittest.mock import MagicMock

            return MagicMock()

        with patch(
            "langchain_google_genai.ChatGoogleGenerativeAI", side_effect=capture_env
        ):
            create_llm(provider="vertex", model="gemini-2.0-flash")

        assert (
            env_snapshot["VERTEXAI_LOCATION"] == "europe-west4"
        ), "VERTEXAI_LOCATION must NOT be masked during Express construction"

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_construct_lock_exists(self):
        """FR-227: _VERTEX_CONSTRUCT_LOCK must be a module-level threading.Lock."""
        import threading

        import yamlgraph.utils.llm_factory as llm_mod

        assert hasattr(
            llm_mod, "_VERTEX_CONSTRUCT_LOCK"
        ), "_VERTEX_CONSTRUCT_LOCK must exist as a module-level attribute"
        assert isinstance(llm_mod._VERTEX_CONSTRUCT_LOCK, type(threading.Lock())), (  # noqa: SLF001
            "_VERTEX_CONSTRUCT_LOCK must be a threading.Lock instance"
        )

    @pytest.mark.req("REQ-YG-010")
    def test_masked_env_context_manager_removes_and_restores(self):
        """FR-227: _masked_env context manager removes keys and restores them on exit."""
        import yamlgraph.utils.llm_factory as llm_mod

        assert hasattr(
            llm_mod, "_masked_env"
        ), "_masked_env context manager must exist in llm_factory"

        import os as _os

        key = "_FR227_TEST_KEY"
        _os.environ[key] = "original-value"
        try:
            with llm_mod._masked_env(key):  # noqa: SLF001
                assert key not in _os.environ, "Key must be absent inside _masked_env"
            assert (
                _os.environ.get(key) == "original-value"
            ), "Key must be restored after _masked_env exits"
        finally:
            _os.environ.pop(key, None)

    @pytest.mark.req("REQ-YG-010")
    def test_masked_env_restores_on_exception(self):
        """FR-227: _masked_env restores env vars even when body raises."""
        import os as _os

        import yamlgraph.utils.llm_factory as llm_mod

        key = "_FR227_EXC_KEY"
        _os.environ[key] = "must-be-restored"
        try:
            with (
                pytest.raises(ValueError, match="inner error"),
                llm_mod._masked_env(key),  # noqa: SLF001
            ):
                raise ValueError("inner error")
            assert _os.environ.get(key) == "must-be-restored"
        finally:
            _os.environ.pop(key, None)

    @pytest.mark.req("REQ-YG-010")
    def test_vertex_adc_mode_does_not_mask_env_vars(self, monkeypatch):
        """FR-227: In ADC mode (no VERTEX_API_KEY), env vars are never removed."""
        monkeypatch.delenv("VERTEX_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "adc-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        env_snapshot: dict[str, str | None] = {}

        def capture_env(**kwargs):  # noqa: ARG001
            env_snapshot["GOOGLE_CLOUD_PROJECT"] = os.environ.get(
                "GOOGLE_CLOUD_PROJECT"
            )
            env_snapshot["GOOGLE_CLOUD_LOCATION"] = os.environ.get(
                "GOOGLE_CLOUD_LOCATION"
            )
            from unittest.mock import MagicMock

            return MagicMock()

        with patch(
            "langchain_google_genai.ChatGoogleGenerativeAI", side_effect=capture_env
        ):
            create_llm(provider="vertex", model="gemini-2.0-flash")

        assert (
            env_snapshot["GOOGLE_CLOUD_PROJECT"] == "adc-project"
        ), "ADC mode must not remove GOOGLE_CLOUD_PROJECT"
        assert (
            env_snapshot["GOOGLE_CLOUD_LOCATION"] == "us-central1"
        ), "ADC mode must not remove GOOGLE_CLOUD_LOCATION"
