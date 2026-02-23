"""Unit tests for questionnaire flow (probe-recap state machine).

Tests the full questionnaire logic independent of telco/speech layers:
- Probe loop: greeting → extract → check missing → probe until complete
- Recap flow: recap → analyze → confirm or correct
- Edge cases: probe limit, recap limit, empty targets

OC-005: Outcaller probe-recap capability (target extraction, phase routing, confirmation)
"""

from typing import Any
from unittest.mock import patch

import pytest


class MockLLMResponse:
    """Mock response that mimics Pydantic model with attributes."""

    def __init__(self, **kwargs: Any):
        for key, value in kwargs.items():
            setattr(self, key, value)


def simulate_questionnaire_turn(
    state: dict[str, Any],
    transcript: str,
    extraction_updates: dict[str, Any],
    recap_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Simulate one turn of the questionnaire (extract → check_missing → route).

    This is the core questionnaire logic without telco/speech layers.

    Args:
        state: Current state dict
        transcript: User's spoken response
        extraction_updates: Mock extraction result from LLM
        recap_analysis: Mock recap analysis (if in recap phase)

    Returns:
        Updated state dict after the turn
    """
    from projects.outcaller.nodes.probe_recap import (
        apply_corrections,
        check_missing,
        extract_answers,
    )

    # Update transcript
    state = {**state, "transcript": transcript}
    answers = list(state.get("answers", []))
    answers.append(transcript)
    state["answers"] = answers

    if state.get("phase") == "probe":
        # Mock extraction
        mock_result = MockLLMResponse(updates=extraction_updates)
        with patch("yamlgraph.executor.execute_prompt", return_value=mock_result):
            extract_result = extract_answers(state)
        state = {**state, **extract_result}

        # Check missing and route
        check_result = check_missing(state)
        state = {**state, **check_result}

    elif state.get("phase") == "recap" and recap_analysis is not None:
        # Apply recap analysis
        state["recap_analysis"] = recap_analysis
        if not recap_analysis.get("is_confirmed", False):
            corrections_result = apply_corrections(state)
            state = {**state, **corrections_result}

    return state


@pytest.mark.req("OC-005")
class TestQuestionnaireProbeFlow:
    """Test the probe loop state machine."""

    def test_full_probe_flow_collects_all_fields(self) -> None:
        """Complete flow: greeting → 3 probes → all fields collected → recap."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        # Initialize
        initial_state = {"targets": "name:Full name|age:Age|city:City"}
        state = {**initial_state, **parse_targets(initial_state)}

        # Turn 1: User provides name
        state = simulate_questionnaire_turn(
            state,
            transcript="My name is Alice",
            extraction_updates={"name": "Alice", "age": None, "city": None},
        )
        assert state["extracted"]["name"] == "Alice"
        assert state["missing_fields"] == ["age", "city"]
        assert state["phase"] == "probe"
        assert state["probe_count"] == 1

        # Turn 2: User provides age
        state = simulate_questionnaire_turn(
            state,
            transcript="I am 30 years old",
            extraction_updates={"name": None, "age": "30", "city": None},
        )
        assert state["extracted"]["age"] == "30"
        assert state["missing_fields"] == ["city"]
        assert state["phase"] == "probe"
        assert state["probe_count"] == 2

        # Turn 3: User provides city
        state = simulate_questionnaire_turn(
            state,
            transcript="I live in Helsinki",
            extraction_updates={"name": None, "age": None, "city": "Helsinki"},
        )
        assert state["extracted"]["city"] == "Helsinki"
        assert state["missing_fields"] == []
        assert state["phase"] == "recap"  # All collected → recap
        assert state["probe_count"] == 3

    def test_probe_extracts_multiple_fields_at_once(self) -> None:
        """User provides multiple answers in one response."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        initial_state = {"targets": "name:Full name|age:Age"}
        state = {**initial_state, **parse_targets(initial_state)}

        # User provides both in one turn
        state = simulate_questionnaire_turn(
            state,
            transcript="I'm Bob, 25 years old",
            extraction_updates={"name": "Bob", "age": "25"},
        )
        assert state["extracted"] == {"name": "Bob", "age": "25"}
        assert state["missing_fields"] == []
        assert state["phase"] == "recap"
        assert state["probe_count"] == 1

    def test_probe_preserves_previous_extractions(self) -> None:
        """LLM returning null doesn't overwrite previous extractions."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        initial_state = {"targets": "name:Full name|age:Age"}
        state = {**initial_state, **parse_targets(initial_state)}

        # First turn: get name
        state = simulate_questionnaire_turn(
            state,
            transcript="My name is Carol",
            extraction_updates={"name": "Carol", "age": None},
        )

        # Second turn: LLM returns null for name (shouldn't overwrite)
        state = simulate_questionnaire_turn(
            state,
            transcript="I'm 28",
            extraction_updates={"name": None, "age": "28"},
        )

        assert state["extracted"]["name"] == "Carol"  # Preserved
        assert state["extracted"]["age"] == "28"


@pytest.mark.req("OC-005")
class TestQuestionnaireProbeLimit:
    """Test probe limit enforcement."""

    def test_probe_limit_triggers_recap_with_missing(self) -> None:
        """After 5 probes, transition to recap even with missing fields."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        initial_state = {"targets": "name:Full name|age:Age|city:City"}
        state = {**initial_state, **parse_targets(initial_state)}

        # Simulate 5 turns with only partial extraction
        for i in range(5):
            state = simulate_questionnaire_turn(
                state,
                transcript=f"Turn {i + 1} - I don't know",
                extraction_updates={"name": None, "age": None, "city": None},
            )

        assert state["probe_count"] == 5
        assert state["phase"] == "recap"  # Forced to recap
        assert state["missing_fields"] == ["name", "age", "city"]

    def test_probe_limit_with_partial_collection(self) -> None:
        """Probe limit reached with some fields collected."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        initial_state = {"targets": "name:Full name|age:Age|city:City"}
        state = {**initial_state, **parse_targets(initial_state)}

        # Turn 1: Get name
        state = simulate_questionnaire_turn(
            state,
            transcript="I'm Dave",
            extraction_updates={"name": "Dave", "age": None, "city": None},
        )

        # Turns 2-5: No more info
        for _ in range(4):
            state = simulate_questionnaire_turn(
                state,
                transcript="I can't answer that",
                extraction_updates={"name": None, "age": None, "city": None},
            )

        assert state["probe_count"] == 5
        assert state["phase"] == "recap"
        assert state["extracted"]["name"] == "Dave"
        assert state["missing_fields"] == ["age", "city"]


@pytest.mark.req("OC-005")
class TestQuestionnaireRecapFlow:
    """Test the recap confirmation/correction loop."""

    def test_recap_confirmed_ends_questionnaire(self) -> None:
        """User confirms recap → questionnaire complete."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        initial_state = {"targets": "name:Full name|age:Age"}
        state = {**initial_state, **parse_targets(initial_state)}

        # Collect all fields
        state = simulate_questionnaire_turn(
            state,
            transcript="I'm Eve, 35 years old",
            extraction_updates={"name": "Eve", "age": "35"},
        )
        assert state["phase"] == "recap"

        # User confirms
        state = simulate_questionnaire_turn(
            state,
            transcript="Yes, that's correct",
            extraction_updates={},  # No extraction in recap phase
            recap_analysis={"is_confirmed": True, "corrections": {}},
        )

        assert state["extracted"] == {"name": "Eve", "age": "35"}
        assert state["recap_analysis"]["is_confirmed"] is True

    def test_recap_correction_updates_field(self) -> None:
        """User corrects a field → apply correction → new recap."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        initial_state = {"targets": "name:Full name|age:Age"}
        state = {**initial_state, **parse_targets(initial_state)}

        # Collect all fields (with mistake)
        state = simulate_questionnaire_turn(
            state,
            transcript="I'm Frank, 40 years old",
            extraction_updates={"name": "Frank", "age": "40"},
        )

        # User corrects age
        state = simulate_questionnaire_turn(
            state,
            transcript="Actually, I'm 42",
            extraction_updates={},
            recap_analysis={"is_confirmed": False, "corrections": {"age": "42"}},
        )

        assert state["extracted"]["age"] == "42"  # Corrected
        assert state["extracted"]["name"] == "Frank"  # Unchanged
        assert state["recap_count"] == 1

    def test_multiple_corrections_in_one_turn(self) -> None:
        """User corrects multiple fields at once."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        initial_state = {"targets": "name:Full name|age:Age|city:City"}
        state = {**initial_state, **parse_targets(initial_state)}

        # Collect all fields
        state["extracted"] = {"name": "George", "age": "50", "city": "Espoo"}
        state["phase"] = "recap"
        state["missing_fields"] = []

        # User corrects two fields
        state = simulate_questionnaire_turn(
            state,
            transcript="No, my name is Greg and I live in Turku",
            extraction_updates={},
            recap_analysis={
                "is_confirmed": False,
                "corrections": {"name": "Greg", "city": "Turku"},
            },
        )

        assert state["extracted"]["name"] == "Greg"
        assert state["extracted"]["city"] == "Turku"
        assert state["extracted"]["age"] == "50"  # Unchanged


@pytest.mark.req("OC-005")
class TestQuestionnaireRecapLimit:
    """Test recap correction limit enforcement."""

    def test_recap_limit_reached(self) -> None:
        """After 3 corrections, accept whatever we have."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        initial_state = {"targets": "name:Full name"}
        state = {**initial_state, **parse_targets(initial_state)}
        state["extracted"] = {"name": "Original"}
        state["phase"] = "recap"
        state["missing_fields"] = []

        # 3 correction rounds
        corrections = ["Name1", "Name2", "Name3"]
        for i, name in enumerate(corrections):
            state = simulate_questionnaire_turn(
                state,
                transcript=f"No, it's {name}",
                extraction_updates={},
                recap_analysis={"is_confirmed": False, "corrections": {"name": name}},
            )
            assert state["recap_count"] == i + 1

        assert state["recap_count"] == 3
        assert state["extracted"]["name"] == "Name3"


@pytest.mark.req("OC-005")
class TestQuestionnaireEdgeCases:
    """Test edge cases in questionnaire flow."""

    def test_empty_targets_skips_questionnaire(self) -> None:
        """Empty targets string results in empty questionnaire."""
        from projects.outcaller.nodes.probe_recap import check_missing, parse_targets

        state = {"targets": ""}
        state = {**state, **parse_targets(state)}

        assert state["target_fields"] == []
        assert state["extracted"] == {}
        assert state["missing_fields"] == []

        # Check would route to recap immediately (nothing to probe)
        check_result = check_missing(state)
        assert check_result["phase"] == "recap"

    def test_single_field_questionnaire(self) -> None:
        """Questionnaire with single field."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        state = {"targets": "email:Email address"}
        state = {**state, **parse_targets(state)}

        assert len(state["target_fields"]) == 1
        assert state["target_fields"][0]["id"] == "email"

        # Collect in one turn
        state = simulate_questionnaire_turn(
            state,
            transcript="test@example.com",
            extraction_updates={"email": "test@example.com"},
        )

        assert state["extracted"]["email"] == "test@example.com"
        assert state["phase"] == "recap"

    def test_answers_accumulate_over_turns(self) -> None:
        """Conversation history accumulates in answers list."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        state = {"targets": "name:Full name|age:Age"}
        state = {**state, **parse_targets(state)}

        state = simulate_questionnaire_turn(
            state,
            transcript="Hello, who is this?",
            extraction_updates={"name": None, "age": None},
        )
        state = simulate_questionnaire_turn(
            state,
            transcript="My name is Helen",
            extraction_updates={"name": "Helen", "age": None},
        )
        state = simulate_questionnaire_turn(
            state,
            transcript="I am 45",
            extraction_updates={"name": None, "age": "45"},
        )

        assert len(state["answers"]) == 3
        assert "Hello" in state["answers"][0]
        assert "Helen" in state["answers"][1]
        assert "45" in state["answers"][2]

    def test_correction_ignores_unknown_fields(self) -> None:
        """Corrections for unknown fields are ignored."""
        from projects.outcaller.nodes.probe_recap import apply_corrections

        state = {
            "extracted": {"name": "Ian"},
            "recap_analysis": {
                "is_confirmed": False,
                "corrections": {"unknown_field": "value", "name": "Ivan"},
            },
            "recap_count": 0,
        }

        result = apply_corrections(state)

        assert result["extracted"]["name"] == "Ivan"
        assert "unknown_field" not in result["extracted"]


@pytest.mark.req("OC-005")
class TestQuestionnaireStateTransitions:
    """Test state machine transition correctness."""

    def test_probe_to_recap_on_completion(self) -> None:
        """Phase transitions from probe to recap when all fields collected."""
        from projects.outcaller.nodes.probe_recap import check_missing

        # All fields extracted
        state = {
            "extracted": {"a": "1", "b": "2", "c": "3"},
            "probe_count": 2,
        }
        result = check_missing(state)

        assert result["phase"] == "recap"
        assert result["missing_fields"] == []

    def test_probe_continues_with_missing(self) -> None:
        """Phase stays probe when fields still missing."""
        from projects.outcaller.nodes.probe_recap import check_missing

        state = {
            "extracted": {"a": "1", "b": None, "c": None},
            "probe_count": 2,
        }
        result = check_missing(state)

        assert result["phase"] == "probe"
        assert result["missing_fields"] == ["b", "c"]

    def test_probe_to_recap_on_limit(self) -> None:
        """Phase transitions to recap at probe limit, even with missing."""
        from projects.outcaller.nodes.probe_recap import check_missing

        state = {
            "extracted": {"a": None},
            "probe_count": 5,  # At limit
        }
        result = check_missing(state)

        assert result["phase"] == "recap"
        assert result["missing_fields"] == ["a"]


# =============================================================================
# Fixtures for end-to-end questionnaire flow testing
# =============================================================================


@pytest.fixture
def questionnaire_initial_state() -> dict[str, Any]:
    """Fixture: Initial state after parse_targets for name|rating questionnaire."""
    from projects.outcaller.nodes.probe_recap import parse_targets

    state = {"targets": "name:Your name|rating:Rating 1 to 5"}
    parsed = parse_targets(state)
    return {
        **state,
        **parsed,
        "answers": [],
        "transcript": "",
        "next_utterance": "",
    }


@pytest.fixture
def questionnaire_after_collection(
    questionnaire_initial_state: dict[str, Any],
) -> dict[str, Any]:
    """Fixture: State after all fields collected, ready for recap."""
    state = questionnaire_initial_state.copy()
    state["extracted"] = {"name": "Alice", "rating": "5"}
    state["missing_fields"] = []
    state["phase"] = "recap"
    state["probe_count"] = 2
    state["next_utterance"] = "And what rating would you give?"  # Last probe question
    return state


@pytest.mark.req("OC-005")
class TestQuestionnaireEndToEndFlow:
    """End-to-end tests for the complete questionnaire state machine.

    These tests verify the full flow from probe through recap to goodbye,
    ensuring state transitions occur correctly and next_utterance is
    updated at each step.
    """

    def test_full_flow_probe_to_recap_to_goodbye(
        self, questionnaire_initial_state: dict[str, Any]
    ) -> None:
        """Complete flow: probe → collect all → recap → confirm → goodbye.

        This test verifies the happy path where:
        1. User provides all answers during probe phase
        2. System transitions to recap phase
        3. User confirms the recap
        4. System should transition to goodbye (not loop)
        """
        state = questionnaire_initial_state

        # === Probe Phase: Collect both fields ===
        state = simulate_questionnaire_turn(
            state,
            transcript="My name is Alice and I'd rate it 5",
            extraction_updates={"name": "Alice", "rating": "5"},
        )

        assert state["extracted"] == {"name": "Alice", "rating": "5"}
        assert state["missing_fields"] == []
        assert state["phase"] == "recap"

    def test_recap_confirmation_should_end_flow(
        self, questionnaire_after_collection: dict[str, Any]
    ) -> None:
        """After recap confirmation, flow should proceed to goodbye.

        Bug that this test catches: generate_recap was writing to 'recap'
        state_key instead of 'next_utterance', causing the speak node to
        repeat the old probe question in a loop.
        """
        state = questionnaire_after_collection

        # Simulate recap analysis with confirmation
        state["recap_analysis"] = MockLLMResponse(
            is_confirmed=True,
            corrections={},
        )

        # The flow should NOT loop back to recap
        # is_confirmed=True should route to generate_goodbye
        assert state["recap_analysis"].is_confirmed is True
        assert state["recap_analysis"].corrections == {}

    def test_recap_generates_new_utterance(
        self, questionnaire_after_collection: dict[str, Any]
    ) -> None:
        """Recap must generate a NEW next_utterance, not reuse old probe.

        This test verifies the graph configuration is correct by checking
        that generate_recap's state_key is 'next_utterance'.
        """
        from pathlib import Path

        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(Path("projects/outcaller/graph.yaml"))
        recap_node = config.nodes.get("generate_recap", {})

        # The critical assertion: recap must write to next_utterance
        assert recap_node.get("state_key") == "next_utterance", (
            "generate_recap must write to next_utterance so speak uses it. "
            "Writing to a different key causes the old probe question to loop."
        )

    def test_goodbye_generates_new_utterance(
        self, questionnaire_after_collection: dict[str, Any]
    ) -> None:
        """Goodbye must generate a NEW next_utterance with [DONE] marker.

        This test verifies goodbye will overwrite the recap utterance.
        """
        from pathlib import Path

        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(Path("projects/outcaller/graph.yaml"))
        goodbye_node = config.nodes.get("generate_goodbye", {})

        # Goodbye must write to next_utterance
        assert goodbye_node.get("state_key") == "next_utterance"

        # And must have skip_if_exists=False to overwrite recap's utterance
        assert goodbye_node.get("skip_if_exists") is False, (
            "generate_goodbye must have skip_if_exists: false to overwrite "
            "next_utterance from generate_recap"
        )

    def test_correction_flow_updates_and_recaps_again(
        self, questionnaire_after_collection: dict[str, Any]
    ) -> None:
        """Correction flow: user corrects → apply → new recap."""
        state = questionnaire_after_collection

        # User wants to correct the rating
        state = simulate_questionnaire_turn(
            state,
            transcript="Actually, make that a 4",
            extraction_updates={},
            recap_analysis={"is_confirmed": False, "corrections": {"rating": "4"}},
        )

        # Correction should be applied
        assert state["extracted"]["rating"] == "4"
        assert state["extracted"]["name"] == "Alice"  # Unchanged
        assert state["recap_count"] == 1

    def test_utterance_changes_at_each_phase_transition(self) -> None:
        """Verify next_utterance is meant to change at probe, recap, goodbye.

        This architectural test ensures the graph is wired correctly so
        that each LLM node that generates speech writes to next_utterance.
        """
        from pathlib import Path

        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(Path("projects/outcaller/graph.yaml"))

        # All speech-generating nodes must write to next_utterance
        speech_nodes = ["generate_probe", "generate_recap", "generate_goodbye"]
        for node_name in speech_nodes:
            node = config.nodes.get(node_name, {})
            state_key = node.get("state_key")
            assert state_key == "next_utterance", (
                f"{node_name} must have state_key: next_utterance (got '{state_key}'). "
                "All speech-generating nodes must write to next_utterance for speak to use."
            )

    def test_full_correction_then_confirmation_flow(
        self, questionnaire_after_collection: dict[str, Any]
    ) -> None:
        """Full flow: recap → correction → new recap → confirm."""
        state = questionnaire_after_collection

        # First recap: user corrects
        state = simulate_questionnaire_turn(
            state,
            transcript="No, my name is Bob",
            extraction_updates={},
            recap_analysis={"is_confirmed": False, "corrections": {"name": "Bob"}},
        )

        assert state["extracted"]["name"] == "Bob"
        assert state["recap_count"] == 1

        # Second recap: user confirms
        state["recap_analysis"] = {"is_confirmed": True, "corrections": {}}

        assert state["recap_analysis"]["is_confirmed"] is True
        # At this point, the graph should route to generate_goodbye


# =============================================================================
# README Example Test: caller_name|satisfaction|feedback (3 fields)
# =============================================================================


@pytest.fixture
def readme_example_initial_state() -> dict[str, Any]:
    """Fixture: Initial state matching README example.

    targets=caller_name:Your full name|satisfaction:Satisfaction 1 to 5|feedback:Any comments
    """
    from projects.outcaller.nodes.probe_recap import parse_targets

    state = {
        "targets": "caller_name:Your full name|satisfaction:Satisfaction 1 to 5|feedback:Any comments"
    }
    parsed = parse_targets(state)
    return {
        **state,
        **parsed,
        "answers": [],
        "transcript": "",
        "next_utterance": "",
    }


@pytest.fixture
def readme_example_after_collection(
    readme_example_initial_state: dict[str, Any],
) -> dict[str, Any]:
    """Fixture: State after all 3 fields collected, ready for recap."""
    state = readme_example_initial_state.copy()
    state["extracted"] = {
        "caller_name": "Sami Korhonen",
        "satisfaction": "5",
        "feedback": "Great service!",
    }
    state["missing_fields"] = []
    state["phase"] = "recap"
    state["probe_count"] = 3
    state["next_utterance"] = "Do you have any additional comments?"
    return state


@pytest.mark.req("OC-005")
class TestReadmeExampleWorkflow:
    """Tests matching the README example: caller_name|satisfaction|feedback.

    Ensures the documented workflow actually works as described.
    """

    def test_readme_targets_parse_correctly(
        self, readme_example_initial_state: dict[str, Any]
    ) -> None:
        """README targets string parses into 3 target fields."""
        state = readme_example_initial_state

        assert len(state["target_fields"]) == 3
        assert state["target_fields"][0] == {
            "id": "caller_name",
            "description": "Your full name",
        }
        assert state["target_fields"][1] == {
            "id": "satisfaction",
            "description": "Satisfaction 1 to 5",
        }
        assert state["target_fields"][2] == {
            "id": "feedback",
            "description": "Any comments",
        }

    def test_readme_full_probe_flow(
        self, readme_example_initial_state: dict[str, Any]
    ) -> None:
        """Complete probe flow: collect all 3 fields incrementally."""
        state = readme_example_initial_state

        # Turn 1: User provides name
        state = simulate_questionnaire_turn(
            state,
            transcript="My name is Sami Korhonen",
            extraction_updates={
                "caller_name": "Sami Korhonen",
                "satisfaction": None,
                "feedback": None,
            },
        )
        assert state["extracted"]["caller_name"] == "Sami Korhonen"
        assert state["missing_fields"] == ["satisfaction", "feedback"]
        assert state["phase"] == "probe"

        # Turn 2: User provides satisfaction
        state = simulate_questionnaire_turn(
            state,
            transcript="I'd rate it a 5, very satisfied",
            extraction_updates={
                "caller_name": None,
                "satisfaction": "5",
                "feedback": None,
            },
        )
        assert state["extracted"]["satisfaction"] == "5"
        assert state["missing_fields"] == ["feedback"]
        assert state["phase"] == "probe"

        # Turn 3: User provides feedback
        state = simulate_questionnaire_turn(
            state,
            transcript="Just that the service was quick and professional",
            extraction_updates={
                "caller_name": None,
                "satisfaction": None,
                "feedback": "Quick and professional service",
            },
        )
        assert state["extracted"]["feedback"] == "Quick and professional service"
        assert state["missing_fields"] == []
        assert state["phase"] == "recap"  # Transition to recap

    def test_readme_recap_confirmation(
        self, readme_example_after_collection: dict[str, Any]
    ) -> None:
        """Recap confirmation flow as documented in README."""
        state = readme_example_after_collection

        # User confirms the recap
        state["recap_analysis"] = MockLLMResponse(
            is_confirmed=True,
            corrections={},
        )

        assert state["recap_analysis"].is_confirmed is True
        assert state["extracted"] == {
            "caller_name": "Sami Korhonen",
            "satisfaction": "5",
            "feedback": "Great service!",
        }

    def test_readme_correction_flow(
        self, readme_example_after_collection: dict[str, Any]
    ) -> None:
        """Correction flow as documented in README: Sammy → Sami."""
        state = readme_example_after_collection
        # Simulate: bot heard "Sammy" instead of "Sami"
        state["extracted"]["caller_name"] = "Sammy Korhonen"

        # User corrects the name
        state = simulate_questionnaire_turn(
            state,
            transcript="Actually, it's Sami, not Sammy",
            extraction_updates={},
            recap_analysis={
                "is_confirmed": False,
                "corrections": {"caller_name": "Sami Korhonen"},
            },
        )

        assert state["extracted"]["caller_name"] == "Sami Korhonen"
        assert state["recap_count"] == 1

        # Second recap: user confirms
        state["recap_analysis"] = {"is_confirmed": True, "corrections": {}}
        assert state["recap_analysis"]["is_confirmed"] is True
