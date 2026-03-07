"""Tests for FR-113: W015 skip_if_exists in cycle lint check.

Tests the linter warning W015 which fires when a node in a cycle
has explicit `skip_if_exists: true` set, which would cause it to
cache its first output and return stale results on every iteration.
"""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "linter"


class TestLinterW015:
    """Linter should warn when cycle node has explicit skip_if_exists: true."""

    @pytest.mark.req("REQ-YG-113")
    def test_w015_fires_on_explicit_skip_if_exists_true_in_cycle(self):
        """Cycle node with explicit skip_if_exists: true should produce W015."""
        from yamlgraph.linter.checks_semantic import check_skip_if_exists_in_cycle

        issues = check_skip_if_exists_in_cycle(
            FIXTURES_DIR / "skip_exists_cycle_explicit_true.yaml"
        )

        codes = [i.code for i in issues]
        assert "W015" in codes
        # The generate node has explicit skip_if_exists: true
        messages = " ".join(i.message for i in issues)
        assert "generate" in messages

    @pytest.mark.req("REQ-YG-113")
    def test_w015_does_not_fire_when_skip_if_exists_absent(self):
        """Cycle node without skip_if_exists should NOT produce W015.

        Runtime handles default via apply_loop_node_defaults().
        """
        from yamlgraph.linter.checks_semantic import check_skip_if_exists_in_cycle

        issues = check_skip_if_exists_in_cycle(
            FIXTURES_DIR / "skip_exists_cycle_absent.yaml"
        )

        codes = [i.code for i in issues]
        assert "W015" not in codes

    @pytest.mark.req("REQ-YG-113")
    def test_w015_does_not_fire_when_skip_if_exists_false(self):
        """Cycle node with explicit skip_if_exists: false should NOT produce W015.

        This is the correct configuration.
        """
        from yamlgraph.linter.checks_semantic import check_skip_if_exists_in_cycle

        issues = check_skip_if_exists_in_cycle(
            FIXTURES_DIR / "skip_exists_cycle_explicit_false.yaml"
        )

        codes = [i.code for i in issues]
        assert "W015" not in codes

    @pytest.mark.req("REQ-YG-113")
    def test_w015_does_not_fire_on_acyclic_graph(self):
        """Acyclic graph with skip_if_exists: true should NOT produce W015.

        skip_if_exists: true is perfectly valid outside cycles.
        """
        from yamlgraph.linter.checks_semantic import check_skip_if_exists_in_cycle

        issues = check_skip_if_exists_in_cycle(
            FIXTURES_DIR / "skip_exists_acyclic.yaml"
        )

        codes = [i.code for i in issues]
        assert "W015" not in codes

    @pytest.mark.req("REQ-YG-113")
    def test_w015_registered_in_lint_graph(self):
        """lint_graph should include W015 checks."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(FIXTURES_DIR / "skip_exists_cycle_explicit_true.yaml")

        codes = [i.code for i in result.issues]
        assert "W015" in codes
