"""Unit tests for async LLM factory module."""

from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.utils.llm_factory_async import (
    create_llm_async,
    get_executor,
    invoke_async,
    shutdown_executor,
)


class TestGetExecutor:
    """Tests for get_executor function."""

    def teardown_method(self):
        """Clean up executor after each test."""
        shutdown_executor()

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_creates_executor(self):
        """Should create a ThreadPoolExecutor."""
        executor = get_executor()
        assert executor is not None

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_returns_same_executor(self):
        """Should return the same executor on subsequent calls."""
        executor1 = get_executor()
        executor2 = get_executor()
        assert executor1 is executor2


class TestShutdownExecutor:
    """Tests for shutdown_executor function."""

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_shutdown_cleans_up(self):
        """Shutdown should clean up executor."""
        # Create an executor
        executor1 = get_executor()
        assert executor1 is not None

        # Shutdown
        shutdown_executor()

        # Next call should create a new executor
        executor2 = get_executor()
        assert executor2 is not executor1

    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    def test_shutdown_when_none(self):
        """Shutdown when no executor should not raise."""
        shutdown_executor()  # Ensure clean state
        shutdown_executor()  # Should not raise


class TestCreateLLMAsync:
    """Tests for create_llm_async function."""

    def teardown_method(self):
        """Clean up executor after each test."""
        shutdown_executor()

    @pytest.mark.asyncio
    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    async def test_creates_llm(self):
        """Should create an LLM instance."""
        llm = await create_llm_async(provider="anthropic", temperature=0.5)
        assert llm is not None
        assert llm.temperature == 0.5

    @pytest.mark.asyncio
    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    async def test_uses_default_provider(self):
        """Should use default provider when not specified."""
        with patch.dict("os.environ", {"PROVIDER": ""}, clear=False):
            llm = await create_llm_async(temperature=0.7)
            # Default is anthropic
            assert "anthropic" in llm.__class__.__name__.lower()


class TestInvokeAsync:
    """Tests for invoke_async function."""

    def teardown_method(self):
        """Clean up executor after each test."""
        shutdown_executor()

    @pytest.mark.asyncio
    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    async def test_invoke_returns_string(self):
        """Should return string content when no output model."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Hello, world!"
        mock_llm.invoke.return_value = mock_response

        messages = [MagicMock()]
        result = await invoke_async(mock_llm, messages)

        assert result == "Hello, world!"
        mock_llm.invoke.assert_called_once_with(messages)

    @pytest.mark.asyncio
    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    async def test_invoke_with_output_model(self):
        """Should use structured output when model provided."""
        from pydantic import BaseModel

        class TestOutput(BaseModel):
            value: str

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = TestOutput(value="test")

        messages = [MagicMock()]
        result = await invoke_async(mock_llm, messages, output_model=TestOutput)

        assert isinstance(result, TestOutput)
        assert result.value == "test"
        mock_llm.with_structured_output.assert_called_once_with(TestOutput)

    @pytest.mark.asyncio
    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    async def test_retries_on_transient_error(self):
        """FR-676: invoke_async retries on retryable errors then succeeds."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "recovered"

        # First call raises retryable, second succeeds
        rate_err = type("RateLimitError", (Exception,), {})("rate limited")
        mock_llm.invoke.side_effect = [rate_err, mock_response]

        messages = [MagicMock()]
        with patch(
            "yamlgraph.utils.llm_factory_async.asyncio.sleep", return_value=None
        ):
            result = await invoke_async(mock_llm, messages)

        assert result == "recovered"
        assert mock_llm.invoke.call_count == 2

    @pytest.mark.asyncio
    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    async def test_structured_output_json_fallback(self):
        """FR-676: invoke_async falls back to JSON extraction when response_format rejected."""
        from pydantic import BaseModel

        class TestOutput(BaseModel):
            value: str

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        # Structured output rejects response_format
        mock_structured_llm.invoke.side_effect = Exception(
            "response_format not supported"
        )
        # Plain invoke returns JSON in text
        plain_response = MagicMock()
        plain_response.content = '{"value": "fallback"}'
        mock_llm.invoke.return_value = plain_response

        messages = [MagicMock()]
        result = await invoke_async(mock_llm, messages, output_model=TestOutput)

        assert isinstance(result, TestOutput)
        assert result.value == "fallback"

    @pytest.mark.asyncio
    @pytest.mark.req("REQ-YG-010", "REQ-YG-011")
    async def test_fallback_raises_on_no_json(self):
        """FR-676/FR-669: fallback raises ValueError with snippet when no JSON found."""
        from pydantic import BaseModel

        class TestOutput(BaseModel):
            value: str

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.side_effect = Exception(
            "response_format not supported"
        )
        plain_response = MagicMock()
        plain_response.content = "I cannot produce JSON for this request."
        mock_llm.invoke.return_value = plain_response

        messages = [MagicMock()]
        with pytest.raises(ValueError, match="could not extract JSON"):
            await invoke_async(mock_llm, messages, output_model=TestOutput)
