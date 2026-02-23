"""Integration tests for outcaller user refusal handling (OC-007).

Tests refusal detection and graceful exit routing.
Follows TDD: tests written BEFORE implementation.
"""

from pathlib import Path

import pytest
import yaml

from yamlgraph.graph_loader import load_graph_config

GRAPH_PATH = Path("projects/outcaller/graph.yaml")
PROMPTS_DIR = Path("projects/outcaller/prompts")


# =============================================================================
# OC-007: State Key Tests
# =============================================================================


@pytest.mark.req("REQ-YG-086")
def test_user_refused_state_key_exists():
    """The graph must have user_refused state key for refusal tracking.

    OC-007: When caller refuses ("I'm not interested", "take me off your list"),
    we need to track this so routing can exit gracefully.
    """
    config = load_graph_config(GRAPH_PATH)
    state = config.raw_config.get("state", {})
    assert "user_refused" in state, (
        "Missing user_refused state key. "
        "OC-007 requires tracking when caller declines to participate."
    )


# =============================================================================
# OC-007: Prompt Schema Tests
# =============================================================================


@pytest.mark.req("REQ-YG-086")
def test_extract_answers_schema_has_user_refused():
    """extract_answers prompt must return user_refused field.

    OC-007: The extraction LLM should detect refusal alongside extraction.
    """
    prompt_path = PROMPTS_DIR / "extract_answers.yaml"
    assert prompt_path.exists(), f"Prompt not found: {prompt_path}"

    with open(prompt_path) as f:
        prompt = yaml.safe_load(f)

    schema = prompt.get("schema", {})
    fields = schema.get("fields", {})

    assert "user_refused" in fields, (
        "extract_answers.yaml schema missing user_refused field. "
        "OC-007: extraction must detect caller refusal."
    )

    # Verify it's a boolean
    user_refused = fields["user_refused"]
    assert user_refused.get("type") == "bool", "user_refused field must be type bool"


@pytest.mark.req("REQ-YG-086")
def test_analyze_recap_response_schema_has_user_refused():
    """analyze_recap_response prompt must return user_refused field.

    OC-007: The recap analysis LLM should detect refusal during confirmation.
    """
    prompt_path = PROMPTS_DIR / "analyze_recap_response.yaml"
    assert prompt_path.exists(), f"Prompt not found: {prompt_path}"

    with open(prompt_path) as f:
        prompt = yaml.safe_load(f)

    schema = prompt.get("schema", {})
    fields = schema.get("fields", {})

    assert "user_refused" in fields, (
        "analyze_recap_response.yaml schema missing user_refused field. "
        "OC-007: recap analysis must detect caller refusal."
    )

    # Verify it's a boolean
    user_refused = fields["user_refused"]
    assert user_refused.get("type") == "bool", "user_refused field must be type bool"


# =============================================================================
# OC-007: Graceful Exit Prompt Tests
# =============================================================================


@pytest.mark.req("REQ-YG-086")
def test_goodbye_refused_prompt_exists():
    """A graceful exit prompt must exist for refusal cases.

    OC-007: When caller refuses, we need a polite goodbye that differs
    from the standard completion goodbye.
    """
    prompt_path = PROMPTS_DIR / "goodbye_refused.yaml"
    assert prompt_path.exists(), (
        "Missing goodbye_refused.yaml prompt. "
        "OC-007: need polite exit message when caller declines."
    )

    with open(prompt_path) as f:
        prompt = yaml.safe_load(f)

    # Must have system or user template
    assert prompt.get("system") or prompt.get(
        "user"
    ), "goodbye_refused.yaml must have system or user template"


@pytest.mark.req("REQ-YG-086")
def test_generate_goodbye_refused_node_exists():
    """Graph must have generate_goodbye_refused node.

    OC-007: Node to generate refusal goodbye message.
    """
    config = load_graph_config(GRAPH_PATH)
    assert "generate_goodbye_refused" in config.nodes, (
        "Missing generate_goodbye_refused node. "
        "OC-007: need node to generate polite exit on refusal."
    )

    node = config.nodes["generate_goodbye_refused"]
    assert (
        node.get("prompt") == "goodbye_refused"
    ), "generate_goodbye_refused must use goodbye_refused prompt"
    assert (
        node.get("state_key") == "next_utterance"
    ), "generate_goodbye_refused must write to next_utterance for speak"


# =============================================================================
# OC-007: Routing Tests
# =============================================================================


@pytest.mark.req("REQ-YG-086")
def test_extract_answers_has_refusal_routing():
    """extract_answers must route to goodbye_refused on refusal.

    OC-007: When user_refused detected during probe phase, exit gracefully.
    """
    config = load_graph_config(GRAPH_PATH)
    edges = config.edges

    # Find edges from extract_answers
    extract_edges = [e for e in edges if e.get("from") == "extract_answers"]

    # Must have edge to generate_goodbye_refused on refusal
    refusal_edge = next(
        (e for e in extract_edges if e.get("to") == "generate_goodbye_refused"),
        None,
    )
    assert refusal_edge is not None, (
        "Missing edge from extract_answers to generate_goodbye_refused. "
        "OC-007: extraction must route to graceful exit on refusal."
    )
    assert "user_refused" in refusal_edge.get(
        "condition", ""
    ), "Refusal edge must check user_refused condition"


@pytest.mark.req("REQ-YG-086")
def test_analyze_recap_has_refusal_routing():
    """analyze_recap_response must route to goodbye_refused on refusal.

    OC-007: When user_refused detected during recap phase, exit gracefully.
    """
    config = load_graph_config(GRAPH_PATH)
    edges = config.edges

    # Find edges from analyze_recap_response
    recap_edges = [e for e in edges if e.get("from") == "analyze_recap_response"]

    # Must have edge to generate_goodbye_refused on refusal
    refusal_edge = next(
        (e for e in recap_edges if e.get("to") == "generate_goodbye_refused"),
        None,
    )
    assert refusal_edge is not None, (
        "Missing edge from analyze_recap_response to generate_goodbye_refused. "
        "OC-007: recap analysis must route to graceful exit on refusal."
    )
    assert "user_refused" in refusal_edge.get(
        "condition", ""
    ), "Refusal edge must check user_refused condition"


@pytest.mark.req("REQ-YG-086")
def test_goodbye_refused_routes_to_speak():
    """generate_goodbye_refused must route to speak node.

    OC-007: Refusal goodbye must be spoken before call ends.
    """
    config = load_graph_config(GRAPH_PATH)
    edges = config.edges

    # Find edge from generate_goodbye_refused
    goodbye_edge = next(
        (e for e in edges if e.get("from") == "generate_goodbye_refused"),
        None,
    )
    assert goodbye_edge is not None, "Missing edge from generate_goodbye_refused"
    assert (
        goodbye_edge.get("to") == "speak"
    ), "generate_goodbye_refused must route to speak"
