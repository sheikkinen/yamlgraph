"""FR-810 RED witnesses — router-visible tool_call outputs via parsed_key.

Judged contract (FR-810 judgement, R-1..R-5): exactly one optional
public field `parsed_key` on tool_call nodes; graph-runtime tools only;
wrapper under state_key preserved unchanged; JSON-object strings parse,
dicts pass through, everything else is a parse failure with no
empty-dict substitution; failures follow on_error (fail raises, skip
returns the failure envelope and never sets parsed_key); lint warns on
statically known shell/python misuse; a deterministic fixture graph
routes an edge condition on a parsed field.
"""

import json
import textwrap

import pytest

from yamlgraph.node_factory.tool_nodes import create_tool_call_node

FINDINGS = {"is_spa": True, "api_found": False, "api_urls": []}


def _registry(result):
    return {"page_analysis": lambda **kwargs: result}


def _make_node(
    result, *, parsed_key="page_findings", on_error=None, graph_tools=("page_analysis",)
):
    config = {
        "tool": "page_analysis",
        "args": {},
        "state_key": "page_analysis",
    }
    if parsed_key is not None:
        config["parsed_key"] = parsed_key
    if on_error is not None:
        config["on_error"] = on_error
    return create_tool_call_node(
        "page_analysis",
        config,
        _registry(result),
        graph_tool_names=set(graph_tools),
    )


# ---------------------------------------------------------------------------
# AC-02: parsed output exposed; wrapper preserved
# ---------------------------------------------------------------------------


class TestParsedKeyHappyPath:
    @pytest.mark.req("REQ-YG-597")
    def test_dict_output_exposed_under_parsed_key(self):
        node = _make_node(dict(FINDINGS))
        update = node({})
        assert update["page_findings"] == FINDINGS

    @pytest.mark.req("REQ-YG-597")
    def test_json_object_string_parses_to_dict(self):
        node = _make_node(json.dumps(FINDINGS))
        update = node({})
        assert update["page_findings"] == FINDINGS

    @pytest.mark.req("REQ-YG-597")
    def test_wrapper_under_state_key_preserved_unchanged(self):
        raw = json.dumps(FINDINGS)
        node = _make_node(raw)
        update = node({})
        wrapper = update["page_analysis"]
        assert set(wrapper) == {"task_id", "tool", "success", "result", "error"}
        assert wrapper["success"] is True
        assert wrapper["result"] == raw  # raw child output, not the parsed dict


# ---------------------------------------------------------------------------
# AC-03: without parsed_key, behavior unchanged
# ---------------------------------------------------------------------------


class TestWithoutParsedKey:
    @pytest.mark.req("REQ-YG-597")
    def test_update_contains_only_state_key_and_current_step(self):
        node = _make_node(dict(FINDINGS), parsed_key=None)
        update = node({})
        assert set(update) == {"page_analysis", "current_step"}


# ---------------------------------------------------------------------------
# AC-04 + AC-05: parse failures fail closed per on_error
# ---------------------------------------------------------------------------

BAD_OUTPUTS = [
    pytest.param("not json at all", id="invalid-json"),
    pytest.param(json.dumps([1, 2, 3]), id="json-list-string"),
    pytest.param([1, 2, 3], id="list"),
    pytest.param(42, id="scalar"),
    pytest.param(None, id="missing-output"),
]


class TestParseFailures:
    @pytest.mark.req("REQ-YG-597")
    @pytest.mark.parametrize("bad", BAD_OUTPUTS)
    def test_fail_raises_at_node(self, bad):
        node = _make_node(bad, on_error="fail")
        with pytest.raises(ValueError) as exc:
            node({})
        assert "page_analysis" in str(exc.value)

    @pytest.mark.req("REQ-YG-597")
    @pytest.mark.parametrize("bad", BAD_OUTPUTS)
    def test_skip_returns_failure_envelope_without_parsed_key(self, bad):
        node = _make_node(bad, on_error="skip")
        update = node({})
        assert "page_findings" not in update
        assert update["page_analysis"]["success"] is False
        assert update["page_analysis"]["error"]

    @pytest.mark.req("REQ-YG-597")
    def test_failed_child_wrapper_never_sets_parsed_key(self):
        def boom(**kwargs):
            raise RuntimeError("child graph exploded")

        node = create_tool_call_node(
            "page_analysis",
            {
                "tool": "page_analysis",
                "args": {},
                "state_key": "page_analysis",
                "parsed_key": "page_findings",
            },
            {"page_analysis": boom},
            graph_tool_names={"page_analysis"},
        )
        update = node({})
        assert "page_findings" not in update
        assert update["page_analysis"]["success"] is False


# ---------------------------------------------------------------------------
# AC-06 (runtime half): dynamic non-graph tool with parsed_key
# ---------------------------------------------------------------------------


class TestNonGraphToolMisuse:
    @pytest.mark.req("REQ-YG-597")
    def test_fail_raises_for_non_graph_tool(self):
        node = _make_node(dict(FINDINGS), on_error="fail", graph_tools=())
        with pytest.raises(ValueError) as exc:
            node({})
        assert "parsed_key" in str(exc.value)

    @pytest.mark.req("REQ-YG-597")
    def test_skip_returns_envelope_for_non_graph_tool(self):
        node = _make_node(dict(FINDINGS), on_error="skip", graph_tools=())
        update = node({})
        assert "page_findings" not in update
        assert update["page_analysis"]["success"] is False


