"""Tests for FR-686 — Novel Fandom Agent-First Rewrite.

REQ-YG-518: Genesis agent node with creation tools
REQ-YG-519: Atomic create_* tools with single-line returns
REQ-YG-520: Worldgen agent node (no map nodes)
REQ-YG-521: Graph-tools self-load canon (agent passes IDs only)
REQ-YG-522: Deterministic terminal gate after agent
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()

_nf_str = str(NOVEL_FANDOM_DIR)
if _nf_str not in sys.path:
    sys.path.insert(0, _nf_str)

_nodes_str = str(NOVEL_FANDOM_DIR / "nodes")
if _nodes_str not in sys.path:
    sys.path.insert(0, _nodes_str)


def _load(mod_name: str, rel_path: str):  # noqa: ANN202
    fpath = NOVEL_FANDOM_DIR / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_graph(name: str) -> dict:
    with open(NOVEL_FANDOM_DIR / name) as f:
        return yaml.safe_load(f)


# ============================================================
# REQ-YG-518: Genesis is a single agent node
# ============================================================


class TestGenesisAgentStructure:
    """AC-1: genesis.yaml has a single agent node for entity creation."""

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_has_agent_node(self) -> None:
        """Genesis graph contains a 'genesis' node of type: agent."""
        config = _load_graph("genesis.yaml")
        assert "genesis" in config["nodes"]
        assert config["nodes"]["genesis"]["type"] == "agent"

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_no_llm_entity_nodes(self) -> None:
        """No type: llm nodes for entity generation (synopsis is allowed)."""
        config = _load_graph("genesis.yaml")
        for name, node in config["nodes"].items():
            if name == "synopsis":
                continue  # AC-1 amendment: synopsis is separate LLM node
            assert (
                node.get("type") != "llm"
            ), f"Node '{name}' is type: llm — FR-686 forbids LLM entity generation"

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_agent_has_creation_tools(self) -> None:
        """Genesis agent has create_character, create_event, etc."""
        config = _load_graph("genesis.yaml")
        agent = config["nodes"]["genesis"]
        tools = agent.get("tools", [])
        for tool_name in (
            "create_character",
            "create_event",
            "create_faction",
            "create_location",
            "create_rule",
        ):
            assert tool_name in tools, f"Missing tool: {tool_name}"

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_agent_has_ref_check_graph_tool(self) -> None:
        """AC-3 (amended): ref_check is in agent tools for final audit."""
        config = _load_graph("genesis.yaml")
        agent = config["nodes"]["genesis"]
        tools = agent.get("tools", [])
        assert "ref_check" in tools

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_synopsis_is_separate_llm_node(self) -> None:
        """Judgement Finding 6: synopsis is separate type: llm node."""
        config = _load_graph("genesis.yaml")
        assert "synopsis" in config["nodes"]
        assert config["nodes"]["synopsis"]["type"] == "llm"

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_agent_has_list_canon_ids(self) -> None:
        """Agent can track progress via list_canon_ids."""
        config = _load_graph("genesis.yaml")
        agent = config["nodes"]["genesis"]
        tools = agent.get("tools", [])
        assert "list_canon_ids" in tools

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_has_persist_synopsis_node(self) -> None:
        """AC-6: persist_synopsis node between synopsis LLM and agent."""
        config = _load_graph("genesis.yaml")
        assert "persist_synopsis" in config["nodes"]
        assert config["nodes"]["persist_synopsis"]["type"] == "python"

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_persist_synopsis_before_agent(self) -> None:
        """Edge: synopsis → persist_synopsis → genesis."""
        config = _load_graph("genesis.yaml")
        edges = config["edges"]
        syn_to_persist = any(
            e.get("from") == "synopsis" and e.get("to") == "persist_synopsis"
            for e in edges
        )
        persist_to_agent = any(
            e.get("from") == "persist_synopsis" and e.get("to") == "genesis"
            for e in edges
        )
        assert syn_to_persist, "Missing edge: synopsis → persist_synopsis"
        assert persist_to_agent, "Missing edge: persist_synopsis → genesis"

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_agent_has_update_refs(self) -> None:
        """FR-689: update_refs replaces standalone dedup_check."""
        config = _load_graph("genesis.yaml")
        agent = config["nodes"]["genesis"]
        tools = agent.get("tools", [])
        assert "update_refs" in tools

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_graph_lints(self) -> None:
        """genesis.yaml loads without error."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(str(NOVEL_FANDOM_DIR / "genesis.yaml"))
        assert config.name == "novel-fandom-genesis"


