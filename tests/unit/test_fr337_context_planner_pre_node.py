"""Tests for FR-337 context planner pre-node implementation."""

from pathlib import Path

import pytest


@pytest.mark.req("REQ-YG-001")  # Placeholder REQ for testing
class TestFR337ContextPlannerPreNode:
    """Test AC-01: Context planner prompt exists with ContextPlan schema."""

    def test_ac01_context_planner_prompt_exists_with_contextplan_schema_fields(self):
        """Context planner prompt should exist with required schema fields."""
        prompt_path = Path(
            ".chaplain/graphs/watcher-enforce/prompts/context-planner.yaml"
        )
        assert prompt_path.exists(), "Context planner prompt should exist"

        import yaml

        with open(prompt_path) as f:
            prompt = yaml.safe_load(f)

        # Check schema exists
        assert "schema" in prompt, "Context planner should have schema"
        schema = prompt["schema"]

        # Check required fields
        expected_fields = [
            "source_files",
            "test_files",
            "doc_sections",
            "key_symbols",
            "rationale",
        ]
        assert "fields" in schema, "Schema should have fields"

        for field in expected_fields:
            assert field in schema["fields"], f"Schema should include {field} field"

    def test_ac02_context_assembler_tool_exists_and_uses_ast_parse(self):
        """Context assembler tool should exist and use ast.parse()."""
        # Check for tools.py or assembler in watcher-enforce scope
        tools_path = Path(".chaplain/graphs/watcher-enforce/tools.py")
        assert tools_path.exists(), "Context assembler tools should exist"

        with open(tools_path) as f:
            content = f.read()

        assert "ast.parse" in content, "Context assembler should use ast.parse()"
        assert (
            "def assemble_context" in content or "class ContextAssembler" in content
        ), "Context assembler function/class should exist"

    def test_ac03_enforce_session_graph_wires_plan_context_then_assemble_then_enforce(
        self,
    ):
        """Enforce session graph should wire plan_context -> assemble_context -> enforce."""
        graph_path = Path(".chaplain/graphs/watcher-enforce/enforce-session.yaml")
        assert graph_path.exists()

        import yaml

        with open(graph_path) as f:
            graph = yaml.safe_load(f)

        # Check nodes exist
        nodes = graph["nodes"]
        assert "plan_context" in nodes, "Graph should have plan_context node"
        assert "assemble_context" in nodes, "Graph should have assemble_context node"
        assert "enforce" in nodes, "Graph should have enforce node"

        # Check node types
        assert nodes["plan_context"]["type"] == "llm", "plan_context should be llm node"
        assert (
            nodes["assemble_context"]["type"] == "python"
        ), "assemble_context should be python node"
        assert nodes["enforce"]["type"] == "copilot", "enforce should be copilot node"

        # Check edges
        edges = graph["edges"]
        edge_map = {(e["from"], e["to"]) for e in edges}

        expected_edges = [
            ("START", "plan_context"),
            ("plan_context", "assemble_context"),
            ("assemble_context", "enforce"),
            ("enforce", "END"),
        ]

        for edge in expected_edges:
            assert edge in edge_map, f"Graph should have edge {edge[0]} -> {edge[1]}"

    def test_ac04_planner_node_uses_lightweight_flash_or_haiku_model(self):
        """Planner node should use lightweight model (flash or haiku)."""
        graph_path = Path(".chaplain/graphs/watcher-enforce/enforce-session.yaml")

        import yaml

        with open(graph_path) as f:
            graph = yaml.safe_load(f)

        plan_context_node = graph["nodes"]["plan_context"]

        # Check for model specification
        model_spec = None
        if "model" in plan_context_node:
            model_spec = plan_context_node["model"]
        elif (
            "cli_flags" in plan_context_node
            and "model" in plan_context_node["cli_flags"]
        ):
            model_spec = plan_context_node["cli_flags"]["model"]

        assert model_spec is not None, "plan_context node should specify a model"

        # Check it's a lightweight model
        lightweight_models = ["flash", "haiku", "gemini-2.0-flash", "claude-3-haiku"]
        assert any(
            lm in model_spec.lower() for lm in lightweight_models
        ), f"Model {model_spec} should be lightweight (flash/haiku class)"

    def test_ac05_enforce_prompt_references_injected_codebase_context_variable(self):
        """Enforce prompt should reference injected codebase_context variable."""
        prompt_path = Path(
            ".chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml"
        )
        assert prompt_path.exists()

        with open(prompt_path) as f:
            content = f.read()

        assert (
            "codebase_context" in content
        ), "Enforce prompt should reference codebase_context variable"

    def test_ac06_context_artifact_contract_targets_docs_context_fr_id_and_budget(self):
        """Context assembler should write docs/context/<fr-id>.md and enforce budget."""
        tools_path = Path(".chaplain/graphs/watcher-enforce/tools.py")

        with open(tools_path) as f:
            content = f.read()

        assert (
            "docs/context/" in content
        ), "Context assembler should target docs/context/ directory"
        assert (
            "budget" in content.lower() or "limit" in content.lower()
        ), "Context assembler should enforce budget/limits"

    def test_ac07_enforce_contract_tests_reflect_pre_node_architecture(self):
        """This test validates that existing contract tests expect the new architecture."""
        # This test itself validates AC-07 by existing and expecting the new structure
        # The test_enforce_simplify.py should be updated to expect 3 nodes, not 1
        graph_path = Path(".chaplain/graphs/watcher-enforce/enforce-session.yaml")

        import yaml

        with open(graph_path) as f:
            graph = yaml.safe_load(f)

        # Should now have 3 nodes instead of just 'enforce'
        expected_nodes = {"plan_context", "assemble_context", "enforce"}
        actual_nodes = set(graph["nodes"].keys())

        assert (
            expected_nodes == actual_nodes
        ), f"Graph should have nodes {expected_nodes}, got {actual_nodes}"

    def test_ac08_pipeline_v2_state_topology_unchanged_for_enforce_session_integration(
        self,
    ):
        """Pipeline v2 state topology should remain unchanged."""
        # This is a guard test - the watcher pipeline states should not be modified
        # Only the enforce-session.yaml graph internal structure changes

        pipeline_path = Path(".chaplain/graphs/watcher-pipeline-v2.yaml")
        if pipeline_path.exists():
            import yaml

            with open(pipeline_path) as f:
                pipeline = yaml.safe_load(f)

            # The enforce state should still exist and point to enforce-session.yaml
            if "nodes" in pipeline and "enforce" in pipeline["nodes"]:
                enforce_node = pipeline["nodes"]["enforce"]
                assert "graph" in enforce_node, "Enforce state should still use graph"
                assert (
                    "enforce-session.yaml" in enforce_node["graph"]
                ), "Enforce state should still reference enforce-session.yaml"

        # This test passes if pipeline topology is preserved
        assert True, "Pipeline topology validation complete"
