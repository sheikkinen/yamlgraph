"""Tests for FR-689 — Genesis Canon Consistency: Integrated Dedup Gate.

REQ-YG-518: Genesis agent node with creation tools (extended)
REQ-YG-519: Atomic create_* tools with single-line returns (extended)
REQ-YG-522: Deterministic terminal gate after agent (extended)

Bug condemnations:
1. persist_synopsis creates dual synopsis (should clear first)
2. create_* pipelines have no dedup gate (duplicate writes are possible)
3. final_gate doesn't detect cross-type ID collisions
4. No update_refs tool for dangling reference repair
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
# Bug 1: persist_synopsis creates dual synopsis
# ============================================================


class TestPersistSynopsisClearsExisting:
    """persist_synopsis must clear existing synopsis files before writing."""

    @pytest.fixture
    def canon_dir(self, tmp_path: Path, monkeypatch) -> Path:
        d = tmp_path / "canon"
        d.mkdir()
        mod = _load("nf_creation_689_synopsis", "nodes/creation_tools.py")
        monkeypatch.setattr(mod, "_CANON_DIR", d)
        return d

    @pytest.fixture
    def tools_mod(self, canon_dir):  # noqa: ANN202
        return sys.modules["nf_creation_689_synopsis"]

    @pytest.mark.req("REQ-YG-518")
    def test_persist_synopsis_clears_existing(self, tools_mod, canon_dir: Path) -> None:
        """If an old synopsis exists, persist_synopsis must delete it first."""
        # Pre-existing synopsis with different ID
        synopsis_dir = canon_dir / "synopsis"
        synopsis_dir.mkdir(parents=True)
        old = {
            "type": "synopsis",
            "id": "floodmark_saga_synopsis",
            "lane": "dynamic",
            "depth": 0,
            "text": "Old synopsis text with Frida.",
        }
        (synopsis_dir / "floodmark_saga_synopsis.yaml").write_text(yaml.dump(old))

        # Call persist_synopsis — should clear the old one
        tools_mod.persist_synopsis({"synopsis": "New synopsis text with Runa."})

        files = list(synopsis_dir.glob("*.yaml"))
        assert len(files) == 1, (
            f"Expected exactly 1 synopsis file, got {len(files)}: "
            f"{[f.name for f in files]}"
        )
        content = yaml.safe_load(files[0].read_text())
        assert content["id"] == "synopsis"
        assert "Runa" in content["text"]


# ============================================================
# Bug 2: create_* pipelines have no dedup gate
# ============================================================


class TestCreatePipelineHasDedupGate:
    """Each create_*.yaml must have a dedup node before persist."""

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
    def test_create_pipeline_has_dedup_node(self, graph_file: str) -> None:
        """Each create_*.yaml must have a dedup gate node."""
        config = _load_graph(graph_file)
        nodes = config.get("nodes", {})
        has_dedup = any("dedup" in name for name in nodes)
        assert has_dedup, (
            f"{graph_file} has no dedup gate node. "
            "FR-689: dedup must be integrated into creation pipeline."
        )

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
    def test_dedup_runs_before_persist(self, graph_file: str) -> None:
        """Dedup gate must execute before persist (can't undo a disk write)."""
        config = _load_graph(graph_file)
        edges = config.get("edges", [])
        # There must be a path from START to dedup before persist
        dedup_node = None
        for name in config.get("nodes", {}):
            if "dedup" in name:
                dedup_node = name
                break
        if dedup_node is None:
            pytest.skip(
                "No dedup node yet (caught by test_create_pipeline_has_dedup_node)"
            )

        # Dedup must come before persist in the edge graph
        # Either dedup → persist directly, or dedup → route → persist
        # The key constraint: START must NOT lead directly to persist
        start_targets = {e["to"] for e in edges if e.get("from") == "START"}
        assert "persist" not in start_targets, (
            f"{graph_file}: START leads directly to persist — "
            "dedup gate must run before persist"
        )


class TestDedupCheckRemovedFromAgents:
    """dedup_check standalone tool must be removed from agent tool lists."""

    @pytest.mark.req("REQ-YG-518")
    def test_genesis_no_standalone_dedup(self) -> None:
        """Genesis agent must NOT have dedup_check in its tool list."""
        config = _load_graph("genesis.yaml")
        agent = config["nodes"]["genesis"]
        tools = agent.get("tools", [])
        assert "dedup_check" not in tools, (
            "dedup_check must be removed from genesis agent tools — "
            "FR-689: dedup is now integrated into create_* pipelines"
        )

    @pytest.mark.req("REQ-YG-520")
    def test_worldgen_no_standalone_dedup(self) -> None:
        """Worldgen agent must NOT have dedup_check in its tool list."""
        config = _load_graph("worldgen.yaml")
        agent = config["nodes"]["worldgen"]
        tools = agent.get("tools", [])
        assert "dedup_check" not in tools, (
            "dedup_check must be removed from worldgen agent tools — "
            "FR-689: dedup is now integrated into create_* pipelines"
        )


# ============================================================
# Bug 3: final_gate doesn't detect cross-type ID collisions
# ============================================================


class TestFinalGateCrossTypeCollision:
    """final_gate must detect and report cross-type ID collisions."""

    @pytest.fixture
    def canon_dir(self, tmp_path: Path, monkeypatch) -> Path:
        d = tmp_path / "canon"
        d.mkdir()
        mod = _load("nf_creation_689_gate", "nodes/creation_tools.py")
        monkeypatch.setattr(mod, "_CANON_DIR", d)
        import canon_tools

        monkeypatch.setattr(canon_tools, "_CANON_DIR", d)
        return d

    @pytest.fixture
    def tools_mod(self, canon_dir):  # noqa: ANN202
        return sys.modules["nf_creation_689_gate"]

    @pytest.mark.req("REQ-YG-522")
    def test_cross_type_collision_detected(self, tools_mod, canon_dir: Path) -> None:
        """Same ID in event/ and rule/ must be reported as invalid."""
        # Create survival_truce as event
        event_dir = canon_dir / "event"
        event_dir.mkdir()
        event = {
            "type": "event",
            "id": "survival_truce",
            "lane": "dynamic",
            "depth": 0,
            "year": 0,
            "scope": "local",
            "participants": [],
        }
        (event_dir / "survival_truce.yaml").write_text(yaml.dump(event))

        # Same ID as rule
        rule_dir = canon_dir / "rule"
        rule_dir.mkdir()
        rule = {
            "type": "rule",
            "id": "survival_truce",
            "lane": "dynamic",
            "depth": 0,
            "domain": "social_rule",
            "title": "Survival Truce",
            "description": "Temporary truce during flood",
        }
        (rule_dir / "survival_truce.yaml").write_text(yaml.dump(rule))

        result = tools_mod.final_gate({})
        gate = result["gate_result"]
        assert not gate[
            "valid"
        ], "final_gate must report cross-type ID collision as invalid"
        assert "id_collisions" in gate, "gate_result must include 'id_collisions' key"
        assert "survival_truce" in gate["id_collisions"]

    @pytest.mark.req("REQ-YG-522")
    def test_no_collision_passes(self, tools_mod, canon_dir: Path) -> None:
        """Unique IDs across types should pass."""
        event_dir = canon_dir / "event"
        event_dir.mkdir()
        event = {
            "type": "event",
            "id": "great_flood",
            "lane": "dynamic",
            "depth": 0,
            "year": 0,
            "scope": "world",
            "participants": [],
        }
        (event_dir / "great_flood.yaml").write_text(yaml.dump(event))

        rule_dir = canon_dir / "rule"
        rule_dir.mkdir()
        rule = {
            "type": "rule",
            "id": "survival_truce",
            "lane": "dynamic",
            "depth": 0,
            "domain": "social_rule",
            "title": "Survival Truce",
            "description": "Truce rules",
        }
        (rule_dir / "survival_truce.yaml").write_text(yaml.dump(rule))

        result = tools_mod.final_gate({})
        gate = result["gate_result"]
        assert gate["valid"]


# ============================================================
# Fix 2: update_refs tool
# ============================================================


class TestUpdateRefsTool:
    """update_refs must rewrite reference fields across canon."""

    @pytest.fixture
    def canon_dir(self, tmp_path: Path, monkeypatch) -> Path:
        d = tmp_path / "canon"
        d.mkdir()
        mod = _load("nf_creation_689_refs", "nodes/creation_tools.py")
        monkeypatch.setattr(mod, "_CANON_DIR", d)
        return d

    @pytest.fixture
    def tools_mod(self, canon_dir):  # noqa: ANN202
        return sys.modules["nf_creation_689_refs"]

    @pytest.mark.req("REQ-YG-518")
    def test_update_refs_rewrites_participants(
        self, tools_mod, canon_dir: Path
    ) -> None:
        """update_refs replaces old_id with new_id in participants."""
        event_dir = canon_dir / "event"
        event_dir.mkdir()
        event = {
            "type": "event",
            "id": "death_of_ragnar",
            "lane": "dynamic",
            "depth": 0,
            "year": -10,
            "scope": "local",
            "participants": ["ragnar", "gunnar"],
            "references": ["ragnar", "blood_feud"],
        }
        (event_dir / "death_of_ragnar.yaml").write_text(yaml.dump(event))

        result = tools_mod.update_refs({"old_id": "ragnar", "new_id": "hildes_father"})
        assert (
            "updated" in result.get("result", "").lower()
            or "rewritten" in result.get("result", "").lower()
        )

        # Verify file was rewritten
        updated = yaml.safe_load((event_dir / "death_of_ragnar.yaml").read_text())
        assert "hildes_father" in updated["participants"]
        assert "ragnar" not in updated["participants"]
        assert "hildes_father" in updated["references"]
        assert "ragnar" not in updated["references"]

    @pytest.mark.req("REQ-YG-518")
    def test_update_refs_rewrites_relationships(
        self, tools_mod, canon_dir: Path
    ) -> None:
        """update_refs replaces old_id in relationship 'to' fields."""
        char_dir = canon_dir / "character"
        char_dir.mkdir()
        char = {
            "type": "character",
            "id": "hilde",
            "lane": "dynamic",
            "depth": 0,
            "name": "Hilde",
            "role": "protagonist",
            "faction": "",
            "relationships": [
                {"to": "ragnar", "kind": "daughter_of", "valence": "grief"},
            ],
        }
        (char_dir / "hilde.yaml").write_text(yaml.dump(char))

        tools_mod.update_refs({"old_id": "ragnar", "new_id": "hildes_father"})

        updated = yaml.safe_load((char_dir / "hilde.yaml").read_text())
        assert updated["relationships"][0]["to"] == "hildes_father"

    @pytest.mark.req("REQ-YG-518")
    def test_update_refs_rewrites_faction(self, tools_mod, canon_dir: Path) -> None:
        """update_refs replaces old_id in faction field."""
        char_dir = canon_dir / "character"
        char_dir.mkdir()
        char = {
            "type": "character",
            "id": "hilde",
            "lane": "dynamic",
            "depth": 0,
            "name": "Hilde",
            "role": "protagonist",
            "faction": "old_clan",
            "relationships": [],
        }
        (char_dir / "hilde.yaml").write_text(yaml.dump(char))

        tools_mod.update_refs({"old_id": "old_clan", "new_id": "aschenwulf"})

        updated = yaml.safe_load((char_dir / "hilde.yaml").read_text())
        assert updated["faction"] == "aschenwulf"

    @pytest.mark.req("REQ-YG-518")
    def test_update_refs_in_genesis_tools(self) -> None:
        """update_refs must be in genesis agent's tool list."""
        config = _load_graph("genesis.yaml")
        agent = config["nodes"]["genesis"]
        tools = agent.get("tools", [])
        assert "update_refs" in tools, (
            "update_refs must be in genesis agent tools — "
            "FR-689: deadlock prevention for dedup gate refusals"
        )


# ============================================================
# Structural: deterministic pre-check before dedup LLM
# ============================================================


class TestDeterministicPreCheck:
    """Pre-check node runs exact-ID + cross-type collision before LLM."""

    @pytest.fixture
    def canon_dir(self, tmp_path: Path, monkeypatch) -> Path:
        d = tmp_path / "canon"
        d.mkdir()
        mod = _load("nf_creation_689_precheck", "nodes/creation_tools.py")
        monkeypatch.setattr(mod, "_CANON_DIR", d)
        return d

    @pytest.fixture
    def tools_mod(self, canon_dir):  # noqa: ANN202
        return sys.modules["nf_creation_689_precheck"]

    @pytest.mark.req("REQ-YG-519")
    def test_precheck_rejects_exact_id_collision(
        self, tools_mod, canon_dir: Path
    ) -> None:
        """If entity with same ID already exists, refuse before LLM."""
        char_dir = canon_dir / "character"
        char_dir.mkdir()
        existing = {
            "type": "character",
            "id": "hilde",
            "lane": "dynamic",
            "depth": 0,
            "name": "Hilde",
            "role": "protagonist",
            "faction": "",
        }
        (char_dir / "hilde.yaml").write_text(yaml.dump(existing))

        result = tools_mod.dedup_pre_check({"entity_type": "character", "id": "hilde"})
        assert result.get("dedup_refused") is True
        assert "hilde" in result.get("result", "")

    @pytest.mark.req("REQ-YG-519")
    def test_precheck_rejects_cross_type_collision(
        self, tools_mod, canon_dir: Path
    ) -> None:
        """If entity with same ID exists under different type, refuse."""
        event_dir = canon_dir / "event"
        event_dir.mkdir()
        existing = {
            "type": "event",
            "id": "survival_truce",
            "lane": "dynamic",
            "depth": 0,
        }
        (event_dir / "survival_truce.yaml").write_text(yaml.dump(existing))

        result = tools_mod.dedup_pre_check(
            {"entity_type": "rule", "id": "survival_truce"}
        )
        assert result.get("dedup_refused") is True

    @pytest.mark.req("REQ-YG-519")
    def test_precheck_permits_new_id(self, tools_mod, canon_dir: Path) -> None:
        """New ID not in canon passes pre-check."""
        result = tools_mod.dedup_pre_check(
            {"entity_type": "character", "id": "new_char"}
        )
        assert result.get("dedup_refused") is False