# ============================================================
# REQ-YG-519: Creation tools — graph-tool pipelines
# Each create_*.yaml is persist → prefetch → LLM check
# ============================================================


class TestCreationToolPipelines:
    """AC-2/AC-8: create_* tools are graph-tool pipelines with LLM check."""

    @pytest.mark.req("REQ-YG-519")
    @pytest.mark.parametrize(
        "graph_file",
        [
            "create_character.yaml",
            "create_event.yaml",
            "create_faction.yaml",
            "create_location.yaml",
            "create_rule.yaml",
            "create_premise.yaml",
        ],
    )
    def test_create_graph_is_type_graph_tool(self, graph_file: str) -> None:
        """Each create_* is declared as type: graph in genesis.yaml."""
        config = _load_graph("genesis.yaml")
        tool_name = graph_file.replace(".yaml", "")
        tools = config.get("tools", {})
        assert tool_name in tools, f"Missing tool definition: {tool_name}"
        assert (
            tools[tool_name].get("type") == "graph"
        ), f"{tool_name} must be type: graph (FR-658 showcase)"

    @pytest.mark.req("REQ-YG-519")
    @pytest.mark.parametrize(
        "graph_file",
        [
            "create_character.yaml",
            "create_event.yaml",
            "create_faction.yaml",
            "create_location.yaml",
            "create_rule.yaml",
            "create_premise.yaml",
        ],
    )
    def test_create_graph_has_llm_check_node(self, graph_file: str) -> None:
        """AC-8: Each create_*.yaml has an LLM node for semantic check."""
        config = _load_graph(graph_file)
        nodes = config.get("nodes", {})
        llm_nodes = [n for n, v in nodes.items() if v.get("type") == "llm"]
        assert (
            len(llm_nodes) >= 1
        ), f"{graph_file} must have at least one LLM check node (AC-8)"

    @pytest.mark.req("REQ-YG-519")
    @pytest.mark.parametrize(
        "graph_file",
        [
            "create_character.yaml",
            "create_event.yaml",
            "create_faction.yaml",
            "create_location.yaml",
            "create_rule.yaml",
            "create_premise.yaml",
        ],
    )
    def test_create_graph_has_persist_node(self, graph_file: str) -> None:
        """Each create_*.yaml has a persist python node."""
        config = _load_graph(graph_file)
        nodes = config.get("nodes", {})
        persist_nodes = [
            n for n, v in nodes.items() if v.get("type") == "python" and "persist" in n
        ]
        assert len(persist_nodes) >= 1, f"{graph_file} must have a persist node"

    @pytest.mark.req("REQ-YG-519")
    @pytest.mark.parametrize(
        "graph_file",
        [
            "create_character.yaml",
            "create_event.yaml",
            "create_faction.yaml",
            "create_location.yaml",
            "create_rule.yaml",
            "create_premise.yaml",
        ],
    )
    def test_create_graph_has_conditional_skip(self, graph_file: str) -> None:
        """LLM check is skipped when persist fails (check_skip condition)."""
        config = _load_graph(graph_file)
        edges = config.get("edges", [])
        has_condition = any(e.get("condition") or e.get("conditions") for e in edges)
        assert (
            has_condition
        ), f"{graph_file} must have conditional edge to skip LLM on persist failure"


