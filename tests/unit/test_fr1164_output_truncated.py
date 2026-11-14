"""FR-1164: replies cut at the output-token limit raise OutputTruncatedError.

Witnesses for the bounded guarantee: the executor attempt
(``attempt_structured_invoke``), the structured policy helpers
(``invoke_structured`` / ``ainvoke_structured``) and the race candidate
(``_invoke_candidate_async``), including their FR-998 second attempt and
FR-464 plain fallback. The truncated structured envelope mirrors the live
probe (evidence/FR-1164-truncation-probe.json): ``parsing_error`` is None and
``parsed`` is a valid model padded with an empty element.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import anthropic
import langchain_anthropic
import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel, ValidationError

from yamlgraph.executor_base import attempt_structured_invoke, is_retryable
from yamlgraph.node_factory import race_node
from yamlgraph.node_factory.race_node import _invoke_candidate_async, _race_async
from yamlgraph.utils import structured_output
from yamlgraph.utils.stop_reason import OutputTruncatedError, ensure_complete
from yamlgraph.utils.structured_output import (
    ainvoke_structured,
    bind_structured_output,
    invoke_structured,
    is_second_attempt_error,
)

SENTINEL = "SECRET-THINKING-SENTINEL"


class Countries(BaseModel):
    countries: list[str]


PADDED = Countries(countries=["Afghanistan", "Albania", "Angola", ""])
COMPLETE = Countries(countries=["Afghanistan", "Albania"])


def _msg(
    content: Any = "answer",
    *,
    stop: dict | None = None,
    usage: dict | None = None,
) -> AIMessage:
    kwargs: dict[str, Any] = {"content": content, "response_metadata": stop or {}}
    if usage is not None:
        kwargs["usage_metadata"] = usage
    return AIMessage(**kwargs)


def _usage(output: int = 2000, reasoning: int | None = 1921) -> dict:
    usage: dict[str, Any] = {
        "input_tokens": 10,
        "output_tokens": output,
        "total_tokens": output + 10,
    }
    if reasoning is not None:
        usage["output_token_details"] = {"reasoning": reasoning}
    return usage


THINKING_ONLY = [{"type": "thinking", "thinking": f"{SENTINEL} pondering"}]
MIXED = [
    {"type": "thinking", "thinking": f"{SENTINEL} pondering"},
    {"type": "text", "text": "The answer is"},
]
PARTIAL = '{"countries": ["Afghanistan", "Alb'
TRUNCATING = [
    {"stop_reason": "max_tokens"},
    {"finish_reason": "length"},
    {"finish_reason": "MAX_TOKENS"},
]


def _envelope(raw: AIMessage, parsed: Any = None, parsing_error: Any = None) -> dict:
    return {"raw": raw, "parsed": parsed, "parsing_error": parsing_error}


def _truncated_envelope() -> dict:
    raw = _msg(
        '{"countries":["Afghanistan","Albania","Angola","',
        stop={"stop_reason": "max_tokens"},
        usage=_usage(16, None),
    )
    return _envelope(raw, parsed=PADDED)


def _complete_envelope(parsed: Any = COMPLETE, parsing_error: Any = None) -> dict:
    return _envelope(
        _msg("{}", stop={"stop_reason": "end_turn"}), parsed, parsing_error
    )


class _Bound:
    def __init__(self, parent: _FakeLLM, kwargs: dict) -> None:
        self._parent = parent
        self._kwargs = kwargs

    def _answer(self, messages: list, config: dict | None) -> Any:
        method = self._kwargs.get("method")
        self._parent.calls.append(("structured", method, config))
        return self._parent.structured[method](messages)

    def invoke(self, messages: list, config: dict | None = None) -> Any:
        return self._answer(messages, config)

    async def ainvoke(self, messages: list, config: dict | None = None) -> Any:
        return self._answer(messages, config)


class _FakeLLM:
    """Records bindings and calls; replies are injected per structured method."""

    model = "fake-model"

    def __init__(
        self,
        structured: dict[str | None, Callable[[list], Any]] | None = None,
        plain: Callable[[list], Any] | None = None,
    ) -> None:
        self.structured = structured or {}
        self.plain = plain
        self.bind_kwargs: list[dict] = []
        self.calls: list[tuple] = []

    def with_structured_output(self, output_model: type, **kwargs: Any) -> _Bound:
        self.bind_kwargs.append(dict(kwargs))
        return _Bound(self, kwargs)

    def invoke(self, messages: list, config: dict | None = None) -> Any:
        self.calls.append(("plain", None, config))
        return self.plain(messages)

    async def ainvoke(self, messages: list, config: dict | None = None) -> Any:
        self.calls.append(("plain", None, config))
        return self.plain(messages)


class _FakeAnthropic(_FakeLLM):
    model = "claude-fake-4-5"


@pytest.fixture
def anthropic_cls(monkeypatch):
    """Make ``_FakeAnthropic`` the provider boundary's isinstance target."""
    monkeypatch.setattr(langchain_anthropic, "ChatAnthropic", _FakeAnthropic)
    return _FakeAnthropic


