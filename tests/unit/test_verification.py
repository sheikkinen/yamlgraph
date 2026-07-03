"""Tests for FR-164/FR-166: Verification Gate Pattern.

Tests cover:
- VerificationConfig schema (question, on_fail, max_retries)
- Deterministic evaluator patterns (count_range, non_empty, contains, annotation)
- Variable interpolation in verification questions
- Runtime behavior (warn, halt, retry)
- Lint rule W022 (on_error: skip without verification)
- FR-166: CountRangeClaim Pydantic model (validation, inverted range, structured details)
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from yamlgraph.linter.checks_contracts import check_skip_without_verification
from yamlgraph.models.graph_schema import NodeConfig
from yamlgraph.models.guard_schema import VerificationConfig
from yamlgraph.models.schemas import ErrorType, VerificationViolation
from yamlgraph.verification import evaluate_verification


def _create_temp_graph(graph_dict: dict) -> Path:
    """Create a temp YAML file from dict."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(graph_dict, f)
        return Path(f.name)


# =============================================================================
# Schema Tests: VerificationConfig and NodeConfig.verification
# =============================================================================


class TestVerificationConfigSchema:
    """VerificationConfig Pydantic model validation."""

    @pytest.mark.req("REQ-YG-154")
    def test_verification_field_optional_on_node(self):
        """NodeConfig accepts verification: None (default)."""
        node = NodeConfig(prompt="test")
        assert node.verification is None

    @pytest.mark.req("REQ-YG-154")
    def test_verification_field_accepts_config(self):
        """NodeConfig accepts a VerificationConfig object."""
        node = NodeConfig(
            prompt="test",
            verification=VerificationConfig(question="Will return non-empty"),
        )
        assert node.verification is not None
        assert node.verification.question == "Will return non-empty"

    @pytest.mark.req("REQ-YG-154")
    def test_verification_on_fail_default_warn(self):
        """on_fail defaults to 'warn'."""
        config = VerificationConfig(question="Will return non-empty")
        assert config.on_fail == "warn"

    @pytest.mark.req("REQ-YG-154")
    def test_verification_on_fail_valid_values(self):
        """on_fail accepts warn, halt, retry."""
        for value in ("warn", "halt", "retry"):
            config = VerificationConfig(question="test", on_fail=value)
            assert config.on_fail == value

    @pytest.mark.req("REQ-YG-154")
    def test_verification_on_fail_invalid_raises(self):
        """on_fail rejects invalid values."""
        with pytest.raises(ValueError, match="on_fail"):
            VerificationConfig(question="test", on_fail="ignore")

    @pytest.mark.req("REQ-YG-154")
    def test_verification_max_retries_default(self):
        """max_retries defaults to 1."""
        config = VerificationConfig(question="test")
        assert config.max_retries == 1

    @pytest.mark.req("REQ-YG-154")
    def test_verification_max_retries_custom(self):
        """max_retries accepts custom positive value."""
        config = VerificationConfig(question="test", max_retries=3)
        assert config.max_retries == 3

    @pytest.mark.req("REQ-YG-154")
    def test_verification_max_retries_zero_invalid(self):
        """max_retries must be >= 1."""
        with pytest.raises(ValueError):
            VerificationConfig(question="test", max_retries=0)

    @pytest.mark.req("REQ-YG-154")
    def test_verification_question_required(self):
        """question field is required."""
        with pytest.raises(ValueError):
            VerificationConfig()

    @pytest.mark.req("REQ-YG-154")
    def test_verification_from_dict(self):
        """NodeConfig parses verification from raw dict (YAML input)."""
        node = NodeConfig(
            prompt="test",
            verification={"question": "Will return 3-10 items", "on_fail": "halt"},
        )
        assert isinstance(node.verification, VerificationConfig)
        assert node.verification.on_fail == "halt"


# =============================================================================
# Evaluator Tests: Deterministic pattern matching
# =============================================================================


