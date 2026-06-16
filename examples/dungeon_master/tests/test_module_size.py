"""Module-size gate for the DM adapter (FR-493 J4).

``session.py`` drifted to 507 lines — over the 450 max in ``CLAUDE.md`` that the
sibling ``*_ops.py`` modules cite as their own reason to exist. This is the
RED→GREEN witness for the ``doc_ops.py`` extraction: it fails at 507 and passes
once the nine-function doc cluster is lifted out, and stays a durable guard
against re-drift.
"""

from __future__ import annotations

from pathlib import Path

_SESSION = Path(__file__).resolve().parents[1] / "api" / "session.py"

# The CLAUDE.md ceiling: target < 400, hard max 450.
_MAX_LINES = 450


def test_session_module_under_size_gate() -> None:
    lines = _SESSION.read_text(encoding="utf-8").count("\n") + 1
    assert lines <= _MAX_LINES, (
        f"session.py is {lines} lines, over the {_MAX_LINES} gate — extract the "
        "doc cluster into doc_ops.py (FR-493)."
    )
