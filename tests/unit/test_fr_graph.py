"""FR-814: Tests for FR knowledge graph extraction.

Tests cover: accuracy against validation fixture, determinism,
cycle detection on causal edges only, and staleness detection.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from scripts.extract_fr_graph import (
    check_staleness,
    classify_edge,
    detect_cycles,
    extract_graph,
    parse_fr_id,
    parse_metadata,
    write_graph,
)


@pytest.mark.req("REQ-YG-601")
class TestMetadataParsing:
    def test_parse_fr_id(self):
        assert parse_fr_id("FR-813-run-graph-async.md") == "FR-813"
        assert parse_fr_id("FR-071-thinking-budget.md") == "FR-071"
        assert parse_fr_id("random-file.md") is None

    def test_parse_metadata(self):
        text = (
            "**Priority:** HIGH\n"
            "**Type:** Bug\n"
            "**Status:** Enforced 2026-08-17\n"
            "**Requested:** 2026-08-17\n"
        )
        meta = parse_metadata(text)
        assert meta["priority"] == "high"
        assert meta["type"] == "bug"
        assert meta["status"] == "enforced"
        assert meta["requested"] == "2026-08-17"


@pytest.mark.req("REQ-YG-601")
class TestEdgeClassification:
    def test_depends_on_keyword(self):
        line = "This depends on FR-811 for the OTel boundary"
        etype, conf, rule = classify_edge(line, "Problem", 18, "", 1)
        assert etype == "depends_on"
        assert conf == 1.0

    def test_regression_keyword(self):
        line = "FR-811 introduced this regression in v0.5.21"
        etype, conf, rule = classify_edge(line, "Problem", 0, "", 1)
        assert etype == "regression_of"

    def test_substrate_keyword(self):
        line = "Built on top of FR-723 route logging substrate"
        etype, conf, rule = classify_edge(line, "Related", 18, "", 1)
        assert etype == "substrate"

    def test_prior_art_section(self):
        line = "- FR-723: Route evidence visualization"
        etype, conf, rule = classify_edge(line, "Related", 2, "", 1)
        assert etype == "prior_art"

    def test_prior_art_marker(self):
        line = "**Prior art:** FR-811 is the governing OTel boundary"
        etype, conf, rule = classify_edge(line, "Summary", 16, "", 1)
        assert etype == "prior_art"

    def test_inverse_prerequisite(self):
        line = "This is the prerequisite for FR-431 routing"
        etype, conf, rule = classify_edge(line, "Summary", 30, "", 1)
        assert etype == "mentions"
        assert "inverse" in rule

    def test_inverse_depends_on_this(self):
        line = "FR-756 depends on this FR's ruling"
        etype, conf, rule = classify_edge(line, "Related", 0, "", 1)
        assert etype == "mentions"
        assert "inverse" in rule

    def test_unclassified_falls_to_mentions(self):
        line = "See also FR-100 for the ebook pipeline"
        etype, conf, rule = classify_edge(line, "Summary", 9, "", 1)
        assert etype == "mentions"
        assert conf == 0.5


@pytest.mark.req("REQ-YG-601")
class TestValidationFixture:
    """AC-03: >85% accuracy on labelled references."""

    @pytest.fixture
    def fixture_data(self):
        path = Path("tests/fixtures/fr_graph_validation.yaml")
        return yaml.safe_load(path.read_text())

    @pytest.fixture
    def graph_data(self):
        path = Path("reference/fr-knowledge-graph.yaml")
        if not path.exists():
            pytest.skip("Generated graph not present")
        return yaml.safe_load(path.read_text())

    def test_accuracy_above_85_percent(self, fixture_data, graph_data):
        """Check that heuristic typing matches manual labels."""
        correct = 0
        total = 0
        ambiguous = 0
        mismatches = []

        for ref in fixture_data["references"]:
            if ref.get("ambiguous"):
                ambiguous += 1
                continue

            total += 1
            source = ref["source"]
            target = ref["target"]
            expected = ref["expected_type"]

            # Compact keys in output: s, t, type
            # 'mentions' edges excluded from output file
            if expected == "mentions":
                # Verify not mis-typed as something stronger
                wrong = [
                    e
                    for e in graph_data["edges"]
                    if e["s"] == source and e["t"] == target
                ]
                if not wrong:
                    correct += 1
                else:
                    mismatches.append(
                        f"  {source}→{target}: expected=mentions(excluded), "
                        f"got={[e['type'] for e in wrong]}"
                    )
                continue

            matching = [
                e
                for e in graph_data["edges"]
                if e["s"] == source and e["t"] == target and e["type"] == expected
            ]
            if matching:
                correct += 1
            else:
                actual = [
                    e
                    for e in graph_data["edges"]
                    if e["s"] == source and e["t"] == target
                ]
                actual_types = [e["type"] for e in actual]
                mismatches.append(
                    f"  {source}→{target}: expected={expected}, got={actual_types}"
                )

        accuracy = correct / total if total > 0 else 0
        msg = (
            f"Accuracy: {correct}/{total} = {accuracy:.1%} "
            f"(ambiguous excluded: {ambiguous})\n"
            f"Mismatches:\n" + "\n".join(mismatches)
        )
        assert accuracy >= 0.85, msg


@pytest.mark.req("REQ-YG-601")
class TestDeterminism:
    """AC-01: Running twice produces identical output."""

    def test_deterministic_output(self):
        graph1 = extract_graph()
        graph2 = extract_graph()
        # Compare serialized form
        with (
            tempfile.NamedTemporaryFile(suffix=".yaml", mode="w") as f1,
            tempfile.NamedTemporaryFile(suffix=".yaml", mode="w") as f2,
        ):
            p1, p2 = Path(f1.name), Path(f2.name)
            write_graph(graph1, p1)
            write_graph(graph2, p2)
            assert p1.read_text() == p2.read_text()


@pytest.mark.req("REQ-YG-601")
class TestCycleDetection:
    """AC-04: Cycles detected only over causal edges."""

    def test_no_cycles_in_associative_only(self):
        """Associative mutual refs should not create cycles."""
        edges = [
            {"source": "FR-1", "target": "FR-2", "type": "prior_art", "causal": False},
            {"source": "FR-2", "target": "FR-1", "type": "prior_art", "causal": False},
        ]
        from scripts.extract_fr_graph import build_causal_dag

        dag = build_causal_dag(edges)
        cycles = detect_cycles(dag)
        assert cycles == []

    def test_cycles_detected_in_causal(self):
        """Genuine causal mutual deps are detected."""
        edges = [
            {"source": "FR-1", "target": "FR-2", "type": "depends_on", "causal": True},
            {"source": "FR-2", "target": "FR-1", "type": "depends_on", "causal": True},
        ]
        from scripts.extract_fr_graph import build_causal_dag

        dag = build_causal_dag(edges)
        cycles = detect_cycles(dag)
        assert len(cycles) == 1


@pytest.mark.req("REQ-YG-601")
class TestStaleness:
    """AC-05: Staleness detection."""

    def test_stale_when_no_output(self, tmp_path):
        fr_dir = tmp_path / "frs"
        fr_dir.mkdir()
        (fr_dir / "FR-001-test.md").write_text("**Status:** Proposed\n")
        output = tmp_path / "graph.yaml"
        assert check_staleness(fr_dir, output) is False

    def test_current_after_generation(self, tmp_path):
        fr_dir = tmp_path / "frs"
        fr_dir.mkdir()
        (fr_dir / "FR-001-test.md").write_text("**Status:** Proposed\n")
        output = tmp_path / "graph.yaml"
        graph = extract_graph(fr_dir)
        write_graph(graph, output)
        assert check_staleness(fr_dir, output) is True

    def test_stale_after_change(self, tmp_path):
        fr_dir = tmp_path / "frs"
        fr_dir.mkdir()
        fr_file = fr_dir / "FR-001-test.md"
        fr_file.write_text("**Status:** Proposed\n")
        output = tmp_path / "graph.yaml"
        graph = extract_graph(fr_dir)
        write_graph(graph, output)
        # Modify source
        fr_file.write_text("**Status:** Implemented\n")
        assert check_staleness(fr_dir, output) is False


@pytest.mark.req("REQ-YG-602")
class TestClusterNaming:
    """FR-816: Cluster display names from member filename nouns."""

    @pytest.fixture
    def graph_data(self):
        path = Path("reference/fr-knowledge-graph.yaml")
        if not path.exists():
            pytest.skip("Generated graph not present")
        return yaml.safe_load(path.read_text())

    def test_schema_version_2(self, graph_data):
        assert graph_data["meta"]["schema_version"] == 2

    def test_clusters_have_name_and_members(self, graph_data):
        for cid, cdata in graph_data["clusters"].items():
            assert isinstance(cdata, dict), f"{cid} is not v2 schema"
            assert "name" in cdata, f"{cid} missing name"
            assert "members" in cdata, f"{cid} missing members"
            assert isinstance(cdata["members"], list)
            assert len(cdata["members"]) >= 2

    def test_cluster_keys_remain_stable(self, graph_data):
        for cid in graph_data["clusters"]:
            assert cid.startswith("cluster-"), f"Key {cid} not stable format"

    def test_naming_deterministic(self):
        from scripts.extract_fr_graph import name_cluster

        fr_map = {
            "FR-723": Path("FR-723-execution-path-visualization.md"),
            "FR-808": Path("FR-808-regulated-evidence-profile.md"),
        }
        name1 = name_cluster(["FR-723", "FR-808"], fr_map)
        name2 = name_cluster(["FR-723", "FR-808"], fr_map)
        assert name1 == name2

    def test_known_clusters_named(self, graph_data):
        named = [
            cid for cid, c in graph_data["clusters"].items() if c["name"] != "unnamed"
        ]
        assert len(named) >= 3

    def test_node_cluster_ids_stable(self, graph_data):
        for _fr_id, meta in graph_data["nodes"].items():
            if "cluster" in meta:
                assert meta["cluster"].startswith("cluster-")


@pytest.mark.req("REQ-YG-603")
class TestCrossClusterMentions:
    """FR-817: Cross-cluster mention report."""

    @pytest.fixture
    def graph_data(self):
        path = Path("reference/fr-knowledge-graph.yaml")
        if not path.exists():
            pytest.skip("Generated graph not present")
        return yaml.safe_load(path.read_text())

    def test_section_present(self, graph_data):
        assert "cross_cluster_mentions" in graph_data

    def test_count_matches_edges(self, graph_data):
        ccm = graph_data["cross_cluster_mentions"]
        assert ccm["count"] == len(ccm["edges"])

    def test_count_under_500(self, graph_data):
        assert graph_data["cross_cluster_mentions"]["count"] < 500

    def test_all_edges_cross_cluster(self, graph_data):
        nodes = graph_data["nodes"]
        for e in graph_data["cross_cluster_mentions"]["edges"]:
            src_cluster = nodes.get(e["s"], {}).get("cluster")
            tgt_cluster = nodes.get(e["t"], {}).get("cluster")
            assert src_cluster is not None, f"{e['s']} has no cluster"
            assert tgt_cluster is not None, f"{e['t']} has no cluster"
            assert (
                src_cluster != tgt_cluster
            ), f"{e['s']}({src_cluster}) and {e['t']}({tgt_cluster}) same cluster"

    def test_edges_deterministic_order(self, graph_data):
        edges = graph_data["cross_cluster_mentions"]["edges"]
        keys = [(e["s"], e["t"], e["ln"]) for e in edges]
        assert keys == sorted(keys)

    def test_artifact_under_500kb(self):
        path = Path("reference/fr-knowledge-graph.yaml")
        assert path.stat().st_size < 500 * 1024
