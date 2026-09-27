"""FR-1121 — the daily_digest example's ranker survives constrained decoding and fails loudly.

RED before GREEN. Since FR-998 (yamlgraph 0.5.25) an Anthropic ``llm`` node is
bound with ``method="json_schema"``; the SDK's strict transform rejects a
schema whose array items are untyped. ``stories: list[Any]`` is exactly that,
so the ranker died on its first call for nine consecutive unattended runs of
the standalone digest — and the run stayed green, because ``rank_stories``
declared no ``on_error`` and the framework's default handler let the graph
continue with an absent result.

Three witnesses (judgement AC-02..AC-05):

- the committed ranker prompt's model passes the Anthropic SDK transform
  (offline, no key; the oracle is the SDK's own function);
- ``rank_stories`` declares ``on_error: fail`` (shape — cheap, never
  sufficient);
- with the real example graph compiled and the ranker forced to raise, the
  ORIGINAL exception propagates from graph invocation and the downstream
  formatting node is never invoked (behaviour — the FR-1073 lesson that a
  correctly spelled key can sit where nothing reads it).
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = REPO / "examples" / "daily_digest"
PROMPT = EXAMPLE / "prompts" / "rank_stories.yaml"
GRAPH = EXAMPLE / "graph.yaml"


RANKER_FIELDS = {"title", "url", "summary", "relevance", "reason"}


def _ranker_model() -> type:
    """The committed prompt's model, whichever schema form it uses."""
    from yamlgraph.schema_loader import load_schema_from_yaml

    model = load_schema_from_yaml(PROMPT)
    assert model is not None, "rank_stories.yaml must declare an output schema"
    return model


@pytest.mark.req("REQ-YG-664")
def test_ranker_schema_survives_anthropic_constrained_transform() -> None:
    """Content witness (FR-1125): the transformed item schema still carries every story field.

    FR-1121's first witness only asserted the transform does not raise; `list[dict]`
    passed it and the model answered `[]`. The assertion is now preservation.
    """
    transform_schema = pytest.importorskip("anthropic").transform_schema
    json_schema = _ranker_model().model_json_schema()
    transformed = transform_schema(copy.deepcopy(json_schema))
    items = transformed["properties"]["stories"]["items"]
    if "$ref" in items:
        items = transformed["$defs"][items["$ref"].rsplit("/", 1)[-1]]
    assert set(items["properties"]) == RANKER_FIELDS
    assert set(items.get("required", [])) == RANKER_FIELDS
    assert items.get("additionalProperties") is False


@pytest.mark.req("REQ-YG-664")
def test_rank_stories_declares_on_error_fail() -> None:
    """Shape assertion: the ranker's policy is written where the compiler reads it."""
    config = yaml.safe_load(GRAPH.read_text(encoding="utf-8"))
    assert config["nodes"]["rank_stories"].get("on_error") == "fail"


class _RankerBoom(RuntimeError):
    """A distinct type so the test can prove identity, not just 'something raised'."""


def _stub_tools(calls: list[str]) -> Callable[..., Callable[[dict], dict]]:
    """Replace every Python tool of the example graph with a canned function.

    The map over ``articles_with_content`` dispatches zero items, so the only
    LLM call in the run is the ranker's.
    """
    canned: dict[str, dict[str, Any]] = {
        "fetch_sources": {"raw_articles": []},
        "filter_recent": {"filtered_articles": []},
        "fetch_article_content": {"articles_with_content": []},
        "format_email": {"digest_html": ""},
        "send_email": {"email_sent": False},
    }

    def fake_loader(config: Any, *, tool_name: str = "", **_: Any) -> Callable:
        update = canned[tool_name]

        def tool(state: dict) -> dict:
            calls.append(tool_name)
            return dict(update)

        return tool

    return fake_loader


@pytest.mark.req("REQ-YG-664")
def test_ranker_failure_propagates_and_formatting_never_runs() -> None:
    """Behavioural witness: node -> graph -> caller fail in order; nothing runs after."""
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    calls: list[str] = []
    fake_loader = _stub_tools(calls)

    def boom(*, prompt_name: str, **_: Any) -> Any:
        raise _RankerBoom(f"forced failure in {prompt_name}")

    with (
        patch(
            "yamlgraph.compile.graph_loader.load_python_function",
            side_effect=fake_loader,
        ),
        patch(
            "yamlgraph.tools.python_tool.load_python_function",
            side_effect=fake_loader,
        ),
        patch("yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=boom),
    ):
        app = compile_graph(load_graph_config(GRAPH)).compile()
        # RED on main: returns normally, ranked_stories absent, errors populated.
        with pytest.raises(_RankerBoom):
            app.invoke({"topics": ["AI"], "today": "2026-09-27"})

    assert "fetch_sources" in calls, "the run must have reached the graph at all"
    assert "format_email" not in calls, "formatting ran after a failed ranker"
    assert "send_email" not in calls