class TestPersistEntityNode:
    """Test persist_entity node function (unit-level, no LLM)."""

    @pytest.fixture
    def canon_dir(self, tmp_path: Path, monkeypatch) -> Path:
        d = tmp_path / "canon"
        d.mkdir()
        mod = _load("nf_creation_tools_686", "nodes/creation_tools.py")
        monkeypatch.setattr(mod, "_CANON_DIR", d)
        return d

    @pytest.fixture
    def tools_mod(self, canon_dir):  # noqa: ANN202
        return sys.modules["nf_creation_tools_686"]

    @pytest.mark.req("REQ-YG-519")
    @pytest.mark.req("REQ-YG-506")
    def test_persist_character(self, tools_mod, canon_dir: Path) -> None:
        result = tools_mod.persist_entity(
            {
                "entity_type": "character",
                "id": "hilde",
                "name": "Hilde",
                "role": "protagonist",
                "faction": "",
                "summary": "War-leader of the Aschenwulf clan",
            }
        )
        assert "Created character hilde" in result["result"]
        assert (canon_dir / "character" / "hilde.yaml").exists()

    @pytest.mark.req("REQ-YG-519")
    def test_persist_event(self, tools_mod, canon_dir: Path) -> None:
        result = tools_mod.persist_entity(
            {
                "entity_type": "event",
                "id": "great_flood",
                "year": "0",
                "scope": "world",
                "participants": "",
                "consequences": "Destroyed old settlements",
                "summary": "The great flood",
            }
        )
        assert "Created event great_flood" in result["result"]
        assert (canon_dir / "event" / "great_flood.yaml").exists()

    @pytest.mark.req("REQ-YG-519")
    def test_persist_faction(self, tools_mod, canon_dir: Path) -> None:
        result = tools_mod.persist_entity(
            {
                "entity_type": "faction",
                "id": "aschenwulf",
                "name": "Aschenwulf",
                "description": "Wolf clan from the ash forests",
                "members": "",
            }
        )
        assert "Created faction aschenwulf" in result["result"]
        assert (canon_dir / "faction" / "aschenwulf.yaml").exists()

    @pytest.mark.req("REQ-YG-519")
    def test_persist_location(self, tools_mod, canon_dir: Path) -> None:
        result = tools_mod.persist_entity(
            {
                "entity_type": "location",
                "id": "high_valley",
                "name": "High Valley",
                "description": "The only ground above the flood",
                "location_type": "valley",
            }
        )
        assert "Created location high_valley" in result["result"]
        assert (canon_dir / "location" / "high_valley.yaml").exists()

    @pytest.mark.req("REQ-YG-519")
    def test_persist_rule(self, tools_mod, canon_dir: Path) -> None:
        result = tools_mod.persist_entity(
            {
                "entity_type": "rule",
                "id": "flood_myth",
                "domain": "social_rule",
                "title": "The flood is divine judgement",
                "description": "Elders teach the flood was sent by the old gods",
            }
        )
        assert "Created rule flood_myth" in result["result"]
        assert (canon_dir / "rule" / "flood_myth.yaml").exists()

    @pytest.mark.req("REQ-YG-519")
    def test_persist_returns_error_on_bad_role(
        self, tools_mod, canon_dir: Path
    ) -> None:
        """Invalid role returns error string, does NOT crash."""
        result = tools_mod.persist_entity(
            {
                "entity_type": "character",
                "id": "x",
                "name": "X",
                "role": "wizard",
                "faction": "",
                "summary": "test",
            }
        )
        assert "Error" in result["result"]
        assert "wizard" in result["result"]
        assert "Usage:" in result["result"]

    @pytest.mark.req("REQ-YG-519")
    def test_persist_returns_error_on_unknown_type(self, tools_mod) -> None:
        result = tools_mod.persist_entity({"entity_type": "dragon"})
        assert result["result"].startswith("Error:")

    @pytest.mark.req("REQ-YG-519")
    def test_persisted_yaml_has_correct_schema(
        self, tools_mod, canon_dir: Path
    ) -> None:
        """Written YAML passes Pydantic validation."""
        tools_mod.persist_entity(
            {
                "entity_type": "character",
                "id": "hilde",
                "name": "Hilde",
                "role": "protagonist",
                "faction": "",
                "summary": "War-leader",
            }
        )
        page_path = canon_dir / "character" / "hilde.yaml"
        page = yaml.safe_load(page_path.read_text())
        assert page["type"] == "character"
        assert page["id"] == "hilde"
        assert page["lane"] == "dynamic"
        assert page["depth"] == 0


