"""Unit tests for FR-1056: DeepSeek non-thinking mode (REQ-YG-684).

DeepSeek enables thinking by default at `high` effort on every model, so the
only way to get a non-reasoning completion is to send
``reasoning_effort: "none"``.  DeepSeek exposes no token budget, so exactly one
``thinking_budget`` value carries meaning here: ``0``.

Frozen four-case contract:
- ``thinking_budget=0``  -> payload carries ``reasoning_effort == "none"``
- omitted                -> no ``reasoning_effort`` key (API default preserved)
- accepted non-zero < 1024 -> no ``reasoning_effort`` key, DEBUG record emitted
- ``>= 1024``            -> ``ValueError`` (unsupported token budget) unchanged

Keyless by construction: the witness is the SDK request payload, never a call.
"""

import logging
import os
from unittest.mock import patch

import pytest
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from yamlgraph.utils.llm_factory import clear_cache, create_llm

_DEEPSEEK_ENV = {"DEEPSEEK_API_KEY": "test-key"}


def _payload(llm: ChatOpenAI) -> dict:
    return llm._get_request_payload([HumanMessage("hi")], stop=None)


def _deepseek(**kwargs) -> ChatOpenAI:
    with patch.dict(os.environ, _DEEPSEEK_ENV, clear=False):
        return create_llm(provider="deepseek", model="deepseek-v4-pro", **kwargs)


@pytest.mark.req("REQ-YG-684")
class TestDeepSeekThinkingToggle:
    def setup_method(self):
        clear_cache()

    def test_zero_budget_disables_thinking(self):
        """AC-01: thinking_budget=0 reaches the wire as reasoning_effort=none."""
        llm = _deepseek(thinking_budget=0)
        assert isinstance(llm, ChatOpenAI)
        assert _payload(llm)["reasoning_effort"] == "none"

    def test_omitted_budget_leaves_api_default(self):
        """AC-02: no budget means DeepSeek's own default is not disturbed."""
        assert "reasoning_effort" not in _payload(_deepseek())

    def test_accepted_nonzero_budget_is_ignored_and_logged(self, caplog):
        """AC-03: 512 (the portability value) is a logged no-op, never an error."""
        with caplog.at_level(logging.DEBUG, logger="yamlgraph.utils.llm_providers"):
            llm = _deepseek(thinking_budget=512)
        assert "reasoning_effort" not in _payload(llm)
        assert any(
            "512" in record.message and "deepseek" in record.message.lower()
            for record in caplog.records
        )

    def test_token_budget_still_rejected(self):
        """AC-04: DeepSeek has no token budget; >= 1024 must stay loud."""
        with pytest.raises(ValueError, match="thinking_budget is only supported"):
            _deepseek(thinking_budget=8000)

    def test_budgets_do_not_alias_in_cache(self):
        """AC-06: the three accepted budgets must not share one cached client."""
        omitted, zero, portable = (
            _deepseek(),
            _deepseek(thinking_budget=0),
            _deepseek(thinking_budget=512),
        )
        assert omitted is not zero
        assert zero is not portable
        assert omitted is not portable