class TestVerificationEvaluator:
    """Deterministic verification evaluator patterns."""

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_pass(self):
        """'Will return 3-10 items' passes with list of 5."""
        result = evaluate_verification(
            question="Will return 3-10 items",
            actual=["a", "b", "c", "d", "e"],
            state={},
        )
        assert result is None  # No violation

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_fail_too_few(self):
        """'Will return 3-10 items' fails with list of 1."""
        result = evaluate_verification(
            question="Will return 3-10 items",
            actual=["a"],
            state={},
        )
        assert result is not None
        assert result.check_type == "count_range"

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_fail_too_many(self):
        """'Will return 3-10 items' fails with list of 15."""
        result = evaluate_verification(
            question="Will return 3-10 items",
            actual=list(range(15)),
            state={},
        )
        assert result is not None
        assert result.check_type == "count_range"

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_documents_variant(self):
        """'Will return 3-10 documents' pattern also works."""
        result = evaluate_verification(
            question="Will return 3-10 documents about AI",
            actual=["doc1", "doc2", "doc3"],
            state={},
        )
        assert result is None

    @pytest.mark.req("REQ-YG-154")
    def test_non_empty_pass(self):
        """'Will return non-empty' passes with truthy result."""
        result = evaluate_verification(
            question="Will return non-empty",
            actual=["something"],
            state={},
        )
        assert result is None

    @pytest.mark.req("REQ-YG-154")
    def test_non_empty_fail(self):
        """'Will return non-empty' fails with empty list."""
        result = evaluate_verification(
            question="Will return non-empty",
            actual=[],
            state={},
        )
        assert result is not None
        assert result.check_type == "non_empty"

    @pytest.mark.req("REQ-YG-154")
    def test_non_empty_fail_none(self):
        """'Will return non-empty' fails with None."""
        result = evaluate_verification(
            question="Will return non-empty",
            actual=None,
            state={},
        )
        assert result is not None
        assert result.check_type == "non_empty"

    @pytest.mark.req("REQ-YG-154")
    def test_contains_keyword_pass(self):
        """'Will contain Python' passes when keyword present."""
        result = evaluate_verification(
            question="Will contain Python",
            actual="A guide to Python programming",
            state={},
        )
        assert result is None

    @pytest.mark.req("REQ-YG-154")
    def test_contains_keyword_fail(self):
        """'Will contain Python' fails when keyword absent."""
        result = evaluate_verification(
            question="Will contain Python",
            actual="A guide to JavaScript programming",
            state={},
        )
        assert result is not None
        assert result.check_type == "contains"

    @pytest.mark.req("REQ-YG-154")
    def test_contains_with_state_variable(self):
        """'Will contain {topic}' interpolates from state."""
        result = evaluate_verification(
            question="Will contain {topic}",
            actual="An article about machine learning and AI",
            state={"topic": "machine learning"},
        )
        assert result is None

    @pytest.mark.req("REQ-YG-154")
    def test_annotation_no_pattern_match(self):
        """Unrecognized pattern degrades to annotation (no failure)."""
        result = evaluate_verification(
            question="This is a custom freeform expectation",
            actual="anything",
            state={},
        )
        assert result is None  # Annotation = no failure

    @pytest.mark.req("REQ-YG-154")
    def test_annotation_logs_info(self):
        """Unrecognized pattern logs at INFO level."""
        with patch("yamlgraph.verification.logger") as mock_logger:
            evaluate_verification(
                question="This is a custom freeform expectation",
                actual="anything",
                state={},
            )
        mock_logger.info.assert_called_once()
        assert "annotation" in mock_logger.info.call_args[0][0].lower()

    @pytest.mark.req("REQ-YG-154")
    def test_variable_interpolation_in_count_range(self):
        """Variable interpolation works in count range questions."""
        result = evaluate_verification(
            question="Will return 3-10 documents about {topic}",
            actual=["a", "b", "c", "d"],
            state={"topic": "AI"},
        )
        assert result is None


# =============================================================================
# VerificationViolation model tests
# =============================================================================


class TestVerificationViolation:
    """VerificationViolation error model."""

    @pytest.mark.req("REQ-YG-154")
    def test_violation_is_pipeline_error(self):
        """VerificationViolation inherits from PipelineError."""
        from yamlgraph.models.schemas import PipelineError

        violation = VerificationViolation(
            type=ErrorType.VERIFICATION_ERROR,
            message="Verification failed",
            node="search",
            prediction="Will return non-empty",
            actual="[]",
            check_type="non_empty",
        )
        assert isinstance(violation, PipelineError)

    @pytest.mark.req("REQ-YG-154")
    def test_violation_has_required_fields(self):
        """VerificationViolation has prediction, actual, check_type fields."""
        violation = VerificationViolation(
            type=ErrorType.VERIFICATION_ERROR,
            message="Verification failed",
            node="search",
            prediction="Will return 3-10 items",
            actual="[1]",
            check_type="count_range",
        )
        assert violation.prediction == "Will return 3-10 items"
        assert violation.actual == "[1]"
        assert violation.check_type == "count_range"

    @pytest.mark.req("REQ-YG-154")
    def test_verification_error_type_exists(self):
        """VERIFICATION_ERROR is a valid ErrorType."""
        assert ErrorType.VERIFICATION_ERROR == "verification_error"


