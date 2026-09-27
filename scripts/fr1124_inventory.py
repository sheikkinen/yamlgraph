"""FR-1124 inventory: top-level llm nodes without on_error, and ledger check.

Usage:
    python scripts/fr1124_inventory.py                 # TSV: graph<TAB>node<TAB>state_key
    python scripts/fr1124_inventory.py --check LEDGER  # identity-set equality

Roots: examples/, graphs/, .github/. Excludes any path under a prompts/
directory. A graph file is a YAML mapping with a ``nodes`` mapping; an
eligible node is a top-level node whose declared or default type is ``llm``
and that declares no ``on_error``. Map sub-nodes are nested under ``node:``
and are not top-level, so they never appear.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOTS = ("examples", "graphs", ".github")


def _graph_files(repo: Path) -> list[Path]:
    files = []
    for root in ROOTS:
        for p in sorted((repo / root).rglob("*.y*ml")):
            if "prompts" in p.relative_to(repo).parts or p.suffix not in (
                ".yaml",
                ".yml",
            ):
                continue
            files.append(p)
    return files


def inventory(repo: Path) -> list[tuple[str, str, str]]:
    rows = []
    for p in _graph_files(repo):
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError):
            continue
        nodes = doc.get("nodes") if isinstance(doc, dict) else None
        if not isinstance(nodes, dict):
            continue
        for name, cfg in nodes.items():
            if not isinstance(cfg, dict) or cfg.get("type", "llm") != "llm":
                continue
            if "on_error" in cfg:
                continue
            rel = p.relative_to(repo).as_posix()
            rows.append((rel, str(name), str(cfg.get("state_key", name))))
    return rows


def ledger_rows(ledger: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[0] in ("graph", "") or set(cells[0]) <= {"-", ":"}:
            continue
        rows.append((cells[0], cells[1], cells[4]))
    return rows


_CLASS_POLICY = {"A": "fail", "B": "skip"}


def _declares(repo: Path, graph: str, node: str, policy: str) -> bool:
    path = repo / graph
    if not path.is_file():
        return False
    nodes = yaml.safe_load(path.read_text(encoding="utf-8")).get("nodes") or {}
    cfg = nodes.get(node)
    return isinstance(cfg, dict) and cfg.get("on_error") == policy


def check(repo: Path, ledger: Path) -> int:
    """Ledger identities == inventory; a row leaves the inventory only by
    declaring its class's policy (B: the S-5 ``skip`` edit; A: an explicit
    ``fail`` landed after the census), so the check holds across drift."""
    inv = {(g, n) for g, n, _ in inventory(repo)}
    rows = ledger_rows(ledger)
    led = [(g, n) for g, n, _ in rows]
    declared = {
        (g, n, c)
        for g, n, c in rows
        if c in _CLASS_POLICY and _declares(repo, g, n, _CLASS_POLICY[c])
    }
    migrated = {(g, n) for g, n, c in declared if c == "B"}
    settled = {(g, n) for g, n, _ in declared}
    bad_class = sorted((g, n) for g, n, c in rows if c not in ("A", "B"))
    dupes = sorted({i for i in led if led.count(i) > 1})
    missing, unknown = sorted(inv - set(led)), sorted(set(led) - inv - settled)
    for label, items in (
        ("duplicate", dupes),
        ("missing", missing),
        ("unknown", unknown),
        ("bad_class", bad_class),
    ):
        for g, n in items:
            print(f"{label}: {g} {n}")
    print(
        f"inventory={len(inv)} ledger_rows={len(led)} migrated_b={len(migrated)}"
        f" declared_a={len(settled) - len(migrated)}"
    )
    return 1 if dupes or missing or unknown or bad_class or not led else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", type=Path)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parent.parent
    if args.check:
        return check(repo, args.check)
    for row in inventory(repo):
        print("\t".join(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