def _returns(value: Any) -> Callable[[list], Any]:
    return lambda messages: value


def _raises(exc: BaseException) -> Callable[[list], Any]:
    def _behaviour(messages: list) -> Any:
        raise exc

    return _behaviour


def _unsupported_error() -> anthropic.BadRequestError:
    message = (
        "output_config.format: structured outputs are not supported for this model"
    )
    body = {
        "type": "error",
        "error": {"type": "invalid_request_error", "message": message},
    }
    return anthropic.BadRequestError(
        f"Error code: 400 - {message}",
        response=MagicMock(status_code=400, headers={}),
        body=body,
    )


def _validation_error() -> ValidationError:
    try:
        Countries.model_validate({})
    except ValidationError as err:
        return err
    raise AssertionError("expected a ValidationError")


MESSAGES = [("user", "list countries")]


# ---------------------------------------------------------------------------
# AC-03: executor plain path rejects every recognized stop value
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-729")
@pytest.mark.parametrize("stop", TRUNCATING)
@pytest.mark.parametrize("content", [THINKING_ONLY, MIXED, PARTIAL])
def test_executor_plain_path_raises_on_truncation(stop, content):
    llm = _FakeLLM(plain=_returns(_msg(content, stop=stop, usage=_usage())))

    with pytest.raises(OutputTruncatedError) as info:
        attempt_structured_invoke(llm, MESSAGES, None)

    text = str(info.value)
    assert next(iter(stop.values())) in text
    assert "2000 output tokens" in text
    assert "1921 of them thinking" in text


# ---------------------------------------------------------------------------
# AC-04: unknown usage stays unknown; stop-key precedence
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-729")
def test_missing_usage_still_raises_and_prints_unknown():
    message = _msg("partial", stop={"stop_reason": "max_tokens"})

    with pytest.raises(OutputTruncatedError) as info:
        ensure_complete(message)

    err = info.value
    assert err.output_tokens is None
    assert err.reasoning_tokens is None
    assert "unknown output tokens, unknown of them thinking" in str(err)
    assert " 0 of them thinking" not in str(err)


@pytest.mark.req("REQ-YG-729")
def test_counts_are_reported_independently():
    message = _msg(
        "partial", stop={"stop_reason": "max_tokens"}, usage=_usage(16, None)
    )

    with pytest.raises(OutputTruncatedError) as info:
        ensure_complete(message)

    assert info.value.output_tokens == 16
    assert info.value.reasoning_tokens is None
    assert "16 output tokens, unknown of them thinking" in str(info.value)


@pytest.mark.req("REQ-YG-729")
def test_none_reasoning_detail_stays_unknown():
    usage = _usage(40, None)
    usage["output_token_details"] = {"reasoning": None}
    # AIMessage validation rejects None here; a provider building the
    # message without validation could still carry it.
    message = AIMessage.model_construct(
        content="partial",
        response_metadata={"finish_reason": "length"},
        usage_metadata=usage,
    )

    with pytest.raises(OutputTruncatedError) as info:
        ensure_complete(message)

    assert info.value.reasoning_tokens is None