class TestBuildCheckContext:
    """Test build_check_context — digest + ref prefetch."""

    @pytest.fixture
    def canon_dir(self, tmp_path: Path, monkeypatch) -> Path:
        d = tmp_path / "canon"
        d.mkdir()
        mod = _load("nf_creation_tools_ctx", "nodes/creation_tools.py")
        monkeypatch.setattr(mod, "_CANON_DIR", d)
        # Also patch the canon_tools module that build_check_context imports
        import canon_tools

        monkeypatch.setattr(canon_tools, "_CANON_DIR", d)
        return d

    @pytest.fixture
    def tools_mod(self, canon_dir):  # noqa: ANN202
        return sys.modules["nf_creation_tools_ctx"]

    @pytest.mark.req("REQ-YG-521")
    def test_check_context_skips_on_error(self, tools_mod) -> None:
        """If persist_entity failed, build_check_context returns check_skip=true."""
        result = tools_mod.build_check_context({"result": "Error: bad input"})
        assert result["check_skip"] is True

    @pytest.mark.req("REQ-YG-521")
    def test_check_context_builds_digest(self, tools_mod, canon_dir: Path) -> None:
        """After persist, check_context builds a digest of existing canon."""
        # Write a page to canon
        char_dir = canon_dir / "character"
        char_dir.mkdir()
        page = {
            "type": "character",
            "id": "hilde",
            "name": "Hilde",
            "personality": "War-leader",
            "relationships": [],
            "lane": "dynamic",
            "depth": 0,
            "role": "protagonist",
            "faction": "",
        }
        (char_dir / "hilde.yaml").write_text(yaml.dump(page))

        result = tools_mod.build_check_context(
            {
                "result": "Created character hilde",
                "persisted_page": page,
            }
        )
        assert result["check_skip"] is False
        assert "hilde" in result["digest"]


# ============================================================
# REQ-YG-520: Worldgen is a single agent node (no map)
# ============================================================