# =============================================================================
# Runtime: Node-level verification behavior
# =============================================================================


class TestVerificationRuntime:
    """Runtime verification behavior in LLM nodes."""

    @pytest.mark.req("REQ-YG-154")
    def test_warn_appends_violation_to_errors(self):
        """on_fail: warn appends VerificationViolation to state errors."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        node_config = {
            "type": "llm",
            "prompt": "test_prompt",
            "state_key": "docs",
            "verification": {
                "question": "Will return non-empty",
                "on_fail": "warn",
            },
        }
        node_fn = create_node_function("search", node_config, defaults={})

        with patch("yamlgraph.node_factory.llm_nodes.execute_prompt", return_value=[]):
            result = node_fn({"current_step": None, "_loop_counts": {}})

        # Result should still contain the state_key (execution succeeded)
        assert "docs" in result
        # But errors should contain a VerificationViolation
        assert "errors" in result
        violations = [
            e for e in result["errors"] if isinstance(e, VerificationViolation)
        ]
        assert len(violations) == 1
        assert violations[0].check_type == "non_empty"

    @pytest.mark.req("REQ-YG-154")
    def test_halt_raises_verification_error(self):
        """on_fail: halt raises VerificationError."""
        from yamlgraph.node_factory.llm_nodes import create_node_function
        from yamlgraph.verification import VerificationError

        node_config = {
            "type": "llm",
            "prompt": "test_prompt",
            "state_key": "docs",
            "verification": {
                "question": "Will return non-empty",
                "on_fail": "halt",
            },
        }
        node_fn = create_node_function("search", node_config, defaults={})

        with (
            patch("yamlgraph.node_factory.llm_nodes.execute_prompt", return_value=[]),
            pytest.raises(VerificationError, match="search"),
        ):
            node_fn({"current_step": None, "_loop_counts": {}})

    @pytest.mark.req("REQ-YG-154")
    def test_retry_reexecutes_then_warns(self):
        """on_fail: retry re-executes node, then falls to warn."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        node_config = {
            "type": "llm",
            "prompt": "test_prompt",
            "state_key": "docs",
            "verification": {
                "question": "Will return non-empty",
                "on_fail": "retry",
                "max_retries": 1,
            },
        }
        node_fn = create_node_function("search", node_config, defaults={})

        # Both attempts return empty — verification fails both times
        with patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt", return_value=[]
        ) as mock_exec:
            result = node_fn({"current_step": None, "_loop_counts": {}})

        # Should have been called twice: initial + 1 retry
        assert mock_exec.call_count == 2
        # Falls through to warn after retries exhausted
        assert "errors" in result
        violations = [
            e for e in result["errors"] if isinstance(e, VerificationViolation)
        ]
        assert len(violations) == 1

    @pytest.mark.req("REQ-YG-154")
    def test_retry_succeeds_on_second_attempt(self):
        """on_fail: retry succeeds when second attempt passes verification."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        node_config = {
            "type": "llm",
            "prompt": "test_prompt",
            "state_key": "docs",
            "verification": {
                "question": "Will return non-empty",
                "on_fail": "retry",
                "max_retries": 1,
            },
        }
        node_fn = create_node_function("search", node_config, defaults={})

        # First attempt empty, second attempt has data
        with patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt",
            side_effect=[[], ["doc1", "doc2"]],
        ):
            result = node_fn({"current_step": None, "_loop_counts": {}})

        assert result["docs"] == ["doc1", "doc2"]
        assert "errors" not in result or not any(
            isinstance(e, VerificationViolation) for e in result.get("errors", [])
        )

    @pytest.mark.req("REQ-YG-154")
    def test_no_verification_passes_through(self):
        """Node without verification works normally."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        node_config = {
            "type": "llm",
            "prompt": "test_prompt",
            "state_key": "output",
        }
        node_fn = create_node_function("gen", node_config, defaults={})

        with patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt", return_value="hello"
        ):
            result = node_fn({"current_step": None, "_loop_counts": {}})

        assert result["output"] == "hello"
        assert "errors" not in result


# =============================================================================
# FR-166: CountRangeClaim Pydantic model
# =============================================================================


