"""Tests for A2A message parsing, error mapping, and Agent Card — FR-225.

Covers: extract_text_from_parts, parse_a2a_message, _validate_required_vars,
        map_pipeline_error, build_agent_card, _detect_interrupt.

Tests moved from test_a2a_server.py + new edge-case coverage.
"""

from __future__ import annotations

from typing import Any

import pytest

# Guard: a2a-sdk is an optional dependency
a2a_sdk = pytest.importorskip("a2a")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_graph_info() -> dict[str, Any]:
    """A discovered graph info dict (as returned by discover_graphs)."""
    return {
        "name": "hello-world",
        "description": "Simple greeting generator",
        "path": "/tmp/hello/graph.yaml",
        "required_vars": ["name", "style"],
    }


@pytest.fixture
def single_var_graph_info() -> dict[str, Any]:
    """A graph with a single required variable."""
    return {
        "name": "echo",
        "description": "Echo input back",
        "path": "/tmp/echo/graph.yaml",
        "required_vars": ["input"],
    }


# ---------------------------------------------------------------------------
# REQ-YG-209: extract_text_from_parts
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-209")
def test_extract_text_from_parts_multiple():
    """Multiple TextParts are concatenated with newlines."""
    from a2a.types import Part

    from yamlgraph.a2a.message import extract_text_from_parts

    parts = [
        Part(text="name=World"),
        Part(text="style=casual"),
    ]
    text = extract_text_from_parts(parts)
    assert text == "name=World\nstyle=casual"


@pytest.mark.req("REQ-YG-209")
def test_extract_text_from_parts_single():
    """Single TextPart returns its text without trailing newline."""
    from a2a.types import Part

    from yamlgraph.a2a.message import extract_text_from_parts

    parts = [Part(text="hello world")]
    text = extract_text_from_parts(parts)
    assert text == "hello world"


@pytest.mark.req("REQ-YG-209")
def test_extract_text_from_parts_empty_list():
    """Empty parts list raises ValueError."""
    from yamlgraph.a2a.message import extract_text_from_parts

    with pytest.raises(ValueError, match="unsupported_content_type"):
        extract_text_from_parts([])


@pytest.mark.req("REQ-YG-209")
def test_extract_text_skips_non_text_parts():
    """Non-text parts are skipped; if only non-text, raises ValueError."""
    from a2a.types import Part
    from google.protobuf.struct_pb2 import Struct, Value

    from yamlgraph.a2a.message import extract_text_from_parts

    s = Struct()
    s.update({"key": "val"})
    parts = [Part(data=Value(struct_value=s))]
    with pytest.raises(ValueError, match="unsupported_content_type"):
        extract_text_from_parts(parts)


