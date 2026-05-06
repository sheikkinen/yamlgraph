"""Tests for FR-223: Refactored LLM node phases.

Tests each extracted phase independently:
- LLMNodeConfig frozen dataclass
- resolve_llm_node_config() pure function
- _apply_verification() verification gate
- _handle_error() error dispatch
- _resolve_route() router routing
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.conftest import FixtureGeneratedContent
from yamlgraph.constants import ErrorHandler, NodeType

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_state():
    """Sample pipeline state."""
    return {
        "thread_id": "test-123",
        "topic": "machine learning",
        "style": "informative",
        "word_count": 300,
        "generated": None,
        "analysis": None,
        "current_step": "init",
        "error": None,
        "errors": [],
    }


@pytest.fixture
def minimal_node_config():
    """Minimal node config dict."""
    return {
        "type": "llm",
        "prompt": "generate",
        "state_key": "generated",
        "variables": {"topic": "{state.topic}"},
    }


@pytest.fixture
def router_node_config():
    """Router node config dict."""
    return {
        "type": "router",
        "prompt": "route",
        "state_key": "route_result",
        "route_field": "decision",
        "routes": {"positive": "happy_path", "negative": "sad_path"},
        "default_route": "happy_path",
    }


@pytest.fixture
def verification_node_config():
    """Node config with verification gate."""
    return {
        "type": "llm",
        "prompt": "generate",
        "state_key": "generated",
        "variables": {},
        "verification": {
            "question": "Will return non-empty",
            "on_fail": "warn",
            "max_retries": 2,
        },
    }


# =============================================================================
# TestLLMNodeConfig
# =============================================================================


class TestLLMNodeConfig:
    """Tests for LLMNodeConfig frozen dataclass."""

    @pytest.mark.req("REQ-YG-223")
    def test_config_is_frozen(self, minimal_node_config):
        """LLMNodeConfig instances are immutable."""
        from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

        cfg = resolve_llm_node_config("test_node", minimal_node_config, {}, None)
        with pytest.raises(AttributeError):
            cfg.prompt_name = "changed"  # type: ignore[misc]

    @pytest.mark.req("REQ-YG-223")
    def test_config_has_all_fields(self, minimal_node_config):
        """LLMNodeConfig exposes all resolved config fields."""
        from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

        cfg = resolve_llm_node_config("test_node", minimal_node_config, {}, None)
        assert cfg.prompt_name == "generate"
        assert cfg.state_key == "generated"
        assert cfg.temperature == 0.7  # default
        assert cfg.parse_json is False
        assert cfg.variable_templates == {"topic": "{state.topic}"}
        assert cfg.requires == []
        assert cfg.on_error is None
        assert cfg.max_retries == 3
        assert cfg.skip_if_exists is True
        assert cfg.verification_question is None

    @pytest.mark.req("REQ-YG-223")
    def test_config_node_defaults(self):
        """Node-level config overrides graph defaults."""
        from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

        node_config = {
            "type": "llm",
            "prompt": "p",
            "temperature": 0.9,
            "provider": "openai",
            "model": "gpt-4",
        }
        defaults = {"temperature": 0.5, "provider": "anthropic", "model": "claude-3"}

        cfg = resolve_llm_node_config("test", node_config, defaults, None)
        assert cfg.temperature == 0.9
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4"

    @pytest.mark.req("REQ-YG-223")
    def test_config_falls_back_to_defaults(self):
        """Config uses defaults when node-level not set."""
        from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

        node_config = {"type": "llm", "prompt": "p"}
        defaults = {"temperature": 0.5, "provider": "anthropic"}

        cfg = resolve_llm_node_config("test", node_config, defaults, None)
        assert cfg.temperature == 0.5
        assert cfg.provider == "anthropic"

    @pytest.mark.req("REQ-YG-223")
    def test_config_state_key_defaults_to_node_name(self):
        """state_key defaults to the node name if not specified."""
        from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

        node_config = {"type": "llm", "prompt": "p"}
        cfg = resolve_llm_node_config("my_node", node_config, {}, None)
        assert cfg.state_key == "my_node"

    @pytest.mark.req("REQ-YG-223")
    def test_config_verification_dict(self, verification_node_config):
        """Verification config parsed from dict."""
        from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

        cfg = resolve_llm_node_config("v_node", verification_node_config, {}, None)
        assert cfg.verification_question == "Will return non-empty"
        assert cfg.verification_on_fail == "warn"
        assert cfg.verification_max_retries == 2

    @pytest.mark.req("REQ-YG-223")
    def test_config_prompts_dir_as_path(self):
        """prompts_dir string is converted to Path."""
        from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

        node_config = {"type": "llm", "prompt": "p"}
        defaults = {"prompts_dir": "/some/dir"}
        cfg = resolve_llm_node_config("test", node_config, defaults, None)
        assert cfg.prompts_dir == Path("/some/dir")


# =============================================================================
# TestResolveRoute
# =============================================================================


class TestResolveRoute:
    """Tests for _resolve_route extracted function."""

    @pytest.mark.req("REQ-YG-223")
    def test_route_from_dict_result(self):
        """Route resolved from dict result using route_field."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _resolve_route,
        )

        cfg = LLMNodeConfig(
            prompt_name="route",
            state_key="route_result",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=None,
            max_retries=3,
            fallback_provider=None,
            routes={"positive": "happy_path", "negative": "sad_path"},
            default_route="happy_path",
            route_field="decision",
            loop_limit=None,
            skip_if_exists=True,
            verification_question=None,
            verification_on_fail=None,
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.ROUTER,
        )

        route, store_value = _resolve_route(cfg, {"decision": "positive"})
        assert route == "happy_path"
        assert store_value == "positive"

    @pytest.mark.req("REQ-YG-223")
    def test_route_from_object_result(self):
        """Route resolved from object result using getattr."""
        from pydantic import BaseModel

        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _resolve_route,
        )

        class RouterOutput(BaseModel):
            decision: str

        cfg = LLMNodeConfig(
            prompt_name="route",
            state_key="route_result",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=None,
            max_retries=3,
            fallback_provider=None,
            routes={"positive": "happy_path", "negative": "sad_path"},
            default_route="happy_path",
            route_field="decision",
            loop_limit=None,
            skip_if_exists=True,
            verification_question=None,
            verification_on_fail=None,
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.ROUTER,
        )

        result = RouterOutput(decision="negative")
        route, store_value = _resolve_route(cfg, result)
        assert route == "sad_path"
        assert store_value == "negative"

    @pytest.mark.req("REQ-YG-223")
    def test_route_falls_back_to_default(self):
        """Unknown route key falls back to default_route."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _resolve_route,
        )

        cfg = LLMNodeConfig(
            prompt_name="route",
            state_key="route_result",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=None,
            max_retries=3,
            fallback_provider=None,
            routes={"positive": "happy_path"},
            default_route="fallback_path",
            route_field="decision",
            loop_limit=None,
            skip_if_exists=True,
            verification_question=None,
            verification_on_fail=None,
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.ROUTER,
        )

        route, _ = _resolve_route(cfg, {"decision": "unknown"})
        assert route == "fallback_path"

    @pytest.mark.req("REQ-YG-223")
    def test_route_returns_none_for_non_router(self):
        """Non-router nodes return (None, None)."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _resolve_route,
        )

        cfg = LLMNodeConfig(
            prompt_name="gen",
            state_key="out",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=None,
            max_retries=3,
            fallback_provider=None,
            routes={},
            default_route=None,
            route_field=None,
            loop_limit=None,
            skip_if_exists=True,
            verification_question=None,
            verification_on_fail=None,
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.LLM,
        )

        route, store_value = _resolve_route(cfg, "some result")
        assert route is None
        assert store_value is None


