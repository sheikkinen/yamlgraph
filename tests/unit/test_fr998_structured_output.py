"""FR-998: structured output must be constrained, not requested.

`claude-sonnet-4-5` under the library-default forced tool call answers
`list[str]` fields with one string (a markdown bullet list in the committed
probe, `docs/spikes/list-type-lie-2026-09-05/probe-output.txt`); Pydantic
rejects it with `list_type` and the run dies. The cure is the provider's
constrained decoding (`method="json_schema"`) selected in ONE place —
`yamlgraph.utils.structured_output` — with exactly one forced-tool-call
second attempt when, and only when, Anthropic answers a typed 400 saying the
model does not support `output_config`.

Fakes are Anthropic *by predicate*: the provider-boundary `isinstance`
target is monkeypatched to the fake class. No class-name equality anywhere.
"""

from __future__ import annotations

import ast
import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID

import anthropic
import langchain_anthropic
import pytest
from pydantic import BaseModel, Field, ValidationError
from yamlgraph.utils.llm_provider_identity import (
    is_anthropic_chat_model,
    is_anthropic_unsupported_structured_output,
)
from yamlgraph.utils.structured_output import (
    ainvoke_structured,
    bind_structured_output,
    invoke_structured,
)

import yamlgraph
from yamlgraph.executor_base import attempt_structured_invoke
from yamlgraph.node_factory.race_node import _invoke_candidate_async
from yamlgraph.tools.agent import _try_structured_output

pytestmark = pytest.mark.req("REQ-YG-664")

MSGS = ["system", "user"]

# Verbatim opening of the recorded raw `unclear` argument (probe run 1, T=0):
# a markdown bullet list, not JSON — `json.loads` repair cannot touch it.
BULLET_PAYLOAD = (
    '\n- "yamlgraph" · is this the name of this project or a tool it uses?'
    '\n- "FR-990" · what does the FR prefix mean?'
    "\n- is yamlgraph a code-generation tool?\n"
)


class _Reading(BaseModel):
    restatement: str = Field(description="plain restatement")
    unclear: list[str] = Field(description="one item per element")
    needs: list[str] = Field(description="one item per element")


TYPED = _Reading(
    restatement="ok",
    unclear=["a", "b", "c", "d", "e"],
    needs=[],
)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _Bound:
    def __init__(self, parent: _FakeLLM, method: str | None) -> None:
        self._parent = parent
        self._method = method

    def invoke(self, messages: list, **kwargs: Any) -> Any:
        self._parent.invocations.append((self._method, messages, kwargs))
        return self._parent.behaviours[self._method](messages)

    async def ainvoke(self, messages: list, **kwargs: Any) -> Any:
        self._parent.invocations.append((self._method, messages, kwargs))
        return self._parent.behaviours[self._method](messages)


class _FakeLLM:
    """Records every binding and invocation; behaviour is injected per method.

    ``behaviours`` maps the ``method`` kwarg the binder passes (``None`` =
    library default) to a callable of the messages; ``"plain"`` serves
    ``invoke``/``ainvoke`` without structured output.
    """

    model = "fake-model"

    def __init__(self, behaviours: dict[str | None, Callable[[list], Any]]) -> None:
        self.behaviours = behaviours
        self.bind_calls: list[dict] = []
        self.invocations: list[tuple[str | None, list, dict]] = []

    def with_structured_output(self, output_model: type, **kwargs: Any) -> _Bound:
        self.bind_calls.append(dict(kwargs))
        method = kwargs.get("method")
        if method not in self.behaviours:
            raise AssertionError(f"unexpected structured-output method {method!r}")
        return _Bound(self, method)

    def invoke(self, messages: list, **kwargs: Any) -> Any:
        self.invocations.append(("plain", messages, kwargs))
        return self.behaviours["plain"](messages)

    async def ainvoke(self, messages: list, **kwargs: Any) -> Any:
        self.invocations.append(("plain", messages, kwargs))
        return self.behaviours["plain"](messages)


class _FakeAnthropic(_FakeLLM):
    model = "claude-fake-4-5"


class _FakeOther(_FakeLLM):
    model = "other-model"


class _BindingFails(_FakeAnthropic):
    def with_structured_output(self, output_model: type, **kwargs: Any) -> _Bound:
        raise TypeError("binding defect")