class TestWorldgenAgentStructure:
    """AC-4: worldgen.yaml has a single agent node, no map nodes."""

    @pytest.mark.req("REQ-YG-520")
    def test_worldgen_has_agent_node(self) -> None:
        config = _load_graph("worldgen.yaml")
        assert "worldgen" in config["nodes"]
        assert config["nodes"]["worldgen"]["type"] == "agent"

    @pytest.mark.req("REQ-YG-520")
    def test_worldgen_no_map_nodes(self) -> None:
        """No type: map nodes — agent decides work order."""
        config = _load_graph("worldgen.yaml")
        for name, node in config["nodes"].items():
            assert (
                node.get("type") != "map"
            ), f"Node '{name}' is type: map — FR-686 forbids map nodes"

    @pytest.mark.req("REQ-YG-520")
    def test_worldgen_agent_has_update_refs(self) -> None:
        """FR-689: update_refs replaces standalone dedup_check."""
        config = _load_graph("worldgen.yaml")
        agent = config["nodes"]["worldgen"]
        tools = agent.get("tools", [])
        assert "update_refs" in tools

    @pytest.mark.req("REQ-YG-520")
    def test_worldgen_agent_has_ref_check(self) -> None:
        """ref_check graph-tool in worldgen agent tools."""
        config = _load_graph("worldgen.yaml")
        agent = config["nodes"]["worldgen"]
        tools = agent.get("tools", [])
        assert "ref_check" in tools

    @pytest.mark.req("REQ-YG-520")
    def test_worldgen_create_tools_are_graph_type(self) -> None:
        """All create_* tools in worldgen are type: graph."""
        config = _load_graph("worldgen.yaml")
        tools = config.get("tools", {})
        for name, tool in tools.items():
            if name.startswith("create_"):
                assert (
                    tool.get("type") == "graph"
                ), f"{name} must be type: graph in worldgen.yaml"

    @pytest.mark.req("REQ-YG-520")
    def test_worldgen_graph_lints(self) -> None:
        """worldgen.yaml loads without error."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(str(NOVEL_FANDOM_DIR / "worldgen.yaml"))
        assert config.name == "novel-fandom-worldgen"


# ============================================================
# REQ-YG-521: Graph-tools self-load canon
# ============================================================


class TestGraphToolsSelfLoad:
    """Finding 2: graph-tools must self-load canon; agent passes only IDs."""

    @pytest.mark.req("REQ-YG-521")
    def test_ref_check_graph_loads_canon_internally(self) -> None:
        """ref_check.yaml does NOT require pages as input."""
        config = _load_graph("ref_check.yaml")
        has_self_load = any(
            n.get("tool") in ("reload_canon", "load_canon")
            for n in config.get("nodes", {}).values()
        )
        assert has_self_load, "ref_check.yaml must self-load canon"

    @pytest.mark.req("REQ-YG-521")
    def test_ref_check_has_llm_audit_node(self) -> None:
        """AC-3: ref_check.yaml contains LLM judgment, not just python."""
        config = _load_graph("ref_check.yaml")
        nodes = config.get("nodes", {})
        llm_nodes = [n for n, v in nodes.items() if v.get("type") == "llm"]
        assert len(llm_nodes) >= 1, "ref_check.yaml must have LLM audit node (AC-3)"

    @pytest.mark.req("REQ-YG-521")
    def test_dedup_check_graph_loads_canon_internally(self) -> None:
        """semantic_dedup.yaml does NOT require full canon_pages from agent."""
        config = _load_graph("semantic_dedup.yaml")
        has_self_load = any(
            n.get("tool") in ("reload_canon", "load_canon")
            for n in config.get("nodes", {}).values()
        )
        assert has_self_load, "semantic_dedup.yaml must self-load canon"

    @pytest.mark.req("REQ-YG-521")
    def test_ref_check_tool_input_is_minimal(self) -> None:
        """Agent-facing ref_check tool takes no args."""
        config = _load_graph("genesis.yaml")
        tools = config.get("tools", {})
        rc = tools.get("ref_check", {})
        input_mapping = rc.get("input_mapping", {})
        assert not input_mapping, "ref_check input_mapping should be empty (self-loads)"

    @pytest.mark.req("REQ-YG-521")
    def test_create_graphs_self_load_via_persist_node(self) -> None:
        """create_*.yaml pipelines self-load canon in build_check_context."""
        for graph_file in (
            "create_character.yaml",
            "create_event.yaml",
            "create_faction.yaml",
            "create_location.yaml",
            "create_rule.yaml",
            "create_premise.yaml",
        ):
            config = _load_graph(graph_file)
            nodes = config.get("nodes", {})
            has_prefetch = any(
                "prefetch" in n or "context" in n or "check" in n for n in nodes
            )
            assert has_prefetch, f"{graph_file} must have a prefetch/context node"


# ============================================================
# REQ-YG-522: Terminal gate after agent
# ============================================================


class TestTerminalGate:
    """AC-10: Deterministic gate after agent surfaces orphan refs."""

    @pytest.mark.req("REQ-YG-522")
    @pytest.mark.req("REQ-YG-516")
    def test_genesis_has_final_gate_node(self) -> None:
        """genesis.yaml has a gate node after the agent."""
        config = _load_graph("genesis.yaml")
        nodes = config["nodes"]
        gate_names = [
            n
            for n, v in nodes.items()
            if v.get("type") == "python" and ("gate" in n or "validate" in n)
        ]
        assert len(gate_names) >= 1, "Missing deterministic final gate node"

    @pytest.mark.req("REQ-YG-522")
    def test_genesis_gate_runs_after_agent(self) -> None:
        """Edge from genesis agent to gate node exists."""
        config = _load_graph("genesis.yaml")
        edges = config["edges"]
        agent_to_gate = any(
            e.get("from") == "genesis" and "gate" in e.get("to", "") for e in edges
        )
        assert agent_to_gate, "Missing edge: genesis → final_gate"

    @pytest.mark.req("REQ-YG-522")
    def test_worldgen_has_final_gate_node(self) -> None:
        """worldgen.yaml has a gate node after the agent."""
        config = _load_graph("worldgen.yaml")
        nodes = config["nodes"]
        gate_names = [
            n
            for n, v in nodes.items()
            if v.get("type") == "python" and ("gate" in n or "validate" in n)
        ]
        assert len(gate_names) >= 1, "Missing deterministic final gate node"


# ============================================================
# Retirement: old files must not exist
# ============================================================


class TestRetiredFiles:
    """Finding 8: retired files are deleted, not just unreferenced."""

    @pytest.mark.req("REQ-YG-518")
    def test_old_genesis_prompts_gone(self) -> None:
        """generate_stubs.yaml and fix_genesis_refs.yaml retired."""
        prompts = NOVEL_FANDOM_DIR / "prompts"
        assert not (prompts / "generate_stubs.yaml").exists()
        assert not (prompts / "fix_genesis_refs.yaml").exists()

    @pytest.mark.req("REQ-YG-520")
    def test_old_worldgen_batch_nodes_gone(self) -> None:
        """split_thin_by_type.py, select_thin.py, collect_red_links.py, apply_merge_map.py retired."""
        nodes = NOVEL_FANDOM_DIR / "nodes"
        for old_file in (
            "split_thin_by_type.py",
            "select_thin.py",
            "collect_red_links.py",
            "apply_merge_map.py",
        ):
            assert not (
                nodes / old_file
            ).exists(), f"Retired file still exists: {old_file}"