# =============================================================================
# TestHandleError
# =============================================================================


class TestHandleError:
    """Tests for _handle_error extracted function."""

    @pytest.mark.req("REQ-YG-223")
    def test_handle_error_skip(self):
        """on_error=skip returns state with None and error recorded."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _handle_error,
        )

        cfg = LLMNodeConfig(
            prompt_name="gen",
            state_key="output",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=ErrorHandler.SKIP,
            max_retries=3,
            fallback_provider=None,
            routes={},
            default_route=None,
            route_field=None,
            loop_limit=None,
            skip_if_exists=True,
            verification_question=None,
            verification_on_fail=None,
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.LLM,
        )

        error = ValueError("API Error")
        loop_counts = {"gen": 1}
        result = _handle_error(
            cfg, "gen", error, {}, loop_counts, lambda p: (None, error)
        )
        assert result["output"] is None
        assert result["_skipped"] is True
        assert result["errors"]

    @pytest.mark.req("REQ-YG-223")
    def test_handle_error_fail_raises(self):
        """on_error=fail raises the original error."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _handle_error,
        )

        cfg = LLMNodeConfig(
            prompt_name="gen",
            state_key="output",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=ErrorHandler.FAIL,
            max_retries=3,
            fallback_provider=None,
            routes={},
            default_route=None,
            route_field=None,
            loop_limit=None,
            skip_if_exists=True,
            verification_question=None,
            verification_on_fail=None,
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.LLM,
        )

        error = ValueError("Fatal")
        with pytest.raises(ValueError, match="Fatal"):
            _handle_error(cfg, "gen", error, {}, {}, lambda p: (None, error))

    @pytest.mark.req("REQ-YG-223")
    def test_handle_error_default(self):
        """Default error handling returns error in state."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _handle_error,
        )

        cfg = LLMNodeConfig(
            prompt_name="gen",
            state_key="output",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=None,
            max_retries=3,
            fallback_provider=None,
            routes={},
            default_route=None,
            route_field=None,
            loop_limit=None,
            skip_if_exists=True,
            verification_question=None,
            verification_on_fail=None,
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.LLM,
        )

        error = ValueError("Something broke")
        result = _handle_error(cfg, "gen", error, {}, {}, lambda p: (None, error))
        assert result.get("errors")


# =============================================================================
# TestApplyVerification
# =============================================================================


class TestApplyVerification:
    """Tests for _apply_verification extracted function."""

    @pytest.mark.req("REQ-YG-223")
    def test_no_verification_passes_through(self):
        """No verification question → result unchanged, no violation."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _apply_verification,
        )

        cfg = LLMNodeConfig(
            prompt_name="gen",
            state_key="output",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=None,
            max_retries=3,
            fallback_provider=None,
            routes={},
            default_route=None,
            route_field=None,
            loop_limit=None,
            skip_if_exists=True,
            verification_question=None,
            verification_on_fail=None,
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.LLM,
        )

        result, violation = _apply_verification(
            cfg, "gen", "some result", {}, lambda p: ("some result", None)
        )
        assert result == "some result"
        assert violation is None

    @pytest.mark.req("REQ-YG-223")
    def test_verification_passes(self):
        """Verification passes → result unchanged, no violation."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _apply_verification,
        )

        cfg = LLMNodeConfig(
            prompt_name="gen",
            state_key="output",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=None,
            max_retries=3,
            fallback_provider=None,
            routes={},
            default_route=None,
            route_field=None,
            loop_limit=None,
            skip_if_exists=True,
            verification_question="Will return non-empty",
            verification_on_fail="warn",
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.LLM,
        )

        result, violation = _apply_verification(
            cfg, "gen", "truthy result", {}, lambda p: ("truthy result", None)
        )
        assert result == "truthy result"
        assert violation is None

    @pytest.mark.req("REQ-YG-223")
    def test_verification_halt_raises(self):
        """on_fail=halt raises VerificationError."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _apply_verification,
        )
        from yamlgraph.verification import VerificationError

        cfg = LLMNodeConfig(
            prompt_name="gen",
            state_key="output",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=None,
            max_retries=3,
            fallback_provider=None,
            routes={},
            default_route=None,
            route_field=None,
            loop_limit=None,
            skip_if_exists=True,
            verification_question="Will return non-empty",
            verification_on_fail="halt",
            verification_max_retries=1,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.LLM,
        )

        with pytest.raises(VerificationError):
            _apply_verification(cfg, "gen", "", {}, lambda p: ("", None))

    @pytest.mark.req("REQ-YG-223")
    def test_verification_retry_succeeds(self):
        """on_fail=retry retries and succeeds on good result."""
        from yamlgraph.node_factory.llm_nodes import (
            LLMNodeConfig,
            _apply_verification,
        )

        cfg = LLMNodeConfig(
            prompt_name="gen",
            state_key="output",
            provider=None,
            model=None,
            temperature=0.7,
            max_tokens=None,
            thinking_budget=None,
            output_model=None,
            parse_json=False,
            variable_templates={},
            requires=[],
            on_error=None,
            max_retries=3,
            fallback_provider=None,
            routes={},
            default_route=None,
            route_field=None,
            loop_limit=None,
            skip_if_exists=True,
            verification_question="Will return non-empty",
            verification_on_fail="retry",
            verification_max_retries=2,
            prompts_dir=None,
            prompts_relative=False,
            node_type=NodeType.LLM,
        )

        # First attempt returns empty (fails), retry returns truthy (passes)
        call_count = 0

        def mock_execute(provider):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "good result", None
            return "good result", None

        result, violation = _apply_verification(cfg, "gen", "", {}, mock_execute)
        assert result == "good result"
        assert violation is None


