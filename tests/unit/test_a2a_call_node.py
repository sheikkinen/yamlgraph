"""Tests for a2a_call node type — FR-240, FR-248.

a2a_call nodes send messages to external A2A agents and store the response
in graph state. This is the client/consumer side of A2A integration.

FR-248 extends with Agent Card discovery, skill selection, and streaming.
"""

from contextvars import copy_context
from typing import Any
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


# =============================================================================
# FR-248: Agent Card Discovery
# =============================================================================


def _make_agent_card_dict(
    *,
    skills: list[dict] | None = None,
    streaming: bool = False,
) -> dict:
    """Build a minimal Agent Card dict for testing."""
    # AgentSkill requires: id, name, description, tags
    full_skills = []
    for s in skills or []:
        full_skills.append(
            {
                "id": s["id"],
                "name": s.get("name", s["id"]),
                "description": s.get("description", f"Skill {s['id']}"),
                "tags": s.get("tags", []),
            }
        )
    return {
        "name": "Test Agent",
        "description": "A test agent",
        "version": "1.0.0",
        "capabilities": {"streaming": streaming},
        "skills": full_skills,
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
    }


def _parse_agent_card(data: dict) -> Any:
    """Parse a dict into an AgentCard protobuf object."""
    from a2a.types import AgentCard
    from google.protobuf.json_format import ParseDict

    return ParseDict(data, AgentCard())


class TestAgentCardFetching:
    """REQ-YG-250: Agent Card fetching via sync httpx.get()."""

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_fetch_agent_card_calls_well_known_url(self, mock_httpx):
        """Should GET {agent_url}/.well-known/agent.json."""
        from yamlgraph.node_factory.a2a_nodes import _fetch_agent_card

        mock_response = MagicMock()
        mock_response.json.return_value = _make_agent_card_dict()
        mock_httpx.get.return_value = mock_response

        _fetch_agent_card("http://localhost:8080")

        mock_httpx.get.assert_called_once()
        url = mock_httpx.get.call_args[0][0]
        assert url == "http://localhost:8080/.well-known/agent.json"

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_fetch_agent_card_strips_trailing_slash(self, mock_httpx):
        """Trailing slash on agent_url should be stripped."""
        from yamlgraph.node_factory.a2a_nodes import _fetch_agent_card

        mock_response = MagicMock()
        mock_response.json.return_value = _make_agent_card_dict()
        mock_httpx.get.return_value = mock_response

        _fetch_agent_card("http://localhost:8080/")

        url = mock_httpx.get.call_args[0][0]
        assert "//." not in url
        assert url == "http://localhost:8080/.well-known/agent.json"

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_fetch_agent_card_returns_agent_card(self, mock_httpx):
        """Should return a parsed AgentCard object."""
        from a2a.types import AgentCard

        from yamlgraph.node_factory.a2a_nodes import _fetch_agent_card

        mock_response = MagicMock()
        mock_response.json.return_value = _make_agent_card_dict(
            skills=[{"id": "search", "name": "Search"}]
        )
        mock_httpx.get.return_value = mock_response

        card = _fetch_agent_card("http://localhost:8080")
        assert isinstance(card, AgentCard)
        assert card.name == "Test Agent"

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_fetch_agent_card_raises_on_http_error(self, mock_httpx):
        """Should raise on HTTP errors (e.g. 404)."""
        from yamlgraph.node_factory.a2a_nodes import _fetch_agent_card

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_httpx.get.return_value = mock_response

        with pytest.raises(Exception, match="404"):
            _fetch_agent_card("http://localhost:8080")

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.node_factory.a2a_nodes.httpx")
    def test_fetch_agent_card_passes_timeout(self, mock_httpx):
        """Should pass timeout to httpx.get()."""
        from yamlgraph.node_factory.a2a_nodes import _fetch_agent_card

        mock_response = MagicMock()
        mock_response.json.return_value = _make_agent_card_dict()
        mock_httpx.get.return_value = mock_response

        _fetch_agent_card("http://localhost:8080", timeout=5)

        call_kwargs = mock_httpx.get.call_args[1]
        assert call_kwargs["timeout"] == 5


