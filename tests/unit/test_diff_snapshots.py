"""FR-587 unit tests for the snapshot-then-diff deterministic helper.

`diff_snapshots` (examples/plot_modeller/nodes/tools.py) is Stage 2 of the
comprehend/represent split: the LLM emits per-beat world-state snapshots and
this pure helper computes the salient per-beat change. These tests pin the four
mechanisms the FR-587 Gate-1 spike depends on — appearance, disappearance,
value-flip, and the intra-chapter `at`-run collapse to net displacement — plus
the first-departure-only suppression that reproduces the ground-truth `at`
departures (FR-587 correction #2).

The module is loaded under a unique name to avoid the `nodes` package-name
collision other example unit tests share in this directory.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

EXAMPLE_DIR = Path(__file__).resolve().parents[2] / "examples" / "plot_modeller"


def _load_diff_snapshots():
    if str(EXAMPLE_DIR) not in sys.path:
        sys.path.insert(0, str(EXAMPLE_DIR))
    spec = importlib.util.spec_from_file_location(
        "plot_modeller_tools_fr587", EXAMPLE_DIR / "nodes" / "tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.diff_snapshots


diff_snapshots = _load_diff_snapshots()


def _fl(pred: str, args: list[str], value) -> dict:
    return {"pred": pred, "args": args, "value": value}


def _has(slice_: list[dict], pred: str, args: list[str], value) -> bool:
    return any(
        f["pred"] == pred and f["args"] == args and f["value"] == value for f in slice_
    )


class TestDiffSnapshots:
    """The four diff mechanisms + waypoint salience collapses."""

    @pytest.mark.req("REQ-YG-020")
    def test_f0_baseline_not_emitted(self):
        """The opening F0 snapshot anchors the diff and is never emitted."""
        snaps = [
            {"id": "F0", "chapter": 1, "world": [_fl("alive", ["A"], True)]},
            {"id": "F1", "chapter": 1, "world": [_fl("alive", ["A"], True)]},
        ]
        out = diff_snapshots(snaps)
        assert [b["id"] for b in out] == ["F1"]
        # Nothing changed between F0 and F1 → empty effect.
        assert out[0]["eff_world"] == []

    @pytest.mark.req("REQ-YG-020")
    def test_appearance(self):
        """A fluent absent in the prior snapshot appears as an effect."""
        snaps = [
            {"id": "F0", "chapter": 1, "world": [_fl("alive", ["A"], True)]},
            {
                "id": "F1",
                "chapter": 1,
                "world": [_fl("alive", ["A"], True), _fl("holds", ["A", "key"], True)],
            },
        ]
        out = diff_snapshots(snaps)
        assert _has(out[0]["eff_world"], "holds", ["A", "key"], True)
        # An appearance has no precondition (nothing flipped).
        assert out[0]["pre_world"] == []

    @pytest.mark.req("REQ-YG-020")
    def test_disappearance(self):
        """A tracked boolean fact that vanishes flips to value false."""
        snaps = [
            {"id": "F0", "chapter": 1, "world": [_fl("holds", ["A", "key"], True)]},
            {"id": "F1", "chapter": 1, "world": []},
        ]
        out = diff_snapshots(snaps)
        assert _has(out[0]["eff_world"], "holds", ["A", "key"], False)
        assert _has(out[0]["pre_world"], "holds", ["A", "key"], True)

    @pytest.mark.req("REQ-YG-020")
    def test_value_flip(self):
        """A fluent whose value changes is an effect with the new value."""
        snaps = [
            {"id": "F0", "chapter": 1, "world": [_fl("alive", ["A"], True)]},
            {"id": "F1", "chapter": 1, "world": [_fl("alive", ["A"], False)]},
        ]
        out = diff_snapshots(snaps)
        assert _has(out[0]["eff_world"], "alive", ["A"], False)
        assert _has(out[0]["pre_world"], "alive", ["A"], True)

    @pytest.mark.req("REQ-YG-020")
    def test_first_at_move_emits_departure_and_arrival(self):
        """The first relocation emits both departure (false) and arrival (true)."""
        snaps = [
            {"id": "F0", "chapter": 1, "world": [_fl("at", ["A", "Home"], True)]},
            {"id": "F1", "chapter": 1, "world": [_fl("at", ["A", "Town"], True)]},
        ]
        out = diff_snapshots(snaps)
        assert _has(out[0]["eff_world"], "at", ["A", "Town"], True)
        assert _has(out[0]["eff_world"], "at", ["A", "Home"], False)
        assert _has(out[0]["pre_world"], "at", ["A", "Home"], True)

    @pytest.mark.req("REQ-YG-020")
    def test_late_departure_suppressed(self):
        """A second relocation is arrival-only — the departure is suppressed."""
        snaps = [
            {"id": "F0", "chapter": 1, "world": [_fl("at", ["A", "Home"], True)]},
            {"id": "F1", "chapter": 1, "world": [_fl("at", ["A", "Town"], True)]},
            {"id": "F2", "chapter": 2, "world": [_fl("at", ["A", "City"], True)]},
        ]
        out = diff_snapshots(snaps)
        f2 = next(b for b in out if b["id"] == "F2")
        assert _has(f2["eff_world"], "at", ["A", "City"], True)
        # No departure for the second move, and no stale precondition for it.
        assert not any(
            f["pred"] == "at" and f["value"] is False for f in f2["eff_world"]
        )
        assert f2["pre_world"] == []

    @pytest.mark.req("REQ-YG-020")
    def test_intra_chapter_run_collapses_to_net_displacement(self):
        """Consecutive same-chapter at-moves collapse to origin→terminus."""
        snaps = [
            {"id": "F0", "chapter": 1, "world": [_fl("at", ["A", "Home"], True)]},
            {"id": "F1", "chapter": 1, "world": [_fl("at", ["A", "Mid"], True)]},
            {"id": "F2", "chapter": 1, "world": [_fl("at", ["A", "End"], True)]},
        ]
        out = diff_snapshots(snaps)
        # The intermediate waypoint is dropped entirely.
        for beat in out:
            assert not _has(beat["eff_world"], "at", ["A", "Mid"], True)
        # Net displacement: departure from the origin, arrival at the terminus.
        f1 = next(b for b in out if b["id"] == "F1")
        f2 = next(b for b in out if b["id"] == "F2")
        assert _has(f1["eff_world"], "at", ["A", "Home"], False)
        assert _has(f2["eff_world"], "at", ["A", "End"], True)

    @pytest.mark.req("REQ-YG-020")
    def test_carried_fact_produces_no_effect(self):
        """A fact true in both snapshots is not re-reported as a change."""
        snaps = [
            {
                "id": "F0",
                "chapter": 1,
                "world": [_fl("alive", ["A"], True), _fl("at", ["A", "Home"], True)],
            },
            {
                "id": "F1",
                "chapter": 1,
                "world": [_fl("alive", ["A"], True), _fl("at", ["A", "Home"], True)],
            },
        ]
        out = diff_snapshots(snaps)
        assert out[0]["eff_world"] == []
        assert out[0]["pre_world"] == []
