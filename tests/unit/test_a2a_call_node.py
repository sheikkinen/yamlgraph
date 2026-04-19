"""Tests for a2a_call node type — FR-240.

a2a_call nodes send messages to external A2A agents and store the response
in graph state. This is the client/consumer side of A2A integration.
"""

from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.constants import NodeType

# =============================================================================
# NodeType enum
# =============================================================================


class TestA2ACallNodeType:
    """A2A_CALL should be a valid NodeType constant."""

    @pytest.mark.req("REQ-YG-243")
    def test_a2a_call_in_node_type_enum(self):
        """A2A_CALL should be a valid NodeType."""
        assert NodeType.A2A_CALL == "a2a_call"

    @pytest.mark.req("REQ-YG-243")
    def test_a2a_call_does_not_require_prompt(self):
        """a2a_call nodes use inline message, not prompt files."""
        assert NodeType.requires_prompt("a2a_call") is False


# =============================================================================
# Node compiler registration
# =============================================================================


class TestA2ACallNodeCompilerRegistration:
    """a2a_call must be registered in NODE_TYPE_HANDLERS."""

    @pytest.mark.req("REQ-YG-243")
    def test_a2a_call_in_node_type_handlers(self):
        """a2a_call should be in the node type registry."""
        from yamlgraph.node_compiler import NODE_TYPE_HANDLERS

        assert "a2a_call" in NODE_TYPE_HANDLERS


# =============================================================================
# Linter: VALID_NODE_TYPES
# =============================================================================


class TestA2ACallLinterNodeType:
    """a2a_call must be a valid node type in the linter."""

    @pytest.mark.req("REQ-YG-243")
    def test_a2a_call_in_valid_node_types(self):
        """a2a_call should be in linter VALID_NODE_TYPES set."""
        from yamlgraph.linter.checks import VALID_NODE_TYPES

        assert "a2a_call" in VALID_NODE_TYPES


# =============================================================================
# Node factory: create_a2a_call_node
# =============================================================================


class TestCreateA2ACallNode:
    """Test the a2a_call node factory function."""

    @pytest.fixture
    def sample_state(self):
        """Minimal state for a2a_call node tests."""
        return {
            "thread_id": "test-a2a-001",
            "topic": "quantum computing",
            "current_step": "init",
            "error": None,
            "errors": [],
            "messages": [],
            "_loop_counts": {},
        }

    @pytest.fixture
    def basic_node_config(self):
        """Basic a2a_call node config."""
        return {
            "type": "a2a_call",
            "agent_url": "http://localhost:8080",
            "message": "Research {{ topic }}",
            "state_key": "research_result",
        }

    @pytest.mark.req("REQ-YG-243")
    def test_create_a2a_call_node_returns_callable(self, basic_node_config):
        """Factory should return a callable node function."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        node_fn = create_a2a_call_node("research", basic_node_config)
        assert callable(node_fn)

    @pytest.mark.req("REQ-YG-243")
    def test_node_function_name(self, basic_node_config):
        """Node function should have a descriptive __name__."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        node_fn = create_a2a_call_node("research", basic_node_config)
        assert "research" in node_fn.__name__

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_invocation_sends_message(
        self, mock_send, basic_node_config, sample_state
    ):
        """Node should render message template and send to agent."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        mock_send.return_value = "Research results about quantum computing"

        node_fn = create_a2a_call_node("research", basic_node_config)
        node_fn(sample_state)

        # Should have called _send_a2a_message with rendered message
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[1]["agent_url"] == "http://localhost:8080"
        assert "quantum computing" in call_args[1]["message"]

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_stores_result_in_state_key(
        self, mock_send, basic_node_config, sample_state
    ):
        """Result should be stored under the configured state_key."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        mock_send.return_value = "Agent response text"

        node_fn = create_a2a_call_node("research", basic_node_config)
        result = node_fn(sample_state)

        assert result["research_result"] == "Agent response text"
        assert result["current_step"] == "research"

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_updates_loop_counts(self, mock_send, basic_node_config, sample_state):
        """Node should track loop counts like other node types."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        mock_send.return_value = "response"

        node_fn = create_a2a_call_node("research", basic_node_config)
        result = node_fn(sample_state)

        assert result["_loop_counts"]["research"] == 1

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_renders_jinja2_template(self, mock_send, sample_state):
        """Message template should be rendered with Jinja2."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Analyze {{ topic }} in depth",
            "state_key": "analysis",
        }
        mock_send.return_value = "analyzed"

        node_fn = create_a2a_call_node("analyze", config)
        node_fn(sample_state)

        call_args = mock_send.call_args
        assert call_args[1]["message"] == "Analyze quantum computing in depth"

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_with_variables(self, mock_send, sample_state):
        """Variables templates should be resolved from state and available."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Research {{ extra_var }}",
            "state_key": "result",
            "variables": {"extra_var": "{state.topic}"},
        }
        mock_send.return_value = "done"

        node_fn = create_a2a_call_node("research", config)
        node_fn(sample_state)

        call_args = mock_send.call_args
        assert call_args[1]["message"] == "Research quantum computing"

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_timeout_passed(self, mock_send, sample_state):
        """Timeout from config should be passed to send function."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Quick task",
            "state_key": "result",
            "timeout": 30,
        }
        mock_send.return_value = "done"

        node_fn = create_a2a_call_node("quick", config)
        node_fn(sample_state)

        call_args = mock_send.call_args
        assert call_args[1]["timeout"] == 30

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_on_error_skip(self, mock_send, sample_state):
        """on_error: skip should catch errors and return None in state_key."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Unreliable task",
            "state_key": "result",
            "on_error": "skip",
        }
        mock_send.side_effect = RuntimeError("Connection refused")

        node_fn = create_a2a_call_node("unreliable", config)
        result = node_fn(sample_state)

        assert result["result"] is None
        assert len(result["errors"]) == 1

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_on_error_fail_raises(self, mock_send, sample_state):
        """on_error: fail (default) should raise the exception."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Critical task",
            "state_key": "result",
        }
        mock_send.side_effect = RuntimeError("Connection refused")

        node_fn = create_a2a_call_node("critical", config)
        with pytest.raises(RuntimeError, match="Connection refused"):
            node_fn(sample_state)


