#!/usr/bin/env python3
"""FR-570 — Plot Modeller L4 spike runner (Mode 1: isolate L4).

For each ground-truth plot, extract its glosses (stripping the authored ``kind``
and ``subject`` labels), run the ``classify_kinds`` graph, and write the
predicted kinds to ``results/<genre>.yaml``. Then invoke the evaluator.

Mode 1 tests classification in isolation: the model sees only id/gloss/chapter
and must recover kind + subject. The corpus is self-derived, so the measured
accuracy is an upper bound (FR-570 J2).

Usage:
    PROVIDER=anthropic python examples/plot_modeller/run.py
    PROVIDER=anthropic python examples/plot_modeller/run.py --genre detective-thriller-the-vanished-witness
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

EXAMPLE_DIR = Path(__file__).resolve().parent
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

from nodes.tools import load_glosses  # noqa: E402

GRAPH_PATH = EXAMPLE_DIR / "graphs" / "classify_kinds.yaml"
GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
RESULTS_DIR = EXAMPLE_DIR / "results"


def _compile():
    """Load and compile the classify_kinds graph."""
    from yamlgraph.graph_loader import compile_graph, load_graph_config

    config = load_graph_config(str(GRAPH_PATH))
    graph = compile_graph(config)
    return graph.compile()


def run_genre(app, gt_path: Path) -> list | None:
    """Run Mode-1 classification for one genre; return predicted kinds or None."""
    glosses = load_glosses(gt_path)
    result = app.invoke({"glosses": glosses})
    kinds = result.get("kinds")
    return kinds if isinstance(kinds, list) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FR-570 L4 spike runner (Mode 1)")
    parser.add_argument("--genre", help="Run a single genre stem (default: all)")
    parser.add_argument(
        "--model",
        default=os.environ.get("ANTHROPIC_MODEL", "unknown"),
        help="Model label to stamp in the evaluation (informational)",
    )
    args = parser.parse_args(argv)

    provider = os.environ.get("PROVIDER", "anthropic")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    gt_paths = sorted(GT_DIR.glob("*.yaml"))
    if args.genre:
        gt_paths = [p for p in gt_paths if p.stem == args.genre]
        if not gt_paths:
            print(f"No ground-truth file matches '{args.genre}'")
            return 1

    app = _compile()
    for gt_path in gt_paths:
        genre = gt_path.stem
        print(f"▶ classifying {genre} ...")
        try:
            predicted = run_genre(app, gt_path)
        except Exception as exc:  # J6: a hard failure is still all-wrong, not a crash
            print(f"  ✗ run failed: {exc}")
            predicted = None
        out_path = RESULTS_DIR / f"{genre}.yaml"
        out_path.write_text(
            yaml.safe_dump(predicted, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        n = len(predicted) if isinstance(predicted, list) else 0
        print(f"  → wrote {n} predicted kinds to {out_path.name}")

    # Evaluate against ground truth.
    from evaluate import main as evaluate_main

    print("\n── evaluation ──")
    return evaluate_main(["--provider", provider, "--model", args.model])


if __name__ == "__main__":
    raise SystemExit(main())
