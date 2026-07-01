"""Tests for streaming support - Phase 3 (004).

TDD: RED phase - write tests first.
"""

from unittest.mock import MagicMock, patch

import pytest

# ==============================================================================
# execute_prompt_streaming tests
# ==============================================================================


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-009")
async def test_execute_prompt_streaming_yields_tokens():
    """execute_prompt_streaming yields tokens from LLM stream."""
    from yamlgraph.executor_async import execute_prompt_streaming

    # Mock LLM with astream method
    mock_chunk1 = MagicMock()
    mock_chunk1.content = "Hello"
    mock_chunk2 = MagicMock()
    mock_chunk2.content = " World"
    mock_chunk3 = MagicMock()
    mock_chunk3.content = "!"

    async def mock_astream(*args, **kwargs):
        for chunk in [mock_chunk1, mock_chunk2, mock_chunk3]:
            yield chunk

    mock_llm = MagicMock()
    mock_llm.astream = mock_astream

    with (
        patch("yamlgraph.executor_async.create_llm", return_value=mock_llm),
        patch("yamlgraph.executor_base.load_prompt") as mock_load,
    ):
        mock_load.return_value = {
            "system": "You are helpful.",
            "user": "Say hello",
        }

        tokens = []
        async for token in execute_prompt_streaming("greet", variables={}):
            tokens.append(token)

        assert tokens == ["Hello", " World", "!"]


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-009")
async def test_execute_prompt_streaming_with_variables():
    """execute_prompt_streaming formats template with variables."""
    from yamlgraph.executor_async import execute_prompt_streaming

    mock_chunk = MagicMock()
    mock_chunk.content = "Hi Alice!"

    async def mock_astream(*args, **kwargs):
        yield mock_chunk

    mock_llm = MagicMock()
    mock_llm.astream = mock_astream

    with (
        patch("yamlgraph.executor_async.create_llm", return_value=mock_llm),
        patch("yamlgraph.executor_base.load_prompt") as mock_load,
        patch(
            "yamlgraph.executor_base.format_prompt", return_value="Say hello to Alice"
        ),
    ):
        mock_load.return_value = {
            "system": "",
            "user": "Say hello to {name}",
        }

        tokens = []
        async for token in execute_prompt_streaming(
            "greet", variables={"name": "Alice"}
        ):
            tokens.append(token)

        assert tokens == ["Hi Alice!"]


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-009")
async def test_execute_prompt_streaming_uses_provider():
    """execute_prompt_streaming passes provider to create_llm."""
    from yamlgraph.executor_async import execute_prompt_streaming

    mock_chunk = MagicMock()
    mock_chunk.content = "test"

    async def mock_astream(*args, **kwargs):
        yield mock_chunk

    mock_llm = MagicMock()
    mock_llm.astream = mock_astream

    with (
        patch(
            "yamlgraph.executor_async.create_llm", return_value=mock_llm
        ) as mock_create,
        patch("yamlgraph.executor_base.load_prompt") as mock_load,
    ):
        mock_load.return_value = {"system": "", "user": "test"}

        async for _ in execute_prompt_streaming(
            "test", variables={}, provider="openai"
        ):
            pass

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs.get("provider") == "openai"


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-009")
async def test_execute_prompt_streaming_handles_empty_chunks():
    """execute_prompt_streaming skips empty chunks."""
    from yamlgraph.executor_async import execute_prompt_streaming

    mock_chunk1 = MagicMock()
    mock_chunk1.content = "Hello"
    mock_chunk2 = MagicMock()
    mock_chunk2.content = ""  # Empty
    mock_chunk3 = MagicMock()
    mock_chunk3.content = None  # None
    mock_chunk4 = MagicMock()
    mock_chunk4.content = "World"

    async def mock_astream(*args, **kwargs):
        for chunk in [mock_chunk1, mock_chunk2, mock_chunk3, mock_chunk4]:
            yield chunk

    mock_llm = MagicMock()
    mock_llm.astream = mock_astream

    with (
        patch("yamlgraph.executor_async.create_llm", return_value=mock_llm),
        patch("yamlgraph.executor_base.load_prompt") as mock_load,
    ):
        mock_load.return_value = {"system": "", "user": "test"}

        tokens = []
        async for token in execute_prompt_streaming("test", variables={}):
            tokens.append(token)

        # Only non-empty tokens
        assert tokens == ["Hello", "World"]


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-009")
async def test_execute_prompt_streaming_propagates_errors():
    """execute_prompt_streaming propagates LLM errors."""
    from yamlgraph.executor_async import execute_prompt_streaming

    async def mock_astream(*args, **kwargs):
        yield MagicMock(content="start")
        raise ValueError("LLM error")

    mock_llm = MagicMock()
    mock_llm.astream = mock_astream

    with (
        patch("yamlgraph.executor_async.create_llm", return_value=mock_llm),
        patch("yamlgraph.executor_base.load_prompt") as mock_load,
    ):
        mock_load.return_value = {"system": "", "user": "test"}

        tokens = []
        with pytest.raises(ValueError, match="LLM error"):
            async for token in execute_prompt_streaming("test", variables={}):
                tokens.append(token)

        # Should have received first token before error
        assert tokens == ["start"]


# ==============================================================================
# Streaming with output collection
# ==============================================================================


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-009")
async def test_execute_prompt_streaming_collect():
    """execute_prompt_streaming can collect all tokens into string."""
    from yamlgraph.executor_async import execute_prompt_streaming

    mock_chunks = [MagicMock(content=c) for c in ["The ", "quick ", "brown ", "fox"]]

    async def mock_astream(*args, **kwargs):
        for chunk in mock_chunks:
            yield chunk

    mock_llm = MagicMock()
    mock_llm.astream = mock_astream

    with (
        patch("yamlgraph.executor_async.create_llm", return_value=mock_llm),
        patch("yamlgraph.executor_base.load_prompt") as mock_load,
    ):
        mock_load.return_value = {"system": "", "user": "test"}

        # Collect all tokens
        result = "".join(
            [token async for token in execute_prompt_streaming("test", {})]
        )

        assert result == "The quick brown fox"


# ==============================================================================