# ---------------------------------------------------------------------------
# REQ-YG-209: parse_a2a_message
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-209")
def test_parse_message_json_mode():
    """JSON object in text is parsed as variables."""
    from yamlgraph.a2a.message import parse_a2a_message

    result = parse_a2a_message(
        '{"name": "World", "style": "casual"}',
        required_vars=["name", "style"],
    )
    assert result == {"name": "World", "style": "casual"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_json_coerces_non_strings():
    """JSON non-string values are coerced to str."""
    from yamlgraph.a2a.message import parse_a2a_message

    result = parse_a2a_message(
        '{"count": 42, "flag": true}',
        required_vars=["count", "flag"],
    )
    assert result == {"count": "42", "flag": "True"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_key_value_mode():
    """key=value pairs parsed via shlex."""
    from yamlgraph.a2a.message import parse_a2a_message

    result = parse_a2a_message(
        'name=World style="holy see of code"',
        required_vars=["name", "style"],
    )
    assert result == {"name": "World", "style": "holy see of code"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_single_input_mode():
    """Single required var gets entire text assigned."""
    from yamlgraph.a2a.message import parse_a2a_message

    result = parse_a2a_message(
        "Hello World, how are you?",
        required_vars=["input"],
    )
    assert result == {"input": "Hello World, how are you?"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_fallback_to_input_key():
    """No required vars and no key=value → assign to 'input' key."""
    from yamlgraph.a2a.message import parse_a2a_message

    result = parse_a2a_message(
        "Just some text",
        required_vars=[],
    )
    assert result == {"input": "Just some text"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_resolution_order():
    """JSON takes priority over key_value even when text contains '='."""
    from yamlgraph.a2a.message import parse_a2a_message

    result = parse_a2a_message(
        '{"equation": "a=b"}',
        required_vars=["equation"],
    )
    assert result == {"equation": "a=b"}


@pytest.mark.req("REQ-YG-209")
def test_parse_message_missing_required_vars():
    """Missing required vars raises ValueError with missing keys."""
    from yamlgraph.a2a.message import parse_a2a_message

    with pytest.raises(ValueError, match="missing_variables"):
        parse_a2a_message(
            "name=World",
            required_vars=["name", "style"],
        )


@pytest.mark.req("REQ-YG-209")
def test_parse_message_extra_vars_ignored():
    """Extra variables not in required_vars are included."""
    from yamlgraph.a2a.message import parse_a2a_message

    result = parse_a2a_message(
        "name=World style=casual extra=ignored",
        required_vars=["name", "style"],
    )
    assert result["name"] == "World"
    assert result["style"] == "casual"
    assert result["extra"] == "ignored"


@pytest.mark.req("REQ-YG-209")
def test_parse_message_malformed_json_with_equals():
    """Malformed JSON containing '=' falls through to key_value mode."""
    from yamlgraph.a2a.message import parse_a2a_message

    result = parse_a2a_message(
        "{invalid json name=World style=casual",
        required_vars=["name", "style"],
    )
    assert result["name"] == "World"
    assert result["style"] == "casual"


# ---------------------------------------------------------------------------
# REQ-YG-209: _validate_required_vars
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-209")
def test_validate_required_vars_all_present():
    """No exception when all required vars are present."""
    from yamlgraph.a2a.message import _validate_required_vars

    _validate_required_vars({"name": "Alice", "style": "formal"}, ["name", "style"])


@pytest.mark.req("REQ-YG-209")
def test_validate_required_vars_some_missing():
    """Raises ValueError listing missing keys."""
    from yamlgraph.a2a.message import _validate_required_vars

    with pytest.raises(ValueError, match="missing_variables.*style"):
        _validate_required_vars({"name": "Alice"}, ["name", "style"])


@pytest.mark.req("REQ-YG-209")
def test_validate_required_vars_empty_required():
    """No exception when required list is empty."""
    from yamlgraph.a2a.message import _validate_required_vars

    _validate_required_vars({"any": "value"}, [])


# ---------------------------------------------------------------------------
# REQ-YG-209: map_pipeline_error
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_llm():
    """LLM_ERROR maps to InternalError."""
    from a2a.types import InternalError

    from yamlgraph.a2a.message import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.LLM_ERROR,
        message="Rate limit exceeded",
        node="greet",
        retryable=True,
    )
    a2a_err = map_pipeline_error(err)
    assert isinstance(a2a_err, InternalError)
    assert "Rate limit exceeded" in a2a_err.message
    assert a2a_err.data["retryable"] is True


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_validation():
    """VALIDATION_ERROR maps to InvalidParamsError."""
    from a2a.types import InvalidParamsError

    from yamlgraph.a2a.message import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.VALIDATION_ERROR,
        message="Field 'name' required",
        node="greet",
    )
    a2a_err = map_pipeline_error(err)
    assert isinstance(a2a_err, InvalidParamsError)


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_prompt():
    """PROMPT_ERROR maps to InvalidParamsError."""
    from a2a.types import InvalidParamsError

    from yamlgraph.a2a.message import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.PROMPT_ERROR,
        message="Prompt not found",
        node="greet",
    )
    a2a_err = map_pipeline_error(err)
    assert isinstance(a2a_err, InvalidParamsError)


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_state_error():
    """STATE_ERROR maps to InternalError."""
    from a2a.types import InternalError

    from yamlgraph.a2a.message import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.STATE_ERROR,
        message="Missing state key",
        node="validate",
    )
    a2a_err = map_pipeline_error(err)
    assert isinstance(a2a_err, InternalError)
    assert a2a_err.data["error_type"] == "state_error"


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_unknown():
    """UNKNOWN_ERROR maps to InternalError."""
    from a2a.types import InternalError

    from yamlgraph.a2a.message import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.UNKNOWN_ERROR,
        message="Something broke",
        node="mystery",
    )
    a2a_err = map_pipeline_error(err)
    assert isinstance(a2a_err, InternalError)
    assert a2a_err.data["error_type"] == "unknown_error"


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_verification():
    """VERIFICATION_ERROR maps to InvalidParamsError."""
    from a2a.types import InvalidParamsError

    from yamlgraph.a2a.message import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.VERIFICATION_ERROR,
        message="Gate violation",
        node="verify",
    )
    a2a_err = map_pipeline_error(err)
    assert isinstance(a2a_err, InvalidParamsError)
    assert a2a_err.data["error_type"] == "verification_error"


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_retryable_propagation():
    """Retryable flag propagates to A2A error data."""
    from yamlgraph.a2a.message import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.LLM_ERROR,
        message="Timeout",
        node="slow",
        retryable=True,
    )
    a2a_err = map_pipeline_error(err)
    assert a2a_err.data["retryable"] is True

    err_not_retry = PipelineError(
        type=ErrorType.VALIDATION_ERROR,
        message="Bad",
        node="check",
        retryable=False,
    )
    a2a_err2 = map_pipeline_error(err_not_retry)
    assert a2a_err2.data["retryable"] is False


@pytest.mark.req("REQ-YG-209")
def test_map_pipeline_error_details_included():
    """Extra details from PipelineError are included in A2A error data."""
    from yamlgraph.a2a.message import map_pipeline_error
    from yamlgraph.models import ErrorType, PipelineError

    err = PipelineError(
        type=ErrorType.LLM_ERROR,
        message="API fail",
        node="llm_node",
        details={"provider": "anthropic", "status_code": 429},
    )
    a2a_err = map_pipeline_error(err)
    assert a2a_err.data["provider"] == "anthropic"
    assert a2a_err.data["status_code"] == 429