class TestCountRangeClaim:
    """FR-166: CountRangeClaim Pydantic model validation."""

    @pytest.mark.req("REQ-YG-155")
    def test_valid_range_creates_claim(self):
        """CountRangeClaim(min_count=3, max_count=10) succeeds."""
        from yamlgraph.verification import CountRangeClaim

        claim = CountRangeClaim(min_count=3, max_count=10)
        assert claim.min_count == 3
        assert claim.max_count == 10

    @pytest.mark.req("REQ-YG-155")
    def test_equal_range_valid(self):
        """CountRangeClaim(min_count=5, max_count=5) is valid (exact count)."""
        from yamlgraph.verification import CountRangeClaim

        claim = CountRangeClaim(min_count=5, max_count=5)
        assert claim.min_count == 5

    @pytest.mark.req("REQ-YG-155")
    def test_inverted_range_raises(self):
        """CountRangeClaim(min_count=10, max_count=3) raises ValueError."""
        from yamlgraph.verification import CountRangeClaim

        with pytest.raises(ValueError, match="Inverted count range"):
            CountRangeClaim(min_count=10, max_count=3)

    @pytest.mark.req("REQ-YG-155")
    def test_negative_min_rejected(self):
        """min_count must be >= 0."""
        from yamlgraph.verification import CountRangeClaim

        with pytest.raises(ValueError):
            CountRangeClaim(min_count=-1, max_count=5)

    @pytest.mark.req("REQ-YG-155")
    def test_zero_range_valid(self):
        """CountRangeClaim(min_count=0, max_count=0) is valid."""
        from yamlgraph.verification import CountRangeClaim

        claim = CountRangeClaim(min_count=0, max_count=0)
        assert claim.min_count == 0
        assert claim.max_count == 0

    @pytest.mark.req("REQ-YG-155")
    def test_inverted_range_in_question_raises(self):
        """'Will return 10-3 items' raises ValueError from CountRangeClaim."""
        with pytest.raises(ValueError, match="Inverted count range"):
            evaluate_verification(
                question="Will return 10-3 items",
                actual=["a", "b"],
                state={},
            )

    @pytest.mark.req("REQ-YG-155")
    def test_count_range_violation_has_structured_details(self):
        """Count range violation exposes expected_min, expected_max, actual_count."""
        result = evaluate_verification(
            question="Will return 3-10 items",
            actual=["a"],
            state={},
        )
        assert result is not None
        assert result.details["expected_min"] == 3
        assert result.details["expected_max"] == 10
        assert result.details["actual_count"] == 1

    @pytest.mark.req("REQ-YG-155")
    def test_count_range_pass_no_violation(self):
        """Passing count range still returns None (no regression)."""
        result = evaluate_verification(
            question="Will return 3-10 items",
            actual=["a", "b", "c", "d", "e"],
            state={},
        )
        assert result is None

    @pytest.mark.req("REQ-YG-155")
    def test_count_range_claim_exported(self):
        """CountRangeClaim is importable from yamlgraph.models."""
        from yamlgraph.models import CountRangeClaim

        assert CountRangeClaim is not None


# =============================================================================
# FR-166: count_range extraction from Pydantic models
# =============================================================================


