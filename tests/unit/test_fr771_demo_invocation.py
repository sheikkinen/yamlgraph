"""FR-771: the demo executes the manifest-declared tool through the registry.

Invocation-boundary artifact tests (judgement AC-03/AC-05/AC-08): the
committed demo graph has exactly one tool (the manifest), a tool_call node,
and args that resolve to real kwargs — proven by feeding the COMMITTED node
config through create_tool_call_node with a recording registry.

RED contract: the demo still runs a python wrapper node.
"""

from pathlib import Path

import pytest
import yaml

from yamlgraph.node_factory import create_tool_call_node

# FR-756: references committed examples/ artifacts
pytestmark = pytest.mark.process

DEMO_DIR = Path("examples/demos/shared-vision-tool")
DEMO_GRAPH = DEMO_DIR / "graph.yaml"


@pytest.fixture
def raw_graph():
    return yaml.safe_load(DEMO_GRAPH.read_text(encoding="utf-8"))


@pytest.mark.req("REQ-YG-574")
def test_manifest_is_the_only_tool(raw_graph):
    assert set(raw_graph["tools"]) == {"describe_image"}
    assert set(raw_graph["tools"]["describe_image"]) == {"manifest"}


@pytest.mark.req("REQ-YG-574")
def test_wrapper_module_is_deleted(raw_graph):
    assert not (DEMO_DIR / "nodes" / "demo.py").exists()
    assert "describe_demo_image" not in yaml.safe_dump(raw_graph)


@pytest.mark.req("REQ-YG-576")
def test_describe_node_is_tool_call(raw_graph):
    node = raw_graph["nodes"]["describe"]
    assert node["type"] == "tool_call"
    assert node["tool"] == "describe_image"


@pytest.mark.req("REQ-YG-576")
def test_committed_args_resolve_to_real_kwargs(raw_graph):
    """AC-05: fails if args collapse to {} or keep literal '{state.image}'."""
    received = {}

    def recorder(**kwargs):
        received.update(kwargs)
        return "ok"

    node_config = raw_graph["nodes"]["describe"]
    node = create_tool_call_node("describe", node_config, {"describe_image": recorder})
    result = node({"image": "examples/demos/shared-vision-tool/fixture.png"})

    assert result[node_config.get("state_key", "result")]["success"] is True
    assert received["image"] == "examples/demos/shared-vision-tool/fixture.png"
    assert "{state." not in str(received)
    assert received["provider"] == "google"
    assert received["instruction"]  # fixed demo instruction present


@pytest.mark.req("REQ-YG-574")
def test_demo_log_proves_tool_call_execution_and_success():
    """AC-07: committed log shows the registry path, not the wrapper."""
    log = (DEMO_DIR / "demo-output.log").read_text(encoding="utf-8")
    assert "type=tool_call" in log or "tool_call" in log
    assert "'success': True" in log or "success: true" in log.lower()
    assert "describe_demo_image" not in log
