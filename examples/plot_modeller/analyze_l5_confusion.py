"""L5 confusion analyzer (FR-584 C5) — where does the model struggle?

Dissects every predicted-vs-truth world-state predicate across all ground-truth
fixtures, using the evaluator's own tolerant matching, and reports:
  - per-beat MISS (a GT fluent no prediction matched)
  - per-beat FP   (a predicted fluent matching no GT fluent)
  - aggregate MISS/FP counts by predicate type (the precision/recall x-ray)
  - the `at` false-positive count (the FR-583 location-flooding tripwire)

Promoted from the throwaway FR-583 dump so the L5 confusion x-ray is a standing,
reusable artifact rather than re-created by hand each spike.

Usage:
    python analyze_l5_confusion.py            # full per-beat + summary
    python analyze_l5_confusion.py --summary  # aggregate table only
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml
from evaluate import _fluent_matches, _load_gt_pre_eff

EXAMPLE_DIR = Path(__file__).resolve().parent
L5_DIR = EXAMPLE_DIR / "results" / "l5"
GT_DIR = EXAMPLE_DIR / "fixtures" / "ground-truth"
_WORLD_SLICES = ("pre_world", "eff_world")


def _fmt(fluent: dict) -> str:
    pred = fluent.get("pred")
    args = ", ".join(map(str, fluent.get("args", []) or []))
    return f"{pred}({args})={fluent.get('value')}"


def _match_slice(pred_list: list, gt_list: list) -> tuple[list, list]:
    """Greedy tolerant match → (missed_gt_fluents, false_positive_predictions)."""
    used: set[int] = set()
    missed = []
    for t in gt_list:
        hit = False
        for i, p in enumerate(pred_list):
            if i in used:
                continue
            if _fluent_matches(p, t):
                used.add(i)
                hit = True
                break
        if not hit:
            missed.append(t)
    false_pos = [p for i, p in enumerate(pred_list) if i not in used]
    return missed, false_pos


def analyze(verbose: bool = True) -> dict:
    """Run the confusion analysis; return aggregate counters."""
    miss_by_pred: Counter = Counter()
    fp_by_pred: Counter = Counter()
    at_fp = 0
    for gt_path in sorted(GT_DIR.glob("*.yaml")):
        genre = gt_path.stem
        pred_path = L5_DIR / f"{genre}.yaml"
        if not pred_path.exists():
            continue
        gt = _load_gt_pre_eff(gt_path)
        pred_data = yaml.safe_load(pred_path.read_text(encoding="utf-8")) or []
        pred_by_id = {
            it["id"]: it for it in pred_data if isinstance(it, dict) and it.get("id")
        }
        if verbose:
            print(f"\n{'=' * 70}\n{genre}\n{'=' * 70}")
        for bid, g in gt.items():
            p = pred_by_id.get(bid, {})
            for slot in _WORLD_SLICES:
                missed, fps = _match_slice(p.get(slot) or [], g.get(slot) or [])
                for m in missed:
                    miss_by_pred[m.get("pred")] += 1
                for f in fps:
                    fp_by_pred[f.get("pred")] += 1
                    if f.get("pred") == "at":
                        at_fp += 1
                if verbose and (missed or fps):
                    print(f"  {bid}.{slot}:")
                    for m in missed:
                        print(f"     MISS  {_fmt(m)}")
                    for f in fps:
                        print(f"     FP    {_fmt(f)}")
    return {
        "miss_by_pred": miss_by_pred,
        "fp_by_pred": fp_by_pred,
        "at_fp": at_fp,
        "miss_total": sum(miss_by_pred.values()),
        "fp_total": sum(fp_by_pred.values()),
    }


def _print_summary(stats: dict) -> None:
    print(f"\n{'=' * 70}\nSUMMARY\n{'=' * 70}")
    print(f"MISS total: {stats['miss_total']}   FP total: {stats['fp_total']}")
    print("MISS by predicate:", dict(stats["miss_by_pred"].most_common()))
    print("FP   by predicate:", dict(stats["fp_by_pred"].most_common()))
    fp_total = stats["fp_total"] or 1
    print(
        f"at-flood: {stats['at_fp']}/{stats['fp_total']} FPs "
        f"({stats['at_fp'] / fp_total:.0%}) are `at` predicates"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FR-584 L5 confusion analyzer")
    parser.add_argument("--summary", action="store_true", help="aggregate table only")
    args = parser.parse_args(argv)
    stats = analyze(verbose=not args.summary)
    _print_summary(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