@pytest.mark.req("REQ-YG-729")
def test_stop_reason_takes_precedence_over_finish_reason():
    message = _msg("done", stop={"stop_reason": "end_turn", "finish_reason": "length"})

    ensure_complete(message)  # stop_reason=end_turn wins: no error


@pytest.mark.req("REQ-YG-729")
def test_empty_stop_reason_falls_through_to_finish_reason():
    message = _msg("cut", stop={"stop_reason": "", "finish_reason": "length"})

    with pytest.raises(OutputTruncatedError) as info:
        ensure_complete(message)

    assert info.value.stop_reason == "length"


# ---------------------------------------------------------------------------
# AC-05: complete or unknown replies pass unchanged
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-729")
@pytest.mark.parametrize(
    "stop",
    [
        {},
        {"stop_reason": "end_turn"},
        {"finish_reason": "stop"},
        {"finish_reason": "weird"},
    ],
)
def test_complete_or_unknown_replies_pass(stop):
    llm = _FakeLLM(plain=_returns(_msg("fine", stop=stop, usage=_usage())))

    assert attempt_structured_invoke(llm, MESSAGES, None) == "fine"


# ---------------------------------------------------------------------------
# AC-06: structured helpers check raw before parsed / parsing_error
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-729")
def test_invoke_structured_rejects_padded_model_from_truncated_raw():
    llm = _FakeLLM(structured={None: _returns(_truncated_envelope())})

    with pytest.raises(OutputTruncatedError):
        invoke_structured(llm, Countries, MESSAGES)


@pytest.mark.req("REQ-YG-729")
def test_ainvoke_structured_rejects_padded_model_from_truncated_raw():
    llm = _FakeLLM(structured={None: _returns(_truncated_envelope())})

    with pytest.raises(OutputTruncatedError):
        asyncio.run(ainvoke_structured(llm, Countries, MESSAGES))


@pytest.mark.req("REQ-YG-729")
def test_complete_structured_returns_parsed_sync_and_async():
    llm = _FakeLLM(structured={None: _returns(_complete_envelope())})

    assert invoke_structured(llm, Countries, MESSAGES) is COMPLETE
    assert asyncio.run(ainvoke_structured(llm, Countries, MESSAGES)) is COMPLETE


@pytest.mark.req("REQ-YG-729")
def test_complete_parsing_error_reraised_identically_sync_and_async():
    error = _validation_error()
    llm = _FakeLLM(structured={None: _returns(_complete_envelope(None, error))})

    with pytest.raises(ValidationError) as sync_info:
        invoke_structured(llm, Countries, MESSAGES)
    with pytest.raises(ValidationError) as async_info:
        asyncio.run(ainvoke_structured(llm, Countries, MESSAGES))

    assert sync_info.value is error
    assert async_info.value is error


@pytest.mark.req("REQ-YG-729")
def test_truncated_raw_wins_over_parsing_error():
    envelope = _truncated_envelope()
    envelope["parsed"] = None
    envelope["parsing_error"] = _validation_error()
    llm = _FakeLLM(structured={None: _returns(envelope)})

    with pytest.raises(OutputTruncatedError):
        invoke_structured(llm, Countries, MESSAGES)


@pytest.mark.req("REQ-YG-729")
def test_second_attempt_truncation_is_marked_sync(anthropic_cls):
    llm = anthropic_cls(
        structured={
            "json_schema": _raises(_unsupported_error()),
            "function_calling": _returns(_truncated_envelope()),
        }
    )

    with pytest.raises(OutputTruncatedError) as info:
        invoke_structured(llm, Countries, MESSAGES)

    assert is_second_attempt_error(info.value)
    assert [c[1] for c in llm.calls] == ["json_schema", "function_calling"]


