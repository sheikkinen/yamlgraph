"""Tests for FR-685 — Genesis self-correcting pipeline.

REQ-YG-516: Genesis gate-route-fix loop
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()


# ---------- AC-1/AC-2: Gate routing in genesis.yaml ----------


class TestGenesisGateRouting:
    """AC-1/AC-2: validate → conditional edge → persist or fix_stubs."""

    @pytest.mark.req("REQ-YG-516")
    def test_conditional_edge_valid_to_persist(self) -> None:
        """gate_result.valid == true routes to persist."""
        with open(NOVEL_FANDOM_DIR / "genesis.yaml") as f:
            config = yaml.safe_load(f)
        edges = config["edges"]
        valid_edge = next(
            (
                e
                for e in edges
                if e.get("from") == "validate"
                and e.get("condition") == "gate_result.valid == true"
            ),
            None,
        )
        assert valid_edge is not None, "Missing valid→persist conditional edge"
        assert valid_edge["to"] == "persist"

    @pytest.mark.req("REQ-YG-516")
    def test_conditional_edge_invalid_to_fix_stubs(self) -> None:
        """gate_result.valid == false routes to fix_stubs."""
        with open(NOVEL_FANDOM_DIR / "genesis.yaml") as f:
            config = yaml.safe_load(f)
        edges = config["edges"]
        invalid_edge = next(
            (
                e
                for e in edges
                if e.get("from") == "validate"
                and e.get("condition") == "gate_result.valid == false"
            ),
            None,
        )
        assert invalid_edge is not None, "Missing invalid→fix_stubs conditional edge"
        assert invalid_edge["to"] == "fix_stubs"

    @pytest.mark.req("REQ-YG-516")
    def test_fix_stubs_loops_back_to_validate(self) -> None:
        """fix_stubs → validate edge exists for the repair loop."""
        with open(NOVEL_FANDOM_DIR / "genesis.yaml") as f:
            config = yaml.safe_load(f)
        edges = config["edges"]
        loop_edge = next(
            (
                e
                for e in edges
                if e.get("from") == "fix_stubs" and e.get("to") == "validate"
            ),
            None,
        )
        assert loop_edge is not None, "Missing fix_stubs→validate loop edge"


# ---------- AC-3: fix_stubs LLM node ----------


class TestFixStubsNode:
    """AC-3: fix_stubs is an LLM node with fix_refs prompt."""

    @pytest.mark.req("REQ-YG-516")
    def test_fix_stubs_node_exists(self) -> None:
        """genesis.yaml has a fix_stubs node."""
        with open(NOVEL_FANDOM_DIR / "genesis.yaml") as f:
            config = yaml.safe_load(f)
        assert "fix_stubs" in config["nodes"], "fix_stubs node missing"

    @pytest.mark.req("REQ-YG-516")
    def test_fix_stubs_is_llm_type(self) -> None:
        """fix_stubs node is type: llm."""
        with open(NOVEL_FANDOM_DIR / "genesis.yaml") as f:
            config = yaml.safe_load(f)
        node = config["nodes"]["fix_stubs"]
        assert node["type"] == "llm"

    @pytest.mark.req("REQ-YG-516")
    def test_fix_stubs_writes_structured_world(self) -> None:
        """fix_stubs outputs to structured_world (same key as stubs)."""
        with open(NOVEL_FANDOM_DIR / "genesis.yaml") as f:
            config = yaml.safe_load(f)
        node = config["nodes"]["fix_stubs"]
        assert node["state_key"] == "structured_world"

    @pytest.mark.req("REQ-YG-516")
    def test_fix_refs_prompt_exists(self) -> None:
        """prompts/fix_genesis_refs.yaml exists."""
        path = NOVEL_FANDOM_DIR / "prompts" / "fix_genesis_refs.yaml"
        assert path.exists(), f"fix_genesis_refs.yaml missing: {path}"


# ---------- AC-4: loop_limits ----------


class TestLoopLimits:
    """AC-4: loop_limits caps validate cycles."""

    @pytest.mark.req("REQ-YG-516")
    def test_validate_loop_limit(self) -> None:
        """loop_limits: validate: 3 is set."""
        with open(NOVEL_FANDOM_DIR / "genesis.yaml") as f:
            config = yaml.safe_load(f)
        limits = config.get("loop_limits", {})
        assert (
            limits.get("validate") == 3
        ), f"Expected loop_limits.validate == 3, got {limits}"

    @pytest.mark.req("REQ-YG-516")
    def test_fix_stubs_loop_limit(self) -> None:
        """loop_limits: fix_stubs: 3 for safety."""
        with open(NOVEL_FANDOM_DIR / "genesis.yaml") as f:
            config = yaml.safe_load(f)
        limits = config.get("loop_limits", {})
        assert limits.get("fix_stubs") == 3


# ---------- AC-6: Genesis lints clean ----------


class TestGenesisLints:
    """AC-6: genesis.yaml still passes graph lint."""

    @pytest.mark.req("REQ-YG-516")
    def test_genesis_yaml_lints(self) -> None:
        """genesis.yaml loads without error."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(str(NOVEL_FANDOM_DIR / "genesis.yaml"))
        assert config.name == "novel-fandom-genesis"
