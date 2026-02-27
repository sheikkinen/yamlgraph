"""Tests for copilot pattern linter validations.

FR-105: Copilot Session Continuations.
"""

import pytest

from yamlgraph.linter.patterns.copilot import (
    check_copilot_node_structure,
)


@pytest.mark.req("REQ-YG-105")
class TestCopilotNodeStructure:
    """Test copilot node structural validation."""

    def test_valid_copilot_node_no_session_flags(self):
        """Should pass valid copilot node without session flags."""
        node_config = {
            "type": "copilot",
            "prompt": "task_prompt",
            "state_key": "result",
            "cli_flags": {
                "allow_all_tools": True,
            },
        }

        issues = check_copilot_node_structure("task", node_config)
        assert len(issues) == 0

    def test_valid_copilot_node_with_resume(self):
        """Should pass copilot node with only resume flag."""
        node_config = {
            "type": "copilot",
            "prompt": "task_prompt",
            "state_key": "result",
            "cli_flags": {
                "resume": "{state.prev_result.session_id}",
            },
        }

        issues = check_copilot_node_structure("task", node_config)
        assert len(issues) == 0

    def test_valid_copilot_node_with_continue_session(self):
        """Should pass copilot node with only continue_session flag."""
        node_config = {
            "type": "copilot",
            "prompt": "task_prompt",
            "state_key": "result",
            "cli_flags": {
                "continue_session": True,
            },
        }

        issues = check_copilot_node_structure("task", node_config)
        assert len(issues) == 0

    def test_error_both_resume_and_continue_session(self):
        """Should error when both resume and continue_session are set."""
        node_config = {
            "type": "copilot",
            "prompt": "task_prompt",
            "state_key": "result",
            "cli_flags": {
                "resume": "abc-123",
                "continue_session": True,
            },
        }

        issues = check_copilot_node_structure("task", node_config)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert issues[0].code == "E-COPILOT-RESUME"
        assert "mutually exclusive" in issues[0].message

    def test_warning_resume_without_session_id_pattern(self):
        """Should warn when resume expression doesn't reference session_id."""
        node_config = {
            "type": "copilot",
            "prompt": "task_prompt",
            "state_key": "result",
            "cli_flags": {
                "resume": "{state.prev_result.output}",  # Wrong path
            },
        }

        issues = check_copilot_node_structure("task", node_config)
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].code == "W-COPILOT-SESSION"
        assert "session_id" in issues[0].message

    def test_no_warning_for_literal_resume_value(self):
        """Should not warn when resume is a literal UUID (not state expression)."""
        node_config = {
            "type": "copilot",
            "prompt": "task_prompt",
            "state_key": "result",
            "cli_flags": {
                "resume": "abc-123-def-456",  # Literal value
            },
        }

        issues = check_copilot_node_structure("task", node_config)
        assert len(issues) == 0

    def test_no_cli_flags_is_valid(self):
        """Should pass when cli_flags is not specified."""
        node_config = {
            "type": "copilot",
            "prompt": "task_prompt",
            "state_key": "result",
        }

        issues = check_copilot_node_structure("task", node_config)
        assert len(issues) == 0
