"""FR-1148: ``thinking_budget`` reaches the Anthropic request payload in the form each model takes.

Witness tests: the rule (``anthropic_thinking._anthropic_thinking_off``) landed on ``main`` before these tests
(FR-1148 re-scope), so they assert the shipped behaviour at the payload, not a RED-then-GREEN change. The model
of every test is explicit, never resolved from ``ANTHROPIC_MODEL``. The mapping of AC-06 is Probe A of
``feature-requests/evidence/FR-1148-thinking-off-probe.md``.
"""

import pytest
from langchain_core.messages import HumanMessage

from yamlgraph.utils.llm_factory import clear_cache, create_llm

# Probe A, every id of models.list on 2026-10-25: the `thinking` form it accepts for "no thinking".
PROBE_A = {
    "claude-sonnet-5-5": {"type": "between_tools"},
    "claude-opus-5-5": None,
    "claude-fable-5-1": None,
    "claude-fable-5": None,
    "claude-haiku-5-5": {"type": "disabled"},
    "claude-sonnet-5": {"type": "disabled"},
    "claude-opus-5": {"type": "disabled"},
    "claude-opus-4-8": {"type": "disabled"},
    "claude-opus-4-7": {"type": "disabled"},
    "claude-sonnet-4-6": {"type": "disabled"},
    "claude-opus-4-6": {"type": "disabled"},
    "claude-opus-4-5-20251101": {"type": "disabled"},
    "claude-haiku-4-5-20251001": {"type": "disabled"},
    "claude-sonnet-4-5-20250929": {"type": "disabled"},
}


def _payload(llm):
    return llm._get_request_payload([HumanMessage("hi")])


@pytest.mark.req("REQ-YG-083")
class TestThinkingOffPayload:
    def setup_method(self):
        clear_cache()

    def test_sonnet_5_5_zero_sends_between_tools(self):
        """AC-01."""
        llm = create_llm(
            provider="anthropic", model="claude-sonnet-5-5", thinking_budget=0
        )
        assert _payload(llm)["thinking"] == {"type": "between_tools"}

    def test_haiku_5_5_zero_sends_disabled(self):
        """AC-02."""
        llm = create_llm(
            provider="anthropic", model="claude-haiku-5-5", thinking_budget=0
        )
        assert _payload(llm)["thinking"] == {"type": "disabled"}

    @pytest.mark.parametrize("model", ["claude-opus-5-5", "claude-fable-5-1"])
    def test_zero_raises_where_thinking_cannot_be_off(self, model):
        """AC-03: raised from create_llm, names the model, and nothing is cached."""
        for _ in range(2):
            with pytest.raises(ValueError, match="cannot be turned off") as err:
                create_llm(provider="anthropic", model=model, thinking_budget=0)
            assert model in str(err.value)

    def test_absent_leaves_the_payload_without_thinking(self):
        """AC-04."""
        llm = create_llm(
            provider="anthropic", model="claude-haiku-5-5", thinking_budget=None
        )
        assert llm.thinking is None
        assert "thinking" not in _payload(llm)

    def test_budget_enables_thinking_and_forces_temperature_one(self):
        """AC-05: FR-071 unchanged."""
        llm = create_llm(
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            thinking_budget=2048,
        )
        assert _payload(llm)["thinking"] == {"type": "enabled", "budget_tokens": 2048}
        assert llm.temperature == 1

    @pytest.mark.parametrize("model", sorted(PROBE_A))
    def test_probe_a_mapping(self, model):
        """AC-06: 1 x between_tools, 3 x raise, 10 x disabled."""
        want = PROBE_A[model]
        if want is None:
            with pytest.raises(ValueError, match="cannot be turned off"):
                create_llm(provider="anthropic", model=model, thinking_budget=0)
            return
        llm = create_llm(provider="anthropic", model=model, thinking_budget=0)
        assert _payload(llm)["thinking"] == want

    def test_probe_a_counts(self):
        """AC-06: the table is the probe's, not a subset."""
        values = list(PROBE_A.values())
        assert len(values) == 14
        assert values.count({"type": "between_tools"}) == 1
        assert values.count(None) == 3
        assert values.count({"type": "disabled"}) == 10
