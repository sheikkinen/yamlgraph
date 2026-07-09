"""FR-703 Status Join Post-Pass — Unit tests (LLM-free).

The FR-id → status join is arithmetic: attach_statuses parses fr_statuses
grep lines into an id→status map and appends [Status: ...] to workstream
lines deterministically. Field evidence: the FR-702 model join silently
dropped NC-346/347/341..344 from a ~50-line input (tmp/recap-ninchat-voice-2.log);
the fallback tag read as verified absence.

Fixture discipline: parse fixtures are VERBATIM field lines (diary
2026-07-09, pattern-freeze heuristic), not invented examples.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

GRAPH_PATH = "examples/demos/recap/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "recap"
)

# Verbatim from the 2026-07-09 ninchat_voice field run / repo HEAD.
FIELD_STATUS_LINE = (
    "HEAD:feature-requests/NC-346-offschema-question-stonewall.md:"
    "**Status:** ENFORCED (2026-07-08) — R-1..R-4 honoured; see Implementation below"
)


def _attach(recap, fr_statuses):
    from examples.demos.recap.nodes.partition import attach_statuses

    return attach_statuses({"recap": recap, "fr_statuses": fr_statuses})


class TestStatusMapParse:
    """fr_statuses grep lines → id→status map."""

    @pytest.mark.req("REQ-YG-535")
    def test_verbatim_field_line_parses_trimmed(self) -> None:
        """The real grep line yields a trimmed status — no path, no **Status:**."""
        result = _attach({"workstreams": ["NC-346: stonewall work"]}, FIELD_STATUS_LINE)
        (line,) = result["recap"]["workstreams"]
        assert "[Status: ENFORCED (2026-07-08)" in line
        assert "**Status:**" not in line, f"double prefix: {line}"
        assert "feature-requests/" not in line

    @pytest.mark.req("REQ-YG-535")
    def test_duplicate_id_first_wins(self) -> None:
        """Two map lines for one id: the first is deterministic winner (F3)."""
        statuses = (
            "HEAD:feature-requests/FR-001-a.md:**Status:** First\n"
            "HEAD:feature-requests/FR-001-b.md:**Status:** Second"
        )
        result = _attach({"workstreams": ["FR-001: thing"]}, statuses)
        (line,) = result["recap"]["workstreams"]
        assert "[Status: First]" in line


class TestWorkstreamJoin:
    """Deterministic join semantics per frozen scope."""

    @pytest.mark.req("REQ-YG-535")
    def test_nc346_field_failure_fixed(self) -> None:
        """The exact field failure: NC-346 line + real status → ENFORCED attached."""
        result = _attach(
            {"workstreams": ["NC-346: offschema question stonewall (commits: 4)"]},
            FIELD_STATUS_LINE,
        )
        (line,) = result["recap"]["workstreams"]
        assert "ENFORCED" in line

    @pytest.mark.req("REQ-YG-535")
    def test_unknown_id_tags_no_fr_status(self) -> None:
        """Id absent from map → verified absence tag."""
        result = _attach({"workstreams": ["NC-999: mystery work"]}, FIELD_STATUS_LINE)
        (line,) = result["recap"]["workstreams"]
        assert "[no FR status]" in line

    @pytest.mark.req("REQ-YG-535")
    def test_line_without_id_untouched(self) -> None:
        """No FR/NC id in the line → line passes through unchanged."""
        ws = "ecosystem/docs refresh and export plumbing (commits: 6)"
        result = _attach({"workstreams": [ws]}, FIELD_STATUS_LINE)
        assert result["recap"]["workstreams"] == [ws]

    @pytest.mark.req("REQ-YG-535")
    def test_lowercase_id_joins(self) -> None:
        """docs(nc-346) style lowercase ids join (IGNORECASE)."""
        result = _attach({"workstreams": ["nc-346 follow-ups"]}, FIELD_STATUS_LINE)
        (line,) = result["recap"]["workstreams"]
        assert "ENFORCED" in line

    @pytest.mark.req("REQ-YG-535")
    def test_empty_map_tags_all_no_fr_status(self) -> None:
        """Empty fr_statuses (bare repo): every id-bearing line gets the tag."""
        result = _attach(
            {"workstreams": ["NC-1: a", "NC-2: b"]},
            "",
        )
        for line in result["recap"]["workstreams"]:
            assert "[no FR status]" in line

    @pytest.mark.req("REQ-YG-535")
    def test_multi_id_equal_statuses_single_tag(self) -> None:
        """F1: several ids, one shared status → one tag."""
        statuses = (
            "HEAD:feature-requests/NC-341-a.md:**Status:** ENFORCED\n"
            "HEAD:feature-requests/NC-342-b.md:**Status:** ENFORCED"
        )
        result = _attach({"workstreams": ["NC-341 NC-342: clobber+reask"]}, statuses)
        (line,) = result["recap"]["workstreams"]
        assert line.count("[Status:") == 1
        assert "[Status: ENFORCED]" in line

    @pytest.mark.req("REQ-YG-535")
    def test_multi_id_distinct_statuses_per_id_tags(self) -> None:
        """F1: distinct statuses → per-id tags, none silently dropped."""
        statuses = (
            "HEAD:feature-requests/NC-341-a.md:**Status:** ENFORCED\n"
            "HEAD:feature-requests/NC-342-b.md:**Status:** Proposed"
        )
        result = _attach({"workstreams": ["NC-341 NC-342: mixed batch"]}, statuses)
        (line,) = result["recap"]["workstreams"]
        assert "NC-341 ENFORCED" in line
        assert "NC-342 Proposed" in line


class TestBoundaryNormalization:
    """F2: recap arrives as dict or Pydantic model."""

    @pytest.mark.req("REQ-YG-535")
    def test_accepts_pydantic_model(self) -> None:
        from pydantic import BaseModel

        class Recap(BaseModel):
            workstreams: list[str]
            orphans: list[str] = []
            hotspots: list[str] = []

        recap = Recap(workstreams=["NC-346: stonewall"])
        result = _attach(recap, FIELD_STATUS_LINE)
        assert "ENFORCED" in result["recap"]["workstreams"][0]

    @pytest.mark.req("REQ-YG-535")
    def test_accepts_plain_dict(self) -> None:
        result = _attach({"workstreams": ["NC-346: stonewall"]}, FIELD_STATUS_LINE)
        assert "ENFORCED" in result["recap"]["workstreams"][0]


class TestGraphAndPromptContract:
    """Topology and template reflect the mechanized join."""

    @pytest.mark.req("REQ-YG-535")
    def test_attach_statuses_node_wired(self) -> None:
        """synthesize → attach_statuses → END; still exactly one LLM node."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        node = raw["nodes"]["attach_statuses"]
        assert node["type"] == "python"
        edges = [(e["from"], e["to"]) for e in raw["edges"]]
        assert ("synthesize", "attach_statuses") in edges
        assert ("attach_statuses", "END") in edges
        llm = [n for n, c in raw["nodes"].items() if c.get("type", "llm") == "llm"]
        assert llm == ["synthesize"]

    @pytest.mark.req("REQ-YG-535")
    def test_prompt_sheds_status_join(self) -> None:
        """No disposition instructions; no fr_statuses input; full-id bound present."""
        text = (DEMO_DIR / "prompts" / "recap.yaml").read_text()
        assert "fr_statuses" not in text
        assert "[no FR status]" not in text
        assert "Disposition" not in text
        assert (
            "full" in text and "shorthand" in text
        ), "full-id formatting bound missing"

    @pytest.mark.req("REQ-YG-535")
    def test_synthesize_variables_shed_fr_statuses(self) -> None:
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        assert "fr_statuses" not in raw["nodes"]["synthesize"].get("variables", {})
        assert "fr_statuses" not in raw["nodes"]["synthesize"].get("requires", [])
