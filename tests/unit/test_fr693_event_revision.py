"""FR-693: Event-revision closure, waiver, byte-identity gates (REQ-YG-534/535).

The event-revision pass closes latent threads by adding events (additive only)
or waives them. Three pure gates plus a `create_event` change that teaches the
tool to emit a `sequence` value. One implementation, two callers.

RED contract: `event_revision_gates.py` ships as always-valid stubs and
`_build_event` does not yet emit `sequence`; every invalid-fixture test below
fails until the real logic lands (GREEN).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

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


_gates = _load("nf_event_revision_gates", "nodes/event_revision_gates.py")
_creation = _load("nf_creation_tools_693", "nodes/creation_tools.py")

check_latent_closure = _gates.check_latent_closure
check_waiver_integrity = _gates.check_waiver_integrity
check_byte_identity = _gates.check_byte_identity
_build_event = _creation._build_event


def _thread(tid: str, status: str, raises: list, releases: list) -> dict:
    return {
        "type": "thread",
        "id": tid,
        "status": status,
        "raises": raises,
        "releases": releases,
    }


def _waiver(
    thread: str, reason: str = "texture, not defect", decided_by: str = "chaplain"
) -> dict:
    return {"thread": thread, "reason": reason, "decided_by": decided_by}


# ----------------------------------------------------- latent closure (RED)


@pytest.mark.req("REQ-YG-534")
def test_closure_rejects_latent_without_events_or_waiver() -> None:
    threads = [_thread("heidrun_legacy", "latent", [], [])]
    result = check_latent_closure(threads, waivers=[])
    assert result["valid"] is False
    assert any("heidrun_legacy" in v for v in result["violations"])


@pytest.mark.req("REQ-YG-534")
def test_closure_rejects_latent_with_raise_but_no_release() -> None:
    threads = [_thread("youth_resentment", "latent", ["young_men_meet"], [])]
    result = check_latent_closure(threads, waivers=[])
    assert result["valid"] is False


@pytest.mark.req("REQ-YG-534")
def test_closure_accepts_latent_with_raise_and_release() -> None:
    threads = [
        _thread("youth_resentment", "latent", ["men_meet"], ["men_settle"]),
    ]
    result = check_latent_closure(threads, waivers=[])
    assert result["valid"] is True


@pytest.mark.req("REQ-YG-534")
def test_closure_accepts_waived_latent() -> None:
    threads = [_thread("heidrun_legacy", "latent", [], [])]
    result = check_latent_closure(threads, waivers=[_waiver("heidrun_legacy")])
    assert result["valid"] is True


@pytest.mark.req("REQ-YG-534")
def test_closure_ignores_non_latent_threads() -> None:
    threads = [_thread("hilde_gunnar_feud", "released", ["a"], ["b"])]
    result = check_latent_closure(threads, waivers=[])
    assert result["valid"] is True


# ---------------------------------------------------- waiver integrity (RED)


@pytest.mark.req("REQ-YG-534")
def test_waiver_rejects_dangling_thread_id() -> None:
    waivers = [_waiver("ghost_thread")]
    result = check_waiver_integrity(waivers, {"heidrun_legacy"})
    assert result["valid"] is False
    assert any("ghost_thread" in v for v in result["violations"])


@pytest.mark.req("REQ-YG-534")
def test_waiver_rejects_missing_reason() -> None:
    waivers = [{"thread": "heidrun_legacy", "reason": "", "decided_by": "x"}]
    result = check_waiver_integrity(waivers, {"heidrun_legacy"})
    assert result["valid"] is False


@pytest.mark.req("REQ-YG-534")
def test_waiver_rejects_missing_decider() -> None:
    waivers = [{"thread": "heidrun_legacy", "reason": "texture", "decided_by": ""}]
    result = check_waiver_integrity(waivers, {"heidrun_legacy"})
    assert result["valid"] is False


@pytest.mark.req("REQ-YG-534")
def test_waiver_accepts_valid_waiver() -> None:
    waivers = [_waiver("heidrun_legacy")]
    result = check_waiver_integrity(waivers, {"heidrun_legacy"})
    assert result["valid"] is True


# ----------------------------------------------------- byte identity (RED)


@pytest.mark.req("REQ-YG-535")
def test_byte_identity_rejects_mutated_preexisting_file() -> None:
    before = {"reinthilde_birth": b"summary: original\n"}
    after = {"reinthilde_birth": b"summary: TAMPERED\n"}
    result = check_byte_identity(before, after)
    assert result["valid"] is False
    assert any("reinthilde_birth" in v for v in result["violations"])


@pytest.mark.req("REQ-YG-535")
def test_byte_identity_rejects_deleted_preexisting_file() -> None:
    before = {"reinthilde_birth": b"x"}
    after: dict[str, bytes] = {}
    result = check_byte_identity(before, after)
    assert result["valid"] is False


@pytest.mark.req("REQ-YG-535")
def test_byte_identity_allows_new_files() -> None:
    before = {"reinthilde_birth": b"x"}
    after = {"reinthilde_birth": b"x", "heidrun_passing": b"new\n"}
    result = check_byte_identity(before, after)
    assert result["valid"] is True


# --------------------------------------- create_event sequence emission (RED)


@pytest.mark.req("REQ-YG-535")
def test_build_event_emits_sequence_when_supplied() -> None:
    page = _build_event({"id": "heidrun_passing", "year": 5, "sequence": 305})
    assert page.get("sequence") == 305


@pytest.mark.req("REQ-YG-535")
def test_build_event_omits_sequence_when_absent() -> None:
    """Genesis/worldgen creates omit sequence — the page must still validate."""
    page = _build_event({"id": "some_event", "year": 0})
    assert "sequence" not in page
