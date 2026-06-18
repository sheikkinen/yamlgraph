"""FR-530 Stage 1 -- tests for the post-generation continuity witness.

Example-scoped (FR-474 J3): NO ``@pytest.mark.req``.
"""

from __future__ import annotations

import json
from pathlib import Path

from examples.dungeon_master.scripts import emit_continuity_witness as ew

_REVIEW_MD = """# Book Review

**Overall:** 4/5

## Continuity

Score: 2/5
- Arnulf declared dead then reappears alive.
- A resolved conflict restarts in the next chapter.

## Synopsis delivery

Score: 5/5
"""


def test_build_witness_projects_score_and_break_count() -> None:
    w = ew.build_witness("10099-BC", _REVIEW_MD)
    assert w["book"] == "10099-BC"
    assert w["continuity_score"] == 2
    assert w["break_count"] == 2
    # FR-522 posture is stamped into the record so consumers cannot mistake it for a gate.
    assert w["posture"] == "visibility-not-gate"


def test_write_witness_emits_machine_readable_json(tmp_path: Path) -> None:
    out = tmp_path / "10099-BC"
    out.mkdir()
    (out / "review.md").write_text(_REVIEW_MD, encoding="utf-8")

    witness = ew.write_witness(out)
    assert witness is not None

    written = out / ew.WITNESS_FILENAME
    assert written.exists()
    loaded = json.loads(written.read_text(encoding="utf-8"))
    # FR-531 can later join this record -- it is structured, not prose.
    assert loaded == {
        "book": "10099-BC",
        "continuity_score": 2,
        "break_count": 2,
        "posture": "visibility-not-gate",
    }


def test_write_witness_is_non_blocking_when_review_absent(tmp_path: Path) -> None:
    out = tmp_path / "no-review"
    out.mkdir()
    # No review.md: the witness must skip, not raise (FR-522 non-blocking posture).
    assert ew.write_witness(out) is None
    assert not (out / ew.WITNESS_FILENAME).exists()
