"""Unit tests for interrupt node functionality.

TDD tests for 001: Interrupt Node feature.
Tests create_interrupt_node() and interrupt YAML handling.
"""

from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.constants import NodeType
from yamlgraph.node_factory import create_interrupt_node


class TestNodeTypeInterrupt:
    """Test NodeType.INTERRUPT constant exists."""

    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_constant_exists(self):
        """NodeType should have INTERRUPT constant."""
        assert hasattr(NodeType, "INTERRUPT")
        assert NodeType.INTERRUPT == "interrupt"

    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_not_requires_prompt(self):
        """Interrupt nodes don't require prompt (can use message)."""
        assert not NodeType.requires_prompt("interrupt")


class TestCreateInterruptNode:
    """Test create_interrupt_node() factory function."""

    @pytest.mark.req("REQ-YG-021")
    def test_create_interrupt_node_with_static_message(self):
        """Interrupt node with static message should work."""
        config = {
            "message": "What is your name?",
            "resume_key": "user_name",
        }
        prepare_fn, interrupt_fn = create_interrupt_node("ask_name", config)
        assert callable(prepare_fn)
        assert callable(interrupt_fn)

    @pytest.mark.req("REQ-YG-021")
    def test_create_interrupt_node_with_prompt(self):
        """Interrupt node with prompt should work."""
        config = {
            "prompt": "dialogue/generate_question",
            "state_key": "pending_question",
            "resume_key": "user_response",
        }
        prepare_fn, interrupt_fn = create_interrupt_node("ask_dynamic", config)
        assert callable(prepare_fn)
        assert callable(interrupt_fn)

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_calls_native_interrupt(self, mock_interrupt):
        """Node should call LangGraph's native interrupt()."""
        mock_interrupt.return_value = "Alice"  # Simulates resume value

        config = {"message": "What is your name?"}
        prepare_fn, interrupt_fn = create_interrupt_node("ask_name", config)

        state = {}
        prep_result = prepare_fn(state)
        state.update(prep_result)
        result = interrupt_fn(state)

        mock_interrupt.assert_called_once_with("What is your name?")
        assert result["user_input"] == "Alice"

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_stores_payload_in_state_key(self, mock_interrupt):
        """Payload should be stored in state_key by prepare_fn."""
        mock_interrupt.return_value = "blue"

        config = {
            "message": "What is your favorite color?",
            "state_key": "pending_question",
            "resume_key": "color_choice",
        }
        prepare_fn, interrupt_fn = create_interrupt_node("ask_color", config)

        state = {}
        prep_result = prepare_fn(state)
        assert prep_result["pending_question"] == "What is your favorite color?"

        state.update(prep_result)
        result = interrupt_fn(state)
        assert result["color_choice"] == "blue"

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_idempotency_skips_prompt_on_resume(self, mock_interrupt):
        """When state_key exists, should not re-execute prompt."""
        mock_interrupt.return_value = "resumed_value"

        config = {
            "prompt": "expensive/llm_call",
            "state_key": "pending_question",
            "resume_key": "user_response",
        }
        prepare_fn, interrupt_fn = create_interrupt_node("ask_dynamic", config)

        # Simulate resume: state already has the payload
        state = {"pending_question": "Previously generated question"}

        with patch("yamlgraph.executor.execute_prompt") as mock_prompt:
            prep_result = prepare_fn(state)

            # execute_prompt should NOT be called (idempotency)
            mock_prompt.assert_not_called()
            assert prep_result["pending_question"] == "Previously generated question"

            state.update(prep_result)
            result = interrupt_fn(state)

            mock_interrupt.assert_called_once_with("Previously generated question")
            assert result["user_response"] == "resumed_value"

    @patch("yamlgraph.executor.execute_prompt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_with_prompt_calls_execute_prompt(self, mock_execute_prompt):
        """First execution with prompt should call execute_prompt in prepare."""
        mock_execute_prompt.return_value = "Generated question from LLM"

        config = {
            "prompt": "dialogue/generate_question",
            "state_key": "pending_question",
            "resume_key": "user_response",
        }
        prepare_fn, interrupt_fn = create_interrupt_node("ask_dynamic", config)

        state = {"context": "some context"}
        prep_result = prepare_fn(state)

        mock_execute_prompt.assert_called_once()
        assert prep_result["pending_question"] == "Generated question from LLM"

        # Verify interrupt_fn reads the committed payload
        state.update(prep_result)
        with patch("langgraph.types.interrupt", return_value="user answer") as m:
            result = interrupt_fn(state)
            m.assert_called_once_with("Generated question from LLM")
            assert result["user_response"] == "user answer"

    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_sets_current_step(self):
        """Both prepare and interrupt set current_step."""
        config = {"message": "Question?"}
        prepare_fn, interrupt_fn = create_interrupt_node("my_node", config)

        prep_result = prepare_fn({})
        assert prep_result["current_step"] == "my_node"

        state = dict(prep_result)
        with patch("langgraph.types.interrupt", return_value="answer"):
            result = interrupt_fn(state)
            assert result["current_step"] == "my_node"

    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_default_keys(self):
        """Default state_key and resume_key should be used if not specified."""
        config = {"message": "Question?"}
        prepare_fn, interrupt_fn = create_interrupt_node("ask", config)

        assert callable(prepare_fn)
        assert callable(interrupt_fn)


class TestInterruptNodeEdgeCases:
    """Edge cases for interrupt node handling."""

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_with_dict_payload(self, mock_interrupt):
        """Interrupt should support dict payloads for structured questions."""
        mock_interrupt.return_value = {"choice": "A", "reason": "because"}

        config = {
            "message": {"question": "Pick A or B", "options": ["A", "B"]},
            "resume_key": "user_choice",
        }
        prepare_fn, interrupt_fn = create_interrupt_node("multi_choice", config)

        prep_result = prepare_fn({})
        state = dict(prep_result)
        result = interrupt_fn(state)

        mock_interrupt.assert_called_once_with(
            {"question": "Pick A or B", "options": ["A", "B"]}
        )
        assert result["user_choice"] == {"choice": "A", "reason": "because"}

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_no_message_uses_node_name(self, mock_interrupt):
        """If no message or prompt, use node name as fallback payload."""
        mock_interrupt.return_value = "answer"

        config = {}  # No message, no prompt
        prepare_fn, interrupt_fn = create_interrupt_node("approval_gate", config)

        prep_result = prepare_fn({})
        state = dict(prep_result)
        interrupt_fn(state)

        # Should use {"node": "approval_gate"} as fallback
        mock_interrupt.assert_called_once_with({"node": "approval_gate"})

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_message_with_jinja2_template(self, mock_interrupt):
        """Message with Jinja2 {{var}} should interpolate from state."""
        mock_interrupt.return_value = "user response"

        config = {
            "message": "{{greeting}}",
            "resume_key": "user_input",
        }
        prepare_fn, interrupt_fn = create_interrupt_node("show_greeting", config)

        state = {"greeting": "Hello! How can I help you today?"}
        prep_result = prepare_fn(state)
        state.update(prep_result)
        interrupt_fn(state)

        mock_interrupt.assert_called_once_with("Hello! How can I help you today?")

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_message_with_simple_template(self, mock_interrupt):
        """Message with simple {var} should interpolate from state."""
        mock_interrupt.return_value = "user response"

        config = {
            "message": "Welcome to {service_name}!",
            "resume_key": "user_input",
        }
        prepare_fn, interrupt_fn = create_interrupt_node("welcome", config)

        state = {"service_name": "Health Clinic"}
        prep_result = prepare_fn(state)
        state.update(prep_result)
        interrupt_fn(state)

        mock_interrupt.assert_called_once_with("Welcome to Health Clinic!")

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_node_message_without_template(self, mock_interrupt):
        """Message without template syntax should pass through unchanged."""
        mock_interrupt.return_value = "response"

        config = {
            "message": "Enter your name:",
            "resume_key": "name",
        }
        prepare_fn, interrupt_fn = create_interrupt_node("ask_name", config)

        prep_result = prepare_fn({})
        state = dict(prep_result)
        interrupt_fn(state)

        mock_interrupt.assert_called_once_with("Enter your name:")


class TestInterruptTwoNodeSplit:
    """FR-060: Interrupt node splits into prepare + interrupt functions.

    The prepare function commits payload to state BEFORE interrupt() fires,
    so state_key holds the payload even when GraphInterrupt is raised.
    """

    @pytest.mark.req("REQ-YG-021")
    def test_create_interrupt_node_returns_tuple(self):
        """create_interrupt_node returns (prepare_fn, interrupt_fn) tuple."""
        config = {"message": "Hello?"}
        result = create_interrupt_node("greet", config)
        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 2
        prepare_fn, interrupt_fn = result
        assert callable(prepare_fn)
        assert callable(interrupt_fn)

    @pytest.mark.req("REQ-YG-021")
    def test_prepare_fn_commits_payload_to_state(self):
        """Prepare function returns state_key: payload without calling interrupt."""
        config = {"message": "What is your name?", "state_key": "greeting"}
        prepare_fn, _interrupt_fn = create_interrupt_node("ask_name", config)

        result = prepare_fn({})

        assert result["greeting"] == "What is your name?"
        assert result["current_step"] == "ask_name"

    @pytest.mark.req("REQ-YG-021")
    def test_prepare_fn_does_not_call_interrupt(self):
        """Prepare function must NOT call interrupt() — only the interrupt_fn does."""
        config = {"message": "Hello?"}
        prepare_fn, _interrupt_fn = create_interrupt_node("greet", config)

        with patch("langgraph.types.interrupt") as mock_interrupt:
            prepare_fn({})
            mock_interrupt.assert_not_called()

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-021")
    def test_interrupt_fn_reads_payload_from_state(self, mock_interrupt):
        """Interrupt function reads payload from state (committed by prepare)."""
        mock_interrupt.return_value = "Alice"
        config = {
            "message": "What is your name?",
            "state_key": "greeting",
            "resume_key": "user_name",
        }
        _prepare_fn, interrupt_fn = create_interrupt_node("ask_name", config)

        # Simulate: prepare already committed payload to state
        state = {"greeting": "What is your name?"}
        result = interrupt_fn(state)

        mock_interrupt.assert_called_once_with("What is your name?")
        assert result["user_name"] == "Alice"

    @pytest.mark.req("REQ-YG-021")
    def test_prepare_fn_idempotent_uses_existing(self):
        """When state_key exists and idempotent=True, prepare reuses it."""
        config = {
            "prompt": "expensive/llm_call",
            "state_key": "question",
            "idempotent": True,
        }
        prepare_fn, _interrupt_fn = create_interrupt_node("ask", config)

        state = {"question": "Previously generated"}
        result = prepare_fn(state)

        assert result["question"] == "Previously generated"

    @pytest.mark.req("REQ-YG-021")
    def test_prepare_fn_with_template(self):
        """Prepare function resolves Jinja2 templates from state."""
        config = {"message": "Welcome to {{service}}!", "state_key": "greeting"}
        prepare_fn, _interrupt_fn = create_interrupt_node("welcome", config)

        state = {"service": "Health Clinic"}
        result = prepare_fn(state)

        assert result["greeting"] == "Welcome to Health Clinic!"

    @patch("yamlgraph.executor.execute_prompt")
    @pytest.mark.req("REQ-YG-021")
    def test_prepare_fn_with_prompt(self, mock_execute):
        """Prepare function calls execute_prompt for dynamic payloads."""
        mock_execute.return_value = "Generated question"
        config = {"prompt": "dialogue/question", "state_key": "question"}
        prepare_fn, _interrupt_fn = create_interrupt_node("ask_dynamic", config)

        result = prepare_fn({"context": "some context"})

        mock_execute.assert_called_once()
        assert result["question"] == "Generated question"

    @pytest.mark.req("REQ-YG-021")
    def test_prepare_fn_dict_payload_fallback(self):
        """When no message/prompt, prepare uses {node: name} fallback."""
        config = {}
        prepare_fn, _interrupt_fn = create_interrupt_node("approval_gate", config)

        result = prepare_fn({})

        assert result["interrupt_message"] == {"node": "approval_gate"}

    @pytest.mark.req("REQ-YG-021")
    def test_compile_node_adds_prepare_and_interrupt(self):
        """compile_node adds both prepare and interrupt nodes to graph."""
        from yamlgraph.compile.node_compiler import compile_node

        graph = MagicMock()
        config = MagicMock()
        config.loop_limits = {}
        config.prompts_relative = False
        config.prompts_dir = None
        config.defaults = {}
        config.source_path = None

        node_config = {"type": "interrupt", "message": "Hello?"}
        compile_node("greet", node_config, graph, config, {}, {}, {})

        # Should add two nodes: greet_prepare and greet
        add_node_calls = graph.add_node.call_args_list
        node_names = [call[0][0] for call in add_node_calls]
        assert "greet_prepare" in node_names, f"Expected greet_prepare in {node_names}"
        assert "greet" in node_names, f"Expected greet in {node_names}"

        # Should add internal edge: greet_prepare → greet
        graph.add_edge.assert_called_once_with("greet_prepare", "greet")
