"""Tests for FR-246: A2A Server Reference Documentation.

Verifies that reference/a2a-server.md exists with all 10 required sections,
reference/cli.md includes a2a subcommands, and reference/README.md links
to the new doc. Documentation-only FR — no Python code changes.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
A2A_SERVER_REF = REPO_ROOT / "reference" / "a2a-server.md"
CLI_REF = REPO_ROOT / "reference" / "cli.md"
REF_README = REPO_ROOT / "reference" / "README.md"
ARCHITECTURE = REPO_ROOT / "ARCHITECTURE.md"


# ---------------------------------------------------------------------------
# AC-1: REQ-YG-245 in ARCHITECTURE.md
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-245")
class TestArchitectureRequirement:
    """Verify REQ-YG-245 is registered in ARCHITECTURE.md."""

    def test_req_in_capabilities_table(self):
        content = ARCHITECTURE.read_text()
        assert (
            "REQ-YG-245" in content
        ), "ARCHITECTURE.md must include REQ-YG-245 in capabilities table"

    def test_req_description_exists(self):
        content = ARCHITECTURE.read_text()
        assert (
            "REQ-YG-245" in content and "a2a-server.md" in content
        ), "ARCHITECTURE.md must have REQ-YG-245 description referencing a2a-server.md"


# ---------------------------------------------------------------------------
# AC-2: reference/a2a-server.md exists with all 10 sections
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefExists:
    """Verify reference/a2a-server.md exists."""

    def test_file_exists(self):
        assert A2A_SERVER_REF.exists(), "reference/a2a-server.md must exist"


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefQuickstart:
    """Section 1: Quickstart."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_quickstart_heading(self):
        assert "## Quickstart" in self.content or "## Setup" in self.content

    def test_quickstart_pip_install(self):
        assert 'pip install' in self.content and 'a2a' in self.content

    def test_quickstart_serve_command(self):
        assert "yamlgraph a2a serve" in self.content

    def test_quickstart_agent_card_curl(self):
        assert "agent-card.json" in self.content

    def test_quickstart_message_send(self):
        assert "message/send" in self.content


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefCLI:
    """Section 2: CLI Commands."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_cli_commands_heading(self):
        assert "## CLI Commands" in self.content

    def test_serve_command_documented(self):
        assert "a2a serve" in self.content

    def test_card_command_documented(self):
        assert "a2a card" in self.content

    def test_port_flag(self):
        assert "--port" in self.content

    def test_host_flag(self):
        assert "--host" in self.content


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefAgentCard:
    """Section 3: Agent Card Generation."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_agent_card_heading(self):
        assert "## Agent Card" in self.content or "Agent Card Generation" in self.content

    def test_build_agent_card_referenced(self):
        assert "build_agent_card" in self.content

    def test_skills_mapping_documented(self):
        assert "skills" in self.content.lower()


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefMessageParsing:
    """Section 4: Message-to-State Mapping."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_message_parsing_heading(self):
        assert "Message" in self.content and "Mapping" in self.content

    def test_json_mode_documented(self):
        assert "JSON" in self.content

    def test_key_value_mode_documented(self):
        assert "key_value" in self.content or "key=value" in self.content

    def test_single_input_mode_documented(self):
        assert "single_input" in self.content or "single required var" in self.content.lower()

    def test_fallback_mode_documented(self):
        assert "fallback" in self.content.lower()

    def test_parse_a2a_message_referenced(self):
        assert "parse_a2a_message" in self.content


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefTaskLifecycle:
    """Section 5: Task Lifecycle."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_task_lifecycle_heading(self):
        assert "Task Lifecycle" in self.content

    def test_message_send_method(self):
        assert "message/send" in self.content

    def test_message_stream_method(self):
        assert "message/stream" in self.content

    def test_task_states_documented(self):
        for state in ["working", "completed", "failed"]:
            assert state in self.content, f"Task state '{state}' must be documented"


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefErrorMapping:
    """Section 6: Error Mapping."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_error_mapping_heading(self):
        assert "Error Mapping" in self.content

    def test_internal_error_documented(self):
        assert "InternalError" in self.content

    def test_invalid_params_documented(self):
        assert "InvalidParamsError" in self.content or "InvalidParams" in self.content

    def test_pipeline_error_types_documented(self):
        assert "LLM_ERROR" in self.content
        assert "VALIDATION_ERROR" in self.content


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefInterrupt:
    """Section 7: Interrupt / Human-in-Loop."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_interrupt_heading(self):
        assert "Interrupt" in self.content or "Human-in-Loop" in self.content

    def test_interrupt_marker_documented(self):
        assert "__interrupt__" in self.content

    def test_input_required_state(self):
        assert "input_required" in self.content or "input-required" in self.content


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefAuthentication:
    """Section 8: Authentication."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_authentication_heading(self):
        assert "Authentication" in self.content

    def test_reverse_proxy_mentioned(self):
        assert "reverse proxy" in self.content.lower() or "nginx" in self.content.lower()


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefDeployment:
    """Section 9: Deployment Patterns."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_deployment_heading(self):
        assert "Deployment" in self.content

    def test_standalone_pattern(self):
        assert "standalone" in self.content.lower() or "development" in self.content.lower()

    def test_container_pattern(self):
        assert "container" in self.content.lower() or "docker" in self.content.lower()


@pytest.mark.req("REQ-YG-245")
class TestA2AServerRefMCPRelationship:
    """Section 10: Relationship to MCP Server."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = A2A_SERVER_REF.read_text()

    def test_mcp_comparison_heading(self):
        assert "MCP" in self.content

    def test_transport_comparison(self):
        assert "stdio" in self.content and "HTTP" in self.content

    def test_shared_discovery(self):
        assert "discovery.py" in self.content or "discover_graphs" in self.content


# ---------------------------------------------------------------------------
# AC-3: Quickstart example verified against implementation
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-245")
class TestQuickstartMatchesImplementation:
    """Verify quickstart examples match the actual hello graph."""

    def test_hello_graph_vars_in_doc(self):
        """Doc quickstart must use variables from the hello graph."""
        hello = (REPO_ROOT / "examples" / "demos" / "hello" / "graph.yaml").read_text()
        content = A2A_SERVER_REF.read_text()
        # hello graph requires name and style
        assert "name" in hello and "style" in hello
        # doc must show these variables
        assert "name" in content and "style" in content


# ---------------------------------------------------------------------------
# AC-4: reference/cli.md updated
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-245")
class TestCliRefUpdated:
    """Verify reference/cli.md includes a2a subcommands."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = CLI_REF.read_text()

    def test_a2a_in_commands_overview(self):
        assert "a2a" in self.content, "cli.md must mention a2a commands"

    def test_a2a_serve_documented(self):
        assert "a2a serve" in self.content

    def test_a2a_card_documented(self):
        assert "a2a card" in self.content


# ---------------------------------------------------------------------------
# AC-5: reference/README.md links to a2a-server.md
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-245")
class TestRefReadmeUpdated:
    """Verify reference/README.md links to a2a-server.md."""

    def test_a2a_server_link(self):
        content = REF_README.read_text()
        assert (
            "a2a-server.md" in content
        ), "reference/README.md must link to a2a-server.md"
