"""Module-size gate for the whole DM ``api/`` package (FR-493 J4, FR-536 A).

The original gate (FR-493) watched only ``session.py`` while three modules drifted
far over the 450-line ceiling in ``CLAUDE.md`` (``turn_ops`` 1169, ``chapter_ops``
955, ``witness_metrics`` 772) — the gate guarded the one compliant file and ignored
the offenders (the ``gate_checks_shape_not_substance`` trap).

FR-536 generalizes it: every ``api/**/*.py`` (excluding the detached ``purgatory/``
prototype) must stay ``<= 450`` lines. The three genuinely-oversized modules are
marked ``xfail(strict=True)`` so the suite is green today; each Workstream-C split
removes exactly one entry from ``_NEEDS_SPLIT`` — and because the xfail is *strict*,
forgetting to remove it after a successful split turns the pass into a failure,
mechanically forcing the bookkeeping. ``world_state.py`` (454) is NOT listed: it is
trimmed under the ceiling within Workstream A, not split.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_API_DIR = Path(__file__).resolve().parents[1] / "api"

# The CLAUDE.md ceiling: target < 400, hard max 450.
_MAX_LINES = 450

# Modules known to be over the ceiling that need a *split* (Workstream C). Each is
# strict-xfail: removing the entry is mandatory the moment its split lands.
_NEEDS_SPLIT = frozenset(
    {
        "turn_ops.py",
        "chapter_ops.py",
    }
)


def _api_modules() -> list[Path]:
    return sorted(p for p in _API_DIR.rglob("*.py") if p.name != "__init__.py")


def _line_count(path: Path) -> int:
    return path.read_text(encoding="utf-8").count("\n") + 1


def _param(path: Path) -> object:
    rel = path.relative_to(_API_DIR).as_posix()
    marks = (
        [pytest.mark.xfail(strict=True, reason=f"FR-536 Workstream C splits {rel}")]
        if path.name in _NEEDS_SPLIT
        else []
    )
    return pytest.param(path, id=rel, marks=marks)


@pytest.mark.parametrize("module", [_param(p) for p in _api_modules()])
def test_api_module_under_size_gate(module: Path) -> None:
    lines = _line_count(module)
    assert lines <= _MAX_LINES, (
        f"{module.relative_to(_API_DIR).as_posix()} is {lines} lines, over the "
        f"{_MAX_LINES} gate (CLAUDE.md). Split it along a concern seam (FR-536)."
    )