# =============================================================================
# A2A message sender
# =============================================================================


class TestA2AMessageSender:
    """Test the _send_a2a_message helper function."""

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_send_message_builds_jsonrpc_request(self, mock_httpx):
        """Should send a valid A2A JSON-RPC message/send request."""
        from yamlgraph.node_factory.a2a_nodes import _send_a2a_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {"state": "completed"},
                "artifacts": [
                    {
                        "parts": [{"text": "Agent says hello"}],
                    }
                ],
            },
        }
        mock_httpx.post.return_value = mock_response

        result = _send_a2a_message(
            agent_url="http://localhost:8080",
            message="Hello agent",
            timeout=60,
        )

        assert result == "Agent says hello"

        # Verify JSON-RPC structure
        call_args = mock_httpx.post.call_args
        body = call_args[1]["json"]
        assert body["jsonrpc"] == "2.0"
        assert body["method"] == "message/send"
        assert body["params"]["message"]["role"] == "user"

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_send_message_extracts_text_from_artifacts(self, mock_httpx):
        """Should extract and concatenate text from all artifact parts."""
        from yamlgraph.node_factory.a2a_nodes import _send_a2a_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {"state": "completed"},
                "artifacts": [
                    {
                        "parts": [
                            {"text": "Part 1"},
                            {"text": "Part 2"},
                        ],
                    },
                    {
                        "parts": [{"text": "Part 3"}],
                    },
                ],
            },
        }
        mock_httpx.post.return_value = mock_response

        result = _send_a2a_message(
            agent_url="http://agent:8080",
            message="Multi-part request",
            timeout=60,
        )

        assert result == "Part 1\nPart 2\nPart 3"

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_send_message_failed_task_raises(self, mock_httpx):
        """Should raise when the A2A task fails."""
        from yamlgraph.node_factory.a2a_nodes import _send_a2a_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {
                    "state": "failed",
                    "message": {
                        "role": "agent",
                        "parts": [{"text": "Internal error"}],
                    },
                },
            },
        }
        mock_httpx.post.return_value = mock_response

        with pytest.raises(RuntimeError, match="A2A task failed"):
            _send_a2a_message(
                agent_url="http://agent:8080",
                message="Failing request",
                timeout=60,
            )

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_send_message_http_error_raises(self, mock_httpx):
        """Should raise on HTTP errors."""
        from yamlgraph.node_factory.a2a_nodes import _send_a2a_message

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server error")
        mock_httpx.post.return_value = mock_response

        with pytest.raises(Exception, match="Server error"):
            _send_a2a_message(
                agent_url="http://agent:8080",
                message="Error request",
                timeout=60,
            )

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_send_message_no_artifacts_returns_status(self, mock_httpx):
        """When task completes with no artifacts, return status message text."""
        from yamlgraph.node_factory.a2a_nodes import _send_a2a_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {
                    "state": "completed",
                    "message": {
                        "role": "agent",
                        "parts": [{"text": "Done successfully"}],
                    },
                },
            },
        }
        mock_httpx.post.return_value = mock_response

        result = _send_a2a_message(
            agent_url="http://agent:8080",
            message="Status-only request",
            timeout=60,
        )

        assert result == "Done successfully"


# =============================================================================
# Linter patterns: a2a_call
# =============================================================================


