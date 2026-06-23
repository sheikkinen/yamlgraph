#!/usr/bin/env python3
"""FR-570 — Plot Modeller L4 spike evaluator.

Compares the classifier's predicted kinds against hand-authored ground truth and
writes a per-genre evaluation YAML. Pure scoring functions (``score_genre``,
``compare``) are import-safe for tests; ``main`` is the CLI entry point.

Judgement constraints honoured here:
  J2 — every evaluation is stamped ``corpus: self-derived (upper-bound)``.
  J3 — per-genre results are fractions alongside percentages; the verdict rests
       on the confusion analysis, not the bare number.
  J4 — no per-kind accuracy table (several kinds have n=1).
  J6 — an absent/unparseable prediction scores the whole genre as all-wrong,
       never crashes.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

EXAMPLE_DIR = Path(__file__).resolve().parent

CORPUS_CEILING = "self-derived (upper-bound)"

# Confusion pairs to watch in the analysis (J3 — the verdict rests on these).
CONFUSION_PAIRS = [
    ("lack", "pursuit"),
    ("donor_test", "struggle"),
    ("recognition", "exposure"),
    ("reconciliation", "victory"),
]


def _norm(text: object) -> str:
    """Normalise a subject string for tolerant comparison."""
    return " ".join(str(text or "").split()).strip().lower()


def load_ground_truth(path: str | Path) -> list[dict]:
    """Read the authored functions (id, kind, subject) from a ground-truth plot."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [
        {"id": fn["id"], "kind": fn.get("kind"), "subject": fn.get("subject")}
        for fn in data.get("functions", [])
    ]


def _fraction(correct: int, total: int) -> str:
    """Format ``correct/total (0.NN)`` — fraction beside percentage (J3)."""
    pct = (correct / total) if total else 0.0
    return f"{correct}/{total} ({pct:.2f})"


def compare(predicted: list | None, truth: list[dict]) -> tuple[list[dict], list[dict]]:
    """Per-function comparison. Returns (per_function rows, confusions).

    A ``predicted`` of ``None`` or a non-list scores every function as wrong
    (J6) without raising.
    """
    by_id: dict[str, dict] = {}
    if isinstance(predicted, list):
        for item in predicted:
            if isinstance(item, dict) and item.get("id"):
                by_id[item["id"]] = item

    per_function: list[dict] = []
    confusions: list[dict] = []
    for fn in truth:
        pred = by_id.get(fn["id"], {})
        pred_kind = pred.get("kind")
        pred_subject = pred.get("subject")
        kind_match = pred_kind == fn["kind"]
        subject_match = _norm(pred_subject) == _norm(fn["subject"])
        per_function.append(
            {
                "id": fn["id"],
                "expected_kind": fn["kind"],
                "predicted_kind": pred_kind,
                "kind_match": kind_match,
                "expected_subject": fn["subject"],
                "predicted_subject": pred_subject,
                "subject_match": subject_match,
            }
        )
        if not kind_match:
            confusions.append(
                {"expected": fn["kind"], "predicted": pred_kind, "function": fn["id"]}
            )
    return per_function, confusions


def score_genre(
    synopsis: str,
    predicted: list | None,
    truth: list[dict],
    provider: str,
    model: str,
) -> dict:
    """Build the full evaluation record for one genre (J2/J3/J6)."""
    produced_valid_yaml = isinstance(predicted, list)
    per_function, confusions = compare(predicted, truth)
    total = len(truth)
    kind_correct = sum(1 for r in per_function if r["kind_match"])
    subject_correct = sum(1 for r in per_function if r["subject_match"])

    return {
        "meta": {
            "synopsis": synopsis,
            "provider": provider,
            "model": model,
            "corpus": CORPUS_CEILING,  # J2
        },
        "summary": {
            "total": total,
            "kind_correct": kind_correct,
            "kind_accuracy": _fraction(kind_correct, total),  # J3
            "subject_correct": subject_correct,
            "subject_accuracy": _fraction(subject_correct, total),
            "produced_valid_yaml": produced_valid_yaml,  # J6
        },
        "per_function": per_function,
        "confusions": confusions,
    }


def summarise(evaluations: list[dict]) -> dict:
    """Aggregate per-genre evaluations into an overall verdict scaffold (J2/J3)."""
    total = sum(e["summary"]["total"] for e in evaluations)
    kind_correct = sum(e["summary"]["kind_correct"] for e in evaluations)
    subject_correct = sum(e["summary"]["subject_correct"] for e in evaluations)
    return {
        "corpus": CORPUS_CEILING,  # J2
        "genres": len(evaluations),
        "total_functions": total,
        "kind_accuracy": _fraction(kind_correct, total),
        "subject_accuracy": _fraction(subject_correct, total),
        "per_genre": {
            e["meta"]["synopsis"]: e["summary"]["kind_accuracy"] for e in evaluations
        },
        "note": (
            "Thresholds are triggers, not the verdict (J3). The REVISE-vs-KILL "
            "call rests on the confusion analysis. Any GO is optimistic pending "
            "a blind-corpus re-test (J2)."
        ),
    }


def _genre_name(path: Path) -> str:
    return path.stem


def main(argv: list[str] | None = None) -> int:
    """CLI: evaluate every result against its ground truth, write eval YAML."""
    parser = argparse.ArgumentParser(description="FR-570 L4 spike evaluator")
    parser.add_argument(
        "--results-dir",
        default=str(EXAMPLE_DIR / "results"),
        help="Directory of <genre>.yaml predicted-kinds files",
    )
    parser.add_argument(
        "--ground-truth-dir",
        default=str(EXAMPLE_DIR / "fixtures" / "ground-truth"),
        help="Directory of ground-truth plot YAML files",
    )
    parser.add_argument(
        "--out-dir",
        default=str(EXAMPLE_DIR / "results" / "evaluation"),
        help="Where to write per-genre evaluation YAML",
    )
    parser.add_argument("--provider", default="unknown")
    parser.add_argument("--model", default="unknown")
    args = parser.parse_args(argv)

    results_dir = Path(args.results_dir)
    gt_dir = Path(args.ground_truth_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    evaluations: list[dict] = []
    for gt_path in sorted(gt_dir.glob("*.yaml")):
        genre = _genre_name(gt_path)
        truth = load_ground_truth(gt_path)
        result_path = results_dir / f"{genre}.yaml"
        predicted: list | None = None
        if result_path.exists():
            try:
                loaded = yaml.safe_load(result_path.read_text(encoding="utf-8"))
                predicted = loaded if isinstance(loaded, list) else None
            except yaml.YAMLError:
                predicted = None  # J6: unparseable → all-wrong

        evaluation = score_genre(genre, predicted, truth, args.provider, args.model)
        evaluations.append(evaluation)
        out_path = out_dir / f"{genre}-eval.yaml"
        out_path.write_text(
            yaml.safe_dump(evaluation, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        acc = evaluation["summary"]["kind_accuracy"]
        valid = evaluation["summary"]["produced_valid_yaml"]
        print(f"  {genre}: kind {acc}  valid_yaml={valid}")

    if evaluations:
        summary = summarise(evaluations)
        (out_dir / "summary.yaml").write_text(
            yaml.safe_dump(summary, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(
            f"\nOverall kind accuracy: {summary['kind_accuracy']}  (corpus: {CORPUS_CEILING})"
        )
    else:
        print("No ground-truth files found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