class TestCountRangePydanticExtraction:
    """FR-166: count_range should extract countable from Pydantic models.

    Pydantic BaseModel does not implement __len__. When count_range checks
    a Pydantic model with a single list field, it should extract that list
    and count its items rather than reporting 0.
    """

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_pydantic_single_list_field_pass(self):
        """count_range passes when Pydantic model's single list field is in range."""
        from pydantic import BaseModel

        class KeyPoints(BaseModel):
            points: list[str]

        model = KeyPoints(points=["a", "b", "c", "d"])  # 4 items

        result = evaluate_verification(
            question="Will return 3-5 items",
            actual=model,
            state={},
        )

        # Should pass: 4 items is within 3-5 range
        assert result is None, f"Expected pass, got violation: {result}"

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_pydantic_single_list_field_fail_too_few(self):
        """count_range fails when Pydantic model's single list field has too few items."""
        from pydantic import BaseModel

        class KeyPoints(BaseModel):
            points: list[str]

        model = KeyPoints(points=["a"])  # 1 item

        result = evaluate_verification(
            question="Will return 3-5 items",
            actual=model,
            state={},
        )

        # Should fail: 1 item is below 3
        assert result is not None
        assert result.check_type == "count_range"
        assert result.details["actual_count"] == 1

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_pydantic_single_list_field_fail_too_many(self):
        """count_range fails when Pydantic model's single list field has too many items."""
        from pydantic import BaseModel

        class KeyPoints(BaseModel):
            points: list[str]

        model = KeyPoints(points=["a", "b", "c", "d", "e", "f", "g"])  # 7 items

        result = evaluate_verification(
            question="Will return 3-5 items",
            actual=model,
            state={},
        )

        # Should fail: 7 items exceeds 5
        assert result is not None
        assert result.check_type == "count_range"
        assert result.details["actual_count"] == 7

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_pydantic_multiple_list_fields_fallback(self):
        """count_range with multiple list fields falls back to len(model) = 0."""
        from pydantic import BaseModel

        class MultiList(BaseModel):
            items: list[str]
            tags: list[str]

        model = MultiList(items=["a", "b", "c"], tags=["x", "y"])

        result = evaluate_verification(
            question="Will return 3-5 items",
            actual=model,
            state={},
        )

        # Ambiguous: multiple list fields, falls through to len(model) = 0
        # This is expected to fail (0 is not in 3-5 range)
        assert result is not None
        assert result.check_type == "count_range"
        assert result.details["actual_count"] == 0

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_pydantic_no_list_field_fallback(self):
        """count_range with no list fields falls back to len(model) = 0."""
        from pydantic import BaseModel

        class NoList(BaseModel):
            name: str
            count: int

        model = NoList(name="test", count=42)

        result = evaluate_verification(
            question="Will return 3-5 items",
            actual=model,
            state={},
        )

        # No list field, falls through to len(model) = 0
        assert result is not None
        assert result.check_type == "count_range"
        assert result.details["actual_count"] == 0

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_plain_list_no_regression(self):
        """count_range with plain list still works (no regression)."""
        result = evaluate_verification(
            question="Will return 3-5 items",
            actual=["a", "b", "c", "d"],
            state={},
        )
        assert result is None  # 4 items in range

    @pytest.mark.req("REQ-YG-154")
    def test_count_range_plain_dict_no_regression(self):
        """count_range with plain dict still works (no regression)."""
        result = evaluate_verification(
            question="Will return 3-5 items",
            actual={"a": 1, "b": 2, "c": 3, "d": 4},
            state={},
        )
        assert result is None  # 4 keys in range


# =============================================================================
# Lint: W022 on_error: skip without verification
# =============================================================================


class TestW022SkipWithoutVerification:
    """W022: on_error: skip without verification question."""

    @pytest.mark.req("REQ-YG-154")
    def test_skip_without_verification_warns(self):
        """Node with on_error: skip but no verification should warn."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "search": {
                        "type": "llm",
                        "prompt": "search",
                        "on_error": "skip",
                    }
                }
            }
        )
        issues = check_skip_without_verification(graph)
        assert len(issues) == 1
        assert issues[0].code == "W022"
        assert "search" in issues[0].message
        assert issues[0].severity == "warning"

    @pytest.mark.req("REQ-YG-154")
    def test_skip_with_verification_no_warn(self):
        """Node with on_error: skip AND verification should not warn."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "search": {
                        "type": "llm",
                        "prompt": "search",
                        "on_error": "skip",
                        "verification": {
                            "question": "Will return non-empty",
                        },
                    }
                }
            }
        )
        issues = check_skip_without_verification(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-154")
    def test_fail_without_verification_no_warn(self):
        """Node with on_error: fail (not skip) should not warn."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "search": {
                        "type": "llm",
                        "prompt": "search",
                        "on_error": "fail",
                    }
                }
            }
        )
        issues = check_skip_without_verification(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-154")
    def test_no_on_error_no_warn(self):
        """Node without on_error should not warn."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "search": {
                        "type": "llm",
                        "prompt": "search",
                    }
                }
            }
        )
        issues = check_skip_without_verification(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-154")
    def test_multiple_nodes_mixed(self):
        """Only nodes with skip and no verification warn."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "search": {
                        "type": "llm",
                        "prompt": "search",
                        "on_error": "skip",
                    },
                    "verified_search": {
                        "type": "llm",
                        "prompt": "search",
                        "on_error": "skip",
                        "verification": {"question": "Will return non-empty"},
                    },
                    "generate": {
                        "type": "llm",
                        "prompt": "gen",
                        "on_error": "fail",
                    },
                }
            }
        )
        issues = check_skip_without_verification(graph)
        assert len(issues) == 1
        assert "search" in issues[0].message