class TestA2ACallLinterPatterns:
    """Linter should validate a2a_call node structure."""

    @pytest.mark.req("REQ-YG-243")
    def test_e901_missing_agent_url(self):
        """E901: a2a_call node missing agent_url."""
        from yamlgraph.linter.patterns.a2a import check_a2a_call_node_structure

        issues = check_a2a_call_node_structure(
            "my_node",
            {
                "type": "a2a_call",
                "message": "Hello",
                "state_key": "result",
            },
        )
        codes = [i.code for i in issues]
        assert "E901" in codes

    @pytest.mark.req("REQ-YG-243")
    def test_e902_missing_message(self):
        """E902: a2a_call node missing message."""
        from yamlgraph.linter.patterns.a2a import check_a2a_call_node_structure

        issues = check_a2a_call_node_structure(
            "my_node",
            {
                "type": "a2a_call",
                "agent_url": "http://agent:8080",
                "state_key": "result",
            },
        )
        codes = [i.code for i in issues]
        assert "E902" in codes

    @pytest.mark.req("REQ-YG-243")
    def test_e903_missing_state_key(self):
        """E903: a2a_call node missing state_key."""
        from yamlgraph.linter.patterns.a2a import check_a2a_call_node_structure

        issues = check_a2a_call_node_structure(
            "my_node",
            {
                "type": "a2a_call",
                "agent_url": "http://agent:8080",
                "message": "Hello",
            },
        )
        codes = [i.code for i in issues]
        assert "E903" in codes

    @pytest.mark.req("REQ-YG-243")
    def test_valid_a2a_call_node_no_issues(self):
        """Valid a2a_call node should produce no issues."""
        from yamlgraph.linter.patterns.a2a import check_a2a_call_node_structure

        issues = check_a2a_call_node_structure(
            "my_node",
            {
                "type": "a2a_call",
                "agent_url": "http://agent:8080",
                "message": "Hello {{ topic }}",
                "state_key": "result",
            },
        )
        assert issues == []

    @pytest.mark.req("REQ-YG-243")
    def test_check_a2a_call_patterns_scans_graph(self, tmp_path):
        """check_a2a_call_patterns should scan all nodes in a graph file."""
        from yamlgraph.linter.patterns.a2a import check_a2a_call_patterns

        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text(
            "name: test\n"
            "nodes:\n"
            "  broken:\n"
            "    type: a2a_call\n"
            "    state_key: result\n"
            "edges:\n"
            "  - from: START\n"
            "    to: broken\n"
        )

        issues = check_a2a_call_patterns(graph_file)
        codes = [i.code for i in issues]
        # Should report missing agent_url and message
        assert "E901" in codes
        assert "E902" in codes


# =============================================================================
# Node factory __init__ export
# =============================================================================


class TestA2ACallExport:
    """a2a_call factory should be importable from node_factory."""

    @pytest.mark.req("REQ-YG-243")
    def test_create_a2a_call_node_importable(self):
        """create_a2a_call_node should be importable from node_factory."""
        from yamlgraph.node_factory import create_a2a_call_node

        assert callable(create_a2a_call_node)


# =============================================================================
# FR-244: A2A SDK v1.0 compatibility — member-name discriminator
# =============================================================================


class TestA2AV1PartFormat:
    """A2A v1.0 uses member-name discriminator (no 'kind' field)."""

    @pytest.mark.req("REQ-YG-245")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_payload_uses_v1_part_format_no_kind(self, mock_httpx):
        """Payload parts must NOT contain 'kind' discriminator (v1.0 format)."""
        from yamlgraph.node_factory.a2a_nodes import _send_a2a_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"text": "ok"}]}],
            },
        }
        mock_httpx.post.return_value = mock_response

        _send_a2a_message(
            agent_url="http://localhost:8080",
            message="Hello",
            timeout=60,
        )

        body = mock_httpx.post.call_args[1]["json"]
        parts = body["params"]["message"]["parts"]
        for part in parts:
            assert "kind" not in part, f"v1.0 parts must not contain 'kind': {part}"

    @pytest.mark.req("REQ-YG-245")
    def test_extract_text_from_v1_artifact_parts(self):
        """Extraction works with v1.0 parts (key-presence, no 'kind')."""
        from yamlgraph.node_factory.a2a_nodes import _extract_text_from_result

        result = {
            "artifacts": [{"parts": [{"text": "Hello from v1"}]}],
            "status": {"state": "completed"},
        }
        assert _extract_text_from_result(result) == "Hello from v1"

    @pytest.mark.req("REQ-YG-245")
    def test_extract_text_from_v1_status_message(self):
        """Extraction from status message works with v1.0 parts."""
        from yamlgraph.node_factory.a2a_nodes import _extract_text_from_result

        result = {
            "status": {
                "state": "completed",
                "message": {"parts": [{"text": "Done via status"}]},
            },
        }
        assert _extract_text_from_result(result) == "Done via status"

    @pytest.mark.req("REQ-YG-245")
    def test_extract_text_skips_non_text_parts(self):
        """Parts without 'text' key are skipped."""
        from yamlgraph.node_factory.a2a_nodes import _extract_text_from_result

        result = {
            "artifacts": [
                {
                    "parts": [
                        {"data": {"key": "val"}},
                        {"text": "Only text"},
                    ],
                }
            ],
            "status": {"state": "completed"},
        }
        assert _extract_text_from_result(result) == "Only text"