@pytest.fixture
def anthropic_llm(monkeypatch):
    """Make ``_FakeAnthropic`` the provider boundary's isinstance target."""
    monkeypatch.setattr(langchain_anthropic, "ChatAnthropic", _FakeAnthropic)

    def _make(behaviours: dict[str | None, Callable[[list], Any]]) -> _FakeAnthropic:
        return _FakeAnthropic(behaviours)

    return _make


def _returns(value: Any) -> Callable[[list], Any]:
    return lambda messages: value


def _raises(exc: BaseException) -> Callable[[list], Any]:
    def _behaviour(messages: list) -> Any:
        raise exc

    return _behaviour


def _status_error(cls: type, status: int, message: str) -> anthropic.APIStatusError:
    response = MagicMock(status_code=status, headers={})
    body = {
        "type": "error",
        "error": {"type": "invalid_request_error", "message": message},
    }
    return cls(f"Error code: {status}", response=response, body=body)


def _unsupported_error() -> anthropic.BadRequestError:
    return _status_error(
        anthropic.BadRequestError,
        400,
        "output_config.format: structured outputs are not supported for this model",
    )


def _validation_error() -> ValidationError:
    try:
        _Reading.model_validate({})
    except ValidationError as err:
        return err
    raise AssertionError("expected a ValidationError")


# ---------------------------------------------------------------------------
# S-2: provider boundary predicates
# ---------------------------------------------------------------------------


class TestProviderBoundary:
    def test_anthropic_identity_is_isinstance_not_class_name(self, anthropic_llm):
        assert is_anthropic_chat_model(anthropic_llm({}))
        assert not is_anthropic_chat_model(_FakeOther({}))

        class _Impostor:
            __name__ = "ChatAnthropic"

        _Impostor.__qualname__ = "ChatAnthropic"
        assert not is_anthropic_chat_model(_Impostor())

    def test_identity_false_without_sdk(self, monkeypatch, anthropic_llm):
        llm = anthropic_llm({})
        monkeypatch.setitem(__import__("sys").modules, "langchain_anthropic", None)
        assert not is_anthropic_chat_model(llm)

    def test_unsupported_predicate_requires_all_four_conditions(self, anthropic_llm):
        llm = anthropic_llm({})
        assert is_anthropic_unsupported_structured_output(llm, _unsupported_error())
        # (1) not an Anthropic model
        assert not is_anthropic_unsupported_structured_output(
            _FakeOther({}), _unsupported_error()
        )
        # (2) not the typed BadRequestError
        assert not is_anthropic_unsupported_structured_output(
            llm, ValueError("output_config is not supported")
        )
        # (3) another 4xx naming the parameter
        assert not is_anthropic_unsupported_structured_output(
            llm,
            _status_error(
                anthropic.PermissionDeniedError, 403, "output_config not supported"
            ),
        )
        # (4) a 400 whose body does not diagnose the capability
        assert not is_anthropic_unsupported_structured_output(
            llm,
            _status_error(anthropic.BadRequestError, 400, "max_tokens: must be > 0"),
        )
        # (4) a 400 naming output_config for another reason (bad schema)
        assert not is_anthropic_unsupported_structured_output(
            llm,
            _status_error(
                anthropic.BadRequestError,
                400,
                "output_config.format.schema: invalid JSON schema at #/properties",
            ),
        )
        # body without the structured payload
        bare = anthropic.BadRequestError(
            "output_config is not supported",
            response=MagicMock(status_code=400, headers={}),
            body=None,
        )
        assert not is_anthropic_unsupported_structured_output(llm, bare)


# ---------------------------------------------------------------------------
# S-1: binder — method selection and explicit override
# ---------------------------------------------------------------------------