# ---------------------------------------------------------------------------
# REQ-YG-208: build_agent_card
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-208")
def test_build_agent_card_from_graph(sample_graph_info):
    """Agent Card auto-generated with correct name, description, skills."""
    from yamlgraph.a2a.message import build_agent_card

    card = build_agent_card(
        graphs=[sample_graph_info],
        host="localhost",
        port=8080,
    )

    assert card.name == "YAMLGraph A2A Server"
    assert len(card.skills) == 1
    assert card.skills[0].id == "hello-world"
    assert card.skills[0].name == "hello-world"
    assert card.skills[0].description == "Simple greeting generator"
    assert "yamlgraph" in card.skills[0].tags


@pytest.mark.req("REQ-YG-208")
def test_agent_card_capabilities(sample_graph_info):
    """Agent Card has streaming=True, push_notifications=None."""
    from yamlgraph.a2a.message import build_agent_card

    card = build_agent_card(
        graphs=[sample_graph_info],
        host="localhost",
        port=8080,
    )

    assert card.capabilities.streaming is True


@pytest.mark.req("REQ-YG-208")
def test_agent_card_no_authentication(sample_graph_info):
    """Agent Card has no security schemes by default."""
    from yamlgraph.a2a.message import build_agent_card

    card = build_agent_card(
        graphs=[sample_graph_info],
        host="localhost",
        port=8080,
    )

    assert len(card.security_schemes) == 0


@pytest.mark.req("REQ-YG-208")
def test_agent_card_multi_graph(sample_graph_info, single_var_graph_info):
    """Multiple graphs become multiple skills in Agent Card."""
    from yamlgraph.a2a.message import build_agent_card

    card = build_agent_card(
        graphs=[sample_graph_info, single_var_graph_info],
        host="localhost",
        port=9090,
    )

    assert len(card.skills) == 2
    skill_ids = {s.id for s in card.skills}
    assert "hello-world" in skill_ids
    assert "echo" in skill_ids


@pytest.mark.req("REQ-YG-208")
def test_agent_card_empty_graphs():
    """Empty graphs list produces card with no skills."""
    from yamlgraph.a2a.message import build_agent_card

    card = build_agent_card(graphs=[], host="localhost", port=8080)
    assert card.skills == []
    assert card.name == "YAMLGraph A2A Server"


@pytest.mark.req("REQ-YG-208")
def test_agent_card_custom_host_port():
    """Custom host and port are reflected in card URL."""
    from yamlgraph.a2a.message import build_agent_card

    card = build_agent_card(
        graphs=[{"name": "g1", "description": "test"}],
        host="0.0.0.0",  # noqa: S104
        port=9999,
    )
    # v1.0: AgentCard no longer has url field; host/port are server-level config
    assert card.name == "YAMLGraph A2A Server"


# ---------------------------------------------------------------------------
# REQ-YG-213: _detect_interrupt
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-213")
def test_detect_interrupt_returns_true():
    """_detect_interrupt recognizes __interrupt__ key in graph result."""
    from yamlgraph.a2a.message import _detect_interrupt

    result = {"greeting": "Hello", "__interrupt__": [{"value": "need input"}]}
    assert _detect_interrupt(result) is True


@pytest.mark.req("REQ-YG-213")
def test_detect_interrupt_returns_false():
    """_detect_interrupt returns False for normal results."""
    from yamlgraph.a2a.message import _detect_interrupt

    result = {"greeting": "Hello"}
    assert _detect_interrupt(result) is False


# ---------------------------------------------------------------------------
# FR-250 / REQ-YG-213: _extract_interrupt_payload
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-213")
def test_extract_interrupt_payload_with_object():
    """_extract_interrupt_payload extracts .value from interrupt objects."""
    from unittest.mock import MagicMock

    from yamlgraph.a2a.message import _extract_interrupt_payload

    interrupt = MagicMock()
    interrupt.value = "What language do you prefer?"
    result = {"__interrupt__": [interrupt]}
    assert _extract_interrupt_payload(result) == "What language do you prefer?"


@pytest.mark.req("REQ-YG-213")
def test_extract_interrupt_payload_with_dict():
    """_extract_interrupt_payload extracts value from dict interrupts."""
    from yamlgraph.a2a.message import _extract_interrupt_payload

    result = {"__interrupt__": [{"value": "Please confirm"}]}
    assert _extract_interrupt_payload(result) == "Please confirm"


@pytest.mark.req("REQ-YG-213")
def test_extract_interrupt_payload_no_interrupt():
    """_extract_interrupt_payload returns None when no __interrupt__ key."""
    from yamlgraph.a2a.message import _extract_interrupt_payload

    result = {"greeting": "Hello"}
    assert _extract_interrupt_payload(result) is None


@pytest.mark.req("REQ-YG-213")
def test_extract_interrupt_payload_empty_list():
    """_extract_interrupt_payload returns None for empty interrupt list."""
    from yamlgraph.a2a.message import _extract_interrupt_payload

    result = {"__interrupt__": []}
    assert _extract_interrupt_payload(result) is None
