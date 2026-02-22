"""Integration tests for outcaller probe-recap (OC-005).

Tests REQ-YG-083, REQ-YG-084, REQ-YG-085.
"""

from pathlib import Path

import pytest

from yamlgraph.graph_loader import load_graph_config

GRAPH_PATH = Path("projects/outcaller/graph.yaml")


@pytest.mark.req("REQ-YG-083")
def test_outcaller_graph_compiles():
    """The outcaller graph should compile without errors."""
    config = load_graph_config(GRAPH_PATH)
    assert config.name == "outcaller-voice-demo"
    # Verify probe-recap nodes exist
    assert "parse_targets" in config.nodes
    assert "extract_answers" in config.nodes
    assert "check_missing" in config.nodes
    assert "generate_probe" in config.nodes
    assert "generate_recap" in config.nodes
    assert "analyze_recap_response" in config.nodes
    assert "apply_corrections" in config.nodes
    assert "generate_goodbye" in config.nodes


@pytest.mark.req("REQ-YG-084")
def test_outcaller_graph_has_targets_branching():
    """The graph should have conditional edges for targets-based routing."""
    config = load_graph_config(GRAPH_PATH)
    edges = config.edges

    # Find edges from initiate_call
    initiate_edges = [e for e in edges if e.get("from") == "initiate_call"]
    assert len(initiate_edges) == 2

    # One goes to parse_targets when targets != None
    parse_edge = next(
        (e for e in initiate_edges if e.get("to") == "parse_targets"), None
    )
    assert parse_edge is not None
    assert "targets != None" in parse_edge.get("condition", "")

    # One goes to generate_response when targets == None
    response_edge = next(
        (e for e in initiate_edges if e.get("to") == "generate_response"), None
    )
    assert response_edge is not None
    assert "targets == None" in response_edge.get("condition", "")


@pytest.mark.req("REQ-YG-085")
def test_outcaller_graph_has_recap_routing():
    """The graph should have conditional edges for recap confirmation loop."""
    config = load_graph_config(GRAPH_PATH)
    edges = config.edges

    # Find edges from analyze_recap_response
    recap_edges = [e for e in edges if e.get("from") == "analyze_recap_response"]
    assert len(recap_edges) >= 2

    # Check for confirmed condition
    confirmed_edge = next(
        (e for e in recap_edges if "is_confirmed == True" in e.get("condition", "")),
        None,
    )
    assert confirmed_edge is not None
    assert confirmed_edge.get("to") == "generate_goodbye"

    # Check for correction loop
    correction_edge = next(
        (e for e in recap_edges if "is_confirmed != True" in e.get("condition", "")),
        None,
    )
    assert correction_edge is not None
    assert correction_edge.get("to") == "apply_corrections"


@pytest.mark.req("REQ-YG-083")
def test_outcaller_new_state_keys():
    """The graph should define new state keys for probe-recap."""
    config = load_graph_config(GRAPH_PATH)
    state = config.raw_config.get("state", {})

    # New keys from OC-005
    assert "targets" in state
    assert "target_fields" in state
    assert "extracted" in state
    assert "missing_fields" in state
    assert "phase" in state
    assert "probe_count" in state
    assert "recap_analysis" in state
    assert "recap_count" in state


@pytest.mark.req("REQ-YG-084")
def test_outcaller_loop_limits_defined():
    """All nodes in cycles should have loop limits."""
    config = load_graph_config(GRAPH_PATH)
    limits = config.loop_limits

    # OC-005 nodes that are in cycles
    cyclic_nodes = [
        "generate_probe",
        "generate_recap",
        "generate_goodbye",
        "extract_answers",
        "check_missing",
        "analyze_recap_response",
        "apply_corrections",
    ]
    for node in cyclic_nodes:
        assert node in limits, f"Missing loop limit for {node}"


@pytest.mark.req("REQ-YG-085")
def test_generate_goodbye_skips_disabled():
    """generate_goodbye must have skip_if_exists: false to overwrite recap utterance.

    Bug: After recap confirmation, generate_goodbye was skipped because next_utterance
    already contained the recap question. The speak node then repeated the recap
    question in a loop until disconnect.

    Fix: generate_goodbye needs skip_if_exists: false so it always runs and
    overwrites next_utterance with the goodbye message containing [DONE].
    """
    config = load_graph_config(GRAPH_PATH)
    goodbye_node = config.nodes.get("generate_goodbye", {})

    # The node must explicitly disable skip_if_exists
    # Default is True, so we need False to overwrite the recap's next_utterance
    skip_if_exists = goodbye_node.get("skip_if_exists", True)
    assert skip_if_exists is False, (
        "generate_goodbye must have skip_if_exists: false to overwrite "
        "next_utterance from generate_recap"
    )


@pytest.mark.req("REQ-YG-085")
def test_generate_goodbye_node_executes_when_utterance_exists():
    """generate_goodbye must execute even when next_utterance already has a value.

    This tests the runtime behavior: when skip_if_exists=False, the node
    should execute and overwrite next_utterance regardless of existing value.
    """
    from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

    # With skip_if_exists=False, should NOT skip even when state has value
    state_with_value = {"next_utterance": "recap question from before"}
    assert _should_skip_if_exists(False, "next_utterance", state_with_value) is False

    # With skip_if_exists=True (the old default), WOULD skip
    assert _should_skip_if_exists(True, "next_utterance", state_with_value) is True


@pytest.mark.req("REQ-YG-085")
def test_generate_recap_writes_to_next_utterance():
    """generate_recap must write to next_utterance so speak can use it.

    Bug: generate_recap was writing to 'recap' state_key with an unsupported
    'on_success' mechanism to copy to next_utterance. The on_success feature
    doesn't exist, so next_utterance kept the old probe question.

    Fix: generate_recap should write directly to next_utterance.
    """
    config = load_graph_config(GRAPH_PATH)
    recap_node = config.nodes.get("generate_recap", {})

    # The node must write to next_utterance for speak to use
    state_key = recap_node.get("state_key")
    assert state_key == "next_utterance", (
        f"generate_recap must have state_key: next_utterance (got '{state_key}'). "
        "The 'on_success' mechanism doesn't exist in yamlgraph."
    )


@pytest.mark.req("REQ-YG-084")
def test_generate_probe_skips_disabled():
    """generate_probe must have skip_if_exists: false to generate new questions.

    Bug: generate_probe was skipped after extraction because next_utterance
    already had a value from the previous question. This caused the same
    greeting to repeat instead of asking about missing fields.

    Log evidence:
    > Node generate_probe skipped - next_utterance already in state

    Fix: generate_probe must have skip_if_exists: false.
    """
    config = load_graph_config(GRAPH_PATH)
    probe_node = config.nodes.get("generate_probe", {})

    # Must have skip_if_exists: false to regenerate on each loop
    skip_if_exists = probe_node.get("skip_if_exists")
    assert skip_if_exists is False, (
        f"generate_probe must have skip_if_exists: false (got '{skip_if_exists}'). "
        "Without this, the same greeting repeats instead of probing for missing fields."
    )
