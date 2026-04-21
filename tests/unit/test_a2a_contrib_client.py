"""Tests for A2A contrib client — FR-253.

The contrib client replaces the dedicated `type: a2a_call` node with a
`type: python` + `yamlgraph.contrib.a2a_client.send_a2a_message` pattern.
This reduces framework surface while preserving all A2A consumer functionality.
"""

import importlib.util
from contextvars import copy_context
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

_a2a_available = importlib.util.find_spec("a2a") is not None
_skip_no_a2a = pytest.mark.skipif(not _a2a_available, reason="a2a SDK not installed")

# =============================================================================
# send_a2a_message — core contract
# =============================================================================


class TestSendA2AMessage:
    """send_a2a_message(state) → dict with 'response' key."""

    @pytest.fixture
    def base_state(self):
        """Minimal state for send_a2a_message tests."""
        return {
            "agent_url": "http://localhost:8080",
            "message": "Hello agent",
        }

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_returns_dict_with_response_key(self, mock_httpx, base_state):
        """Function returns {'response': text}."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"text": "Agent says hello"}]}],
            },
        }
        mock_httpx.post.return_value = mock_response

        result = send_a2a_message(base_state)

        assert isinstance(result, dict)
        assert "response" in result
        assert result["response"] == "Agent says hello"

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_sends_jsonrpc_to_agent_url(self, mock_httpx, base_state):
        """Sends JSON-RPC SendMessage to agent_url."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
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

        send_a2a_message(base_state)

        call_args = mock_httpx.post.call_args
        assert call_args[0][0] == "http://localhost:8080"
        body = call_args[1]["json"]
        assert body["jsonrpc"] == "2.0"
        assert body["method"] == "SendMessage"
        assert body["params"]["message"]["parts"][0]["text"] == "Hello agent"

    @pytest.mark.req("REQ-YG-243")
    def test_missing_agent_url_raises(self):
        """Missing agent_url raises ValueError."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        with pytest.raises(ValueError, match="agent_url"):
            send_a2a_message({"message": "hello"})

    @pytest.mark.req("REQ-YG-243")
    def test_missing_message_raises(self):
        """Missing both message and message_template raises ValueError."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        with pytest.raises(ValueError, match="message"):
            send_a2a_message({"agent_url": "http://agent:8080"})

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_renders_message_template(self, mock_httpx):
        """message_template is rendered with Jinja2 from state."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
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

        state = {
            "agent_url": "http://agent:8080",
            "message_template": "Research {{ topic }}",
            "topic": "quantum computing",
        }
        send_a2a_message(state)

        body = mock_httpx.post.call_args[1]["json"]
        assert body["params"]["message"]["parts"][0]["text"] == (
            "Research quantum computing"
        )

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_timeout_from_state(self, mock_httpx, base_state):
        """timeout from state is passed to httpx."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
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

        base_state["timeout"] = "30"
        send_a2a_message(base_state)

        assert mock_httpx.post.call_args[1]["timeout"] == 30

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_default_timeout_120(self, mock_httpx, base_state):
        """Default timeout is 120 seconds."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
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

        send_a2a_message(base_state)

        assert mock_httpx.post.call_args[1]["timeout"] == 120

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_failed_task_raises(self, mock_httpx, base_state):
        """A2A task with failed state raises RuntimeError."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {"state": "failed"},
            },
        }
        mock_httpx.post.return_value = mock_response

        with pytest.raises(RuntimeError, match="A2A task failed"):
            send_a2a_message(base_state)

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_jsonrpc_error_raises(self, mock_httpx, base_state):
        """JSON-RPC error in response raises RuntimeError."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "error": {"code": -32600, "message": "Invalid request"},
        }
        mock_httpx.post.return_value = mock_response

        with pytest.raises(RuntimeError, match="JSON-RPC error"):
            send_a2a_message(base_state)

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_extracts_multiple_artifact_parts(self, mock_httpx, base_state):
        """Concatenates text from multiple artifact parts."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {"state": "completed"},
                "artifacts": [
                    {"parts": [{"text": "Part 1"}, {"text": "Part 2"}]},
                    {"parts": [{"text": "Part 3"}]},
                ],
            },
        }
        mock_httpx.post.return_value = mock_response

        result = send_a2a_message(base_state)
        assert result["response"] == "Part 1\nPart 2\nPart 3"

    @pytest.mark.req("REQ-YG-243")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_no_artifacts_falls_back_to_status(self, mock_httpx, base_state):
        """When no artifacts, extract text from status message."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {
                    "state": "completed",
                    "message": {
                        "role": "agent",
                        "parts": [{"text": "Done via status"}],
                    },
                },
            },
        }
        mock_httpx.post.return_value = mock_response

        result = send_a2a_message(base_state)
        assert result["response"] == "Done via status"


# =============================================================================
# Agent Card Discovery
# =============================================================================


def _make_agent_card_dict(
    *,
    skills: list[dict] | None = None,
    streaming: bool = False,
) -> dict:
    """Build a minimal Agent Card dict for testing."""
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
    """REQ-YG-250: Agent Card fetch via sync httpx.get(). Skipped without a2a SDK."""

    pytestmark = _skip_no_a2a

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_fetch_agent_card_well_known_url(self, mock_httpx):
        """Should GET {agent_url}/.well-known/agent.json."""
        from yamlgraph.contrib.a2a_client import _fetch_agent_card

        mock_response = MagicMock()
        mock_response.json.return_value = _make_agent_card_dict()
        mock_httpx.get.return_value = mock_response

        _fetch_agent_card("http://localhost:8080")

        url = mock_httpx.get.call_args[0][0]
        assert url == "http://localhost:8080/.well-known/agent.json"

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_fetch_strips_trailing_slash(self, mock_httpx):
        """Trailing slash stripped before building card URL."""
        from yamlgraph.contrib.a2a_client import _fetch_agent_card

        mock_response = MagicMock()
        mock_response.json.return_value = _make_agent_card_dict()
        mock_httpx.get.return_value = mock_response

        _fetch_agent_card("http://localhost:8080/")

        url = mock_httpx.get.call_args[0][0]
        assert url == "http://localhost:8080/.well-known/agent.json"

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_fetch_returns_agent_card(self, mock_httpx):
        """Should return parsed AgentCard object."""
        from a2a.types import AgentCard

        from yamlgraph.contrib.a2a_client import _fetch_agent_card

        mock_response = MagicMock()
        mock_response.json.return_value = _make_agent_card_dict(
            skills=[{"id": "search"}]
        )
        mock_httpx.get.return_value = mock_response

        card = _fetch_agent_card("http://localhost:8080")
        assert isinstance(card, AgentCard)


class TestAgentCardCaching:
    """REQ-YG-250: ContextVar-scoped Agent Card cache. Skipped without a2a SDK."""

    pytestmark = _skip_no_a2a

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.contrib.a2a_client._fetch_agent_card")
    def test_caches_by_url(self, mock_fetch):
        """Second call with same URL uses cache."""
        from yamlgraph.contrib.a2a_client import _get_agent_card

        card = _parse_agent_card(_make_agent_card_dict())
        mock_fetch.return_value = card

        result1 = _get_agent_card("http://agent:8080")
        result2 = _get_agent_card("http://agent:8080")

        assert result1 is result2
        mock_fetch.assert_called_once()

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.contrib.a2a_client._fetch_agent_card")
    def test_different_urls_fetch_separately(self, mock_fetch):
        """Different URLs cached independently."""
        from yamlgraph.contrib.a2a_client import _get_agent_card

        card = _parse_agent_card(_make_agent_card_dict())
        mock_fetch.return_value = card

        _get_agent_card("http://agent-a:8080")
        _get_agent_card("http://agent-b:8080")

        assert mock_fetch.call_count == 2

    @pytest.mark.req("REQ-YG-250")
    @patch("yamlgraph.contrib.a2a_client._fetch_agent_card")
    def test_context_var_isolation(self, mock_fetch):
        """Separate ContextVar contexts have independent caches."""
        from yamlgraph.contrib.a2a_client import _agent_card_cache, _get_agent_card

        card = _parse_agent_card(_make_agent_card_dict())
        mock_fetch.return_value = card

        def _run_in_fresh_context() -> None:
            _get_agent_card("http://agent:8080")

        ctx1 = copy_context()
        ctx2 = copy_context()
        ctx1.run(_agent_card_cache.set, {})
        ctx2.run(_agent_card_cache.set, {})
        ctx1.run(_run_in_fresh_context)
        ctx2.run(_run_in_fresh_context)

        assert mock_fetch.call_count == 2


# =============================================================================
# Skill Validation
# =============================================================================


class TestSkillValidation:
    """REQ-YG-251: Skill selection and validation. Skipped without a2a SDK."""

    pytestmark = _skip_no_a2a

    @pytest.mark.req("REQ-YG-251")
    def test_validate_skill_found(self):
        """Matching skill ID returns without error."""
        from yamlgraph.contrib.a2a_client import _validate_skill

        card = _parse_agent_card(
            _make_agent_card_dict(skills=[{"id": "search"}, {"id": "summarize"}])
        )
        _validate_skill("search", card)

    @pytest.mark.req("REQ-YG-251")
    def test_validate_skill_not_found_raises(self):
        """Missing skill raises ValueError listing available skills."""
        from yamlgraph.contrib.a2a_client import _validate_skill

        card = _parse_agent_card(
            _make_agent_card_dict(skills=[{"id": "search"}, {"id": "summarize"}])
        )
        with pytest.raises(ValueError, match="translate") as exc_info:
            _validate_skill("translate", card)

        msg = str(exc_info.value)
        assert "search" in msg
        assert "summarize" in msg

    @pytest.mark.req("REQ-YG-251")
    def test_validate_skill_empty_skills_raises(self):
        """Agent with no skills raises ValueError."""
        from yamlgraph.contrib.a2a_client import _validate_skill

        card = _parse_agent_card(_make_agent_card_dict(skills=[]))
        with pytest.raises(ValueError, match="no skills"):
            _validate_skill("anything", card)

    @pytest.mark.req("REQ-YG-251")
    @patch("yamlgraph.contrib.a2a_client._get_agent_card")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_send_with_skill_validates_against_card(self, mock_httpx, mock_get_card):
        """skill in state triggers Agent Card fetch + validation."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        card = _parse_agent_card(_make_agent_card_dict(skills=[{"id": "research"}]))
        mock_get_card.return_value = card

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"text": "result"}]}],
            },
        }
        mock_httpx.post.return_value = mock_response

        state = {
            "agent_url": "http://agent:8080",
            "message": "Do research",
            "skill": "research",
        }
        result = send_a2a_message(state)

        mock_get_card.assert_called_once_with("http://agent:8080")
        assert result["response"] == "result"

    @pytest.mark.req("REQ-YG-251")
    @patch("yamlgraph.contrib.a2a_client._get_agent_card")
    def test_send_with_invalid_skill_raises(self, mock_get_card):
        """Invalid skill ID raises ValueError."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        card = _parse_agent_card(_make_agent_card_dict(skills=[{"id": "search"}]))
        mock_get_card.return_value = card

        state = {
            "agent_url": "http://agent:8080",
            "message": "Translate this",
            "skill": "translate",
        }
        with pytest.raises(ValueError, match="translate"):
            send_a2a_message(state)


# =============================================================================
# Streaming Support
# =============================================================================


class TestStreamingSupport:
    """REQ-YG-252: Streaming via A2AClient in dedicated thread. Skipped without a2a SDK."""

    pytestmark = _skip_no_a2a

    @pytest.mark.req("REQ-YG-252")
    @patch("yamlgraph.contrib.a2a_client._get_agent_card")
    @patch("yamlgraph.contrib.a2a_client._send_streaming")
    def test_streaming_uses_streaming_transport(self, mock_stream, mock_get_card):
        """streaming: true uses _send_streaming."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        card = _parse_agent_card(_make_agent_card_dict(streaming=True))
        mock_get_card.return_value = card
        mock_stream.return_value = "streamed result"

        state = {
            "agent_url": "http://agent:8080",
            "message": "Generate report",
            "streaming": True,
        }
        result = send_a2a_message(state)

        mock_stream.assert_called_once()
        assert result["response"] == "streamed result"

    @pytest.mark.req("REQ-YG-252")
    @patch("yamlgraph.contrib.a2a_client._get_agent_card")
    def test_streaming_fails_when_agent_doesnt_support(self, mock_get_card):
        """streaming: true fails if agent doesn't support streaming."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        card = _parse_agent_card(_make_agent_card_dict(streaming=False))
        mock_get_card.return_value = card

        state = {
            "agent_url": "http://agent:8080",
            "message": "Stream this",
            "streaming": True,
        }
        with pytest.raises(ValueError, match="streaming"):
            send_a2a_message(state)

    @pytest.mark.req("REQ-YG-252")
    def test_extract_text_from_streaming_events(self):
        """Should extract text from streaming events."""
        from a2a.types import Artifact, Part, TaskArtifactUpdateEvent

        from yamlgraph.contrib.a2a_client import _extract_text_from_streaming_events

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
        """Empty event list returns empty string."""
        from yamlgraph.contrib.a2a_client import _extract_text_from_streaming_events

        assert _extract_text_from_streaming_events([]) == ""

    @pytest.mark.req("REQ-YG-252")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_non_streaming_uses_sync_transport(self, mock_httpx):
        """No streaming key uses sync httpx.post."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"text": "sync result"}]}],
            },
        }
        mock_httpx.post.return_value = mock_response

        state = {"agent_url": "http://agent:8080", "message": "Quick"}
        result = send_a2a_message(state)

        mock_httpx.post.assert_called_once()
        assert result["response"] == "sync result"


# =============================================================================
# V1 SDK compatibility
# =============================================================================


class TestV1PartFormat:
    """REQ-YG-245: V1 part format (no 'kind' discriminator)."""

    @pytest.mark.req("REQ-YG-245")
    @patch("yamlgraph.contrib.a2a_client.httpx")
    def test_payload_uses_v1_part_format(self, mock_httpx):
        """Parts must NOT contain 'kind' discriminator (v1.0)."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        mock_response = MagicMock()
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

        send_a2a_message({"agent_url": "http://localhost:8080", "message": "Hello"})

        body = mock_httpx.post.call_args[1]["json"]
        for part in body["params"]["message"]["parts"]:
            assert "kind" not in part


# =============================================================================
# Module exports
# =============================================================================


class TestContribExport:
    """send_a2a_message should be importable from contrib (REQ-YG-253)."""

    @pytest.mark.req("REQ-YG-253")
    def test_importable_from_contrib(self):
        """send_a2a_message importable from yamlgraph.contrib.a2a_client."""
        from yamlgraph.contrib.a2a_client import send_a2a_message

        assert callable(send_a2a_message)
