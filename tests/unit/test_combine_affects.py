"""FR-596 unit tests for the per-agent affect combine helpers.

The FR-596 decomposition fans out one ``affect_throughline`` + ``encode_affect``
pass per agent (a single character's emotional arc → AffectDelta list keyed by
beat id), then the outer map collects those per-agent records for
``combine_affects`` to assemble into the unified per-beat ``eff_affect`` that the
frozen FR-578 L7 gate (``evaluate.main_l7``) re-scores against ground truth.

These tests pin the **pure** combine mechanics — per-beat grouping across agents,
union recall (an affect felt by exactly one agent survives), relational ``toward``
cross-reference preservation, deterministic ``_map_index`` ordering, and the
per-cell open/close balance diagnostic (``affect_balance``). Affect is
feeler-owned, so unlike the symmetric ``rel`` facts in ``combine_perspectives``
there is **no dedup**: two agents never emit the same delta, so the union is a
clean concatenation (FR-596 Judgement).

The module is loaded under a unique name to avoid the ``nodes`` package-name
collision other example unit tests share in this directory.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE_DIR = Path(__file__).resolve().parents[2] / "examples" / "plot_modeller"


def _load_tools():
    if str(EXAMPLE_DIR) not in sys.path:
        sys.path.insert(0, str(EXAMPLE_DIR))
    spec = importlib.util.spec_from_file_location(
        "plot_modeller_tools_fr596", EXAMPLE_DIR / "nodes" / "tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_tools()
combine_affects = _mod.combine_affects
affect_balance = _mod.affect_balance


def _delta(op: str, char: str, kind: str, toward: str | None = None) -> dict:
    d = {"op": op, "char": char, "kind": kind}
    if toward is not None:
        d["toward"] = toward
    return d


def _beat(bid: str, deltas: list) -> dict:
    return {"id": bid, "eff_affect": deltas}


def _record(beats: list, agent: str = "X", map_index: int | None = None) -> dict:
    """One agent's collected affect record as the FR-596 map node yields it."""
    rec: dict = {"agent": agent, "throughline": "", "affects": beats}
    if map_index is not None:
        rec["_map_index"] = map_index
    return rec


def _by_id(result: list[dict]) -> dict[str, dict]:
    return {b["id"]: b for b in result}


# --- combine_affects: assemble per-agent records into per-beat eff_affect ---


@pytest.mark.req("REQ-YG-020")
def test_per_beat_grouping_across_two_agents():
    """Two agents who each feel a different affect on the SAME beat union there."""
    pell = _record([_beat("F2", [_delta("open", "Pell", "guilt")])], agent="Pell")
    marren = _record(
        [_beat("F2", [_delta("open", "Marren", "betrayal", toward="Pell")])],
        agent="Marren",
    )
    result = _by_id(combine_affects([pell, marren]))
    kinds = {(d["char"], d["kind"]) for d in result["F2"]["eff_affect"]}
    assert ("Pell", "guilt") in kinds
    assert ("Marren", "betrayal") in kinds


@pytest.mark.req("REQ-YG-020")
def test_union_recall_single_feeler_survives():
    """An affect felt by exactly one agent on a beat no other touches survives."""
    pell = _record([_beat("F5", [_delta("open", "Pell", "hope")])], agent="Pell")
    marren = _record([_beat("F1", [_delta("open", "Marren", "loss")])], agent="Marren")
    result = _by_id(combine_affects([pell, marren]))
    assert {(d["char"], d["kind"]) for d in result["F5"]["eff_affect"]} == {
        ("Pell", "hope")
    }
    assert {(d["char"], d["kind"]) for d in result["F1"]["eff_affect"]} == {
        ("Marren", "loss")
    }


@pytest.mark.req("REQ-YG-020")
def test_relational_toward_preserved():
    """The relational ``toward`` cross-reference is carried through untouched."""
    marren = _record(
        [_beat("F3", [_delta("close", "Marren", "retaliation", toward="Pell")])],
        agent="Marren",
    )
    result = _by_id(combine_affects([marren]))
    delta = result["F3"]["eff_affect"][0]
    assert delta["toward"] == "Pell"
    assert delta["op"] == "close"


@pytest.mark.req("REQ-YG-020")
def test_no_dedup_affect_is_feeler_owned():
    """Identical-looking deltas from two agents both survive (no symmetric dedup)."""
    a = _record([_beat("F4", [_delta("open", "Pell", "hope")])], agent="Pell")
    b = _record([_beat("F4", [_delta("open", "Pell", "hope")])], agent="Echo")
    result = _by_id(combine_affects([a, b]))
    assert len(result["F4"]["eff_affect"]) == 2


@pytest.mark.req("REQ-YG-020")
def test_map_index_ordering_deterministic():
    """``_map_index`` fixes the collect order regardless of input order."""
    late = _record([_beat("F9", [_delta("open", "Z", "hope")])], agent="Z", map_index=2)
    early = _record(
        [_beat("F1", [_delta("open", "A", "loss")])], agent="A", map_index=0
    )
    result = combine_affects([late, early])
    assert [b["id"] for b in result] == ["F1", "F9"]


@pytest.mark.req("REQ-YG-020")
def test_bare_list_mode():
    """A bare list of {id, eff_affect} beats (direct caller) is accepted."""
    beats = [_beat("F1", [_delta("open", "A", "loss")])]
    result = _by_id(combine_affects([beats]))
    assert result["F1"]["eff_affect"][0]["char"] == "A"


@pytest.mark.req("REQ-YG-020")
def test_dict_graph_tool_mode():
    """Graph-tool mode: state dict in, ``{"affects": [...]}`` out."""
    rec = _record([_beat("F1", [_delta("open", "A", "loss")])], agent="A")
    out = combine_affects({"affect_views": [rec]})
    assert isinstance(out, dict)
    assert _by_id(out["affects"])["F1"]["eff_affect"][0]["kind"] == "loss"


# --- affect_balance: per-cell open/close arc balance diagnostic ---


@pytest.mark.req("REQ-YG-020")
def test_affect_balance_closed_arc_is_balanced():
    """An arc opened then closed on the same (char, kind, toward) is balanced."""
    beats = [
        _beat("F2", [_delta("open", "Pell", "guilt")]),
        _beat("F7", [_delta("close", "Pell", "guilt")]),
    ]
    bal = affect_balance(beats)
    assert bal["balanced"] is True
    assert bal["unclosed"] == []


@pytest.mark.req("REQ-YG-020")
def test_affect_balance_surfaces_dangling_open():
    """An opened arc never closed is surfaced as unclosed (dangling)."""
    beats = [_beat("F2", [_delta("open", "Pell", "betrayal", toward="Marren")])]
    bal = affect_balance(beats)
    assert bal["balanced"] is False
    assert any("betrayal" in u for u in bal["unclosed"])