@pytest.mark.req("REQ-YG-729")
def test_second_attempt_truncation_is_marked_async_with_own_config(anthropic_cls):
    llm = anthropic_cls(
        structured={
            "json_schema": _raises(_unsupported_error()),
            "function_calling": _returns(_truncated_envelope()),
        }
    )
    second = {"run_id": "second"}

    with pytest.raises(OutputTruncatedError) as info:
        asyncio.run(
            ainvoke_structured(
                llm,
                Countries,
                MESSAGES,
                config={"run_id": "first"},
                second_attempt_config=lambda: second,
            )
        )

    assert is_second_attempt_error(info.value)
    assert [c[2] for c in llm.calls] == [{"run_id": "first"}, second]


# ---------------------------------------------------------------------------
# AC-07: binder defaults and the FR-998 policy are preserved
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-729")
def test_direct_binder_default_omits_include_raw():
    llm = _FakeLLM()

    bind_structured_output(llm, Countries)
    bind_structured_output(llm, Countries, include_raw=True)

    assert llm.bind_kwargs == [{}, {"include_raw": True}]


@pytest.mark.req("REQ-YG-729")
def test_include_raw_is_keyword_only():
    parameter = inspect.signature(bind_structured_output).parameters["include_raw"]

    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is False


@pytest.mark.req("REQ-YG-729")
def test_helpers_request_raw_on_both_attempts(anthropic_cls):
    llm = anthropic_cls(
        structured={
            "json_schema": _raises(_unsupported_error()),
            "function_calling": _returns(_complete_envelope()),
        }
    )

    assert invoke_structured(llm, Countries, MESSAGES, config={"k": 1}) is COMPLETE

    assert llm.bind_kwargs == [
        {"method": "json_schema", "include_raw": True},
        {"method": "function_calling", "include_raw": True},
    ]
    assert [c[2] for c in llm.calls] == [{"k": 1}, {"k": 1}]


@pytest.mark.req("REQ-YG-729")
def test_primary_truncation_earns_no_second_attempt(anthropic_cls):
    llm = anthropic_cls(structured={"json_schema": _returns(_truncated_envelope())})

    with pytest.raises(OutputTruncatedError) as info:
        invoke_structured(llm, Countries, MESSAGES)

    assert not is_second_attempt_error(info.value)
    assert len(llm.calls) == 1


@pytest.mark.req("REQ-YG-729")
def test_one_production_with_structured_output_call():
    source = inspect.getsource(structured_output)

    assert source.count(".with_structured_output(") == 1


# ---------------------------------------------------------------------------
# AC-08: FR-464 fallbacks reject truncation; structured truncation earns none
# ---------------------------------------------------------------------------


def _response_format_error() -> ValueError:
    return ValueError("response_format json_schema is not supported by this model")


@pytest.mark.req("REQ-YG-729")
def test_executor_fallback_rejects_truncated_plain_reply():
    llm = _FakeLLM(
        structured={None: _raises(_response_format_error())},
        plain=_returns(_msg('{"countries": ["A', stop={"finish_reason": "length"})),
    )

    with pytest.raises(OutputTruncatedError):
        attempt_structured_invoke(llm, MESSAGES, Countries)

    assert [c[0] for c in llm.calls] == ["structured", "plain"]


@pytest.mark.req("REQ-YG-729")
def test_executor_structured_truncation_earns_no_fallback():
    llm = _FakeLLM(
        structured={None: _returns(_truncated_envelope())},
        plain=_returns(_msg('{"countries": []}')),
    )

    with pytest.raises(OutputTruncatedError):
        attempt_structured_invoke(llm, MESSAGES, Countries)

    assert [c[0] for c in llm.calls] == ["structured"]


@pytest.mark.req("REQ-YG-729")
def test_race_fallback_rejects_truncated_plain_reply_with_distinct_run_ids():
    llm = _FakeLLM(
        structured={None: _raises(_response_format_error())},
        plain=_returns(_msg('{"countries": ["A', stop={"finish_reason": "length"})),
    )

    with pytest.raises(OutputTruncatedError):
        asyncio.run(_invoke_candidate_async({}, llm, MESSAGES, Countries, False))

    assert [c[0] for c in llm.calls] == ["structured", "plain"]
    run_ids = [c[2]["run_id"] for c in llm.calls]
    assert all(isinstance(r, UUID) for r in run_ids)
    assert run_ids[0] != run_ids[1]