# ---------------------------------------------------------------------------
# AC-01: public schema — parsed_key only, aliases rejected
# ---------------------------------------------------------------------------


class TestConfigSurface:
    @pytest.mark.req("REQ-YG-597")
    def test_parsed_key_accepted(self):
        from yamlgraph.models.node_schema import NodeConfig

        cfg = NodeConfig(type="tool_call", tool="t", args={}, parsed_key="findings")
        assert cfg.parsed_key == "findings"

    @pytest.mark.req("REQ-YG-597")
    @pytest.mark.parametrize("alias", ["parse_result", "result_key"])
    def test_aliases_rejected(self, alias):
        from pydantic import ValidationError

        from yamlgraph.models.node_schema import NodeConfig

        with pytest.raises(ValidationError):
            NodeConfig(type="tool_call", tool="t", args={}, **{alias: "findings"})


# ---------------------------------------------------------------------------
# AC-02 (state surface): parsed_key joins the generated state class
# ---------------------------------------------------------------------------


class TestStateSurface:
    @pytest.mark.req("REQ-YG-597")
    def test_parsed_key_in_generated_state_fields(self):
        from yamlgraph.models.state_builder import build_state_class

        raw = {
            "name": "fixture",
            "nodes": {
                "step": {
                    "type": "tool_call",
                    "tool": "t",
                    "args": {},
                    "state_key": "wrapper",
                    "parsed_key": "findings",
                }
            },
        }
        state_cls = build_state_class(raw)
        assert "findings" in state_cls.__annotations__


# ---------------------------------------------------------------------------
# AC-06 (lint half): warn on statically known non-graph tool
# ---------------------------------------------------------------------------


class TestLinter:
    def _lint(self, tmp_path, tool_decl):
        from yamlgraph.linter.checks_tool_call import check_tool_call_nodes

        graph = tmp_path / "graph.yaml"
        graph.write_text(
            textwrap.dedent(f"""\
            version: "1.0"
            name: fixture
            tools:
              mytool:
                {tool_decl}
            nodes:
              step:
                type: tool_call
                tool: mytool
                args: {{}}
                state_key: wrapper
                parsed_key: findings
            edges:
              - from: START
                to: step
              - from: step
                to: END
            """)
        )
        return check_tool_call_nodes(graph)

    @pytest.mark.req("REQ-YG-597")
    def test_warns_on_shell_tool(self, tmp_path):
        issues = self._lint(tmp_path, "command: echo hi")
        assert any(i.code == "W703" for i in issues)

    @pytest.mark.req("REQ-YG-597")
    def test_no_warning_on_graph_tool(self, tmp_path):
        issues = self._lint(
            tmp_path, "type: graph\n                path: child/graph.yaml"
        )
        assert not any(i.code == "W703" for i in issues)


# ---------------------------------------------------------------------------
# AC-02 + AC-09: deterministic compiled-graph witness — edge condition
# routes on a parsed field
# ---------------------------------------------------------------------------


def _write_fixture_graphs(tmp_path, is_spa):
    child_dir = tmp_path / "child"
    child_dir.mkdir()
    (child_dir / "graph.yaml").write_text(
        textwrap.dedent(f"""\
        version: "1.0"
        name: child-analyzer
        state:
          findings: dict
        nodes:
          analyze:
            type: passthrough
            output:
              findings:
                is_spa: {str(is_spa).lower()}
                api_found: false
        edges:
          - from: START
            to: analyze
          - from: analyze
            to: END
        """)
    )
    (tmp_path / "graph.yaml").write_text(
        textwrap.dedent("""\
        version: "1.0"
        name: parent-router
        state:
          route_taken: str
        tools:
          analyzer:
            type: graph
            path: child/graph.yaml
            input_mapping: {}
            output_key: findings
        nodes:
          page_analysis:
            type: tool_call
            tool: analyzer
            args: {}
            state_key: page_analysis
            parsed_key: page_findings
            on_error: fail
          sniff:
            type: passthrough
            output:
              route_taken: sniff
          no_sniff:
            type: passthrough
            output:
              route_taken: no_sniff
        edges:
          - from: START
            to: page_analysis
          - from: page_analysis
            to: sniff
            condition: "page_findings.is_spa == true"
          - from: page_analysis
            to: no_sniff
            condition: "page_findings.is_spa != true"
          - from: sniff
            to: END
          - from: no_sniff
            to: END
        """)
    )
    return tmp_path / "graph.yaml"


class TestCompiledGraphRouting:
    @pytest.mark.req("REQ-YG-597")
    @pytest.mark.parametrize(
        ("is_spa", "expected_route"),
        [(True, "sniff"), (False, "no_sniff")],
        ids=["spa-routes-to-sniff", "non-spa-skips-sniff"],
    )
    def test_edge_condition_routes_on_parsed_field(
        self, tmp_path, is_spa, expected_route
    ):
        from yamlgraph.compile.graph_loader import load_and_compile

        graph_path = _write_fixture_graphs(tmp_path, is_spa)
        compiled = load_and_compile(graph_path).compile()
        final = compiled.invoke({})
        assert final["route_taken"] == expected_route
        assert final["page_findings"]["is_spa"] is is_spa
