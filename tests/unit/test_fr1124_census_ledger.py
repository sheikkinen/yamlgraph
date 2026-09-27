"""FR-1124 AC-08: the committed census ledger reconciles with the inventory."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "docs" / "issues-2026-09-27-fr1124-census.md"


def _inventory_module():
    spec = importlib.util.spec_from_file_location(
        "fr1124_inventory", REPO / "scripts" / "fr1124_inventory.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.req("REQ-YG-715")
def test_ac08_committed_ledger_reconciles_with_inventory() -> None:
    assert _inventory_module().check(REPO, LEDGER) == 0


@pytest.mark.req("REQ-YG-715")
@pytest.mark.parametrize("tamper", ["duplicate", "omit", "unknown", "class"])
def test_ac08_tampered_ledger_fails_the_check(tmp_path, tamper) -> None:
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    first = next(i for i, ln in enumerate(lines) if ln.startswith("| `examples/"))
    row = lines[first]
    if tamper == "duplicate":
        lines.insert(first, row)
    elif tamper == "omit":
        del lines[first]
    elif tamper == "unknown":
        lines.insert(first, row.replace("`examples/", "`examples/nope/", 1))
    else:
        lines[first] = row.replace("| A |", "| C |", 1)
    bad = tmp_path / "ledger.md"
    bad.write_text("\n".join(lines), encoding="utf-8")
    assert _inventory_module().check(REPO, bad) == 1


@pytest.mark.req("REQ-YG-715")
@pytest.mark.parametrize(
    ("klass", "declared", "rc"),
    [("A", "fail", 0), ("A", "skip", 1), ("B", "skip", 0), ("B", "fail", 1)],
)
def test_ac08_row_leaves_inventory_only_by_declaring_its_class_policy(
    tmp_path, klass, declared, rc
) -> None:
    graph = tmp_path / "examples" / "g.yaml"
    graph.parent.mkdir()
    graph.write_text(
        f"nodes:\n  n:\n    type: llm\n    prompt: p\n    on_error: {declared}\n",
        encoding="utf-8",
    )
    ledger = tmp_path / "ledger.md"
    ledger.write_text(
        f"| `examples/g.yaml` | `n` | `k` | -> END | {klass} | ev | policy |\n",
        encoding="utf-8",
    )
    assert _inventory_module().check(tmp_path, ledger) == rc
