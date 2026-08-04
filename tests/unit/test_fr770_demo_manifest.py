"""FR-770: the shared-vision demo is FR-768's committed manifest consumer.

AC-05: the round trip is pinned on a real repo artifact, not a tmp_path
fixture — the demo graph declares `describe_image` via `manifest:` only,
and the load-boundary translation reproduces the previous inline form.

RED contract: the demo graph currently declares the tool inline.
"""

from pathlib import Path

import pytest
import yaml

from yamlgraph.compile.graph_loader import load_graph_config

# FR-756: references committed examples/ artifacts
pytestmark = pytest.mark.process

DEMO_GRAPH = Path("examples/demos/shared-vision-tool/graph.yaml")
MANIFEST = Path("examples/shared/describe_image.tool.yaml")


@pytest.mark.req("REQ-YG-574")
def test_demo_declares_describe_image_via_manifest_only():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    entry = raw["tools"]["describe_image"]
    assert set(entry) == {"manifest"}, (
        f"describe_image must be declared via manifest only, got keys: "
        f"{sorted(entry)}"
    )


@pytest.mark.req("REQ-YG-574")
def test_manifest_file_is_committed_and_named_for_its_tool():
    assert MANIFEST.is_file()
    manifest = yaml.safe_load(MANIFEST.read_text())
    assert manifest["name"] == "describe_image"
    assert manifest["runtime"]["type"] == "python"


@pytest.mark.req("REQ-YG-574")
def test_translation_reproduces_previous_inline_form():
    config = load_graph_config(DEMO_GRAPH)
    translated = config.tools["describe_image"]
    assert translated["type"] == "python"
    assert translated["module"] == "examples.shared.vision_tool"
    assert translated["function"] == "describe_image"
    assert translated["description"] == "Describe an image: title, description, tags"
