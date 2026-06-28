"""FR-590/591 unit tests for the multi-perspective conversion helpers.

The FR-591 graph decomposes per-character: an inner subgraph turns each agent's
viewpoint prose into typed beats (``parse_perspective`` assembles the
``{agent, viewpoint, beats}`` record), and the outer map collects those records
for ``combine_perspectives`` to assemble into the unified per-beat L5. These
tests pin the pure helpers the graph depends on — the tolerant beat parser, the
perspective record assembly, per-beat grouping across agents, symmetric-``rel``
dedup, pre/eff pairing, union recall, and deterministic ``_map_index`` ordering.

The encode contract is **provisional** (recall-preserving, precision-open —
FR-591 J1); these tests fix the *assembly* mechanics, not the encoding quality.

The module is loaded under a unique name to avoid the `nodes` package-name
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
        "plot_modeller_tools_fr591", EXAMPLE_DIR / "nodes" / "tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_tools()
combine_perspectives = _mod.combine_perspectives
parse_perspective = _mod.parse_perspective


def _fl(pred: str, args: list[str], value) -> dict:
    return {"pred": pred, "args": args, "value": value}


def _beat(bid: str, pre=None, eff=None) -> dict:
    return {"id": bid, "pre_world": pre or [], "eff_world": eff or []}


def _persp(beats: list, agent: str = "X", map_index: int | None = None) -> dict:
    """Build a collected perspective record as the FR-591 map node yields it."""
    rec: dict = {"agent": agent, "viewpoint": "", "beats": beats}
    if map_index is not None:
        rec["_map_index"] = map_index
    return rec


def _slice_has(fluents: list[dict], pred: str, args: list[str], value) -> bool:
    norm = [(f["pred"], [a.lower() for a in f["args"]], f["value"]) for f in fluents]
    return (pred, [a.lower() for a in args], value) in norm


def _by_id(result: list[dict]) -> dict[str, dict]:
    return {b["id"]: b for b in result}


# --- combine_perspectives: assemble per-agent records into per-beat L5 ---


@pytest.mark.req("REQ-YG-020")
def test_two_agents_distinct_beats_grouped():
    """Each agent's beats land under the right id; both ids are present."""
    pell = _persp([_beat("F1", eff=[_fl("at", ["Pell", "Warehouse"], True)])], "Pell")
    marren = _persp([_beat("F2", eff=[_fl("at", ["Marren", "Court"], True)])], "Marren")
    result = _by_id(combine_perspectives([pell, marren]))
    assert set(result) == {"F1", "F2"}
    assert _slice_has(result["F1"]["eff_world"], "at", ["Pell", "Warehouse"], True)
    assert _slice_has(result["F2"]["eff_world"], "at", ["Marren", "Court"], True)


@pytest.mark.req("REQ-YG-020")
def test_same_beat_unions_both_agents():
    """Two agents contributing to the same beat union their fluents."""
    pell = _persp([_beat("F1", eff=[_fl("at", ["Pell", "Warehouse"], True)])], "Pell")
    marren = _persp(
        [_beat("F1", eff=[_fl("holds", ["Marren", "the relic"], True)])], "Marren"
    )
    result = _by_id(combine_perspectives([pell, marren]))
    eff = result["F1"]["eff_world"]
    assert _slice_has(eff, "at", ["Pell", "Warehouse"], True)
    assert _slice_has(eff, "holds", ["Marren", "the relic"], True)
    assert len(eff) == 2


@pytest.mark.req("REQ-YG-020")
def test_symmetric_rel_deduped():
    """A relationship reported from both sides collapses to one fluent."""
    pell = _persp(
        [_beat("F3", eff=[_fl("rel", ["Pell", "Marren"], "hostile")])], "Pell"
    )
    marren = _persp(
        [_beat("F3", eff=[_fl("rel", ["Pell", "Marren"], "hostile")])], "Marren"
    )
    result = _by_id(combine_perspectives([pell, marren]))
    rels = [f for f in result["F3"]["eff_world"] if f["pred"] == "rel"]
    assert len(rels) == 1


