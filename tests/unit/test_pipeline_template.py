"""Unit tests for FR-235: Compile-Time Pipeline Templates.

TDD RED phase — tests define the expected behavior of pipeline template
expansion. All tests must fail initially, then pass after implementation.
"""

import pytest

# ---------------------------------------------------------------------------
# 1. NodeType enum — PIPELINE constant
# ---------------------------------------------------------------------------


class TestNodeTypePipeline:
    """NodeType.PIPELINE constant should exist."""

    @pytest.mark.req("REQ-YG-235")
    def test_enum_value_exists(self):
        """NodeType should have PIPELINE constant."""
        from yamlgraph.constants import NodeType

        assert hasattr(NodeType, "PIPELINE")
        assert NodeType.PIPELINE == "pipeline"

    @pytest.mark.req("REQ-YG-235")
    def test_not_requires_prompt(self):
        """Pipeline nodes don't require prompt (they are meta-nodes)."""
        from yamlgraph.constants import NodeType

        assert not NodeType.requires_prompt("pipeline")


# ---------------------------------------------------------------------------
# 2. expand_pipeline_templates — core expansion logic
# ---------------------------------------------------------------------------


class TestExpandPipelineTemplates:
    """Pipeline template expansion produces correct nodes and edges."""

    @staticmethod
    def _make_config(
        items: list[dict],
        stages: list[dict],
        edges: list[dict] | None = None,
    ) -> dict:
        """Build a minimal graph config with a pipeline node."""
        config = {
            "name": "test-graph",
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": items,
                    "stages": stages,
                }
            },
            "edges": edges
            or [
                {"from": "START", "to": "chapters"},
                {"from": "chapters", "to": "END"},
            ],
        }
        return config

    @pytest.mark.req("REQ-YG-235")
    def test_basic_expansion_produces_concrete_nodes(self):
        """Pipeline with 2 items × 2 stages → 4 concrete nodes."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = self._make_config(
            items=[
                {"name": "intro", "prompt_prefix": "chapter/intro"},
                {"name": "outro", "prompt_prefix": "chapter/outro"},
            ],
            stages=[
                {
                    "name": "write",
                    "type": "copilot",
                    "prompt": "{item.prompt_prefix}",
                    "state_key": "current_chapter",
                },
                {
                    "name": "judge",
                    "type": "copilot",
                    "prompt": "judge/chapter",
                    "state_key": "current_chapter",
                },
            ],
        )

        result = expand_pipeline_templates(config)
        nodes = result["nodes"]

        # Original pipeline node should be removed
        assert "chapters" not in nodes

        # 4 concrete nodes should exist
        expected_names = [
            "chapters__intro__write",
            "chapters__intro__judge",
            "chapters__outro__write",
            "chapters__outro__judge",
        ]
        for name in expected_names:
            assert name in nodes, f"Expected node '{name}' not found"

        assert len(nodes) == 4

    @pytest.mark.req("REQ-YG-235")
    def test_expanded_node_type_preserved(self):
        """Expanded nodes inherit 'type' from stage definition."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = self._make_config(
            items=[{"name": "intro", "prompt_prefix": "chapter/intro"}],
            stages=[
                {
                    "name": "write",
                    "type": "copilot",
                    "prompt": "{item.prompt_prefix}",
                    "state_key": "current_chapter",
                },
            ],
        )

        result = expand_pipeline_templates(config)
        assert result["nodes"]["chapters__intro__write"]["type"] == "copilot"

    @pytest.mark.req("REQ-YG-235")
    def test_item_field_interpolation_in_prompt(self):
        """{item.field} in prompt is replaced with item value."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = self._make_config(
            items=[{"name": "intro", "prompt_prefix": "chapter/intro"}],
            stages=[
                {
                    "name": "write",
                    "type": "copilot",
                    "prompt": "{item.prompt_prefix}",
                    "state_key": "current_chapter",
                },
            ],
        )

        result = expand_pipeline_templates(config)
        node = result["nodes"]["chapters__intro__write"]
        assert node["prompt"] == "chapter/intro"

    @pytest.mark.req("REQ-YG-235")
    def test_item_field_interpolation_in_variables(self):
        """{item.field} in variables dict values is replaced."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = self._make_config(
            items=[
                {
                    "name": "intro",
                    "prompt_prefix": "chapter/intro",
                    "filename": "{state.filename_intro}",
                }
            ],
            stages=[
                {
                    "name": "write",
                    "type": "copilot",
                    "prompt": "{item.prompt_prefix}",
                    "variables": {"filename": "{item.filename}"},
                    "state_key": "current_chapter",
                },
            ],
        )

        result = expand_pipeline_templates(config)
        node = result["nodes"]["chapters__intro__write"]
        assert node["variables"]["filename"] == "{state.filename_intro}"

    @pytest.mark.req("REQ-YG-235")
    def test_item_field_interpolation_in_state_key(self):
        """{item.field} in state_key is replaced."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = self._make_config(
            items=[
                {"name": "intro", "key": "intro_output"},
            ],
            stages=[
                {
                    "name": "write",
                    "type": "copilot",
                    "prompt": "write/chapter",
                    "state_key": "{item.key}",
                },
            ],
        )

        result = expand_pipeline_templates(config)
        node = result["nodes"]["chapters__intro__write"]
        assert node["state_key"] == "intro_output"

    @pytest.mark.req("REQ-YG-235")
    def test_non_string_fields_copied_verbatim(self):
        """Non-string stage fields (timeout, temperature) are NOT interpolated."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = self._make_config(
            items=[{"name": "intro", "prompt_prefix": "chapter/intro"}],
            stages=[
                {
                    "name": "write",
                    "type": "copilot",
                    "prompt": "{item.prompt_prefix}",
                    "state_key": "current_chapter",
                    "timeout": 300,
                    "temperature": 0.7,
                },
            ],
        )

        result = expand_pipeline_templates(config)
        node = result["nodes"]["chapters__intro__write"]
        assert node["timeout"] == 300
        assert node["temperature"] == 0.7

    @pytest.mark.req("REQ-YG-235")
    def test_no_pipeline_nodes_returns_config_unchanged(self):
        """Config without pipeline nodes is returned as-is."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = {
            "name": "simple",
            "nodes": {
                "greet": {"type": "llm", "prompt": "greet", "state_key": "greeting"},
            },
            "edges": [
                {"from": "START", "to": "greet"},
                {"from": "greet", "to": "END"},
            ],
        }

        result = expand_pipeline_templates(config)
        assert result["nodes"] == config["nodes"]
        assert result["edges"] == config["edges"]

    @pytest.mark.req("REQ-YG-235")
    def test_original_config_not_mutated(self):
        """expand_pipeline_templates works on a deep copy."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = self._make_config(
            items=[{"name": "intro", "prompt_prefix": "chapter/intro"}],
            stages=[
                {
                    "name": "write",
                    "type": "copilot",
                    "prompt": "{item.prompt_prefix}",
                    "state_key": "current_chapter",
                },
            ],
        )

        # Keep original node count
        original_nodes = set(config["nodes"].keys())
        expand_pipeline_templates(config)
        assert set(config["nodes"].keys()) == original_nodes


