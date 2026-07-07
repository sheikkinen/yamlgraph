"""FR-691: Plot thread + throughline gates (REQ-YG-530).

The story pipeline extracts threads (by conflict) and throughlines (by
character). These gates are the mechanical invariants the pipeline enforces and
CI proves — one implementation in `nodes/thread_gates.py`, two callers.

RED contract: `thread_gates.py` ships as an always-valid stub; every
invalid-fixture test below fails until the real logic lands (GREEN). Schema
tests pass immediately (the schema is not stubbed).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from pydantic import ValidationError

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()
_nf_str = str(NOVEL_FANDOM_DIR)
if _nf_str not in sys.path:
    sys.path.insert(0, _nf_str)


def _load(mod_name: str, rel_path: str) -> ModuleType:
    fpath = NOVEL_FANDOM_DIR / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_story = _load("novel_fandom_schema_story", "schema/story.py")
_gates = _load("novel_fandom_nodes_thread_gates", "nodes/thread_gates.py")

Thread = _story.Thread
Throughline = _story.Throughline
check_citation_integrity = _gates.check_citation_integrity
check_ledger_walk = _gates.check_ledger_walk
check_cap_and_distinctness = _gates.check_cap_and_distinctness
check_id_stability = _gates.check_id_stability
check_throughlines = _gates.check_throughlines


def _thread(**kw: object) -> dict:
    base = {
        "id": "t",
        "kind": "feud",
        "carriers": ["hilde"],
        "sources": ["blood_feud_custom"],
        "opposition": "the flood forces cooperation",
        "raises": [],
        "releases": [],
        "status": "latent",
    }
    base.update(kw)
    return base


# --- Schema tests (not stubbed — pass immediately) ---


class TestThreadSchema:
    @pytest.mark.req("REQ-YG-530")
    def test_thread_validates(self) -> None:
        t = Thread.model_validate(_thread())
        assert t.id == "t"
        assert t.kind == "feud"

    @pytest.mark.req("REQ-YG-530")
    def test_thread_rejects_unknown_kind(self) -> None:
        with pytest.raises(ValidationError):
            Thread.model_validate(_thread(kind="romance"))

    @pytest.mark.req("REQ-YG-530")
    def test_opposition_required(self) -> None:
        data = _thread()
        del data["opposition"]
        with pytest.raises(ValidationError):
            Thread.model_validate(data)

    @pytest.mark.req("REQ-YG-530")
    def test_throughline_validates(self) -> None:
        tl = Throughline.model_validate(
            {
                "character": "hilde",
                "entries": [{"event": "dawn_raid", "emotion": "fury", "delta": "gain"}],
            }
        )
        assert tl.character == "hilde"
        assert tl.entries[0].delta == "gain"


# --- Gate 1: citation integrity ---


class TestCitationIntegrity:
    CANON = {"hilde", "arnulf", "blood_feud_custom", "dawn_raid", "bonding_rite"}

    @pytest.mark.req("REQ-YG-530")
    def test_orphan_carrier_fails(self) -> None:
        threads = [_thread(carriers=["ghost_who_is_not_canon"])]
        result = check_citation_integrity(threads, self.CANON)
        assert result["valid"] is False
        assert any("ghost_who_is_not_canon" in v for v in result["violations"])

    @pytest.mark.req("REQ-YG-530")
    def test_orphan_raise_event_fails(self) -> None:
        threads = [_thread(raises=["no_such_event"])]
        result = check_citation_integrity(threads, self.CANON)
        assert result["valid"] is False

    @pytest.mark.req("REQ-YG-530")
    def test_all_resolve_passes(self) -> None:
        threads = [
            _thread(
                carriers=["hilde", "arnulf"],
                sources=["blood_feud_custom"],
                raises=["dawn_raid"],
                releases=["bonding_rite"],
            )
        ]
        result = check_citation_integrity(threads, self.CANON)
        assert result["valid"] is True


# --- Gate 2: ledger walk ---


class TestLedgerWalk:
    SEQ = {"dawn_raid": 20, "great_flood": 30, "bonding_rite": 180}

    @pytest.mark.req("REQ-YG-530")
    def test_release_before_raise_fails(self) -> None:
        # release at seq 30, raise at seq 180 -> release precedes its raise
        threads = [_thread(raises=["bonding_rite"], releases=["great_flood"])]
        result = check_ledger_walk(threads, self.SEQ)
        assert result["valid"] is False

    @pytest.mark.req("REQ-YG-530")
    def test_release_without_any_raise_fails(self) -> None:
        threads = [_thread(raises=[], releases=["bonding_rite"])]
        result = check_ledger_walk(threads, self.SEQ)
        assert result["valid"] is False

    @pytest.mark.req("REQ-YG-530")
    def test_raise_then_release_passes(self) -> None:
        threads = [_thread(raises=["dawn_raid"], releases=["bonding_rite"])]
        result = check_ledger_walk(threads, self.SEQ)
        assert result["valid"] is True

    @pytest.mark.req("REQ-YG-530")
    def test_one_raise_many_releases_passes(self) -> None:
        # De-escalation happens in steps: one raise opens, several releases
        # resolve. Each release only needs a raise BEFORE it, not its own raise.
        threads = [
            _thread(raises=["dawn_raid"], releases=["great_flood", "bonding_rite"])
        ]
        result = check_ledger_walk(threads, self.SEQ)
        assert result["valid"] is True

    @pytest.mark.req("REQ-YG-530")
    def test_status_released_requires_release_event(self) -> None:
        threads = [_thread(status="released", raises=["dawn_raid"], releases=[])]
        result = check_ledger_walk(threads, self.SEQ)
        assert result["valid"] is False


# --- Gate 3: cap and distinctness ---


class TestCapAndDistinctness:
    @pytest.mark.req("REQ-YG-530")
    def test_over_cap_fails(self) -> None:
        threads = [_thread(id=f"t{i}", carriers=[f"c{i}"]) for i in range(9)]
        result = check_cap_and_distinctness(threads)
        assert result["valid"] is False
        assert any("8" in v or "cap" in v.lower() for v in result["violations"])

    @pytest.mark.req("REQ-YG-530")
    def test_duplicate_carrier_set_fails(self) -> None:
        threads = [
            _thread(id="a", carriers=["hilde", "arnulf"]),
            _thread(id="b", carriers=["arnulf", "hilde"]),
        ]
        result = check_cap_and_distinctness(threads)
        assert result["valid"] is False

    @pytest.mark.req("REQ-YG-530")
    def test_empty_opposition_fails(self) -> None:
        threads = [_thread(opposition="   ")]
        result = check_cap_and_distinctness(threads)
        assert result["valid"] is False

    @pytest.mark.req("REQ-YG-530")
    def test_distinct_within_cap_passes(self) -> None:
        threads = [
            _thread(id="a", carriers=["hilde"]),
            _thread(id="b", carriers=["arnulf"]),
        ]
        result = check_cap_and_distinctness(threads)
        assert result["valid"] is True

    @pytest.mark.req("REQ-YG-530")
    def test_same_carriers_different_kind_passes(self) -> None:
        # A feud and a survival crisis between the same two people are distinct
        # threads. Distinctness keys on (kind, carriers), not carriers alone.
        threads = [
            _thread(id="feud", kind="feud", carriers=["hilde", "gunnar"]),
            _thread(id="ledge", kind="survival", carriers=["gunnar", "hilde"]),
        ]
        result = check_cap_and_distinctness(threads)
        assert result["valid"] is True


# --- Gate 4: id stability ---


class TestIdStability:
    @pytest.mark.req("REQ-YG-530")
    def test_dropped_prior_without_reason_fails(self) -> None:
        # prior had 'gone'; current set lacks it and it is not in dropped
        threads = [_thread(id="kept")]
        result = check_id_stability(threads, prior_ids={"kept", "gone"}, dropped=[])
        assert result["valid"] is False
        assert any("gone" in v for v in result["violations"])

    @pytest.mark.req("REQ-YG-530")
    def test_dropped_with_reason_passes(self) -> None:
        threads = [_thread(id="kept")]
        result = check_id_stability(
            threads,
            prior_ids={"kept", "gone"},
            dropped=[{"id": "gone", "reason": "merged into kept"}],
        )
        assert result["valid"] is True

    @pytest.mark.req("REQ-YG-530")
    def test_first_run_empty_prior_is_noop(self) -> None:
        threads = [_thread(id="new")]
        result = check_id_stability(threads, prior_ids=set(), dropped=[])
        assert result["valid"] is True


# --- Gate 5: throughlines ---


class TestThroughlines:
    CANON = {"hilde", "arnulf", "dawn_raid", "great_flood", "bonding_rite"}
    SEQ = {"dawn_raid": 20, "great_flood": 30, "bonding_rite": 180}
    MAJOR = {"hilde", "arnulf"}

    def _tl(self, **kw: object) -> dict:
        base = {
            "character": "hilde",
            "entries": [
                {
                    "event": "dawn_raid",
                    "emotion": "fury",
                    "delta": "gain",
                    "slack": False,
                },
                {
                    "event": "bonding_rite",
                    "emotion": "peace",
                    "delta": "loss",
                    "slack": True,
                },
            ],
            "arc_taut": False,
        }
        base.update(kw)
        return base

    @pytest.mark.req("REQ-YG-530")
    def test_out_of_sequence_fails(self) -> None:
        tl = self._tl(
            entries=[
                {"event": "bonding_rite", "emotion": "peace", "delta": "gain"},
                {"event": "dawn_raid", "emotion": "fury", "delta": "loss"},
            ]
        )
        result = check_throughlines([tl], self.CANON, self.SEQ, self.MAJOR)
        assert result["valid"] is False

    @pytest.mark.req("REQ-YG-530")
    def test_unknown_event_fails(self) -> None:
        tl = self._tl(entries=[{"event": "phantom", "emotion": "x", "delta": "gain"}])
        result = check_throughlines([tl], self.CANON, self.SEQ, self.MAJOR)
        assert result["valid"] is False

    @pytest.mark.req("REQ-YG-530")
    def test_zero_delta_major_fails(self) -> None:
        tl = self._tl(
            entries=[
                {
                    "event": "dawn_raid",
                    "emotion": "flat",
                    "delta": "none",
                    "slack": True,
                },
                {
                    "event": "bonding_rite",
                    "emotion": "flat",
                    "delta": "none",
                    "slack": True,
                },
            ]
        )
        result = check_throughlines([tl], self.CANON, self.SEQ, self.MAJOR)
        assert result["valid"] is False

    @pytest.mark.req("REQ-YG-530")
    def test_no_slack_no_taut_fails(self) -> None:
        tl = self._tl(
            entries=[
                {
                    "event": "dawn_raid",
                    "emotion": "fury",
                    "delta": "gain",
                    "slack": False,
                },
                {
                    "event": "bonding_rite",
                    "emotion": "peace",
                    "delta": "loss",
                    "slack": False,
                },
            ],
            arc_taut=False,
        )
        result = check_throughlines([tl], self.CANON, self.SEQ, self.MAJOR)
        assert result["valid"] is False

    @pytest.mark.req("REQ-YG-530")
    def test_valid_throughline_passes(self) -> None:
        result = check_throughlines([self._tl()], self.CANON, self.SEQ, self.MAJOR)
        assert result["valid"] is True

    @pytest.mark.req("REQ-YG-530")
    def test_taut_arc_without_slack_passes(self) -> None:
        tl = self._tl(
            entries=[
                {
                    "event": "dawn_raid",
                    "emotion": "fury",
                    "delta": "gain",
                    "slack": False,
                },
                {
                    "event": "bonding_rite",
                    "emotion": "resolve",
                    "delta": "loss",
                    "slack": False,
                },
            ],
            arc_taut=True,
        )
        result = check_throughlines([tl], self.CANON, self.SEQ, self.MAJOR)
        assert result["valid"] is True


class TestPersistIdempotence:
    """Regeneration must not leave orphaned thread files on disk.

    A thread that leaves the union between runs must leave `story/thread/` too,
    or the persisted set drifts above the cap the in-state gate just cleared.
    """

    @pytest.mark.req("REQ-YG-530")
    def test_persist_removes_orphaned_threads(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        persist = _load("novel_fandom_nodes_persist_story", "nodes/persist_story.py")
        monkeypatch.setattr(persist, "_STORY_DIR", tmp_path)
        thread_dir = tmp_path / "thread"
        thread_dir.mkdir(parents=True)
        # A stale thread from a prior run that the new union does not contain.
        (thread_dir / "ledge_survival.yaml").write_text("id: ledge_survival\n")

        persist.persist_threads(
            {"reconcile_result": {"threads": [_thread(id="hilde_gunnar_feud")]}}
        )

        remaining = {f.stem for f in thread_dir.glob("*.yaml")}
        assert remaining == {"hilde_gunnar_feud"}
        assert not (thread_dir / "ledge_survival.yaml").exists()
