"""The hello demo consumes the shared toast tool (FR-1030, REQ-YG-672).

The unit suite for `send_toast` itself proves the tool. These tests prove the
*composition*: that the committed `examples/demos/hello/graph.yaml` wires it
correctly, and that the graph's declared `on_error: skip` tolerance behaves as
the FR says it does.

Both paths matter, and the failure path matters more. A graph that reaches END
after a failed toast is only acceptable because the failure is *recorded*; if
the skip path ever started swallowing the error instead of writing an FR-778
envelope, the demo would look identical from the outside and the operator would
be told nothing while believing otherwise.

No LLM call and no notification process: `execute_prompt` and `send_toast` are
both doubled, and the tool double is installed before the graph compiles
because `load_python_function` resolves the callable at compile time.
"""

from unittest.mock import patch

import pytest

from examples.shared.notify_toast import ToastError
from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

# FR-756: references committed examples/ artifacts
pytestmark = pytest.mark.process

GRAPH = "examples/demos/hello/graph.yaml"
GREETING = {
    "greeting": "Hey there, World!",
    "emoji": "🌍",
    "formality_level": "informal",
}


def run_hello(toast):
    """Compile and run the committed hello graph with both boundaries doubled."""
    with (
        patch("examples.shared.notify_toast.send_toast", toast),
        patch("yamlgraph.node_factory.llm_nodes.execute_prompt", return_value=GREETING),
    ):
        compiled = compile_graph(load_graph_config(GRAPH)).compile()
        return compiled.invoke({"name": "World", "style": "enthusiastic"})


class TestSubmissionPath:
    @pytest.mark.req("REQ-YG-672")
    def test_successful_submission_is_recorded_in_state(self):
        calls = []

        def toast(**kwargs):
            calls.append(kwargs)
            return {"submitted": True, "backend": "osascript"}

        result = run_hello(toast)

        assert result["notified"]["success"] is True
        assert result["notified"]["result"] == {
            "submitted": True,
            "backend": "osascript",
        }
        assert result["notified"]["error"] is None
        assert result["current_step"] == "notify"

    @pytest.mark.req("REQ-YG-672")
    def test_the_greeting_the_llm_produced_is_what_gets_notified(self):
        calls = []

        def toast(**kwargs):
            calls.append(kwargs)
            return {"submitted": True, "backend": "osascript"}

        run_hello(toast)

        assert calls == [{"title": "Hello, World", "message": "Hey there, World!"}]


class TestSkipPath:
    @pytest.mark.req("REQ-YG-672")
    def test_toast_error_still_reaches_end_but_is_not_silent(self):
        def toast(**kwargs):
            raise ToastError("notify-send not found on this system")

        result = run_hello(toast)

        # END was reached — the quickstart survives a host with no notifier ...
        assert result["current_step"] == "notify"
        assert result["greeting"] == GREETING
        # ... and the failure is on the record, not swallowed.
        assert result["notified"]["success"] is False
        assert result["notified"]["result"] is None
        assert "notify-send not found" in result["notified"]["error"]

    @pytest.mark.req("REQ-YG-672")
    def test_skip_envelope_is_never_submitted_shaped(self):
        def toast(**kwargs):
            raise ToastError("no desktop session")

        notified = run_hello(toast)["notified"]

        assert "submitted" not in str(notified["result"])
