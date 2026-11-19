"""Unit tests for FR-1170: Azure non-thinking mode (REQ-YG-732).

Azure reasoning deployments (gpt-5.x, gpt-6) think by default and then reject
``temperature: 0``. ``thinking_budget: 0`` must reach the wire as
``reasoning_effort: "none"``; the FR-1056 four-case contract applies:

- ``thinking_budget=0``    -> ``reasoning_effort == "none"``
- omitted                  -> no ``reasoning_effort`` (API default preserved)
- accepted non-zero < 1024 -> no ``reasoning_effort``, DEBUG record emitted
- ``>= 1024``              -> ``ValueError`` (unsupported token budget)

Two witness layers, both keyless:
- ``TestAzureThinkingKwargs`` replaces ``langchain_azure_ai`` with a fake
  module, so it runs without the optional ``azure`` extra (CI).
- ``TestAzureThinkingPayload`` and ``TestRaceAzurePayload`` use the real SDK
  request payload and skip when the extra is absent.
"""

import logging
import os
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from yamlgraph.utils.llm_factory import clear_cache, create_llm

_AZURE_ENV = {
    "AZURE_AI_ENDPOINT": "https://dummy.services.ai.azure.com/openai/v1",
    "AZURE_AI_API_KEY": "dummy-key",
}
_MODEL = "aaa-gpt-6-luna"


def _azure(**kwargs):
    with patch.dict(os.environ, _AZURE_ENV, clear=False):
        return create_llm(provider="azure", model=_MODEL, temperature=0.0, **kwargs)


@pytest.fixture
def fake_azure_class():
    chat_cls = MagicMock(side_effect=lambda **kw: MagicMock())
    parent = ModuleType("langchain_azure_ai")
    child = ModuleType("langchain_azure_ai.chat_models")
    child.AzureAIOpenAIApiChatModel = chat_cls
    with patch.dict(
        sys.modules,
        {"langchain_azure_ai": parent, "langchain_azure_ai.chat_models": child},
    ):
        yield chat_cls


@pytest.fixture(autouse=True)
def _fresh_cache():
    clear_cache()
    yield
    clear_cache()


@pytest.mark.req("REQ-YG-732")
class TestAzureThinkingKwargs:
    def test_zero_budget_sets_reasoning_effort_none(self, fake_azure_class):
        """AC-01 (SDK-free): 0 becomes reasoning_effort='none' at construction."""
        _azure(thinking_budget=0)
        kwargs = fake_azure_class.call_args.kwargs
        assert kwargs["reasoning_effort"] == "none"
        assert kwargs["temperature"] == 0.0

    def test_omitted_budget_sends_no_reasoning_effort(self, fake_azure_class):
        """AC-02 (SDK-free): omission leaves the deployment default alone."""
        _azure()
        assert "reasoning_effort" not in fake_azure_class.call_args.kwargs

    def test_accepted_nonzero_budget_is_ignored_and_logged(
        self, fake_azure_class, caplog
    ):
        """AC-03: 512 is a logged no-op, never an error."""
        with caplog.at_level(logging.DEBUG, logger="yamlgraph.utils.llm_providers"):
            _azure(thinking_budget=512)
        assert "reasoning_effort" not in fake_azure_class.call_args.kwargs
        assert any(
            "512" in record.message and "azure" in record.message.lower()
            for record in caplog.records
        )

    def test_token_budget_still_rejected(self, fake_azure_class):
        """AC-04: Azure has no token budget; >= 1024 must stay loud."""
        with pytest.raises(ValueError, match="thinking_budget is only supported"):
            _azure(thinking_budget=8000)
        fake_azure_class.assert_not_called()


def _payload(llm) -> dict:
    return llm._get_request_payload([HumanMessage("hi")], stop=None)


@pytest.mark.req("REQ-YG-732")
class TestAzureThinkingPayload:
    @pytest.fixture(autouse=True)
    def _sdk(self):
        pytest.importorskip("langchain_azure_ai", reason="azure extra not installed")

    def test_zero_budget_payload(self):
        """AC-01: the real request payload carries reasoning_effort='none'."""
        from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel

        llm = _azure(thinking_budget=0)
        assert isinstance(llm, AzureAIOpenAIApiChatModel)
        payload = _payload(llm)
        assert payload["reasoning_effort"] == "none"
        assert payload["temperature"] == 0.0

    def test_omitted_budget_payload(self):
        """AC-02: no budget, no reasoning_effort key on the wire."""
        assert "reasoning_effort" not in _payload(_azure())

    def test_budgets_do_not_alias_in_cache(self):
        """AC-06: omitted, 0 and 512 must not share one cached client."""
        omitted, zero, portable = (
            _azure(),
            _azure(thinking_budget=0),
            _azure(thinking_budget=512),
        )
        assert omitted is not zero
        assert zero is not portable
        assert omitted is not portable


def _race_config(**extra) -> dict:
    return {
        "type": "race",
        "prompt": "test_prompt",
        "state_key": "response",
        "temperature": 0.0,
        "candidates": [
            {"provider": "vertex", "model": "gemini-2.5-flash"},
            {"provider": "azure", "model": _MODEL},
        ],
        **extra,
    }


def _mock_llm(text: str):
    llm = MagicMock()

    async def ainvoke(messages, config=None):
        result = MagicMock()
        result.content = text
        return result

    llm.ainvoke = ainvoke
    return llm


@pytest.mark.req("REQ-YG-732")
class TestRaceAzurePayload:
    """AC-05: the real race path builds the real Azure client; only invocation
    is mocked."""

    @pytest.fixture(autouse=True)
    def _sdk(self):
        pytest.importorskip("langchain_azure_ai", reason="azure extra not installed")

    def _azure_payload_via_race(self, node_extra: dict, defaults: dict) -> dict:
        from yamlgraph.node_factory.race_node import create_race_node
        from yamlgraph.utils import llm_providers

        built: list = []
        real_azure = llm_providers._create_azure_llm

        def spy_azure(*args, **kwargs):
            built.append(real_azure(*args, **kwargs))
            return _mock_llm("z")

        state = {"thread_id": "t", "errors": [], "messages": [], "_loop_counts": {}}
        with (
            patch.dict(os.environ, _AZURE_ENV, clear=False),
            patch.dict(
                llm_providers._PROVIDER_FACTORIES,
                {"vertex": MagicMock(return_value=_mock_llm("v")), "azure": spy_azure},
            ),
            patch(
                "yamlgraph.node_factory.race_node.prepare_messages",
                return_value=([MagicMock()], "vertex", None),
            ),
        ):
            create_race_node("race_az", _race_config(**node_extra), defaults)(state)

        assert len(built) == 1
        return _payload(built[0])

    def test_node_zero_reaches_azure_payload(self):
        payload = self._azure_payload_via_race({"thinking_budget": 0}, {})
        assert payload["reasoning_effort"] == "none"
        assert payload["temperature"] == 0.0

    def test_node_512_overrides_inherited_zero(self):
        payload = self._azure_payload_via_race(
            {"thinking_budget": 512}, {"thinking_budget": 0}
        )
        assert "reasoning_effort" not in payload