@pytest.mark.req("REQ-YG-729")
def test_race_structured_truncation_earns_no_fallback():
    llm = _FakeLLM(
        structured={None: _returns(_truncated_envelope())},
        plain=_returns(_msg('{"countries": []}')),
    )

    with pytest.raises(OutputTruncatedError):
        asyncio.run(_invoke_candidate_async({}, llm, MESSAGES, Countries, False))

    assert [c[0] for c in llm.calls] == ["structured"]


# ---------------------------------------------------------------------------
# AC-09: a truncated candidate cannot win; truncation is not retryable
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-729")
@pytest.mark.parametrize("parse_json", [False, True])
def test_race_plain_candidate_truncation_raises(parse_json):
    llm = _FakeLLM(plain=_returns(_msg('{"a": 1', stop={"stop_reason": "max_tokens"})))

    with pytest.raises(OutputTruncatedError):
        asyncio.run(_invoke_candidate_async({}, llm, MESSAGES, None, parse_json))


class _SlowComplete(_FakeLLM):
    async def ainvoke(self, messages: list, config: dict | None = None) -> Any:
        await asyncio.sleep(0.05)
        return await super().ainvoke(messages, config)


@pytest.mark.req("REQ-YG-729")
def test_truncated_candidate_cannot_defeat_complete_candidate():
    fast_cut = _FakeLLM(plain=_returns(_msg("cut", stop={"stop_reason": "max_tokens"})))
    slow_done = _SlowComplete(
        plain=_returns(_msg("done", stop={"stop_reason": "end_turn"}))
    )
    armed = [({"provider": "cut"}, fast_cut), ({"provider": "done"}, slow_done)]

    winner, result = asyncio.run(_race_async(armed, MESSAGES, None, False, None))

    assert winner == {"provider": "done"}
    assert result == "done"


@pytest.mark.req("REQ-YG-729")
def test_truncation_is_not_retryable():
    with pytest.raises(OutputTruncatedError) as info:
        ensure_complete(_msg("x", stop={"stop_reason": "max_tokens"}))

    assert is_retryable(info.value) is False


# ---------------------------------------------------------------------------
# AC-10: diagnostics carry visible text only
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-729")
@pytest.mark.parametrize("content", [THINKING_ONLY, MIXED])
def test_thinking_text_never_reaches_the_error(content):
    with pytest.raises(OutputTruncatedError) as info:
        ensure_complete(
            _msg(content, stop={"stop_reason": "max_tokens"}, usage=_usage())
        )

    err = info.value
    assert SENTINEL not in str(err)
    assert SENTINEL not in err.preview


@pytest.mark.req("REQ-YG-729")
def test_fields_and_preview_come_from_visible_text():
    visible = "x" * 250
    content = [*THINKING_ONLY, {"type": "text", "text": visible}]

    with pytest.raises(OutputTruncatedError) as info:
        ensure_complete(
            _msg(content, stop={"finish_reason": "MAX_TOKENS"}, usage=_usage())
        )

    err = info.value
    assert err.stop_reason == "MAX_TOKENS"
    assert err.output_tokens == 2000
    assert err.reasoning_tokens == 1921
    assert err.visible_chars == 250
    assert err.preview == visible[:200]
    assert "250 visible characters" in str(err)


@pytest.mark.req("REQ-YG-729")
def test_message_cannot_trigger_the_response_format_fallback():
    with pytest.raises(OutputTruncatedError) as info:
        ensure_complete(_msg("x", stop={"stop_reason": "max_tokens"}, usage=_usage()))

    assert "response_format" not in str(info.value)


@pytest.mark.req("REQ-YG-729")
def test_race_module_uses_the_shared_classifier():
    assert race_node.ensure_complete is ensure_complete