# =============================================================================
# TestRefactoredCreateNodeFunction
# =============================================================================


class TestRefactoredCreateNodeFunction:
    """Verify the refactored create_node_function preserves all behavior."""

    @pytest.mark.req("REQ-YG-223")
    def test_refactored_node_calls_execute_prompt(self, sample_state):
        """Refactored node still calls execute_prompt with correct args."""
        node_config = {
            "type": "llm",
            "prompt": "generate",
            "output_model": "yamlgraph.models.GenericReport",
            "temperature": 0.8,
            "variables": {"topic": "{state.topic}"},
            "state_key": "generated",
        }

        mock_result = FixtureGeneratedContent(
            title="Test", content="Content", word_count=100, tags=[]
        )

        with patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt",
            return_value=mock_result,
        ) as mock:
            from yamlgraph.node_factory.llm_nodes import create_node_function

            node_fn = create_node_function(
                "generate", node_config, {"provider": "mistral"}
            )
            result = node_fn(sample_state)

            mock.assert_called_once()
            assert mock.call_args[1]["temperature"] == 0.8
            assert result["generated"] == mock_result

    @pytest.mark.req("REQ-YG-223")
    def test_resolve_config_is_pure(self, minimal_node_config):
        """resolve_llm_node_config has no side effects."""
        from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

        defaults = {"provider": "anthropic"}
        defaults_copy = dict(defaults)
        config_copy = dict(minimal_node_config)

        resolve_llm_node_config("test", minimal_node_config, defaults, None)

        # Inputs unchanged
        assert defaults == defaults_copy
        assert minimal_node_config == config_copy


