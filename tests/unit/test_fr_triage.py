#!/usr/bin/env python3


"""FR-745: fr_triage — witnesses (REQ-YG-564).

Pins (parallel judgement 2026-07-17):
- Never a verdict: append_triage refuses to touch the Status line and
  refuses non-Proposed FRs.
- F3 schema pins are enforced in CODE too: caps applied on append
  (≤3 canon answers, ≤5 witnesses, single lines).
- Zero-yield raises (Commandment 6; the FR-744 lineage).
- F4 gate scope: [pending] triage + Status Judged-or-later blocks;
  Proposed-status drafts pass freely.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "graphs/fr_triage/tools.py"


def _load():
    spec = importlib.util.spec_from_file_location("triage_tools", TOOLS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["triage_tools"] = mod
    spec.loader.exec_module(mod)
    return mod


def _fr(tmp_path: Path, status: str = "Proposed") -> Path:
    p = tmp_path / "FR-900-test.md"
    p.write_text(f"# FR-900: Test\n\n**Status:** {status}\n\n## Summary\nbody\n", encoding="utf-8")
    return p


DISTILLED = {
    "canon_answers": ["q1: yes", "q2: no", "q3: maybe", "q4: EXCESS"],
    "pre_mortem_witnesses": ["w1", "w2", "w3", "w4", "w5", "w6-EXCESS"],
    "value_prop_check": "completable: for authors, kills rework, vs manual",
}


@pytest.mark.req("REQ-YG-564")
def test_append_triage_pending_markers_and_caps(tmp_path):
    t = _load()
    fr = _fr(tmp_path)
    out = t.append_triage({"fr_path": str(fr), "triage": DISTILLED})
    assert out["appended"] is True
    text = fr.read_text(encoding="utf-8")
    assert "## Triage" in text
    assert text.count("[pending]") >= 4
    assert "EXCESS" not in text  # F3 caps enforced in code (≤3 / ≤5)


@pytest.mark.req("REQ-YG-564")
def test_append_triage_never_touches_status(tmp_path):
    t = _load()
    fr = _fr(tmp_path)
    before = [ln for ln in fr.read_text(encoding="utf-8").splitlines() if "Status" in ln]
    t.append_triage({"fr_path": str(fr), "triage": DISTILLED})
    after = [ln for ln in fr.read_text(encoding="utf-8").splitlines() if "Status" in ln]
    assert before == after


@pytest.mark.req("REQ-YG-564")
def test_append_triage_refuses_non_proposed(tmp_path):
    t = _load()
    fr = _fr(tmp_path, status="Judged — APPROVED")
    with pytest.raises(ValueError, match="[Pp]roposed"):
        t.append_triage({"fr_path": str(fr), "triage": DISTILLED})


@pytest.mark.req("REQ-YG-564")
def test_empty_triage_raises(tmp_path):
    t = _load()
    fr = _fr(tmp_path)
    with pytest.raises(ValueError):
        t.append_triage(
            {
                "fr_path": str(fr),
                "triage": {
                    "canon_answers": [],
                    "pre_mortem_witnesses": [],
                    "value_prop_check": "",
                },
            }
        )


@pytest.mark.req("REQ-YG-564")
def test_gate_blocks_judged_with_pending_and_passes_proposed(tmp_path):
    t = _load()
    judged = _fr(tmp_path, status="Judged — APPROVED")
    judged.write_text(judged.read_text(encoding="utf-8") + "\n## Triage\n- [pending] w1\n", encoding="utf-8")
    assert t.gate_check(judged.read_text(encoding="utf-8")) is False  # blocks
    proposed = _fr(tmp_path)
    proposed.write_text(proposed.read_text(encoding="utf-8") + "\n## Triage\n- [pending] w1\n", encoding="utf-8")
    assert t.gate_check(proposed.read_text(encoding="utf-8")) is True  # drafts pass (F4)
    dispositioned = _fr(tmp_path, status="Judged — APPROVED")
    dispositioned.write_text(
        dispositioned.read_text(encoding="utf-8") + "\n## Triage\n- [accepted → AC-03] w1\n"
    , encoding="utf-8")
    assert t.gate_check(dispositioned.read_text(encoding="utf-8")) is True