class TestBinder:
    def test_anthropic_default_selects_json_schema_via_executor(self, anthropic_llm):
        llm = anthropic_llm({"json_schema": _returns(TYPED)})
        assert attempt_structured_invoke(llm, MSGS, _Reading) is TYPED
        assert llm.bind_calls == [{"method": "json_schema"}]

    def test_non_anthropic_default_omits_method_kwarg(self):
        llm = _FakeOther({None: _returns(TYPED)})
        assert attempt_structured_invoke(llm, MSGS, _Reading) is TYPED
        assert llm.bind_calls == [{}]

    def test_explicit_override_forwarded_unchanged_for_anthropic(self, anthropic_llm):
        llm = anthropic_llm({"function_calling": _returns(TYPED)})
        bound = bind_structured_output(llm, _Reading, method="function_calling")
        assert bound.invoke(MSGS) is TYPED
        assert llm.bind_calls == [{"method": "function_calling"}]

    def test_explicit_override_forwarded_for_non_anthropic(self):
        llm = _FakeOther({"json_schema": _returns(TYPED)})
        bind_structured_output(llm, _Reading, method="json_schema")
        assert llm.bind_calls == [{"method": "json_schema"}]


# ---------------------------------------------------------------------------
# S-4 §3: the incident
# ---------------------------------------------------------------------------


class TestIncident:
    def test_bullet_payload_fails_forced_tool_call_and_passes_constrained(
        self, anthropic_llm
    ):
        def _forced_tool_call(messages: list) -> _Reading:
            # What PydanticToolsParser does with the recorded tool arguments.
            return _Reading.model_validate(
                {
                    "restatement": "ok",
                    "unclear": BULLET_PAYLOAD,
                    "needs": BULLET_PAYLOAD,
                }
            )

        def _constrained(messages: list) -> _Reading:
            return _Reading.model_validate(
                {"restatement": "ok", "unclear": TYPED.unclear, "needs": []}
            )

        llm = anthropic_llm(
            {"function_calling": _forced_tool_call, "json_schema": _constrained}
        )

        with pytest.raises(ValidationError) as excinfo:
            llm.with_structured_output(_Reading, method="function_calling").invoke(MSGS)
        assert {e["type"] for e in excinfo.value.errors()} == {"list_type"}
        assert {e["loc"][0] for e in excinfo.value.errors()} == {"unclear", "needs"}

        result = invoke_structured(llm, _Reading, MSGS)
        assert isinstance(result.unclear, list)
        assert len(result.unclear) == 5
        assert all(isinstance(item, str) for item in result.unclear)
        assert result.needs == []


# ---------------------------------------------------------------------------
# S-4 §4: the one typed second attempt, sync and native-async
# ---------------------------------------------------------------------------


def _fr998_records(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if "FR-998" in r.getMessage()]


class TestTypedSecondAttempt:
    def test_sync_one_function_calling_attempt_and_one_info_line(
        self, anthropic_llm, caplog
    ):
        llm = anthropic_llm(
            {
                "json_schema": _raises(_unsupported_error()),
                "function_calling": _returns(TYPED),
            }
        )
        with caplog.at_level(logging.INFO, logger="yamlgraph.utils.structured_output"):
            assert invoke_structured(llm, _Reading, MSGS) is TYPED

        assert [c.get("method") for c in llm.bind_calls] == [
            "json_schema",
            "function_calling",
        ]
        assert [m for m, _, _ in llm.invocations] == ["json_schema", "function_calling"]
        records = _fr998_records(caplog)
        assert len(records) == 1
        assert records[0].levelno == logging.INFO
        assert "claude-fake-4-5" in records[0].getMessage()

    @pytest.mark.asyncio
    async def test_async_one_function_calling_attempt_and_one_info_line(
        self, anthropic_llm, caplog
    ):
        llm = anthropic_llm(
            {
                "json_schema": _raises(_unsupported_error()),
                "function_calling": _returns(TYPED),
            }
        )
        with caplog.at_level(logging.INFO, logger="yamlgraph.utils.structured_output"):
            result = await ainvoke_structured(llm, _Reading, MSGS)

        assert result is TYPED
        assert [c.get("method") for c in llm.bind_calls] == [
            "json_schema",
            "function_calling",
        ]
        records = _fr998_records(caplog)
        assert len(records) == 1
        assert "claude-fake-4-5" in records[0].getMessage()

    @pytest.mark.asyncio
    async def test_async_is_native_not_threaded(self):
        src = ast.dump(
            ast.parse(
                Path(yamlgraph.__file__)
                .with_name("utils")
                .joinpath("structured_output.py")
                .read_text(encoding="utf-8")
            )
        )
        assert "run_in_executor" not in src
        assert "to_thread" not in src
        assert "ainvoke" in src