@pytest.mark.req("REQ-YG-020")
def test_pre_and_eff_kept_separate():
    """Preconditions and effects are merged into their own slices, not mixed."""
    agent = _persp(
        [
            _beat(
                "F2",
                pre=[_fl("at", ["Naima", "Timbuktu"], True)],
                eff=[_fl("at", ["Naima", "River"], True)],
            )
        ],
        "Naima",
    )
    result = _by_id(combine_perspectives([agent]))
    assert _slice_has(result["F2"]["pre_world"], "at", ["Naima", "Timbuktu"], True)
    assert _slice_has(result["F2"]["eff_world"], "at", ["Naima", "River"], True)
    assert not _slice_has(result["F2"]["eff_world"], "at", ["Naima", "Timbuktu"], True)


@pytest.mark.req("REQ-YG-020")
def test_union_recall_single_reporter_survives():
    """A fact named by only ONE of two agents is not lost in the merge."""
    witness = _persp([_beat("F5", eff=[_fl("alive", ["Brynn"], False)])], "Witness")
    bystander = _persp([_beat("F5", eff=[_fl("at", ["Fen", "Tunnels"], True)])], "Fen")
    result = _by_id(combine_perspectives([witness, bystander]))
    assert _slice_has(result["F5"]["eff_world"], "alive", ["Brynn"], False)


@pytest.mark.req("REQ-YG-020")
def test_belief_slices_empty():
    """Combine emits empty belief slices (belief is not the L5 wound)."""
    agent = _persp([_beat("F1", eff=[_fl("at", ["Pell", "Warehouse"], True)])], "Pell")
    out = combine_perspectives([agent])
    assert out[0]["pre_belief"] == []
    assert out[0]["eff_belief"] == []


@pytest.mark.req("REQ-YG-020")
def test_map_index_order_is_deterministic():
    """Records are merged in ``_map_index`` order regardless of arrival order."""
    a_late = _persp([_beat("F3"), _beat("F1")], "A", map_index=1)
    a_early = _persp([_beat("F2"), _beat("F1")], "B", map_index=0)
    # Pass out of order; combine must sort by _map_index before grouping.
    result = combine_perspectives([a_late, a_early])
    assert [b["id"] for b in result] == ["F2", "F1", "F3"]


@pytest.mark.req("REQ-YG-020")
def test_tolerates_bare_lists_and_malformed_entries():
    """Bare beat-lists, non-dict beats, and value-less fluents are skipped."""
    agent = [
        "garbage",
        _beat("F1", eff=[_fl("at", ["Pell", "Court"], True), {"args": ["x"]}]),
    ]
    result = combine_perspectives([agent, "not-a-list"])
    eff = result[0]["eff_world"]
    assert _slice_has(eff, "at", ["Pell", "Court"], True)
    assert len(eff) == 1


# --- parse_perspective: assemble one agent's record inside the inner subgraph ---


@pytest.mark.req("REQ-YG-020")
def test_parse_perspective_assembles_record():
    """The tool joins agent + viewpoint to the parsed encoding under ``perspective``."""
    raw = (
        "- id: F1\n"
        "  pre_world: []\n"
        "  eff_world:\n"
        "    - {pred: at, args: [Mara, Seoul], value: true}\n"
    )
    out = parse_perspective(
        {"agent": "Mara", "viewpoint": "I arrived in Seoul. (F1)", "encoded_raw": raw}
    )
    persp = out["perspective"]
    assert persp["agent"] == "Mara"
    assert persp["viewpoint"] == "I arrived in Seoul. (F1)"
    assert len(persp["beats"]) == 1
    assert persp["beats"][0]["id"] == "F1"


@pytest.mark.req("REQ-YG-020")
def test_parse_perspective_strips_code_fences():
    """A fenced ```yaml payload is unwrapped before parsing."""
    raw = "```yaml\n- id: F2\n  eff_world: []\n```"
    out = parse_perspective({"agent": "Pell", "encoded_raw": raw})
    assert [b["id"] for b in out["perspective"]["beats"]] == ["F2"]


@pytest.mark.req("REQ-YG-020")
def test_parse_perspective_tolerates_garbage():
    """A malformed payload yields an empty beat list, not an exception."""
    out = parse_perspective({"agent": "Fen", "encoded_raw": "not: [valid: yaml: ::"})
    assert out["perspective"]["agent"] == "Fen"
    assert out["perspective"]["beats"] == []


@pytest.mark.req("REQ-YG-020")
def test_parse_perspective_missing_fields_default():
    """Absent viewpoint/encoded_raw default to empty prose and no beats."""
    out = parse_perspective({"agent": "Lone"})
    assert out["perspective"] == {"agent": "Lone", "viewpoint": "", "beats": []}
