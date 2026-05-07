"""RED acceptance tests for FR-346 shared FSM bridge extraction."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.req("REQ-YG-319")
def test_ac01_shared_fsm_package_path_exists() -> None:
    """AC-01: shared FSM bridge package exists under yamlgraph/utils/fsm."""
    assert (ROOT / "yamlgraph" / "utils" / "fsm").is_dir()


@pytest.mark.req("REQ-YG-319")
def test_ac02_shared_fsm_public_api_is_importable() -> None:
    """AC-02: shared module exports bridge API from yamlgraph.utils.fsm."""
    from yamlgraph.utils.fsm import (  # noqa: PLC0415
        YamlgraphAsyncAction,
        extract_event,
        json_safe,
        resolve_context_ref,
    )

    assert YamlgraphAsyncAction
    assert extract_event
    assert json_safe
    assert resolve_context_ref


@pytest.mark.req("REQ-YG-319")
def test_ac03_fsm_router_action_is_thin_wrapper() -> None:
    """AC-03: fsm-router action delegates to shared module import."""
    action_path = (
        ROOT / "examples" / "fsm-router" / "actions" / "yamlgraph_async_action.py"
    )
    source = action_path.read_text(encoding="utf-8")
    assert "from yamlgraph.utils.fsm" in source


@pytest.mark.req("REQ-YG-319")
def test_ac04_pattern_doc_points_to_shared_module() -> None:
    """AC-04: pattern doc names yamlgraph.utils.fsm as canonical bridge path."""
    doc_path = ROOT / "reference" / "patterns" / "fsm-as-conductor.md"
    source = doc_path.read_text(encoding="utf-8")
    assert "yamlgraph.utils.fsm" in source