@pytest.mark.req("REQ-YG-154")
def test_pre_guard_halt_prevents_execute_prompt():
    """Pre-guard halt fails fast and does not invoke execute_prompt."""
    from yamlgraph.models.schemas import ErrorType
    from yamlgraph.node_factory.llm_nodes import create_node_function

    node_fn = create_node_function(
        "guarded",
        {
            "type": "llm",
            "prompt": "generate",
            "state_key": "generated",
            "guards": {
                "pre": [{"check": "state.ready == True", "on_fail": "halt"}],
            },
        },
        {},
    )
    with patch("yamlgraph.node_factory.llm_nodes.execute_prompt") as mock_execute:
        result = node_fn({"ready": False})

    mock_execute.assert_not_called()
    assert result["current_step"] == "guarded"
    assert result["errors"][0].type == ErrorType.GUARD_ERROR


@pytest.mark.req("REQ-YG-154")
def test_post_guard_retry_reexecutes_until_pass_or_exhausted():
    """Post-guard retry re-executes and returns violation when retries are exhausted."""
    from yamlgraph.models.schemas import ErrorType
    from yamlgraph.node_factory.llm_nodes import create_node_function

    node_config = {
        "type": "llm",
        "prompt": "generate",
        "state_key": "generated",
        "skip_if_exists": False,
        "guards": {
            "post": [
                {"check": "output == 'good'", "on_fail": "retry", "max_retries": 1}
            ]
        },
    }

    with patch(
        "yamlgraph.node_factory.llm_nodes.execute_prompt",
        side_effect=["bad", "good"],
    ) as mock_execute:
        node_fn = create_node_function("guarded", node_config, {})
        success = node_fn({})
    assert mock_execute.call_count == 2
    assert success["generated"] == "good"
    assert "errors" not in success

    with patch(
        "yamlgraph.node_factory.llm_nodes.execute_prompt",
        side_effect=["bad", "still_bad"],
    ) as mock_execute:
        node_fn = create_node_function("guarded", node_config, {})
        exhausted = node_fn({})
    assert mock_execute.call_count == 2
    assert exhausted["generated"] == "still_bad"
    assert exhausted["errors"][0].type == ErrorType.GUARD_ERROR


@pytest.mark.req("REQ-YG-154")
def test_pre_guard_skip_returns_explicit_skipped_metadata():
    """Pre-guard skip returns explicit skip markers and no external call."""
    from yamlgraph.node_factory.llm_nodes import create_node_function

    node_fn = create_node_function(
        "guarded",
        {
            "type": "llm",
            "prompt": "generate",
            "state_key": "generated",
            "guards": {
                "pre": [{"check": "state.ready == True", "on_fail": "skip"}],
            },
        },
        {},
    )
    with patch("yamlgraph.node_factory.llm_nodes.execute_prompt") as mock_execute:
        result = node_fn({"ready": False})
    mock_execute.assert_not_called()
    assert result["_skipped"] is True
    assert result["_skip_reason"] == "guard"
    assert result["generated"] is None
