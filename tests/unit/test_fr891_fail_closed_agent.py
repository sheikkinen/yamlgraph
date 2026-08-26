"""FR-891: Fail-closed agent tool boundary.

An agent run whose tool calls ALL failed must raise instead of handing
error strings to the LLM as evidence (Commandment 6; incident
research/mercury-census/runs/run-grounded-FAILED-OPEN.log).

Deterministic only (judgement R-4): stubbed LLM/tools, no live network.
"""

from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.tools.agent import create_agent_node
from yamlgraph.tools.python_tool import PythonToolConfig

MOCK_AGENT_PROMPT = {
    "system": "You are a helpful assistant.",
    "user": "{input}",
}


@pytest.fixture(autouse=True)
def mock_load_prompt():
    with patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_AGENT_PROMPT):
        yield


def _failing_tool(query: str) -> str:
    raise RuntimeError("boom: dependency missing")


def _ok_tool(query: str) -> str:
    return f"result for {query}"


def _tool_call_response(name: str, call_id: str) -> MagicMock:
    resp = MagicMock()
    resp.tool_calls = [{"id": call_id, "name": name, "args": {"query": "x"}}]
    resp.content = ""
    return resp


def _final_response(content: str = "fluent answer") -> MagicMock:
    resp = MagicMock()
    resp.tool_calls = []
    resp.content = content
    return resp


def _make_node(py_tools: dict, max_iterations: int = 3):
    node_config = {
        "prompt": "agent",
        "tools": list(py_tools),
        "max_iterations": max_iterations,
        "state_key": "result",
    }
    return create_agent_node("agent", node_config, {}, python_tools=py_tools)


PY_FAIL = {
    "search": PythonToolConfig(
        module="tests.unit.test_fr891_fail_closed_agent",
        function="_failing_tool",
        description="always fails",
    )
}

PY_MIXED = {
    "search": PythonToolConfig(
        module="tests.unit.test_fr891_fail_closed_agent",
        function="_failing_tool",
        description="always fails",
    ),
    "lookup": PythonToolConfig(
        module="tests.unit.test_fr891_fail_closed_agent",
        function="_ok_tool",
        description="succeeds",
    ),
}


class TestAllFailedRaises:
    """AC-01/AC-02/AC-03: all-failed runs raise on both finalization paths."""

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_all_failed_no_more_tool_calls_path_raises(self, mock_create_llm):
        """The witnessed incident path: tools fail, LLM stops calling tools."""
        from yamlgraph.tools.agent import AllToolCallsFailedError

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [
            _tool_call_response("search", "c1"),
            _final_response(),
        ]
        mock_create_llm.return_value = mock_llm

        node_fn = _make_node(PY_FAIL)
        with pytest.raises(AllToolCallsFailedError) as exc:
            node_fn({"input": "q"})
        msg = str(exc.value)
        assert "agent" in msg
        assert "1" in msg  # failure census present
        assert "search" in msg

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_all_failed_max_iterations_path_raises(self, mock_create_llm):
        """Max-iterations finalization must also be gated (judgement R-1)."""
        from yamlgraph.tools.agent import AllToolCallsFailedError

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = _tool_call_response("search", "c1")
        mock_create_llm.return_value = mock_llm

        node_fn = _make_node(PY_FAIL, max_iterations=2)
        with pytest.raises(AllToolCallsFailedError):
            node_fn({"input": "q"})

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_census_includes_counts_and_first_error(self, mock_create_llm):
        """AC-03: census carries totals, tool names, first failure output."""
        from yamlgraph.tools.agent import AllToolCallsFailedError

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [
            _tool_call_response("search", "c1"),
            _tool_call_response("search", "c2"),
            _final_response(),
        ]
        mock_create_llm.return_value = mock_llm

        node_fn = _make_node(PY_FAIL)
        with pytest.raises(AllToolCallsFailedError) as exc:
            node_fn({"input": "q"})
        msg = str(exc.value)
        assert "2" in msg  # two failed calls
        assert "boom" in msg  # first failure output


class TestNonFatalPaths:
    """AC-04/AC-05: partial failure and no-tool-call runs are unchanged."""

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_partial_failure_reaches_final_answer(self, mock_create_llm):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        first = MagicMock()
        first.tool_calls = [
            {"id": "c1", "name": "search", "args": {"query": "x"}},
            {"id": "c2", "name": "lookup", "args": {"query": "x"}},
        ]
        first.content = ""
        mock_llm.invoke.side_effect = [first, _final_response("done")]
        mock_create_llm.return_value = mock_llm

        node_fn = _make_node(PY_MIXED)
        result = node_fn({"input": "q"})
        assert result["result"] == "done"

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_no_tool_calls_reaches_final_answer(self, mock_create_llm):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = _final_response("direct")
        mock_create_llm.return_value = mock_llm

        node_fn = _make_node(PY_FAIL)
        result = node_fn({"input": "q"})
        assert result["result"] == "direct"


class TestSearchWebContract:
    """AC-06/AC-07: search_web raises instead of returning error strings."""

    @pytest.mark.req("REQ-YG-018")
    def test_empty_query_raises_value_error(self):
        from examples.shared.websearch import search_web

        with pytest.raises(ValueError):
            search_web("   ")

    @pytest.mark.req("REQ-YG-018")
    def test_missing_ddgs_raises_import_error(self, monkeypatch):
        import examples.shared.websearch as ws

        monkeypatch.setattr(ws, "DUCKDUCKGO_AVAILABLE", False)
        with pytest.raises(ImportError):
            ws.search_web("anything")

    @pytest.mark.req("REQ-YG-018")
    def test_empty_results_return_data_string(self, monkeypatch):
        import examples.shared.websearch as ws

        fake = MagicMock()
        fake.return_value.__enter__.return_value.text.return_value = iter([])
        monkeypatch.setattr(ws, "DUCKDUCKGO_AVAILABLE", True)
        monkeypatch.setattr(ws, "DDGS", fake)
        out = ws.search_web("obscure query")
        assert out.startswith("No results found")

    @pytest.mark.req("REQ-YG-018")
    def test_transport_exception_propagates(self, monkeypatch):
        import examples.shared.websearch as ws

        fake = MagicMock()
        fake.return_value.__enter__.side_effect = ConnectionError("net down")
        monkeypatch.setattr(ws, "DUCKDUCKGO_AVAILABLE", True)
        monkeypatch.setattr(ws, "DDGS", fake)
        with pytest.raises(ConnectionError):
            ws.search_web("anything")

    @pytest.mark.req("REQ-YG-018")
    def test_no_error_string_returns_remain(self):
        """The 'Error: ...' return convention is deleted from the tool."""
        import inspect

        import examples.shared.websearch as ws

        src = inspect.getsource(ws.search_web)
        assert 'return "Error' not in src
        assert 'return f"Error' not in src
