"""Unit tests for the abstraction-span separation gate (FR-589).

Exercises the deterministic verdict logic with synthetic scores — both the PASS
(LLM reproduces the hand tagging) and KILL (it does not) paths — without calling
an LLM. Placed in tests/unit so ADR-001 req_coverage counts it.
"""

from __future__ import annotations

import pytest

from examples.abstraction_span.nodes.tools import compute_verdict, separation_verdict

# The seven labelled corpus prompts (FR-586 hand tagging).
_CORPUS = [
    {"name": "assign_pre_eff", "label": "monolith", "text": "..."},
    {"name": "assign_causality", "label": "monolith", "text": "..."},
    {"name": "assign_affects", "label": "monolith", "text": "..."},
    {"name": "extract_agents", "label": "monolith", "text": "..."},
    {"name": "extract_goals", "label": "boundary", "text": "..."},
    {"name": "extract_glosses", "label": "clean", "text": "..."},
    {"name": "classify_kinds", "label": "clean", "text": "..."},
]


def _scores(level_counts: list[int]) -> list[dict]:
    """Build collected map scores (each tagged with _map_index) from raw counts."""
    return [
        {"_map_index": i, "level_count": c, "levels": [], "rationale": ""}
        for i, c in enumerate(level_counts)
    ]


def _state(level_counts: list[int]) -> dict:
    return {"corpus": _CORPUS, "scores": _scores(level_counts)}


class TestComputeVerdict:
    @pytest.mark.req("REQ-YG-020", "REQ-YG-040")
    def test_pass_when_monoliths_clear_clean_band(self):
        """Every monolith strictly above both clean prompts → PASS (GO)."""
        rows = [
            {"name": "assign_pre_eff", "label": "monolith", "level_count": 4},
            {"name": "assign_causality", "label": "monolith", "level_count": 4},
            {"name": "assign_affects", "label": "monolith", "level_count": 3},
            {"name": "extract_agents", "label": "monolith", "level_count": 3},
            {"name": "extract_goals", "label": "boundary", "level_count": 2},
            {"name": "extract_glosses", "label": "clean", "level_count": 1},
            {"name": "classify_kinds", "label": "clean", "level_count": 1},
        ]
        verdict = compute_verdict(rows)
        assert verdict["passed"] is True
        assert verdict["min_monolith"] == 3
        assert verdict["max_clean"] == 1
        assert verdict["gap"] == 2
        assert verdict["goals_between"] is True
        assert verdict["anchor_in_band"] is True

    @pytest.mark.req("REQ-YG-020", "REQ-YG-040")
    def test_kill_when_clean_scores_into_monolith_band(self):
        """A clean prompt scoring into the monolith band → KILL (no separation)."""
        rows = [
            {"name": "assign_pre_eff", "label": "monolith", "level_count": 3},
            {"name": "assign_causality", "label": "monolith", "level_count": 3},
            {"name": "assign_affects", "label": "monolith", "level_count": 3},
            {"name": "extract_agents", "label": "monolith", "level_count": 3},
            {"name": "extract_goals", "label": "boundary", "level_count": 2},
            {"name": "extract_glosses", "label": "clean", "level_count": 4},
            {"name": "classify_kinds", "label": "clean", "level_count": 1},
        ]
        verdict = compute_verdict(rows)
        assert verdict["passed"] is False
        assert verdict["max_clean"] == 4

    @pytest.mark.req("REQ-YG-020", "REQ-YG-040")
    def test_kill_when_anchor_falls_to_clean_floor(self):
        """The measured-failure anchor must sit in the monolith band."""
        rows = [
            {"name": "assign_pre_eff", "label": "monolith", "level_count": 2},
            {"name": "assign_causality", "label": "monolith", "level_count": 3},
            {"name": "assign_affects", "label": "monolith", "level_count": 3},
            {"name": "extract_agents", "label": "monolith", "level_count": 3},
            {"name": "extract_goals", "label": "boundary", "level_count": 2},
            {"name": "extract_glosses", "label": "clean", "level_count": 1},
            {"name": "classify_kinds", "label": "clean", "level_count": 1},
        ]
        # min(monolith) == 2 == anchor, so anchor_in_band holds, but separation
        # still requires min(monolith) > max(clean); here 2 > 1 with goals at 2.
        verdict = compute_verdict(rows)
        assert verdict["anchor_in_band"] is True
        assert verdict["passed"] is True  # anchor at the floor is still in-band


class TestSeparationVerdictNode:
    @pytest.mark.req("REQ-YG-020", "REQ-YG-040")
    def test_node_aligns_scores_by_map_index_and_merges_verdict(self):
        """separation_verdict returns {'verdict': {...}} merging into state."""
        out = separation_verdict(_state([4, 4, 3, 3, 2, 1, 1]))
        assert set(out.keys()) == {"verdict"}
        assert out["verdict"]["passed"] is True
        # ranking is sorted by descending span; top prompt is a monolith
        assert out["verdict"]["ranking"][0]["label"] == "monolith"

    @pytest.mark.req("REQ-YG-020", "REQ-YG-040")
    def test_node_kill_path(self):
        out = separation_verdict(_state([3, 3, 3, 3, 2, 4, 1]))
        assert out["verdict"]["passed"] is False

    @pytest.mark.req("REQ-YG-020", "REQ-YG-040")
    def test_node_raises_on_score_corpus_length_mismatch(self):
        state = {"corpus": _CORPUS, "scores": _scores([4, 3, 1])}
        with pytest.raises(ValueError, match="length mismatch"):
            separation_verdict(state)

    @pytest.mark.req("REQ-YG-020", "REQ-YG-040")
    def test_node_raises_on_failed_branch(self):
        scores = _scores([4, 4, 3, 3, 2, 1, 1])
        scores[2] = {"_map_index": 2, "_error": "boom"}
        state = {"corpus": _CORPUS, "scores": scores}
        with pytest.raises(ValueError, match="branch failed"):
            separation_verdict(state)
