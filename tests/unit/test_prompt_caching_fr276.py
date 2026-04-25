"""Acceptance tests for FR-276: Prompt Caching & CAG Baseline.

These tests define the contract that the enforce phase must satisfy.
All tests must FAIL on the current unmodified codebase (RED phase).
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from langchain_core.messages import SystemMessage


class TestPromptSegmentSchema:
    """Test system_segments YAML schema support (AC-2)."""

    @pytest.mark.req("REQ-YG-287")
    def test_system_segments_schema_validation(self, tmp_path: Path) -> None:
        """Prompt schema should support system_segments with per-segment cache boolean."""
        from yamlgraph.utils.prompts import load_prompt

        prompt_content = """
        system_segments:
          - content: |
              You are an expert assistant.
              {{architecture_context}}
            cache: true
          - content: |
              Current task: {{task_description}}
            cache: false
        user: |
          Please help with: {topic}
        """

        prompt_file = tmp_path / "test_segments.yaml"
        prompt_file.write_text(prompt_content)

        result = load_prompt("test_segments", prompts_dir=tmp_path)

        # Should parse system_segments as list with cache flags
        assert "system_segments" in result
        assert isinstance(result["system_segments"], list)
        assert len(result["system_segments"]) == 2
        assert result["system_segments"][0]["cache"] is True
        assert result["system_segments"][1]["cache"] is False

        # Test prepare_messages can handle system_segments (this should fail)
        from yamlgraph.executor_base import prepare_messages

        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = prompt_file

            # This should fail because prepare_messages doesn't know about system_segments yet
            messages, provider, model = prepare_messages(
                "test_segments",
                variables={
                    "topic": "test",
                    "architecture_context": "ctx",
                    "task_description": "desc",
                },
                prompts_dir=tmp_path,
            )

            # Should handle system_segments by creating appropriate SystemMessage
            assert len(messages) == 2
            system_msg = messages[0]
            assert isinstance(system_msg, SystemMessage)

            # This will fail - current implementation doesn't handle system_segments
            assert "expert assistant" in system_msg.content
            assert "Current task" in system_msg.content

    @pytest.mark.req("REQ-YG-287")
    def test_system_segments_without_cache_defaults_false(self, tmp_path: Path) -> None:
        """Segments without explicit cache should default to False."""
        from yamlgraph.utils.prompts import load_prompt

        prompt_content = """
        system_segments:
          - content: "You are helpful."
          - content: "Task: {{task}}"
            cache: true
        user: "Help me with {topic}"
        """

        prompt_file = tmp_path / "test_defaults.yaml"
        prompt_file.write_text(prompt_content)

        result = load_prompt("test_defaults", prompts_dir=tmp_path)

        # First segment should default cache: false
        assert result["system_segments"][0].get("cache", False) is False
        assert result["system_segments"][1]["cache"] is True


class TestBackwardCompatibility:
    """Test existing scalar system: prompts remain valid (AC-1, AC-3)."""

    @pytest.mark.req("REQ-YG-288")
    def test_scalar_system_prompt_unchanged(self, tmp_path: Path) -> None:
        """Existing prompts with scalar system should work unchanged."""
        from yamlgraph.executor_base import prepare_messages

        prompt_content = """
        system: |
          You are a helpful assistant.
          Always be polite and informative.
        user: |
          Please help me with: {topic}
        """

        prompt_file = tmp_path / "test_scalar.yaml"
        prompt_file.write_text(prompt_content)

        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = prompt_file
            with patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load:
                mock_load.return_value = {
                    "system": "You are a helpful assistant.\nAlways be polite and informative.",
                    "user": "Please help me with: {topic}",
                }

                messages, provider, model = prepare_messages(
                    "test_scalar", variables={"topic": "cooking"}, prompts_dir=tmp_path
                )

                # Should create SystemMessage with scalar content
                assert len(messages) == 2
                assert isinstance(messages[0], SystemMessage)
                assert "helpful assistant" in messages[0].content
                assert "Always be polite" in messages[0].content

    @pytest.mark.req("REQ-YG-288")
    def test_system_list_format_support(self, tmp_path: Path) -> None:
        """System field should accept list format for migration."""
        from yamlgraph.executor_base import prepare_messages

        # Write a real YAML file so load_prompt can open it
        prompt_file = tmp_path / "test_list.yaml"
        prompt_file.write_text(
            "system:\n"
            '  - content: "You are helpful."\n'
            "    cache: false\n"
            '  - content: "Task context: important"\n'
            "    cache: true\n"
            'user: "Help with {topic}"\n'
        )

        messages, provider, model = prepare_messages(
            "test_list", variables={"topic": "test"}, prompts_dir=tmp_path
        )

        # Should flatten list format into single SystemMessage for non-Anthropic
        assert len(messages) == 2
        assert isinstance(messages[0], SystemMessage)
        # Content should be concatenated
        assert "You are helpful" in messages[0].content
        assert "Task context" in messages[0].content


class TestAnthropicCacheControl:
    """Test Anthropic-specific cache_control injection (AC-4)."""

    @pytest.mark.req("REQ-YG-289")
    def test_anthropic_cache_control_injection(self, tmp_path: Path) -> None:
        """Anthropic provider should inject cache_control on cached segments."""
        from yamlgraph.executor_base import prepare_messages

        # Create a temp file for the test
        prompt_content = """
        system_segments:
          - content: "Stable context here"
            cache: true
          - content: "Dynamic content {{var}}"
            cache: false
        user: "Query: {topic}"
        """

        prompt_file = tmp_path / "test_anthropic.yaml"
        prompt_file.write_text(prompt_content)

        # This should fail because prepare_messages doesn't handle system_segments yet
        messages, provider, model = prepare_messages(
            "test_anthropic",
            variables={"topic": "test", "var": "value"},
            provider="anthropic",
            prompts_dir=tmp_path,
        )

        # For Anthropic, should create content blocks with cache_control
        assert len(messages) == 2
        system_msg = messages[0]
        assert isinstance(system_msg, SystemMessage)

        # This will fail until implementation - SystemMessage should have
        # additional_kwargs with content blocks and cache_control
        assert hasattr(system_msg, "additional_kwargs")
        cache_blocks = system_msg.additional_kwargs.get("content", [])
        assert len(cache_blocks) == 2
        assert cache_blocks[0].get("cache_control") == {"type": "ephemeral"}
        assert "cache_control" not in cache_blocks[1]

    @pytest.mark.req("REQ-YG-289")
    def test_anthropic_only_caches_true_segments(self, tmp_path: Path) -> None:
        """Only segments with cache: true should get cache_control."""
        from yamlgraph.executor_base import prepare_messages

        prompt_content = """
        system_segments:
          - content: "Not cached"
            cache: false
          - content: "Also not cached"
          - content: "This is cached"
            cache: true
        user: "Test {input}"
        """

        prompt_file = tmp_path / "test_selective.yaml"
        prompt_file.write_text(prompt_content)

        messages, provider, model = prepare_messages(
            "test_selective",
            variables={"input": "query"},
            provider="anthropic",
            prompts_dir=tmp_path,
        )

        system_msg = messages[0]
        cache_blocks = system_msg.additional_kwargs.get("content", [])

        # Only third block should have cache_control
        assert "cache_control" not in cache_blocks[0]
        assert "cache_control" not in cache_blocks[1]
        assert cache_blocks[2].get("cache_control") == {"type": "ephemeral"}


class TestNonAnthropicFlattening:
    """Test non-Anthropic providers flatten segments (AC-5)."""

    @pytest.mark.req("REQ-YG-290")
    def test_non_anthropic_flattens_segments(self) -> None:
        """Non-Anthropic providers should flatten system_segments to single string."""
        from yamlgraph.executor_base import prepare_messages

        with (
            patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve,
            patch("builtins.open", mock_open(read_data="")),
            patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load,
        ):
            mock_resolve.return_value = Path("test.yaml")
            mock_load.return_value = {
                "system_segments": [
                    {"content": "First segment", "cache": True},
                    {"content": "Second segment", "cache": False},
                ],
                "user": "Query: {topic}",
            }

            for provider in ["openai", "google", "mistral", None]:
                messages, _, _ = prepare_messages(
                    "test_flattening",
                    variables={"topic": "test"},
                    provider=provider,
                )

                # Should create single SystemMessage with concatenated content
                assert len(messages) == 2
                system_msg = messages[0]
                assert isinstance(system_msg, SystemMessage)

                # Content should contain both segments, cache flags ignored
                assert "First segment" in system_msg.content
                assert "Second segment" in system_msg.content

                # Should not have cache-related additional_kwargs
                assert not system_msg.additional_kwargs.get("content")

    @pytest.mark.req("REQ-YG-290")
    def test_non_anthropic_ignores_cache_flags_gracefully(self) -> None:
        """Non-Anthropic providers should ignore cache flags without error."""
        from yamlgraph.executor_base import prepare_messages

        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = Path("test.yaml")
            with patch("builtins.open", mock_open(read_data="")):
                with patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load:
                    mock_load.return_value = {
                        "system_segments": [
                            {"content": "Cached segment", "cache": True},
                            {"content": "Uncached segment", "cache": False},
                        ],
                        "user": "Test input",
                    }

                    # Should not raise any errors for any non-Anthropic provider
                    for provider in ["openai", "google", "mistral", "vertex", "azure"]:
                        try:
                            messages, _, _ = prepare_messages(
                                "test_graceful", provider=provider
                            )
                            # Should succeed and create valid messages
                            assert len(messages) == 2
                        except Exception as e:
                            pytest.fail(
                                f"Provider {provider} should handle cache flags gracefully, got: {e}"
                            )


class TestExecutorPathConsistency:
    """Test sync/async/streaming paths have same behavior (AC-6)."""

    @pytest.mark.req("REQ-YG-291")
    def test_async_executor_system_segments(self) -> None:
        """Async executor should handle system_segments same as sync."""
        from yamlgraph.executor_async import prepare_messages_async

        # This will fail until async path is implemented
        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = Path("test.yaml")
            with patch("builtins.open", mock_open(read_data="")):
                with patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load:
                    mock_load.return_value = {
                        "system_segments": [
                            {"content": "Context", "cache": True},
                            {"content": "Query", "cache": False},
                        ],
                        "user": "Input: {text}",
                    }

                    # prepare_messages_async should exist and behave like sync version
                    messages, provider, model = prepare_messages_async(
                        "test_async", variables={"text": "test"}, provider="anthropic"
                    )

                    assert len(messages) == 2
                    system_msg = messages[0]
                    assert isinstance(system_msg, SystemMessage)

                    # Should have same Anthropic cache_control behavior
                    cache_blocks = system_msg.additional_kwargs.get("content", [])
                    assert len(cache_blocks) == 2
                    assert cache_blocks[0].get("cache_control") == {"type": "ephemeral"}

    @pytest.mark.req("REQ-YG-291")
    def test_streaming_executor_system_segments(self) -> None:
        """Streaming execution should handle system_segments consistently."""
        # This will need to test whatever streaming message preparation exists
        # For now, assume it follows same pattern as sync/async
        from yamlgraph.executor_async import prepare_messages_async

        # Test that streaming mode (if different) handles segments same way
        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = Path("test.yaml")
            with patch("builtins.open", mock_open(read_data="")):
                with patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load:
                    mock_load.return_value = {
                        "system_segments": [{"content": "Stable", "cache": True}],
                        "user": "Stream this: {input}",
                    }

                    # Streaming should produce same message structure
                    messages, _, _ = prepare_messages_async(
                        "test_streaming", variables={"input": "data"}
                    )

                    assert len(messages) == 2
                    assert isinstance(messages[0], SystemMessage)


class TestErrorHandling:
    """Test validation and error cases (AC-10)."""

    @pytest.mark.req("REQ-YG-292")
    def test_conflicting_system_and_system_segments_error(self) -> None:
        """Should error when both system and system_segments are provided."""
        from yamlgraph.executor_base import prepare_messages

        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = Path("test.yaml")
            with patch("builtins.open", mock_open(read_data="")):
                with patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load:
                    mock_load.return_value = {
                        "system": "Traditional system prompt",
                        "system_segments": [
                            {"content": "Segmented prompt", "cache": True}
                        ],
                        "user": "Test input",
                    }

                    with pytest.raises(
                        ValueError, match="Cannot specify both.*system.*system_segments"
                    ):
                        prepare_messages("test_conflict")

    @pytest.mark.req("REQ-YG-292")
    def test_system_segments_precedence_over_system(self) -> None:
        """When both exist, should raise ValueError (AC-10 conflict detection)."""
        from yamlgraph.executor_base import prepare_messages

        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = Path("test.yaml")
            with patch("builtins.open", mock_open(read_data="")):
                with patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load:
                    mock_load.return_value = {
                        "system": "Should be ignored",
                        "system_segments": [
                            {"content": "Should be used", "cache": False}
                        ],
                        "user": "Test",
                    }

                    # Implementation chose error-on-conflict (consistent with test_conflicting above)
                    with pytest.raises(
                        ValueError, match="Cannot specify both.*system.*system_segments"
                    ):
                        prepare_messages("test_precedence")

    @pytest.mark.req("REQ-YG-292")
    def test_empty_system_segments_validation(self) -> None:
        """Empty system_segments should be validated appropriately."""
        from yamlgraph.executor_base import prepare_messages

        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = Path("test.yaml")
            with patch("builtins.open", mock_open(read_data="")):
                with patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load:
                    mock_load.return_value = {
                        "system_segments": [],  # Empty list
                        "user": "Test",
                    }

                    # Should handle empty segments gracefully
                    messages, _, _ = prepare_messages("test_empty")

                    # Should create empty SystemMessage or skip it entirely
                    assert len(messages) >= 1  # At least user message
                    if len(messages) == 2:
                        # If SystemMessage created, should be empty
                        assert isinstance(messages[0], SystemMessage)
                        assert messages[0].content == ""


class TestSegmentContentProcessing:
    """Test segment content handling and variable substitution."""

    @pytest.mark.req("REQ-YG-293")
    def test_system_segments_variable_substitution(self) -> None:
        """System segments should support variable substitution like scalar system."""
        from yamlgraph.executor_base import prepare_messages

        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = Path("test.yaml")
            with patch("builtins.open", mock_open(read_data="")):
                with patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load:
                    mock_load.return_value = {
                        "system_segments": [
                            {"content": "Hello {name}, you are {role}", "cache": True},
                            {"content": "Current task: {task}", "cache": False},
                        ],
                        "user": "Help me",
                    }

                    messages, _, _ = prepare_messages(
                        "test_variables",
                        variables={
                            "name": "Alice",
                            "role": "assistant",
                            "task": "coding",
                        },
                    )

                    system_msg = messages[0]
                    # Variables should be substituted in all segments
                    assert "Hello Alice" in system_msg.content
                    assert "you are assistant" in system_msg.content
                    assert "Current task: coding" in system_msg.content

    @pytest.mark.req("REQ-YG-293")
    def test_system_segments_jinja2_support(self) -> None:
        """System segments should support Jinja2 templates like scalar system."""
        from yamlgraph.executor_base import prepare_messages

        with patch("yamlgraph.utils.prompts.resolve_prompt_path") as mock_resolve:
            mock_resolve.return_value = Path("test.yaml")
            with patch("builtins.open", mock_open(read_data="")):
                with patch("yamlgraph.utils.prompts.yaml.safe_load") as mock_load:
                    mock_load.return_value = {
                        "system_segments": [
                            {
                                "content": "{% for item in items %}{{ item }}\n{% endfor %}",
                                "cache": True,
                            }
                        ],
                        "user": "Process these",
                    }

                    messages, _, _ = prepare_messages(
                        "test_jinja", variables={"items": ["first", "second", "third"]}
                    )

                    system_msg = messages[0]
                    # Jinja2 should be processed
                    assert "first" in system_msg.content
                    assert "second" in system_msg.content
                    assert "third" in system_msg.content
