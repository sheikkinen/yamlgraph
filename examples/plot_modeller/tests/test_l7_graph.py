"""FR-609 — beat-free goal-GRAPH extraction + comparability partition.

Witness tests for the additive functions added to ``evaluate.py`` (the frozen
``_l7_counts`` / ``main_l7`` path is untouched):

  derive_goal_graph     — per fixture, the BEAT-FREE inter-goal causal graph
                          (goals + ``enables``/``threatens`` among goals + agent),
                          its referent goals, incomparable referent pairs, and the
                          BRANCHING / TOTAL-ORDER topology verdict. The anti-tautology
                          gate (J corr 1): the rendered graph must contain NO ``F\\d``
                          beat token, or mode A becomes a leak rather than a test.
  goal_graph_partition  — CLEAN (branching: order cannot leak placement) vs
                          QUARANTINED (total-order: a placement win is order-
                          confounded). Asserts the partition matches the FR-609
                          Topology Pre-Check table — a regression guard so a future
                          fixture edit cannot silently move a fixture across the line.
"""

from __future__ import annotations

import re
from pathlib import Path

from evaluate import derive_goal_graph, goal_graph_partition

GT_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "ground-truth"


# The FR-609 Topology Pre-Check table (2026-06-26), keyed by GT file stem.
_PRECHECK = {
    "detective-thriller-the-vanished-witness": "TOTAL-ORDER",
    "quest-adventure-the-sunken-crown": "TOTAL-ORDER",
    "horror-survival-the-last-light": "BRANCHING",
    "historical-fiction-the-salt-road": "BRANCHING",
    "scifi-hybrid-the-loom": "BRANCHING",
}


def test_every_fixture_topology_matches_precheck() -> None:
    for path in sorted(GT_DIR.glob("*.yaml")):
        graph = derive_goal_graph(path)
        assert graph["topology"] == _PRECHECK[path.stem], path.stem


def test_partition_matches_precheck_table() -> None:
    part = goal_graph_partition(GT_DIR)
    assert set(part["QUARANTINED"]) == {
        "detective-thriller-the-vanished-witness",
        "quest-adventure-the-sunken-crown",
    }
    assert set(part["CLEAN"]) == {
        "horror-survival-the-last-light",
        "historical-fiction-the-salt-road",
        "scifi-hybrid-the-loom",
    }


def test_graph_is_beat_free_no_F_token() -> None:
    """The anti-tautology / leak gate (J corr 1): a graph naming a beat id would
    hand the model the close beat for any feeling whose referent is that goal."""
    for path in sorted(GT_DIR.glob("*.yaml")):
        graph = derive_goal_graph(path)
        rendered = repr(graph["goals"])
        assert re.search(r"\bF\d+\b", rendered) is None, path.stem


def test_graph_carries_intergoal_relations() -> None:
    """The materially-more-signal claim (Open Q3): goals must carry inter-goal
    ``enables``/``threatens`` edges, not a flat id+desc list."""
    quest = derive_goal_graph(GT_DIR / "quest-adventure-the-sunken-crown.yaml")
    by_id = {g["id"]: g for g in quest["goals"]}
    # retrieve_crown enables deliver_crown (F6->F7 enabling chain), beat-free.
    assert "deliver_crown" in by_id["retrieve_crown"]["enables"]
    # legitimize_queen is threatened by the usurper's seize_throne.
    assert by_id["legitimize_queen"]["threatened_by"]


def test_scifi_referent_pair_is_incomparable() -> None:
    """The cleanest anchoring test in the set: expose_ARIA and save_Jonas are on
    different limbs (an antichain), so only structure — not chain order — can
    disambiguate them."""
    loom = derive_goal_graph(GT_DIR / "scifi-hybrid-the-loom.yaml")
    pairs = {tuple(sorted(p)) for p in loom["incomparable_pairs"]}
    assert ("expose_ARIA", "save_Jonas") in pairs