class TestAgentCardCaching:
    """REQ-YG-250: Agent Card caching with ContextVar isolation."""

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.node_factory.a2a_nodes._fetch_agent_card")
    def test_get_agent_card_caches_by_url(self, mock_fetch):
        """Second call with same URL should use cache, not fetch again."""
        from yamlgraph.node_factory.a2a_nodes import _get_agent_card

        card = _parse_agent_card(_make_agent_card_dict())
        mock_fetch.return_value = card

        # Call twice — should only fetch once
        result1 = _get_agent_card("http://agent:8080")
        result2 = _get_agent_card("http://agent:8080")

        assert result1 is result2
        mock_fetch.assert_called_once()

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.node_factory.a2a_nodes._fetch_agent_card")
    def test_get_agent_card_different_urls_fetch_separately(self, mock_fetch):
        """Different URLs should be cached independently."""
        from yamlgraph.node_factory.a2a_nodes import _get_agent_card

        card = _parse_agent_card(_make_agent_card_dict())
        mock_fetch.return_value = card

        _get_agent_card("http://agent-a:8080")
        _get_agent_card("http://agent-b:8080")

        assert mock_fetch.call_count == 2

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.node_factory.a2a_nodes._fetch_agent_card")
    def test_context_var_isolation_across_invocations(self, mock_fetch):
        """Separate ContextVar contexts should have independent caches."""
        from yamlgraph.node_factory.a2a_nodes import (
            _agent_card_cache,
            _get_agent_card,
        )

        card = _parse_agent_card(_make_agent_card_dict())
        mock_fetch.return_value = card

        # Create clean contexts without prior cache state
        def _run_in_fresh_context() -> None:
            _get_agent_card("http://agent:8080")

        ctx1 = copy_context()
        ctx2 = copy_context()

        # Clear cache in each context before running
        ctx1.run(_agent_card_cache.set, {})
        ctx2.run(_agent_card_cache.set, {})

        ctx1.run(_run_in_fresh_context)
        ctx2.run(_run_in_fresh_context)

        # Each context should fetch independently
        assert mock_fetch.call_count == 2


# =============================================================================
# FR-248: Skill Selection
# =============================================================================