# ---------------------------------------------------------------------------
# 3. Edge rewriting
# ---------------------------------------------------------------------------


class TestEdgeRewriting:
    """External edges referencing pipeline node are rewritten."""

    @staticmethod
    def _make_config(items, stages, edges):
        return {
            "name": "test-graph",
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": items,
                    "stages": stages,
                }
            },
            "edges": edges,
        }

    @pytest.mark.req("REQ-YG-235")
    def test_start_to_pipeline_rewrites_to_first_node(self):
        """Edge 'from: START, to: chapters' → 'to: chapters__intro__write'."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = self._make_config(
            items=[
                {"name": "intro", "prompt_prefix": "chapter/intro"},
                {"name": "outro", "prompt_prefix": "chapter/outro"},
            ],
            stages=[
                {
                    "name": "write",
                    "type": "copilot",
                    "prompt": "{item.prompt_prefix}",
                    "state_key": "current_chapter",
                },
            ],
            edges=[
                {"from": "START", "to": "chapters"},
                {"from": "chapters", "to": "END"},
            ],
        )

        result = expand_pipeline_templates(config)
        edges = result["edges"]

        start_edge = next(e for e in edges if e["from"] == "START")
        assert start_edge["to"] == "chapters__intro__write"

    @pytest.mark.req("REQ-YG-235")
    def test_pipeline_to_end_rewrites_from_last_node(self):
        """Edge 'from: chapters, to: END' → 'from: chapters__outro__write'."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = self._make_config(
            items=[
                {"name": "intro", "prompt_prefix": "chapter/intro"},
                {"name": "outro", "prompt_prefix": "chapter/outro"},
            ],
            stages=[
                {
                    "name": "write",
                    "type": "copilot",
                    "prompt": "{item.prompt_prefix}",
                    "state_key": "current_chapter",
                },
            ],
            edges=[
                {"from": "START", "to": "chapters"},
                {"from": "chapters", "to": "END"},
            ],
        )

        result = expand_pipeline_templates(config)
        edges = result["edges"]

        end_edge = next(e for e in edges if e["to"] == "END")
        assert end_edge["from"] == "chapters__outro__write"

    @pytest.mark.req("REQ-YG-235")
    def test_pipeline_to_other_node_rewrites(self):
        """Edge 'from: chapters, to: finalize' → from last expanded node."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = {
            "name": "test-graph",
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        },
                        {
                            "name": "judge",
                            "type": "copilot",
                            "prompt": "judge/chapter",
                            "state_key": "out",
                        },
                    ],
                },
                "finalize": {
                    "type": "llm",
                    "prompt": "finalize",
                    "state_key": "final",
                },
            },
            "edges": [
                {"from": "START", "to": "chapters"},
                {"from": "chapters", "to": "finalize"},
                {"from": "finalize", "to": "END"},
            ],
        }

        result = expand_pipeline_templates(config)
        edges = result["edges"]

        finalize_edge = next(e for e in edges if e["to"] == "finalize")
        assert finalize_edge["from"] == "chapters__ch1__judge"

    @pytest.mark.req("REQ-YG-235")
    def test_edge_condition_preserved_during_rewrite(self):
        """External edge conditions survive rewriting."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = {
            "name": "test-graph",
            "nodes": {
                "setup": {"type": "llm", "prompt": "setup", "state_key": "s"},
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        },
                    ],
                },
            },
            "edges": [
                {"from": "START", "to": "setup"},
                {
                    "from": "setup",
                    "to": "chapters",
                    "condition": "ready == 'yes'",
                },
                {"from": "chapters", "to": "END"},
            ],
        }

        result = expand_pipeline_templates(config)
        edges = result["edges"]

        conditional_edge = next(e for e in edges if e.get("condition"))
        assert conditional_edge["to"] == "chapters__ch1__write"
        assert conditional_edge["condition"] == "ready == 'yes'"


