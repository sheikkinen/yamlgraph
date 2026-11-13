"""FR-1155 AC-08: a real Anthropic cache write then read, metered by the token tracker.

Two ``claude-haiku-5-5`` calls share one nonce-prefixed ``cache: true`` system segment built by yamlgraph's own
``_build_system_message_from_segments``. A skip is owed, never a pass.
"""

import os
import uuid

import pytest
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from yamlgraph.executor_base import _build_system_message_from_segments
from yamlgraph.utils.llm_factory import create_llm
from yamlgraph.utils.token_tracker import TokenUsageCallbackHandler

load_dotenv()
MODEL = "claude-haiku-5-5"


def _stable_prefix() -> str:
    lines = [f"[fr1155 witness {uuid.uuid4().hex}] You are a terse rules engine."]
    lines += [
        f"Rule {i}: When a player declares action number {i}, check the inventory, "
        f"the location graph and the faction ledger, then answer with exactly one "
        f"short sentence naming the outcome and the cost."
        for i in range(1, 51)
    ]
    return "\n".join(lines)


@pytest.mark.req("REQ-YG-064")
@pytest.mark.req("REQ-YG-289")
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set (owed)"
)
def test_anthropic_system_segment_cache_read_live():
    system = _build_system_message_from_segments(
        [{"content": _stable_prefix(), "cache": True}], {}, None, "anthropic"
    )
    llm = create_llm(provider="anthropic", model=MODEL, max_tokens=32)
    tracker = TokenUsageCallbackHandler()
    config = {"callbacks": [tracker]}

    first = llm.invoke([system, HumanMessage(content="Action 3.")], config=config)
    after_first = tracker.summary()
    second = llm.invoke([system, HumanMessage(content="Action 7.")], config=config)
    after_second = tracker.summary()

    print("call 1 input_token_details:", first.usage_metadata["input_token_details"])
    print("after call 1:", after_first)
    print("call 2 input_token_details:", second.usage_metadata["input_token_details"])
    print("after call 2:", after_second)

    assert after_first["total_cache_write_tokens"] > 0
    assert after_first["total_cache_read_tokens"] == 0
    assert (
        after_second["total_cache_read_tokens"] > after_first["total_cache_read_tokens"]
    )