class TestSkillValidation:
    """REQ-YG-251: Skill selection and validation."""

    @pytest.mark.req("REQ-YG-251")
    def test_validate_skill_found(self):
        """Skill ID matching a card skill should return without error."""
        from yamlgraph.node_factory.a2a_nodes import _validate_skill

        card = _parse_agent_card(
            _make_agent_card_dict(
                skills=[
                    {"id": "search", "name": "Search"},
                    {"id": "summarize", "name": "Summarize"},
                ]
            )
        )
        # Should not raise
        _validate_skill("search", card)

    @pytest.mark.req("REQ-YG-251")
    def test_validate_skill_not_found_raises_value_error(self):
        """Missing skill should raise ValueError listing available skills."""
        from yamlgraph.node_factory.a2a_nodes import _validate_skill

        card = _parse_agent_card(
            _make_agent_card_dict(
                skills=[
                    {"id": "search", "name": "Search"},
                    {"id": "summarize", "name": "Summarize"},
                ]
            )
        )
        with pytest.raises(ValueError, match="translate") as exc_info:
            _validate_skill("translate", card)

        # Error message should list available skills
        msg = str(exc_info.value)
        assert "search" in msg
        assert "summarize" in msg

    @pytest.mark.req("REQ-YG-251")
    def test_validate_skill_empty_skills_raises(self):
        """Agent with no skills should raise ValueError."""
        from yamlgraph.node_factory.a2a_nodes import _validate_skill

        card = _parse_agent_card(_make_agent_card_dict(skills=[]))
        with pytest.raises(ValueError, match="no skills"):
            _validate_skill("anything", card)

    @pytest.mark.req("REQ-YG-251")
    @patch("yamlgraph.node_factory.a2a_nodes._get_agent_card")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_with_skill_validates_against_card(self, mock_send, mock_get_card):
        """Node with skill field should fetch card and validate skill."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        card = _parse_agent_card(
            _make_agent_card_dict(skills=[{"id": "research", "name": "Research"}])
        )
        mock_get_card.return_value = card
        mock_send.return_value = "result text"

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Do research",
            "state_key": "result",
            "skill": "research",
        }
        state = {"current_step": "init", "_loop_counts": {}}

        node_fn = create_a2a_call_node("test_node", config)
        result = node_fn(state)

        mock_get_card.assert_called_once_with("http://agent:8080")
        assert result["result"] == "result text"

    @pytest.mark.req("REQ-YG-251")
    @patch("yamlgraph.node_factory.a2a_nodes._get_agent_card")
    def test_node_with_invalid_skill_raises(self, mock_get_card):
        """Node with skill not on card should raise ValueError."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        card = _parse_agent_card(
            _make_agent_card_dict(skills=[{"id": "search", "name": "Search"}])
        )
        mock_get_card.return_value = card

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Do translate",
            "state_key": "result",
            "skill": "translate",
        }
        state = {"current_step": "init", "_loop_counts": {}}

        node_fn = create_a2a_call_node("test_node", config)
        with pytest.raises(ValueError, match="translate"):
            node_fn(state)

    @pytest.mark.req("REQ-YG-251")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_node_without_skill_skips_card_fetch(self, mock_send):
        """Node without skill field should NOT fetch Agent Card."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        mock_send.return_value = "result text"

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Hello",
            "state_key": "result",
        }
        state = {"current_step": "init", "_loop_counts": {}}

        node_fn = create_a2a_call_node("test_node", config)
        result = node_fn(state)

        assert result["result"] == "result text"


# =============================================================================
# FR-248: Streaming Support
# =============================================================================


class TestStreamingSupport:
    """REQ-YG-252: Streaming via A2AClient in dedicated thread."""

    @pytest.mark.req("REQ-YG-252")
    @patch("yamlgraph.node_factory.a2a_nodes._get_agent_card")
    @patch("yamlgraph.node_factory.a2a_nodes._send_streaming")
    def test_streaming_node_uses_streaming_transport(self, mock_stream, mock_get_card):
        """streaming: true should use _send_streaming instead of _send_a2a_message."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        card = _parse_agent_card(_make_agent_card_dict(streaming=True))
        mock_get_card.return_value = card
        mock_stream.return_value = "streamed result"

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Generate report",
            "state_key": "report",
            "streaming": True,
        }
        state = {"current_step": "init", "_loop_counts": {}}

        node_fn = create_a2a_call_node("streamer", config)
        result = node_fn(state)

        mock_stream.assert_called_once()
        assert result["report"] == "streamed result"

    @pytest.mark.req("REQ-YG-252")
    @patch("yamlgraph.node_factory.a2a_nodes._get_agent_card")
    def test_streaming_fails_when_agent_doesnt_support(self, mock_get_card):
        """streaming: true should fail if card.capabilities.streaming is False."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        card = _parse_agent_card(_make_agent_card_dict(streaming=False))
        mock_get_card.return_value = card

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Stream this",
            "state_key": "result",
            "streaming": True,
        }
        state = {"current_step": "init", "_loop_counts": {}}

        node_fn = create_a2a_call_node("streamer", config)
        with pytest.raises(ValueError, match="streaming"):
            node_fn(state)

    @pytest.mark.req("REQ-YG-252")
    def test_extract_text_from_streaming_events(self):
        """Should extract text from collected streaming events."""
        from a2a.types import (
            Artifact,
            Part,
            TaskArtifactUpdateEvent,
        )

        from yamlgraph.node_factory.a2a_nodes import (
            _extract_text_from_streaming_events,
        )

        events = [
            TaskArtifactUpdateEvent(
                task_id="t1",
                context_id="c1",
                artifact=Artifact(
                    artifact_id="a1",
                    parts=[Part(text="Hello ")],
                ),
            ),
            TaskArtifactUpdateEvent(
                task_id="t1",
                context_id="c1",
                artifact=Artifact(
                    artifact_id="a2",
                    parts=[Part(text="World")],
                ),
            ),
        ]

        result = _extract_text_from_streaming_events(events)
        assert "Hello" in result
        assert "World" in result

    @pytest.mark.req("REQ-YG-252")
    def test_extract_text_from_empty_events(self):
        """Empty event list should return empty string."""
        from yamlgraph.node_factory.a2a_nodes import (
            _extract_text_from_streaming_events,
        )

        assert _extract_text_from_streaming_events([]) == ""

    @pytest.mark.req("REQ-YG-252")
    @patch("yamlgraph.node_factory.a2a_nodes._send_a2a_message")
    def test_non_streaming_node_uses_sync_transport(self, mock_send):
        """streaming: false (default) should use sync _send_a2a_message."""
        from yamlgraph.node_factory.a2a_nodes import create_a2a_call_node

        mock_send.return_value = "sync result"

        config = {
            "type": "a2a_call",
            "agent_url": "http://agent:8080",
            "message": "Quick task",
            "state_key": "result",
            "streaming": False,
        }
        state = {"current_step": "init", "_loop_counts": {}}

        node_fn = create_a2a_call_node("sync_node", config)
        result = node_fn(state)

        mock_send.assert_called_once()
        assert result["result"] == "sync result"


# =============================================================================
# FR-248: Schema — skill and streaming fields on NodeConfig
# =============================================================================


class TestNodeConfigSchemaFR248:
    """NodeConfig should accept skill and streaming fields."""

    @pytest.mark.req("REQ-YG-251")
    def test_node_config_accepts_skill_field(self):
        """NodeConfig should accept optional skill field."""
        from yamlgraph.models.graph_schema import NodeConfig

        config = NodeConfig(
            type="a2a_call",
            agent_url="http://agent:8080",
            message="Hello",
            state_key="result",
            skill="research",
        )
        assert config.skill == "research"

    @pytest.mark.req("REQ-YG-251")
    def test_node_config_skill_defaults_none(self):
        """skill field should default to None."""
        from yamlgraph.models.graph_schema import NodeConfig

        config = NodeConfig(
            type="a2a_call",
            agent_url="http://agent:8080",
            message="Hello",
            state_key="result",
        )
        assert config.skill is None

    @pytest.mark.req("REQ-YG-252")
    def test_node_config_accepts_streaming_field(self):
        """NodeConfig should accept optional streaming field."""
        from yamlgraph.models.graph_schema import NodeConfig

        config = NodeConfig(
            type="a2a_call",
            agent_url="http://agent:8080",
            message="Hello",
            state_key="result",
            streaming=True,
        )
        assert config.streaming is True

    @pytest.mark.req("REQ-YG-252")
    def test_node_config_streaming_defaults_none(self):
        """streaming field should default to None."""
        from yamlgraph.models.graph_schema import NodeConfig

        config = NodeConfig(
            type="a2a_call",
            agent_url="http://agent:8080",
            message="Hello",
            state_key="result",
        )
        assert config.streaming is None


# =============================================================================
# FR-248: Linter — W901, E904
# =============================================================================


class TestA2ACallLinterFR248:
    """REQ-YG-253: Linter checks W901 and E904."""

    @pytest.mark.req("REQ-YG-253")
    def test_w901_skill_advisory_warning(self):
        """W901: skill field on a2a_call should produce advisory warning."""
        from yamlgraph.linter.patterns.a2a import check_a2a_call_node_structure

        issues = check_a2a_call_node_structure(
            "my_node",
            {
                "type": "a2a_call",
                "agent_url": "http://agent:8080",
                "message": "Hello",
                "state_key": "result",
                "skill": "research",
            },
        )
        codes = [i.code for i in issues]
        assert "W901" in codes
        # Should be a warning, not error
        w901 = [i for i in issues if i.code == "W901"][0]
        assert w901.severity == "warning"

    @pytest.mark.req("REQ-YG-253")
    def test_no_w901_without_skill(self):
        """No W901 when skill field is absent."""
        from yamlgraph.linter.patterns.a2a import check_a2a_call_node_structure

        issues = check_a2a_call_node_structure(
            "my_node",
            {
                "type": "a2a_call",
                "agent_url": "http://agent:8080",
                "message": "Hello",
                "state_key": "result",
            },
        )
        codes = [i.code for i in issues]
        assert "W901" not in codes

    @pytest.mark.req("REQ-YG-253")
    def test_e904_streaming_on_non_a2a_call(self):
        """E904: streaming: true on non-a2a_call node should error."""
        from yamlgraph.linter.patterns.a2a import check_streaming_on_wrong_type

        issues = check_streaming_on_wrong_type(
            "my_node",
            {"type": "llm", "streaming": True, "prompt": "test", "state_key": "out"},
        )
        codes = [i.code for i in issues]
        assert "E904" in codes

    @pytest.mark.req("REQ-YG-253")
    def test_no_e904_on_a2a_call(self):
        """No E904 when streaming: true on a2a_call node."""
        from yamlgraph.linter.patterns.a2a import check_streaming_on_wrong_type

        issues = check_streaming_on_wrong_type(
            "my_node",
            {
                "type": "a2a_call",
                "streaming": True,
                "agent_url": "http://agent:8080",
                "message": "Hello",
                "state_key": "result",
            },
        )
        codes = [i.code for i in issues]
        assert "E904" not in codes

    @pytest.mark.req("REQ-YG-253")
    def test_no_e904_without_streaming(self):
        """No E904 when streaming is not set."""
        from yamlgraph.linter.patterns.a2a import check_streaming_on_wrong_type

        issues = check_streaming_on_wrong_type(
            "my_node",
            {"type": "llm", "prompt": "test", "state_key": "out"},
        )
        codes = [i.code for i in issues]
        assert "E904" not in codes

    @pytest.mark.req("REQ-YG-253")
    def test_e904_integrated_in_graph_check(self, tmp_path):
        """check_a2a_call_patterns should include E904 for all nodes."""
        from yamlgraph.linter.patterns.a2a import check_a2a_call_patterns

        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text(
            "name: test\n"
            "nodes:\n"
            "  bad_stream:\n"
            "    type: llm\n"
            "    prompt: test\n"
            "    state_key: out\n"
            "    streaming: true\n"
            "edges:\n"
            "  - from: START\n"
            "    to: bad_stream\n"
        )

        issues = check_a2a_call_patterns(graph_file)
        codes = [i.code for i in issues]
        assert "E904" in codes