# ---------------------------------------------------------------------------
# S-4 §5: everything else propagates, with no second invocation
# ---------------------------------------------------------------------------


_PROPAGATING_ERRORS = [
    pytest.param(_validation_error, id="pydantic-validation"),
    pytest.param(
        lambda: _status_error(anthropic.AuthenticationError, 401, "invalid x-api-key"),
        id="authentication",
    ),
    pytest.param(
        lambda: _status_error(anthropic.PermissionDeniedError, 403, "forbidden"),
        id="permission",
    ),
    pytest.param(
        lambda: _status_error(anthropic.RateLimitError, 429, "rate limited"),
        id="rate-limit",
    ),
    pytest.param(lambda: anthropic.APITimeoutError(request=MagicMock()), id="timeout"),
    pytest.param(
        lambda: anthropic.APIConnectionError(request=MagicMock()), id="connection"
    ),
    pytest.param(
        lambda: _status_error(anthropic.InternalServerError, 500, "overloaded"),
        id="server",
    ),
    pytest.param(
        lambda: _status_error(
            anthropic.BadRequestError, 400, "max_tokens: must be > 0"
        ),
        id="unrelated-400",
    ),
]


class TestPropagation:
    @pytest.mark.parametrize("make_error", _PROPAGATING_ERRORS)
    def test_sync_propagates_unchanged(self, anthropic_llm, make_error):
        err = make_error()
        llm = anthropic_llm(
            {"json_schema": _raises(err), "function_calling": _returns(TYPED)}
        )
        with pytest.raises(type(err)) as excinfo:
            invoke_structured(llm, _Reading, MSGS)
        assert excinfo.value is err
        assert llm.bind_calls == [{"method": "json_schema"}]
        assert len(llm.invocations) == 1

    @pytest.mark.parametrize("make_error", _PROPAGATING_ERRORS)
    @pytest.mark.asyncio
    async def test_async_propagates_unchanged(self, anthropic_llm, make_error):
        err = make_error()
        llm = anthropic_llm(
            {"json_schema": _raises(err), "function_calling": _returns(TYPED)}
        )
        with pytest.raises(type(err)) as excinfo:
            await ainvoke_structured(llm, _Reading, MSGS)
        assert excinfo.value is err
        assert len(llm.invocations) == 1

    def test_binding_defect_propagates(self, anthropic_llm):
        llm = _BindingFails({})
        with pytest.raises(TypeError, match="binding defect"):
            invoke_structured(llm, _Reading, MSGS)
        assert llm.invocations == []

    def test_error_from_second_attempt_propagates(self, anthropic_llm):
        second = _status_error(anthropic.BadRequestError, 400, "tool_choice: invalid")
        llm = anthropic_llm(
            {
                "json_schema": _raises(_unsupported_error()),
                "function_calling": _raises(second),
            }
        )
        with pytest.raises(anthropic.BadRequestError) as excinfo:
            invoke_structured(llm, _Reading, MSGS)
        assert excinfo.value is second
        assert [m for m, _, _ in llm.invocations] == ["json_schema", "function_calling"]

    def test_unsupported_error_from_non_anthropic_model_propagates(self):
        err = _unsupported_error()
        llm = _FakeOther({None: _raises(err), "function_calling": _returns(TYPED)})
        with pytest.raises(anthropic.BadRequestError) as excinfo:
            invoke_structured(llm, _Reading, MSGS)
        assert excinfo.value is err
        assert llm.bind_calls == [{}]


# ---------------------------------------------------------------------------
# S-4 §6 / §7: composition with the race node and FR-464
# ---------------------------------------------------------------------------


def _run_ids(llm: _FakeLLM) -> list[Any]:
    return [kw["config"]["run_id"] for _, _, kw in llm.invocations]