# ---------------------------------------------------------------------------
# 4. Sequential chaining (intra-item and inter-item)
# ---------------------------------------------------------------------------


class TestSequentialChaining:
    """Internal edges chain stages within and between items."""

    @pytest.mark.req("REQ-YG-235")
    def test_intra_item_stage_chaining(self):
        """Stages within same item are chained: write→judge→amend."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = {
            "name": "test-graph",
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "intro", "prompt_prefix": "ch/intro"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        },
                        {
                            "name": "judge",
                            "type": "copilot",
                            "prompt": "judge/ch",
                            "state_key": "out",
                        },
                        {
                            "name": "amend",
                            "type": "copilot",
                            "prompt": "amend/ch",
                            "state_key": "out",
                        },
                    ],
                }
            },
            "edges": [
                {"from": "START", "to": "chapters"},
                {"from": "chapters", "to": "END"},
            ],
        }

        result = expand_pipeline_templates(config)
        edges = result["edges"]

        # Check internal edges
        assert {
            "from": "chapters__intro__write",
            "to": "chapters__intro__judge",
        } in edges
        assert {
            "from": "chapters__intro__judge",
            "to": "chapters__intro__amend",
        } in edges

    @pytest.mark.req("REQ-YG-235")
    def test_inter_item_chaining(self):
        """Last stage of item N chains to first stage of item N+1."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = {
            "name": "test-graph",
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [
                        {"name": "intro", "prompt_prefix": "ch/intro"},
                        {"name": "outro", "prompt_prefix": "ch/outro"},
                    ],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        },
                        {
                            "name": "judge",
                            "type": "copilot",
                            "prompt": "judge/ch",
                            "state_key": "out",
                        },
                    ],
                }
            },
            "edges": [
                {"from": "START", "to": "chapters"},
                {"from": "chapters", "to": "END"},
            ],
        }

        result = expand_pipeline_templates(config)
        edges = result["edges"]

        # Inter-item: intro__judge → outro__write
        assert {
            "from": "chapters__intro__judge",
            "to": "chapters__outro__write",
        } in edges

    @pytest.mark.req("REQ-YG-235")
    def test_single_item_single_stage(self):
        """Degenerate case: 1 item × 1 stage → 1 node, no internal edges."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = {
            "name": "test-graph",
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "only", "prompt_prefix": "ch/only"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        },
                    ],
                }
            },
            "edges": [
                {"from": "START", "to": "chapters"},
                {"from": "chapters", "to": "END"},
            ],
        }

        result = expand_pipeline_templates(config)
        nodes = result["nodes"]
        edges = result["edges"]

        assert len(nodes) == 1
        assert "chapters__only__write" in nodes

        # Only rewritten external edges, no internal chaining edges
        assert {"from": "START", "to": "chapters__only__write"} in edges
        assert {"from": "chapters__only__write", "to": "END"} in edges


# ---------------------------------------------------------------------------
# 5. Non-pipeline nodes preserved
# ---------------------------------------------------------------------------


class TestNonPipelineNodesPreserved:
    """Non-pipeline nodes are preserved during expansion."""

    @pytest.mark.req("REQ-YG-235")
    def test_other_nodes_untouched(self):
        """Nodes other than pipeline are preserved in result."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = {
            "name": "test-graph",
            "nodes": {
                "setup": {"type": "llm", "prompt": "setup", "state_key": "s"},
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        },
                    ],
                },
                "finalize": {
                    "type": "llm",
                    "prompt": "finalize",
                    "state_key": "final",
                },
            },
            "edges": [
                {"from": "START", "to": "setup"},
                {"from": "setup", "to": "chapters"},
                {"from": "chapters", "to": "finalize"},
                {"from": "finalize", "to": "END"},
            ],
        }

        result = expand_pipeline_templates(config)
        nodes = result["nodes"]

        # Non-pipeline nodes preserved
        assert "setup" in nodes
        assert "finalize" in nodes

        # Pipeline replaced
        assert "chapters" not in nodes
        assert "chapters__ch1__write" in nodes

    @pytest.mark.req("REQ-YG-235")
    def test_unrelated_edges_preserved(self):
        """Edges between non-pipeline nodes are not affected."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = {
            "name": "test-graph",
            "nodes": {
                "setup": {"type": "llm", "prompt": "setup", "state_key": "s"},
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        },
                    ],
                },
            },
            "edges": [
                {"from": "START", "to": "setup"},
                {"from": "setup", "to": "chapters"},
                {"from": "chapters", "to": "END"},
            ],
        }

        result = expand_pipeline_templates(config)
        edges = result["edges"]

        # START→setup edge preserved
        assert {"from": "START", "to": "setup"} in edges


# ---------------------------------------------------------------------------
# 6. Stage name excluded from config (FR-235 naming convention)
# ---------------------------------------------------------------------------


class TestStageNameExclusion:
    """The 'name' field should not appear in the expanded node config."""

    @pytest.mark.req("REQ-YG-235")
    def test_stage_name_not_in_expanded_config(self):
        """The 'name' field from stage definition is not in expanded node."""
        from yamlgraph.pipeline_template import expand_pipeline_templates

        config = {
            "name": "test-graph",
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        },
                    ],
                }
            },
            "edges": [
                {"from": "START", "to": "chapters"},
                {"from": "chapters", "to": "END"},
            ],
        }

        result = expand_pipeline_templates(config)
        node = result["nodes"]["chapters__ch1__write"]
        assert "name" not in node
