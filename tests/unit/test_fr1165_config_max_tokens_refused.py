"""FR-1165: graph-level config.max_tokens is refused at load.

The key was parsed (feature request 027) but never read by any LLM call;
`defaults.max_tokens` is the one graph-wide output-token setting.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from yamlgraph.compile.graph_loader import load_and_compile, load_graph_config

REPO = Path(__file__).resolve().parents[2]

GRAPH = """
version: "1.0"
name: fr1165
{extra}
nodes:
  ask:
    type: llm
    prompt: ask
{node_extra}    state_key: answer
edges:
  - from: START
    to: ask
  - from: ask
    to: END
"""


def _write(tmp_path: Path, extra: str = "", node_extra: str = "") -> Path:
    path = tmp_path / "graph.yaml"
    path.write_text(GRAPH.format(extra=extra, node_extra=node_extra), encoding="utf-8")
    return path


@pytest.mark.req("REQ-YG-060")
@pytest.mark.parametrize(
    "extra",
    [
        "config:\n  max_tokens: 4096",
        "config:\n  max_tokens: null",
        "defaults:\n  max_tokens: 100\nconfig:\n  max_tokens: 4096",
    ],
    ids=["value", "null", "with-defaults"],
)
def test_config_max_tokens_refused_at_load(tmp_path, extra):
    with pytest.raises(ValueError) as exc:
        load_graph_config(_write(tmp_path, extra))
    message = str(exc.value)
    assert "config.max_tokens" in message
    assert "defaults.max_tokens" in message


@pytest.mark.req("REQ-YG-060")
@pytest.mark.parametrize(
    ("extra", "node_extra", "expected"),
    [
        ("defaults:\n  max_tokens: 123", "", 123),
        ("defaults:\n  max_tokens: 123", "    max_tokens: 456\n", 456),
        ("", "", None),
    ],
    ids=["defaults", "node-override", "neither"],
)
def test_defaults_max_tokens_reaches_executor(tmp_path, extra, node_extra, expected):
    path = _write(tmp_path, extra, node_extra)
    with patch(
        "yamlgraph.node_factory.llm_nodes.execute_prompt", return_value="ok"
    ) as mock_execute:
        app = load_and_compile(path).compile()
        result = app.invoke({})
    assert result["answer"] == "ok"
    mock_execute.assert_called_once()
    assert mock_execute.call_args.kwargs["max_tokens"] == expected


@pytest.mark.req("REQ-YG-060")
def test_loaded_graph_has_no_max_tokens_attribute(tmp_path):
    config = load_graph_config(_write(tmp_path))
    assert not hasattr(config, "max_tokens")


@pytest.mark.req("REQ-YG-060")
def test_schema_does_not_advertise_config_max_tokens():
    schema = json.loads(
        (REPO / "yamlgraph" / "schemas" / "graph-v1.json").read_text(encoding="utf-8")
    )
    config = schema["properties"]["config"]
    assert "max_tokens" not in config["properties"]
    assert config["additionalProperties"] is True


@pytest.mark.req("REQ-YG-060")
def test_reference_documents_defaults_max_tokens_only():
    text = (REPO / "reference" / "graph-yaml.md").read_text(encoding="utf-8")
    config_section = text.split("### `config`", 1)[1].split("\n---", 1)[0]
    assert "max_tokens" not in config_section
    assert "| `max_tokens` | `int` | from defaults |" in text
    assert "defaults.max_tokens" in text