class TestRaceComposition:
    @pytest.mark.asyncio
    async def test_both_attempts_carry_distinct_run_ids(self, anthropic_llm):
        llm = anthropic_llm(
            {
                "json_schema": _raises(_unsupported_error()),
                "function_calling": _returns(TYPED),
            }
        )
        candidate = {"provider": "anthropic", "model": "claude-fake-4-5"}
        got, result = await _invoke_candidate_async(
            candidate, llm, MSGS, _Reading, False
        )
        assert got is candidate
        assert result is TYPED
        ids = _run_ids(llm)
        assert len(ids) == 2
        assert all(isinstance(i, UUID) for i in ids)
        assert ids[0] != ids[1]

    @pytest.mark.asyncio
    async def test_cancellation_during_second_attempt_closes_its_own_span(
        self, anthropic_llm
    ):
        llm = anthropic_llm(
            {
                "json_schema": _raises(_unsupported_error()),
                "function_calling": _raises(asyncio.CancelledError()),
            }
        )
        candidate = {"provider": "anthropic", "model": "claude-fake-4-5"}
        with (
            patch("yamlgraph.node_factory.race_node._close_cancelled_run") as close,
            pytest.raises(asyncio.CancelledError),
        ):
            await _invoke_candidate_async(
                candidate, llm, MSGS, _Reading, False, {"k": 1}
            )
        ids = _run_ids(llm)
        assert len(ids) == 2
        close.assert_called_once_with(ids[1], {"k": 1})

    @pytest.mark.asyncio
    async def test_response_format_rejection_still_reaches_json_extraction(self):
        llm = _FakeOther(
            {
                None: _raises(
                    Exception("400 - This response_format type is unavailable now")
                ),
                "plain": _returns(
                    _FakeResponse('{"restatement": "x", "unclear": [], "needs": []}')
                ),
            }
        )
        _, result = await _invoke_candidate_async(
            {"provider": "deepseek"}, llm, MSGS, _Reading, False
        )
        assert isinstance(result, _Reading)
        assert result.restatement == "x"
        assert [m for m, _, _ in llm.invocations] == [None, "plain"]
        assert _run_ids(llm)[0] != _run_ids(llm)[1]


class TestExecutorComposition:
    def test_response_format_rejection_still_reaches_json_extraction(self):
        llm = _FakeOther(
            {
                None: _raises(ValueError("response_format is not supported")),
                "plain": _returns(
                    _FakeResponse('{"restatement": "y", "unclear": [], "needs": []}')
                ),
            }
        )
        result = attempt_structured_invoke(llm, MSGS, _Reading)
        assert isinstance(result, _Reading)
        assert result.restatement == "y"


# ---------------------------------------------------------------------------
# S-4 §8: agent composition — tiers keep their order, override cannot upgrade
# ---------------------------------------------------------------------------


class TestAgentComposition:
    def test_default_tier_binds_constrained_for_anthropic(self, anthropic_llm):
        llm = anthropic_llm({"json_schema": _returns(TYPED)})
        result = _try_structured_output(
            "prose without json", msgs=[], output_model=_Reading, llm_base=llm
        )
        assert result == TYPED.model_dump()
        assert llm.bind_calls == [{"method": "json_schema"}]

    def test_recovery_tier_stays_function_calling_for_anthropic(self, anthropic_llm):
        llm = anthropic_llm(
            {
                "json_schema": _raises(
                    Exception("invalid_json_schema: additionalProperties")
                ),
                "function_calling": _returns(TYPED),
            }
        )
        result = _try_structured_output(
            "prose without json", msgs=[], output_model=_Reading, llm_base=llm
        )
        assert result == TYPED.model_dump()
        assert [c.get("method") for c in llm.bind_calls] == [
            "json_schema",
            "function_calling",
        ]


# ---------------------------------------------------------------------------
# S-4 §9 / AC-04: one production call site; generic modules stay SDK-free
# ---------------------------------------------------------------------------

_GENERIC_MODULES = (
    "executor_base.py",
    "node_factory/race_node.py",
    "tools/agent.py",
)


class TestBoundaries:
    def test_single_production_call_expression(self):
        root = Path(yamlgraph.__file__).parent
        hits = {}
        for path in root.rglob("*.py"):
            count = path.read_text(encoding="utf-8").count(".with_structured_output(")
            if count:
                hits[path.relative_to(root).as_posix()] = count
        assert hits == {"utils/structured_output.py": 1}

    @pytest.mark.parametrize("module", _GENERIC_MODULES)
    def test_generic_modules_import_no_provider_sdk(self, module):
        source = (Path(yamlgraph.__file__).parent / module).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any(
            name == "anthropic"
            or name.startswith(("anthropic.", "langchain_anthropic"))
            for name in imported
        ), imported
        assert "__name__ ==" not in source
        assert "ChatAnthropic" not in source
