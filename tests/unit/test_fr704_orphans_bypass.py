"""FR-704 Orphans Bypass the Model — Unit tests (LLM-free).

Two field runs reproduced a one-character orphan hash corruption
(703b72d -> 703b72e) in the model's copy-verbatim step. Cure: orphans are
assembled in code by finalize_recap — unreferenced lines copied bit-exact,
convention orphans via a deterministic window rule. The schema keeps only
judgement fields.

Fixtures are verbatim field lines (pattern-freeze heuristic, diary 2026-07-09).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

GRAPH_PATH = "examples/demos/recap/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "recap"
)

# Verbatim from the ninchat_voice field runs — the line the model corrupted
# (it emitted 703b72e twice; the real hash is 703b72d).
CORRUPTED_IN_FIELD = (
    "703b72d|2026-07-08|docs(diary): held against the Letter - "
    "proxy gates validate correlates"
)


def _finalize(recap, **state):
    from examples.demos.recap.nodes.partition import finalize_recap

    return finalize_recap({"recap": recap, **state})


class TestOrphanCopyBitExact:
    """Orphan commit lines never transit the model."""

    @pytest.mark.req("REQ-YG-536")
    def test_field_corruption_class_dead(self) -> None:
        """The exact line the model corrupted twice arrives bit-exact."""
        result = _finalize(
            {"workstreams": [], "hotspots": []},
            unreferenced=CORRUPTED_IN_FIELD,
            churn="",
            fragments="",
            fr_statuses="",
        )
        assert result["recap"]["orphans"] == [CORRUPTED_IN_FIELD]
        assert result["recap"]["orphans"][0].split("|")[0] == "703b72d"

    @pytest.mark.req("REQ-YG-536")
    def test_order_preserved_blanks_skipped(self) -> None:
        """Orphans = unreferenced lines in order; blank lines dropped (J2)."""
        unref = "a1|d|one\n\nb2|d|two\nc3|d|three"
        result = _finalize(
            {"workstreams": []},
            unreferenced=unref,
            churn="",
            fragments="x",
            fr_statuses="",
        )
        assert result["recap"]["orphans"] == ["a1|d|one", "b2|d|two", "c3|d|three"]

    @pytest.mark.req("REQ-YG-536")
    def test_empty_unreferenced_no_convention_churn(self) -> None:
        """Nothing unreferenced, fragments present → empty orphans, no error."""
        result = _finalize(
            {"workstreams": []},
            unreferenced="",
            churn="abc123\n10\t2\tyamlgraph/executor.py",
            fragments="changelog/unreleased/x.md",
            fr_statuses="",
        )
        assert result["recap"]["orphans"] == []


class TestConventionOrphans:
    """Window rule: graph/prompt churn + zero fragments → flagged paths (J3)."""

    CHURN = (
        "abc123\n"
        "5\t1\tgraphs/flex_navigator/prompts/classify_intents.yaml\n"
        "3\t0\tyamlgraph/executor.py\n"
        "2\t2\tprompts/blackbox_judge.yaml\n"
        "1\t1\tgraphs/flex_navigator/prompts/classify_intents.yaml"
    )

    @pytest.mark.req("REQ-YG-536")
    def test_fragmentless_window_flags_graph_prompt_paths(self) -> None:
        """Graph/prompt paths flagged once each (dedup, first occurrence)."""
        result = _finalize(
            {"workstreams": []},
            unreferenced="",
            churn=self.CHURN,
            fragments="",
            fr_statuses="",
        )
        orphans = result["recap"]["orphans"]
        assert len(orphans) == 2
        assert "classify_intents.yaml" in orphans[0]
        assert "blackbox_judge.yaml" in orphans[1]
        assert all("no changelog fragment" in o for o in orphans)
        assert not any("executor.py" in o for o in orphans)

    @pytest.mark.req("REQ-YG-536")
    def test_fragments_present_suppresses_convention_entries(self) -> None:
        result = _finalize(
            {"workstreams": []},
            unreferenced="",
            churn=self.CHURN,
            fragments="changelog/unreleased/fr-1.md",
            fr_statuses="",
        )
        assert result["recap"]["orphans"] == []

    @pytest.mark.req("REQ-YG-536")
    def test_commit_orphans_precede_convention_entries(self) -> None:
        """J2: commit orphans first, convention entries appended after."""
        result = _finalize(
            {"workstreams": []},
            unreferenced="a1|d|loose commit",
            churn=self.CHURN,
            fragments="",
            fr_statuses="",
        )
        orphans = result["recap"]["orphans"]
        assert orphans[0] == "a1|d|loose commit"
        assert "no changelog fragment" in orphans[1]


class TestFinalizeComposesStatuses:
    """finalize_recap still applies the FR-703 status join (J1)."""

    @pytest.mark.req("REQ-YG-536")
    def test_statuses_still_attached(self) -> None:
        result = _finalize(
            {"workstreams": ["NC-346: stonewall"]},
            unreferenced="",
            churn="",
            fragments="x",
            fr_statuses=(
                "HEAD:feature-requests/NC-346-offschema-question-stonewall.md:"
                "**Status:** ENFORCED (2026-07-08)"
            ),
        )
        assert "ENFORCED" in result["recap"]["workstreams"][0]


class TestGraphAndPromptContract:
    """Schema is judgement-only; topology routes through finalize_recap."""

    @pytest.mark.req("REQ-YG-536")
    def test_schema_two_judgement_fields(self) -> None:
        prompt = yaml.safe_load((DEMO_DIR / "prompts" / "recap.yaml").read_text())
        assert set(prompt["schema"]["fields"]) == {"workstreams", "hotspots"}

    @pytest.mark.req("REQ-YG-536")
    def test_prompt_sheds_orphan_transport(self) -> None:
        text = (DEMO_DIR / "prompts" / "recap.yaml").read_text()
        assert "UNREFERENCED" not in text
        assert "orphan" not in text.lower()
        assert "verbatim" not in text.lower()

    @pytest.mark.req("REQ-YG-536")
    def test_finalize_node_wired(self) -> None:
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        node = raw["nodes"]["finalize_recap"]
        assert node["type"] == "python"
        edges = [(e["from"], e["to"]) for e in raw["edges"]]
        assert ("synthesize", "finalize_recap") in edges
        assert ("finalize_recap", "END") in edges
        llm = [n for n, c in raw["nodes"].items() if c.get("type", "llm") == "llm"]
        assert llm == ["synthesize"]

    @pytest.mark.req("REQ-YG-536")
    def test_synthesize_sheds_unreferenced(self) -> None:
        """J5: unreferenced is code's input now, not the model's."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        synth = raw["nodes"]["synthesize"]
        assert "unreferenced" not in synth.get("variables", {})
        assert "unreferenced" not in synth.get("requires", [])
        assert "referenced" in synth.get("variables", {})
