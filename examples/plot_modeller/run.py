#!/usr/bin/env python3
"""Plot Modeller spike runner — Mode 1–4.

Mode 1 (FR-570): classify kinds from glosses.
Mode 2 (FR-573): extract agents/world/belief from synopsis.
Mode 3 (FR-574): extract goals from synopsis + agents.
Mode 4 (FR-575): extract glosses (beat decomposition) from synopsis.
Mode 5 (FR-576): assign world/belief pre/eff to classified beats.

Usage:
    PROVIDER=anthropic python examples/plot_modeller/run.py
    PROVIDER=anthropic python examples/plot_modeller/run.py --mode extract-agents
    PROVIDER=anthropic python examples/plot_modeller/run.py --mode extract-goals
    PROVIDER=anthropic python examples/plot_modeller/run.py --mode extract-glosses
    PROVIDER=anthropic python examples/plot_modeller/run.py --mode assign-pre-eff
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

from nodes.tools import (  # noqa: E402
    load_glosses,
    load_glosses_with_kinds,
    load_synopsis,
)

GRAPH_PATHS = {
    "classify-kinds": EXAMPLE_DIR / "graphs" / "classify_kinds.yaml",
    "extract-agents": EXAMPLE_DIR / "graphs" / "extract_agents.yaml",
    "extract-goals": EXAMPLE_DIR / "graphs" / "extract_goals.yaml",
    "extract-glosses": EXAMPLE_DIR / "graphs" / "extract_glosses.yaml",
    "assign-pre-eff": EXAMPLE_DIR / "graphs" / "assign_pre_eff.yaml",
}
GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
SYNOPSIS_DIR = EXAMPLE_DIR / "fixtures" / "synopses"
RESULTS_DIR = EXAMPLE_DIR / "results"


def _compile(graph_key: str):
    """Load and compile a graph by key."""
    from yamlgraph.graph_loader import compile_graph, load_graph_config

    config = load_graph_config(str(GRAPH_PATHS[graph_key]))
    graph = compile_graph(config)
    return graph.compile()


def run_classify(app, gt_path: Path) -> list | None:
    """Run Mode-1 classification for one genre; return predicted kinds or None."""
    glosses = load_glosses(gt_path)
    result = app.invoke({"glosses": glosses})
    kinds = result.get("kinds")
    return kinds if isinstance(kinds, list) else None


def run_extract_agents(app, synopsis_path: Path) -> dict | None:
    """Run Mode-2 L1 extraction for one genre; return extraction dict or None."""
    synopsis = load_synopsis(synopsis_path)
    result = app.invoke({"synopsis": synopsis})
    agents = result.get("agents")
    if not isinstance(agents, list):
        return None
    return {
        "agents": agents,
        "initial_world": result.get("initial_world", []),
        "initial_belief": result.get("initial_belief", []),
    }


def _main_classify(args, provider: str) -> int:
    """Mode 1: classify kinds."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    gt_paths = sorted(GT_DIR.glob("*.yaml"))
    if args.genre:
        gt_paths = [p for p in gt_paths if p.stem == args.genre]
        if not gt_paths:
            print(f"No ground-truth file matches '{args.genre}'")
            return 1

    app = _compile("classify-kinds")
    for gt_path in gt_paths:
        genre = gt_path.stem
        print(f"▶ classifying {genre} ...")
        try:
            predicted = run_classify(app, gt_path)
        except Exception as exc:  # J6: hard failure → all-wrong, not a crash
            print(f"  ✗ run failed: {exc}")
            predicted = None
        out_path = RESULTS_DIR / f"{genre}.yaml"
        out_path.write_text(
            yaml.safe_dump(predicted, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        n = len(predicted) if isinstance(predicted, list) else 0
        print(f"  → wrote {n} predicted kinds to {out_path.name}")

    from evaluate import main as evaluate_main

    print("\n── evaluation ──")
    return evaluate_main(["--provider", provider, "--model", args.model])


def _main_extract_agents(args, provider: str) -> int:
    """Mode 2: extract agents from synopses."""
    l1_dir = RESULTS_DIR / "l1"
    l1_dir.mkdir(parents=True, exist_ok=True)

    synopsis_paths = sorted(SYNOPSIS_DIR.glob("*.txt"))
    if args.genre:
        synopsis_paths = [p for p in synopsis_paths if p.stem == args.genre]
        if not synopsis_paths:
            print(f"No synopsis file matches '{args.genre}'")
            return 1

    app = _compile("extract-agents")
    for syn_path in synopsis_paths:
        genre = syn_path.stem
        print(f"▶ extracting agents from {genre} ...")
        try:
            extracted = run_extract_agents(app, syn_path)
        except Exception as exc:
            print(f"  ✗ run failed: {exc}")
            extracted = None
        out_path = l1_dir / f"{genre}.yaml"
        out_path.write_text(
            yaml.safe_dump(extracted, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        n = len(extracted["agents"]) if isinstance(extracted, dict) else 0
        print(f"  → wrote {n} agents to {out_path.name}")

    from evaluate import main_l1 as evaluate_l1

    print("\n── L1 evaluation ──")
    return evaluate_l1(["--provider", provider, "--model", args.model])


def _load_gt_agents(gt_path: Path) -> list[str]:
    """Load the ground-truth agent list for L2 isolation."""
    data = yaml.safe_load(gt_path.read_text(encoding="utf-8"))
    return data.get("agents", [])


def run_extract_goals(app, synopsis_path: Path, agents: list[str]) -> list | None:
    """Run Mode-3 L2 goal extraction; return goals list or None."""
    synopsis = load_synopsis(synopsis_path)
    result = app.invoke({"synopsis": synopsis, "agents": agents})
    goals = result.get("goals")
    return goals if isinstance(goals, list) else None


def _main_extract_goals(args, provider: str) -> int:
    """Mode 3: extract goals from synopses (using ground-truth agents for isolation)."""
    l2_dir = RESULTS_DIR / "l2"
    l2_dir.mkdir(parents=True, exist_ok=True)

    synopsis_paths = sorted(SYNOPSIS_DIR.glob("*.txt"))
    if args.genre:
        synopsis_paths = [p for p in synopsis_paths if p.stem == args.genre]
        if not synopsis_paths:
            print(f"No synopsis file matches '{args.genre}'")
            return 1

    app = _compile("extract-goals")
    for syn_path in synopsis_paths:
        genre = syn_path.stem
        gt_path = GT_DIR / f"{genre}.yaml"
        if not gt_path.exists():
            print(f"  ✗ no ground-truth file for {genre}")
            continue
        agents = _load_gt_agents(gt_path)
        print(f"▶ extracting goals from {genre} ({len(agents)} agents) ...")
        try:
            goals = run_extract_goals(app, syn_path, agents)
        except Exception as exc:
            print(f"  ✗ run failed: {exc}")
            goals = None
        out_path = l2_dir / f"{genre}.yaml"
        out_path.write_text(
            yaml.safe_dump(goals, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        n = len(goals) if isinstance(goals, list) else 0
        print(f"  → wrote {n} goals to {out_path.name}")

    from evaluate import main_l2 as evaluate_l2

    print("\n── L2 evaluation ──")
    return evaluate_l2(["--provider", provider, "--model", args.model])


def run_extract_glosses(app, synopsis_path: Path) -> list | None:
    """Run Mode-4 L3 beat decomposition; return glosses list or None."""
    synopsis = load_synopsis(synopsis_path)
    result = app.invoke({"synopsis": synopsis})
    glosses = result.get("glosses")
    return glosses if isinstance(glosses, list) else None


def _main_extract_glosses(args, provider: str) -> int:
    """Mode 4: extract glosses (beat decomposition) from synopses."""
    l3_dir = RESULTS_DIR / "l3"
    l3_dir.mkdir(parents=True, exist_ok=True)

    synopsis_paths = sorted(SYNOPSIS_DIR.glob("*.txt"))
    if args.genre:
        synopsis_paths = [p for p in synopsis_paths if p.stem == args.genre]
        if not synopsis_paths:
            print(f"No synopsis file matches '{args.genre}'")
            return 1

    app = _compile("extract-glosses")
    for syn_path in synopsis_paths:
        genre = syn_path.stem
        print(f"▶ extracting glosses from {genre} ...")
        try:
            glosses = run_extract_glosses(app, syn_path)
        except Exception as exc:
            print(f"  ✗ run failed: {exc}")
            glosses = None
        out_path = l3_dir / f"{genre}.yaml"
        out_path.write_text(
            yaml.safe_dump(glosses, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        n = len(glosses) if isinstance(glosses, list) else 0
        print(f"  → wrote {n} glosses to {out_path.name}")

    from evaluate import main_l3 as evaluate_l3

    print("\n── L3 evaluation ──")
    return evaluate_l3(["--provider", provider, "--model", args.model])


def run_assign_pre_eff(app, gt_path: Path, agents: list[str]) -> list | None:
    """Run Mode-5 L5 pre/eff assignment; return pre_eff list or None."""
    glosses = load_glosses_with_kinds(gt_path)
    result = app.invoke({"glosses": glosses, "agents": agents})
    pre_eff = result.get("pre_eff")
    return pre_eff if isinstance(pre_eff, list) else None


def _main_assign_pre_eff(args, provider: str) -> int:
    """Mode 5: assign pre/eff to classified beats (ground-truth glosses+kinds)."""
    l5_dir = RESULTS_DIR / "l5"
    l5_dir.mkdir(parents=True, exist_ok=True)

    gt_paths = sorted(GT_DIR.glob("*.yaml"))
    if args.genre:
        gt_paths = [p for p in gt_paths if p.stem == args.genre]
        if not gt_paths:
            print(f"No ground-truth file matches '{args.genre}'")
            return 1

    app = _compile("assign-pre-eff")
    for gt_path in gt_paths:
        genre = gt_path.stem
        agents = _load_gt_agents(gt_path)
        print(f"▶ assigning pre/eff for {genre} ({len(agents)} agents) ...")
        try:
            pre_eff = run_assign_pre_eff(app, gt_path, agents)
        except Exception as exc:  # J6: hard failure → all-wrong, not a crash
            print(f"  ✗ run failed: {exc}")
            pre_eff = None
        out_path = l5_dir / f"{genre}.yaml"
        out_path.write_text(
            yaml.safe_dump(pre_eff, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        n = len(pre_eff) if isinstance(pre_eff, list) else 0
        print(f"  → wrote pre/eff for {n} beats to {out_path.name}")

    from evaluate import main_l5 as evaluate_l5

    print("\n── L5 evaluation ──")
    return evaluate_l5(["--provider", provider, "--model", args.model])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plot Modeller spike runner")
    parser.add_argument(
        "--mode",
        choices=[
            "classify-kinds",
            "extract-agents",
            "extract-goals",
            "extract-glosses",
            "assign-pre-eff",
        ],
        default="classify-kinds",
        help="Which spike mode to run (default: classify-kinds)",
    )
    parser.add_argument("--genre", help="Run a single genre stem (default: all)")
    parser.add_argument(
        "--model",
        default=os.environ.get("ANTHROPIC_MODEL", "unknown"),
        help="Model label to stamp in the evaluation (informational)",
    )
    args = parser.parse_args(argv)

    provider = os.environ.get("PROVIDER", "anthropic")

    if args.mode == "extract-agents":
        return _main_extract_agents(args, provider)
    if args.mode == "extract-goals":
        return _main_extract_goals(args, provider)
    if args.mode == "extract-glosses":
        return _main_extract_glosses(args, provider)
    if args.mode == "assign-pre-eff":
        return _main_assign_pre_eff(args, provider)
    return _main_classify(args, provider)


if __name__ == "__main__":
    raise SystemExit(main())
