"""FR-679: consolidate the retry/fallback attempt shared by sync & async paths.

FR-676 achieved sync/async parity by *copying* the FR-464 structured-output
fallback into both `executor.py::_invoke_with_retry` and
`llm_factory_async.py::invoke_async`. This suite condemns that duplication:
the single-attempt policy must live in exactly one place
(`executor_base.attempt_structured_invoke`) which both callers delegate to,
and it must carry FR-678's narrowed exception boundary.
"""

import inspect

import pytest
from pydantic import BaseModel, Field

from yamlgraph import executor_base
from yamlgraph.executor_base import attempt_structured_invoke


class _Verdict(BaseModel):
    verdict: str = Field(description="pass or fail")
    reasoning: str = Field(description="why")


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _StructuredOK:
    """LLM whose with_structured_output path succeeds."""

    def __init__(self, model_instance):
        self._model_instance = model_instance

    def with_structured_output(self, model):
        parent = self

        class _Bound:
            def invoke(self, messages):
                return parent._model_instance

        return _Bound()

    def invoke(self, messages):  # pragma: no cover - not reached in this path
        raise AssertionError("plain invoke should not be called")


class _ResponseFormatReject:
    """LLM that rejects with_structured_output (response_format) then serves JSON."""

    def __init__(self, fallback_content):
        self._fallback_content = fallback_content
        self.plain_invocations = 0

    def with_structured_output(self, model):
        class _Bound:
            def invoke(self, messages):
                raise ValueError("response_format is not supported by this provider")

        return _Bound()

    def invoke(self, messages):
        self.plain_invocations += 1
        return _FakeResponse(self._fallback_content)


class _NonResponseFormatError:
    """LLM whose structured path raises a non-response_format error (FR-678)."""

    def with_structured_output(self, model):
        class _Bound:
            def invoke(self, messages):
                raise TypeError("programming defect, not a provider capability gap")

        return _Bound()

    def invoke(self, messages):  # pragma: no cover - must not be reached
        raise AssertionError("must not fall back on a non-response_format error")


class _PlainLLM:
    def __init__(self, content):
        self._content = content

    def invoke(self, messages):
        return _FakeResponse(self._content)


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_helper_exists_in_executor_base():
    """The shared attempt policy lives in exactly one module."""
    assert callable(attempt_structured_invoke)


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_no_output_model_returns_normalized_string():
    llm = _PlainLLM("plain text answer")
    result = attempt_structured_invoke(llm, ["hi"], None)
    assert result == "plain text answer"


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_structured_success_returns_model_instance():
    instance = _Verdict(verdict="pass", reasoning="ok")
    llm = _StructuredOK(instance)
    result = attempt_structured_invoke(llm, ["hi"], _Verdict)
    assert result is instance


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_response_format_rejection_falls_back_to_json_extraction():
    llm = _ResponseFormatReject('{"verdict": "pass", "reasoning": "extracted"}')
    result = attempt_structured_invoke(llm, ["hi"], _Verdict)
    assert isinstance(result, _Verdict)
    assert result.reasoning == "extracted"
    assert llm.plain_invocations == 1


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_fallback_raises_valueerror_when_no_json():
    llm = _ResponseFormatReject("sorry, I have no JSON for you")
    with pytest.raises(ValueError, match="could not extract JSON"):
        attempt_structured_invoke(llm, ["hi"], _Verdict)


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_non_response_format_error_propagates():
    """FR-678: only response_format triggers fallback; other errors propagate."""
    llm = _NonResponseFormatError()
    with pytest.raises(TypeError, match="programming defect"):
        attempt_structured_invoke(llm, ["hi"], _Verdict)


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_sync_and_async_paths_both_delegate_to_helper():
    """Consolidation proof: both retry loops call the one helper by name."""
    from yamlgraph import executor
    from yamlgraph.utils import llm_factory_async

    sync_src = inspect.getsource(executor.PromptExecutor._invoke_with_retry)
    async_src = inspect.getsource(llm_factory_async.invoke_async)

    assert "attempt_structured_invoke" in sync_src
    assert "attempt_structured_invoke" in async_src


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_fallback_block_not_duplicated_in_callers():
    """The schema-hint + extract_json fallback appears only in the helper."""
    from yamlgraph import executor
    from yamlgraph.utils import llm_factory_async

    helper_src = inspect.getsource(executor_base.attempt_structured_invoke)
    assert "extract_json" in helper_src

    sync_src = inspect.getsource(executor.PromptExecutor._invoke_with_retry)
    async_src = inspect.getsource(llm_factory_async.invoke_async)
    assert "extract_json" not in sync_src
    assert "extract_json" not in async_src
