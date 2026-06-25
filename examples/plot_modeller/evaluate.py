#!/usr/bin/env python3
"""Plot Modeller spike evaluator — L4 kinds + L1 agents.

L4 (FR-570): compares predicted kinds against ground truth.
L1 (FR-573): compares extracted agents/world/belief against ground truth.

Pure scoring functions are import-safe for tests; ``main`` / ``main_l1`` are
the CLI entry points.

Judgement constraints honoured:
  J2 — every evaluation is stamped ``corpus: self-derived (upper-bound)``.
  J3 — per-genre results are fractions alongside percentages.
  J6 — absent/unparseable prediction → all-wrong, never crashes.
  C1 — world_recall uses tolerant matching (normalize + contains/prefix).
  C2 — belief_recall is informational, expected low (J2 leakage).
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


# ---------------------------------------------------------------------------
# L1 evaluation — agents, world state, belief (FR-573)
# ---------------------------------------------------------------------------


def _norm_args(args: list) -> list[str]:
    """Normalise fluent args for tolerant matching (C1).

    Strips articles, lowercases, collapses whitespace, normalises
    underscores to spaces (FR-581 failure mode 3).
    """
    articles = {"a", "an", "the"}
    out: list[str] = []
    for a in args:
        words = str(a).lower().replace("_", " ").split()
        words = [w for w in words if w not in articles]
        out.append(" ".join(words).strip())
    return out


def _norm_value(v: object) -> str:
    """Normalise a fluent value for tolerant comparison."""
    return str(v).strip().lower()


# FR-583 Part 1: token-set Jaccard tolerance for multi-word args. Single-word
# args keep exact/contains matching — the threshold loosens ONLY multi-word
# overlaps (order-swapped or non-contiguous), never single-word synonyms.
_ARGS_JACCARD_THRESHOLD = 0.5


def _args_jaccard_match(
    pa: str, ta: str, threshold: float = _ARGS_JACCARD_THRESHOLD
) -> bool:
    """Multi-word arg tolerance (FR-583 Part 1): token-set Jaccard >= threshold.

    Returns False when both sides are single tokens, so genuine single-word
    synonym gaps (``together`` vs ``lovers``) stay rejected (AC#7). For
    multi-word args, accepts when ``|intersection| / |union|`` >= threshold,
    bridging order-swapped (``road river`` vs ``river road``) and non-contiguous
    superset (``Seoul quarter lab`` vs ``Seoul lab``) overlaps that the
    substring check misses.
    """
    p_tokens = set(pa.split())
    t_tokens = set(ta.split())
    if len(p_tokens) <= 1 and len(t_tokens) <= 1:
        return False
    return _jaccard(p_tokens, t_tokens) >= threshold


def _arg_matches(pa: str, ta: str) -> bool:
    """Shared per-arg comparator (FR-583 C1): exact, contains/prefix, or
    multi-word Jaccard fallback. Called by both ``_fluent_matches`` (L1/L5
    world) and ``_goal_matches`` (L2) so the arg tolerance cannot drift between
    layers.
    """
    if pa == ta or pa in ta or ta in pa:
        return True
    return _args_jaccard_match(pa, ta)


def _fluent_matches(pred: dict, truth: dict) -> bool:
    """Tolerant fluent matching (C1): same pred, args contains/prefix, value tolerant."""
    if not isinstance(pred, dict) or not isinstance(truth, dict):
        return False
    if _norm(pred.get("pred")) != _norm(truth.get("pred")):
        return False
    pred_args = _norm_args(pred.get("args", []))
    truth_args = _norm_args(truth.get("args", []))
    if len(pred_args) != len(truth_args):
        return False
    for pa, ta in zip(pred_args, truth_args, strict=False):
        if not _arg_matches(pa, ta):
            return False
    # Value: tolerant comparison
    return _norm_value(pred.get("value", True)) == _norm_value(truth.get("value", True))


def _count_world_matches(predicted: list, truth: list) -> int:
    """Count how many ground-truth fluents are matched by predicted (C1 tolerant)."""
    matched = 0
    used: set[int] = set()
    for t in truth:
        for i, p in enumerate(predicted):
            if i not in used and _fluent_matches(p, t):
                matched += 1
                used.add(i)
                break
    return matched


def _norm_agent(name: object) -> str:
    """Normalise an agent name for comparison."""
    return _norm(name)


def _agent_matches(pred_agents: list[str], truth_agents: list[str]) -> tuple[int, int]:
    """Agent recall numerator and precision numerator (tolerant name matching).

    Returns (recall_hits, precision_hits).
    """
    pred_normed = {_norm_agent(a): a for a in pred_agents}
    truth_normed = {_norm_agent(a): a for a in truth_agents}

    recall_hits = 0
    for tn in truth_normed:
        # Exact normalised match, or contains/prefix
        for pn in pred_normed:
            if pn == tn or pn in tn or tn in pn:
                recall_hits += 1
                break

    precision_hits = 0
    for pn in pred_normed:
        for tn in truth_normed:
            if pn == tn or pn in tn or tn in pn:
                precision_hits += 1
                break

    return recall_hits, precision_hits


def score_l1(
    genre: str,
    predicted: dict | None,
    truth: dict,
    provider: str,
    model: str,
) -> dict:
    """Build L1 evaluation record for one genre (FR-573)."""
    truth_agents = truth.get("agents", [])
    truth_world = truth.get("initial_world", [])
    truth_belief = truth.get("initial_belief", [])

    if not isinstance(predicted, dict):
        return {
            "meta": {"genre": genre, "provider": provider, "model": model},
            "summary": {
                "agent_recall": _fraction(0, len(truth_agents)),
                "agent_precision": _fraction(0, 0),
                "world_recall": _fraction(0, len(truth_world)),
                "belief_recall": _fraction(0, len(truth_belief)),
                "produced_valid_yaml": False,
            },
        }

    pred_agents = predicted.get("agents", [])
    pred_world = predicted.get("initial_world", [])
    pred_belief = predicted.get("initial_belief", [])

    recall_hits, precision_hits = _agent_matches(pred_agents, truth_agents)
    world_correct = _count_world_matches(pred_world, truth_world)

    # Belief matching: tolerant on fluent, exact on observer
    belief_correct = 0
    used_beliefs: set[int] = set()
    for tb in truth_belief:
        if not isinstance(tb, dict):
            continue
        for i, pb in enumerate(pred_belief):
            if i in used_beliefs or not isinstance(pb, dict):
                continue
            if _norm(pb.get("observer")) != _norm(tb.get("observer")):
                continue
            if _fluent_matches(pb.get("fluent", {}), tb.get("fluent", {})):
                belief_correct += 1
                used_beliefs.add(i)
                break

    return {
        "meta": {"genre": genre, "provider": provider, "model": model},
        "summary": {
            "agent_recall": _fraction(recall_hits, len(truth_agents)),
            "agent_precision": _fraction(precision_hits, len(pred_agents)),
            "world_recall": _fraction(world_correct, len(truth_world)),
            "belief_recall": _fraction(belief_correct, len(truth_belief)),
            "produced_valid_yaml": True,
        },
        "agents": {
            "truth": truth_agents,
            "predicted": pred_agents,
        },
    }


def summarise_l1(evaluations: list[dict]) -> dict:
    """Aggregate L1 per-genre evaluations into an overall summary (FR-573)."""

    def _sum_fraction(evals: list[dict], key: str) -> tuple[int, int]:
        total_num = 0
        total_den = 0
        for e in evals:
            frac = e["summary"][key]
            parts = frac.split("/")
            num = int(parts[0])
            den = int(parts[1].split(" ")[0])
            total_num += num
            total_den += den
        return total_num, total_den

    ar_n, ar_d = _sum_fraction(evaluations, "agent_recall")
    ap_n, ap_d = _sum_fraction(evaluations, "agent_precision")
    wr_n, wr_d = _sum_fraction(evaluations, "world_recall")
    br_n, br_d = _sum_fraction(evaluations, "belief_recall")

    return {
        "corpus": {
            "synopses": len(evaluations),
            "self_derived": sum(
                1
                for e in evaluations
                if e["meta"]["genre"] != "historical-fiction-the-salt-road"
            ),
            "blind": sum(
                1
                for e in evaluations
                if e["meta"]["genre"] == "historical-fiction-the-salt-road"
            ),
        },
        "agent_recall": _fraction(ar_n, ar_d),
        "agent_precision": _fraction(ap_n, ap_d),
        "world_recall": _fraction(wr_n, wr_d),
        "belief_recall": _fraction(br_n, br_d),
        "per_genre": {
            e["meta"]["genre"]: {
                "agent_recall": e["summary"]["agent_recall"],
                "world_recall": e["summary"]["world_recall"],
            }
            for e in evaluations
        },
        "verdict": "pending",
        "conditions": [
            "agent recall >= 0.90 for GO",
            "borderline 0.70-0.90 defaults to REVISE (J:N2)",
        ],
        "note": (
            "World/belief recall are informational — the gate is on agents. "
            "World state extraction is harder (the model must infer predicates "
            "from prose) and is expected to be lower than agent recall (C1). "
            "Belief recall is expected low — ground-truth beliefs encode dramatic "
            "irony from full-plot knowledge, not extractable from synopsis alone (C2)."
        ),
    }


def _load_gt_l1(path: Path) -> dict:
    """Load agents, initial_world, initial_belief from a ground-truth plot."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return {
        "agents": data.get("agents", []),
        "initial_world": data.get("initial_world", []),
        "initial_belief": data.get("initial_belief", []),
    }


def main_l1(argv: list[str] | None = None) -> int:
    """CLI: evaluate L1 extraction results against ground truth."""
    parser = argparse.ArgumentParser(description="FR-573 L1 evaluator")
    parser.add_argument(
        "--results-dir",
        default=str(EXAMPLE_DIR / "results" / "l1"),
        help="Directory of <genre>.yaml L1 extraction files",
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
        truth = _load_gt_l1(gt_path)
        result_path = results_dir / f"{genre}.yaml"
        predicted: dict | None = None
        if result_path.exists():
            try:
                loaded = yaml.safe_load(result_path.read_text(encoding="utf-8"))
                predicted = loaded if isinstance(loaded, dict) else None
            except yaml.YAMLError:
                predicted = None

        evaluation = score_l1(genre, predicted, truth, args.provider, args.model)
        evaluations.append(evaluation)
        out_path = out_dir / f"{genre}-l1-eval.yaml"
        out_path.write_text(
            yaml.safe_dump(evaluation, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        ar = evaluation["summary"]["agent_recall"]
        wr = evaluation["summary"]["world_recall"]
        print(f"  {genre}: agent_recall {ar}  world_recall {wr}")

    if evaluations:
        summary = summarise_l1(evaluations)
        (out_dir / "l1-summary.yaml").write_text(
            yaml.safe_dump(summary, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"\nOverall agent recall: {summary['agent_recall']}")
        print(f"Overall world recall: {summary['world_recall']}")
        print(f"Overall belief recall: {summary['belief_recall']}")
    else:
        print("No ground-truth files found.")
    return 0


# ---------------------------------------------------------------------------
# L2 evaluation — goals (FR-574)
# ---------------------------------------------------------------------------


def _goal_matches(pred: dict, truth: dict) -> bool:
    """Tolerant goal matching (C3): same pred, order-insensitive args for symmetric
    predicates (rel, faction), tolerant value comparison.
    """
    if not isinstance(pred, dict) or not isinstance(truth, dict):
        return False
    if _norm(pred.get("pred")) != _norm(truth.get("pred")):
        return False

    pred_args = _norm_args(pred.get("args", []))
    truth_args = _norm_args(truth.get("args", []))

    # For symmetric predicates, try both orderings (C3)
    sym_preds = {"rel", "faction"}
    if _norm(truth.get("pred")) in sym_preds:
        if sorted(pred_args) != sorted(truth_args) and not _args_tolerant_match(
            pred_args, truth_args
        ):
            return False
    elif len(pred_args) != len(truth_args):
        return False
    else:
        for pa, ta in zip(pred_args, truth_args, strict=False):
            if not _arg_matches(pa, ta):
                return False

    # Value: tolerant comparison (contains/prefix)
    pv = _norm_value(pred.get("value", True))
    tv = _norm_value(truth.get("value", True))
    return not (pv != tv and pv not in tv and tv not in pv)


def _args_tolerant_match(pred_args: list[str], truth_args: list[str]) -> bool:
    """Check if args match with contains/prefix, order-insensitive."""
    if len(pred_args) != len(truth_args):
        return False
    ps = sorted(pred_args)
    ts = sorted(truth_args)
    return all(_arg_matches(pa, ta) for pa, ta in zip(ps, ts, strict=False))


def _count_goal_matches(predicted: list, truth: list) -> int:
    """Count how many ground-truth goals are matched by predicted (C3 tolerant)."""
    matched = 0
    used: set[int] = set()
    for t in truth:
        for i, p in enumerate(predicted):
            if i not in used and _goal_matches(p, t):
                matched += 1
                used.add(i)
                break
    return matched


def score_l2(
    genre: str,
    predicted: list | None,
    truth_goals: list,
    provider: str,
    model: str,
) -> dict:
    """Build L2 evaluation record for one genre (FR-574)."""
    if not isinstance(predicted, list):
        return {
            "meta": {"genre": genre, "provider": provider, "model": model},
            "summary": {
                "goal_recall": _fraction(0, len(truth_goals)),
                "goal_precision": _fraction(0, 0),
                "produced_valid_yaml": False,
            },
        }

    recall_hits = _count_goal_matches(predicted, truth_goals)
    precision_hits = _count_goal_matches(truth_goals, predicted)

    return {
        "meta": {"genre": genre, "provider": provider, "model": model},
        "summary": {
            "goal_recall": _fraction(recall_hits, len(truth_goals)),
            "goal_precision": _fraction(precision_hits, len(predicted)),
            "produced_valid_yaml": True,
        },
        "goals": {
            "truth": truth_goals,
            "predicted": predicted,
        },
    }


def summarise_l2(evaluations: list[dict]) -> dict:
    """Aggregate L2 per-genre evaluations into an overall summary (FR-574)."""

    def _sum_fraction(evals: list[dict], key: str) -> tuple[int, int]:
        total_num = 0
        total_den = 0
        for e in evals:
            frac = e["summary"][key]
            parts = frac.split("/")
            num = int(parts[0])
            den = int(parts[1].split(" ")[0])
            total_num += num
            total_den += den
        return total_num, total_den

    gr_n, gr_d = _sum_fraction(evaluations, "goal_recall")
    gp_n, gp_d = _sum_fraction(evaluations, "goal_precision")

    return {
        "corpus": {"synopses": len(evaluations)},
        "goal_recall": _fraction(gr_n, gr_d),
        "goal_precision": _fraction(gp_n, gp_d),
        "per_genre": {
            e["meta"]["genre"]: e["summary"]["goal_recall"] for e in evaluations
        },
        "verdict": "pending",
        "conditions": [
            "goal recall >= 0.80 for GO",
            "borderline 0.50-0.80 defaults to REVISE (J:N2)",
        ],
        "note": (
            "Goal extraction is inherently ambiguous — reasonable humans disagree "
            "on what counts as a goal. Matching uses order-insensitive args for "
            "symmetric predicates and tolerant value comparison (C3). The spike is "
            "'done' when the metric is measured and a verdict recorded (C4)."
        ),
    }


def _load_gt_goals(path: Path) -> list:
    """Load goals from a ground-truth plot."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data.get("goals", [])


def main_l2(argv: list[str] | None = None) -> int:
    """CLI: evaluate L2 goal extraction results against ground truth."""
    parser = argparse.ArgumentParser(description="FR-574 L2 evaluator")
    parser.add_argument(
        "--results-dir",
        default=str(EXAMPLE_DIR / "results" / "l2"),
    )
    parser.add_argument(
        "--ground-truth-dir",
        default=str(EXAMPLE_DIR / "fixtures" / "ground-truth"),
    )
    parser.add_argument(
        "--out-dir",
        default=str(EXAMPLE_DIR / "results" / "evaluation"),
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
        truth_goals = _load_gt_goals(gt_path)
        result_path = results_dir / f"{genre}.yaml"
        predicted: list | None = None
        if result_path.exists():
            try:
                loaded = yaml.safe_load(result_path.read_text(encoding="utf-8"))
                predicted = loaded if isinstance(loaded, list) else None
            except yaml.YAMLError:
                predicted = None

        evaluation = score_l2(genre, predicted, truth_goals, args.provider, args.model)
        evaluations.append(evaluation)
        out_path = out_dir / f"{genre}-l2-eval.yaml"
        out_path.write_text(
            yaml.safe_dump(evaluation, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        gr = evaluation["summary"]["goal_recall"]
        print(f"  {genre}: goal_recall {gr}")

    if evaluations:
        summary = summarise_l2(evaluations)
        (out_dir / "l2-summary.yaml").write_text(
            yaml.safe_dump(summary, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"\nOverall goal recall: {summary['goal_recall']}")
        print(f"Overall goal precision: {summary['goal_precision']}")
    else:
        print("No ground-truth files found.")
    return 0


# ---------------------------------------------------------------------------
# L3 evaluation — beat decomposition / glosses (FR-575)
# ---------------------------------------------------------------------------

# English stopwords for Jaccard calculation (C6 — strip before computing overlap).
_STOPWORDS = frozenset(
    "a an the and or but in on at to for of is are was were be been being "
    "has have had do does did will would shall should can could may might "
    "not no nor so yet if then than that this these those it its he she "
    "his her him they them their we us our you your who whom which what "
    "with from by as into through during before after above below between "
    "out up down off over under again further once here there when where "
    "why how all each every both few more most other some such only own "
    "same just also very".split()
)


def _content_words(text: str) -> set[str]:
    """Extract content words (lowercased, stopwords stripped) for Jaccard (C6)."""
    return {w for w in text.lower().split() if w.isalpha() and w not in _STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity on content-word sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# Default threshold — calibrated on known-good pair (C6).
# Detective-thriller GT-F2 vs P-F2 ("discovers witness gone" vs "confirms witness
# gone") scores 0.208 Jaccard on content words — a clear semantic match. Setting
# threshold to 0.15 admits genuine paraphrase while still rejecting unrelated beats
# (disjoint pairs score < 0.05).
BEAT_MATCH_THRESHOLD = 0.15


def _best_gloss_match(pred_beat: dict, truth_beats: list[dict]) -> tuple[int, float]:
    """Find the truth beat with highest Jaccard to the predicted beat.

    Returns (best_index, best_score). Returns (-1, 0.0) if no truth beats.
    """
    pred_words = _content_words(str(pred_beat.get("gloss", "")))
    best_idx = -1
    best_score = 0.0
    for i, tb in enumerate(truth_beats):
        truth_words = _content_words(str(tb.get("gloss", "")))
        score = _jaccard(pred_words, truth_words)
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx, best_score


def _count_beat_recall(
    predicted: list[dict], truth: list[dict], threshold: float
) -> int:
    """Many-to-one beat recall (C5): each truth beat can match ANY predicted beat.

    A single coarse predicted beat covering two truth beats counts both as
    recalled. This is explicitly many-to-one, NOT bipartite 1:1.
    """
    recalled = 0
    for tb in truth:
        truth_words = _content_words(str(tb.get("gloss", "")))
        for pb in predicted:
            pred_words = _content_words(str(pb.get("gloss", "")))
            if _jaccard(pred_words, truth_words) >= threshold:
                recalled += 1
                break
    return recalled


def _count_beat_precision(
    predicted: list[dict], truth: list[dict], threshold: float
) -> int:
    """Beat precision: how many predicted beats match at least one truth beat."""
    matched = 0
    for pb in predicted:
        pred_words = _content_words(str(pb.get("gloss", "")))
        for tb in truth:
            truth_words = _content_words(str(tb.get("gloss", "")))
            if _jaccard(pred_words, truth_words) >= threshold:
                matched += 1
                break
    return matched


def score_l3(
    genre: str,
    predicted: list | None,
    truth_glosses: list[dict],
    provider: str,
    model: str,
    threshold: float = BEAT_MATCH_THRESHOLD,
) -> dict:
    """Build L3 evaluation record for one genre (FR-575)."""
    if not isinstance(predicted, list):
        return {
            "meta": {"genre": genre, "provider": provider, "model": model},
            "summary": {
                "beat_recall": _fraction(0, len(truth_glosses)),
                "beat_precision": _fraction(0, 0),
                "count_delta": len(truth_glosses),
                "produced_valid_yaml": False,
                "threshold": threshold,
            },
        }

    recall_hits = _count_beat_recall(predicted, truth_glosses, threshold)
    precision_hits = _count_beat_precision(predicted, truth_glosses, threshold)

    return {
        "meta": {"genre": genre, "provider": provider, "model": model},
        "summary": {
            "beat_recall": _fraction(recall_hits, len(truth_glosses)),
            "beat_precision": _fraction(precision_hits, len(predicted)),
            "count_delta": abs(len(predicted) - len(truth_glosses)),
            "produced_valid_yaml": True,
            "threshold": threshold,
        },
    }


def summarise_l3(evaluations: list[dict]) -> dict:
    """Aggregate L3 per-genre evaluations into an overall summary (FR-575)."""

    def _sum_fraction(evals: list[dict], key: str) -> tuple[int, int]:
        total_num = 0
        total_den = 0
        for e in evals:
            frac = e["summary"][key]
            parts = frac.split("/")
            num = int(parts[0])
            den = int(parts[1].split(" ")[0])
            total_num += num
            total_den += den
        return total_num, total_den

    br_n, br_d = _sum_fraction(evaluations, "beat_recall")
    bp_n, bp_d = _sum_fraction(evaluations, "beat_precision")

    return {
        "corpus": {"synopses": len(evaluations)},
        "beat_recall": _fraction(br_n, br_d),
        "beat_precision": _fraction(bp_n, bp_d),
        "per_genre": {
            e["meta"]["genre"]: e["summary"]["beat_recall"] for e in evaluations
        },
        "verdict": "pending",
        "conditions": [
            "beat recall >= 0.80 for GO",
            "borderline 0.55-0.80 defaults to REVISE (J:N2)",
        ],
        "note": (
            "Beat matching uses many-to-one assignment (C5) — a single coarse "
            "extracted beat covering two GT beats counts both as recalled. "
            "Jaccard is computed on content words with stopwords stripped (C6). "
            f"Threshold: {evaluations[0]['summary']['threshold'] if evaluations else 'N/A'}."
        ),
    }


def _load_gt_glosses(path: Path) -> list[dict]:
    """Load glosses (id, gloss, chapter) from a ground-truth plot."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [
        {
            "id": fn["id"],
            "gloss": " ".join(str(fn.get("gloss", "")).split()),
            "chapter": fn.get("chapter"),
        }
        for fn in data.get("functions", [])
    ]


def main_l3(argv: list[str] | None = None) -> int:
    """CLI: evaluate L3 beat decomposition results against ground truth."""
    parser = argparse.ArgumentParser(description="FR-575 L3 evaluator")
    parser.add_argument(
        "--results-dir",
        default=str(EXAMPLE_DIR / "results" / "l3"),
    )
    parser.add_argument(
        "--ground-truth-dir",
        default=str(EXAMPLE_DIR / "fixtures" / "ground-truth"),
    )
    parser.add_argument(
        "--out-dir",
        default=str(EXAMPLE_DIR / "results" / "evaluation"),
    )
    parser.add_argument("--provider", default="unknown")
    parser.add_argument("--model", default="unknown")
    parser.add_argument(
        "--threshold",
        type=float,
        default=BEAT_MATCH_THRESHOLD,
        help=f"Jaccard threshold for beat matching (default: {BEAT_MATCH_THRESHOLD})",
    )
    args = parser.parse_args(argv)

    results_dir = Path(args.results_dir)
    gt_dir = Path(args.ground_truth_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    evaluations: list[dict] = []
    for gt_path in sorted(gt_dir.glob("*.yaml")):
        genre = _genre_name(gt_path)
        truth_glosses = _load_gt_glosses(gt_path)
        result_path = results_dir / f"{genre}.yaml"
        predicted: list | None = None
        if result_path.exists():
            try:
                loaded = yaml.safe_load(result_path.read_text(encoding="utf-8"))
                predicted = loaded if isinstance(loaded, list) else None
            except yaml.YAMLError:
                predicted = None

        evaluation = score_l3(
            genre, predicted, truth_glosses, args.provider, args.model, args.threshold
        )
        evaluations.append(evaluation)
        out_path = out_dir / f"{genre}-l3-eval.yaml"
        out_path.write_text(
            yaml.safe_dump(evaluation, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        br = evaluation["summary"]["beat_recall"]
        print(f"  {genre}: beat_recall {br}")

    if evaluations:
        summary = summarise_l3(evaluations)
        (out_dir / "l3-summary.yaml").write_text(
            yaml.safe_dump(summary, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"\nOverall beat recall: {summary['beat_recall']}")
        print(f"Overall beat precision: {summary['beat_precision']}")
    else:
        print("No ground-truth files found.")
    return 0


# ---------------------------------------------------------------------------
# L5 evaluation — assign world/belief pre/eff (FR-576)
# ---------------------------------------------------------------------------

# Per-beat pre/eff slices scored independently (the gate is combined world).
_WORLD_SLICES = ("pre_world", "eff_world")
_BELIEF_SLICES = ("pre_belief", "eff_belief")


def _count_belief_matches(predicted: list, truth: list) -> int:
    """Count GT beliefs matched by predicted (tolerant fluent, exact observer)."""
    matched = 0
    used: set[int] = set()
    for tb in truth:
        if not isinstance(tb, dict):
            continue
        for i, pb in enumerate(predicted):
            if i in used or not isinstance(pb, dict):
                continue
            if _norm(pb.get("observer")) != _norm(tb.get("observer")):
                continue
            if _fluent_matches(pb.get("fluent", {}), tb.get("fluent", {})):
                matched += 1
                used.add(i)
                break
    return matched


def _slice_counts(predicted: list | None, truth_by_id: dict) -> dict:
    """Accumulate per-slice (hits, gt_total, pred_total) across all beats.

    ``predicted`` is a list of ``{id, pre_world, eff_world, pre_belief,
    eff_belief}``. A ``None``/non-list scores every GT predicate as missed
    (J6) without raising.
    """
    by_id: dict[str, dict] = {}
    if isinstance(predicted, list):
        for item in predicted:
            if isinstance(item, dict) and item.get("id"):
                by_id[item["id"]] = item

    counts = {
        slot: {"hits": 0, "gt": 0, "pred": 0}
        for slot in (*_WORLD_SLICES, *_BELIEF_SLICES)
    }
    for bid, gt in truth_by_id.items():
        pred = by_id.get(bid, {})
        for slot in _WORLD_SLICES:
            gt_list = gt.get(slot) or []
            pred_list = pred.get(slot) or []
            counts[slot]["gt"] += len(gt_list)
            counts[slot]["pred"] += len(pred_list)
            counts[slot]["hits"] += _count_world_matches(pred_list, gt_list)
        for slot in _BELIEF_SLICES:
            gt_list = gt.get(slot) or []
            pred_list = pred.get(slot) or []
            counts[slot]["gt"] += len(gt_list)
            counts[slot]["pred"] += len(pred_list)
            counts[slot]["hits"] += _count_belief_matches(pred_list, gt_list)
    return counts


def score_l5(
    genre: str,
    predicted: list | None,
    truth_by_id: dict,
    provider: str,
    model: str,
) -> dict:
    """Build L5 evaluation record for one genre (FR-576)."""
    counts = _slice_counts(predicted, truth_by_id)

    world_hits = counts["pre_world"]["hits"] + counts["eff_world"]["hits"]
    world_gt = counts["pre_world"]["gt"] + counts["eff_world"]["gt"]
    pred_total = sum(c["pred"] for c in counts.values())
    hit_total = sum(c["hits"] for c in counts.values())

    return {
        "meta": {"genre": genre, "provider": provider, "model": model},
        "summary": {
            "world_recall": _fraction(world_hits, world_gt),  # GATE slice
            "eff_world_recall": _fraction(
                counts["eff_world"]["hits"], counts["eff_world"]["gt"]
            ),
            "pre_world_recall": _fraction(
                counts["pre_world"]["hits"], counts["pre_world"]["gt"]
            ),
            "eff_belief_recall": _fraction(
                counts["eff_belief"]["hits"], counts["eff_belief"]["gt"]
            ),
            "predicate_precision": _fraction(hit_total, pred_total),
            "produced_valid_yaml": isinstance(predicted, list),
        },
        "_counts": counts,  # carried for the summary aggregation
    }


def summarise_l5(evaluations: list[dict]) -> dict:
    """Aggregate L5 per-genre evaluations into an overall summary (FR-576)."""

    agg = {
        slot: {"hits": 0, "gt": 0, "pred": 0}
        for slot in (*_WORLD_SLICES, *_BELIEF_SLICES)
    }
    for e in evaluations:
        for slot, c in e["_counts"].items():
            agg[slot]["hits"] += c["hits"]
            agg[slot]["gt"] += c["gt"]
            agg[slot]["pred"] += c["pred"]

    world_hits = agg["pre_world"]["hits"] + agg["eff_world"]["hits"]
    world_gt = agg["pre_world"]["gt"] + agg["eff_world"]["gt"]
    pred_total = sum(c["pred"] for c in agg.values())
    hit_total = sum(c["hits"] for c in agg.values())

    # FR-595: world_recall is DEMOTED from the L5 gate to a diagnostic. FR-594
    # proved it scores agreement with a lossy GT predicate skeleton, not story
    # capture; the power analysis (n=5) showed the gateable axis is the
    # GT-anchored simulability discrimination, stamped in l5-measure-summary.yaml.
    # This summary therefore reports world_recall but emits no GO/REVISE/KILL.
    verdict = "informational"

    return {
        "corpus": {
            "synopses": len(evaluations),
            "isolation": "ground-truth glosses + kinds (Mode 1)",
        },
        "world_recall": _fraction(world_hits, world_gt),  # DIAGNOSTIC (FR-595)
        "eff_world_recall": _fraction(agg["eff_world"]["hits"], agg["eff_world"]["gt"]),
        "pre_world_recall": _fraction(agg["pre_world"]["hits"], agg["pre_world"]["gt"]),
        "eff_belief_recall": _fraction(
            agg["eff_belief"]["hits"], agg["eff_belief"]["gt"]
        ),
        "predicate_precision": _fraction(hit_total, pred_total),
        "per_genre": {
            e["meta"]["genre"]: e["summary"]["world_recall"] for e in evaluations
        },
        "verdict": verdict,
        "conditions": [
            "world_recall is informational only (FR-595): it scores agreement with "
            "a lossy GT skeleton, not story capture (FR-594).",
            "the L5 GATE is the GT-anchored simulability discrimination in "
            "l5-measure-summary.yaml (run --mode measure-l5).",
        ],
        "note": (
            "world_recall is a DIAGNOSTIC, not the L5 gate (FR-595). The gate is "
            "the regenerability discrimination (gt_sim - ours_sim, corpus mean) in "
            "l5-measure-summary.yaml — the only axis the FR-594 power analysis "
            "(n=5, paired gap 0.337 +/- 0.035, t(4)=21.6) showed is gateable at "
            "small n. Matching here is tolerant (normalized args, contains/prefix) "
            "— exact pred+args+value equality is forbidden since L5 invents the "
            "tokens it is scored on (J:C1). eff_belief recall is informational: "
            "ground-truth beliefs encode full-plot dramatic irony, an upper bound "
            "a single-beat view cannot recover. Denominators are small — read the "
            "per-slice fractions, never a bare percentage (J:C5)."
        ),
    }


def _load_gt_pre_eff(path: Path) -> dict:
    """Load per-beat pre/eff slices, keyed by beat id, from a ground-truth plot."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for fn in data.get("functions", []):
        out[fn["id"]] = {
            "pre_world": fn.get("pre_world", []) or [],
            "eff_world": fn.get("eff_world", []) or [],
            "pre_belief": fn.get("pre_belief", []) or [],
            "eff_belief": fn.get("eff_belief", []) or [],
        }
    return out


def main_l5(argv: list[str] | None = None) -> int:
    """CLI: evaluate L5 pre/eff assignment results against ground truth."""
    parser = argparse.ArgumentParser(description="FR-576 L5 evaluator")
    parser.add_argument("--results-dir", default=str(EXAMPLE_DIR / "results" / "l5"))
    parser.add_argument(
        "--ground-truth-dir", default=str(EXAMPLE_DIR / "fixtures" / "ground-truth")
    )
    parser.add_argument(
        "--out-dir", default=str(EXAMPLE_DIR / "results" / "evaluation")
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
        truth_by_id = _load_gt_pre_eff(gt_path)
        result_path = results_dir / f"{genre}.yaml"
        predicted: list | None = None
        if result_path.exists():
            try:
                loaded = yaml.safe_load(result_path.read_text(encoding="utf-8"))
                predicted = loaded if isinstance(loaded, list) else None
            except yaml.YAMLError:
                predicted = None

        evaluation = score_l5(genre, predicted, truth_by_id, args.provider, args.model)
        evaluations.append(evaluation)
        out_path = out_dir / f"{genre}-l5-eval.yaml"
        # Drop the private _counts before writing the per-genre record.
        record = {k: v for k, v in evaluation.items() if k != "_counts"}
        out_path.write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        wr = evaluation["summary"]["world_recall"]
        print(f"  {genre}: world_recall {wr}")

    if evaluations:
        summary = summarise_l5(evaluations)
        (out_dir / "l5-summary.yaml").write_text(
            yaml.safe_dump(summary, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"\nOverall world recall: {summary['world_recall']}")
        print(f"Predicate precision: {summary['predicate_precision']}")
        print(f"Verdict: {summary['verdict']}")
    else:
        print("No ground-truth files found.")
    return 0


# ---------------------------------------------------------------------------
# L6 evaluation — causality: enables / motivation / threatens (FR-577)
# ---------------------------------------------------------------------------


def _goal_phrase_matches(pred_goal: object, truth_goal: object) -> bool:
    """Tolerant goal-phrase match (J:C1): snake_case-insensitive, token-overlap.

    Goal phrases are free-form snake_case strings the LLM invents, so exact
    equality is forbidden (J:C1). Normalize (lowercase, ``_``->space), then
    accept equality, containment, or >=0.34 Jaccard token overlap.
    """
    p = _norm(str(pred_goal or "").replace("_", " "))
    t = _norm(str(truth_goal or "").replace("_", " "))
    if not p or not t:
        return False
    if p == t or p in t or t in p:
        return True
    pt, tt = set(p.split()), set(t.split())
    if not pt or not tt:
        return False
    return len(pt & tt) / len(pt | tt) >= 0.34


def _person_goal_matches(pred: object, truth: object) -> bool:
    """A {agent, goal} pair matches when the agent is exact and the goal is
    tolerant (J:C3 — informational, never gating)."""
    if not isinstance(pred, dict) or not isinstance(truth, dict):
        return False
    if _norm(pred.get("agent")) != _norm(truth.get("agent")):
        return False
    return _goal_phrase_matches(pred.get("goal"), truth.get("goal"))


def _l6_counts(predicted: list | None, truth_by_id: dict) -> dict:
    """Tally enables/motivation/threatens hits, gt, and pred over all beats.

    ``enables`` is matched by exact beat-ID set intersection (IDs are canonical
    referents, not invented tokens). ``motivation``/``threatens`` use exact
    agent + tolerant goal; ``agent_hits`` is the softer agent-only signal that
    drives confusion analysis (J:C3).
    """
    counts = {
        "enables": {"hits": 0, "gt": 0, "pred": 0},
        "motivation": {"hits": 0, "gt": 0, "agent_hits": 0, "pred": 0},
        "threatens": {"hits": 0, "gt": 0, "agent_hits": 0, "pred": 0},
    }
    pred_by_id: dict[str, dict] = {}
    if isinstance(predicted, list):
        for item in predicted:
            if isinstance(item, dict) and item.get("id"):
                pred_by_id[item["id"]] = item

    for bid, t in truth_by_id.items():
        p = pred_by_id.get(bid, {})

        t_en = set(t.get("enables") or [])
        p_raw = p.get("enables")
        p_en = set(p_raw) if isinstance(p_raw, list) else set()
        counts["enables"]["gt"] += len(t_en)
        counts["enables"]["pred"] += len(p_en)
        counts["enables"]["hits"] += len(t_en & p_en)

        for slot in ("motivation", "threatens"):
            tv = t.get(slot)
            pv = p.get(slot)
            if tv:
                counts[slot]["gt"] += 1
            if pv:
                counts[slot]["pred"] += 1
            if tv and pv and _person_goal_matches(pv, tv):
                counts[slot]["hits"] += 1
            if (
                isinstance(tv, dict)
                and isinstance(pv, dict)
                and _norm(pv.get("agent")) == _norm(tv.get("agent"))
            ):
                counts[slot]["agent_hits"] += 1

    return counts


def _l6_verdict(enables_recall: float) -> str:
    """GATE on enables recall: GO>=0.75, REVISE 0.50-0.75, KILL<0.50 (J:N2)."""
    if enables_recall >= 0.75:
        return "GO"
    if enables_recall >= 0.50:
        return "REVISE"
    return "KILL"


def score_l6(
    genre: str,
    predicted: list | None,
    truth_by_id: dict,
    provider: str,
    model: str,
) -> dict:
    """Build L6 evaluation record for one genre (FR-577)."""
    counts = _l6_counts(predicted, truth_by_id)
    en, mot, thr = counts["enables"], counts["motivation"], counts["threatens"]
    return {
        "meta": {"genre": genre, "provider": provider, "model": model},
        "summary": {
            "enables_recall": _fraction(en["hits"], en["gt"]),  # GATE
            "enables_precision": _fraction(en["hits"], en["pred"]),  # over-link
            "motivation_recall": _fraction(mot["hits"], mot["gt"]),
            "motivation_agent_recall": _fraction(mot["agent_hits"], mot["gt"]),
            "threatens_recall": _fraction(thr["hits"], thr["gt"]),
            "threatens_agent_recall": _fraction(thr["agent_hits"], thr["gt"]),
            "produced_valid_yaml": isinstance(predicted, list),
        },
        "_counts": counts,  # carried for the summary aggregation
    }


def summarise_l6(evaluations: list[dict]) -> dict:
    """Aggregate L6 per-genre evaluations into an overall summary (FR-577)."""
    agg = {
        "enables": {"hits": 0, "gt": 0, "pred": 0},
        "motivation": {"hits": 0, "gt": 0, "agent_hits": 0, "pred": 0},
        "threatens": {"hits": 0, "gt": 0, "agent_hits": 0, "pred": 0},
    }
    for e in evaluations:
        for slot, c in e["_counts"].items():
            for k, v in c.items():
                agg[slot][k] += v

    en, mot, thr = agg["enables"], agg["motivation"], agg["threatens"]
    enables_recall = (en["hits"] / en["gt"]) if en["gt"] else 0.0
    verdict = _l6_verdict(enables_recall)

    return {
        "corpus": {
            "synopses": len(evaluations),
            "isolation": "ground-truth glosses + kinds (Mode 1)",
        },
        "enables_recall": _fraction(en["hits"], en["gt"]),  # GATE
        "enables_precision": _fraction(en["hits"], en["pred"]),  # over-link detector
        "motivation_recall": _fraction(mot["hits"], mot["gt"]),
        "motivation_agent_recall": _fraction(mot["agent_hits"], mot["gt"]),
        "threatens_recall": _fraction(thr["hits"], thr["gt"]),
        "threatens_agent_recall": _fraction(thr["agent_hits"], thr["gt"]),
        "per_genre": {
            e["meta"]["genre"]: e["summary"]["enables_recall"] for e in evaluations
        },
        "verdict": verdict,
        "conditions": [
            "enables recall >= 0.75 for GO (denominator computed mechanically, J:C1)",
            "borderline 0.50-0.75 defaults to REVISE (J:N2)",
            "KILL only if < 0.50 AND the confusion pattern is not a fixable prompt issue",
        ],
        "note": (
            "Gate is enables recall — the causal backbone (J:N2). enables_precision "
            "is the over-link detector: a low value means the model invents edges "
            "the corpus does not authorise (J:C4). motivation/threatens recall are "
            "INFORMATIONAL (J:C3): goal phrases are free-form, so they use tolerant "
            "matching (agent exact + goal token-overlap, J:C1) and the *_agent_recall "
            "softer signal separates 'right agent, different wording' from a true "
            "miss. Denominators are small — read the fractions, never a bare "
            "percentage (J:C5)."
        ),
    }


def _load_gt_causality(path: Path) -> dict:
    """Load per-beat causality (enables/motivation/threatens), keyed by beat id."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for fn in data.get("functions", []):
        out[fn["id"]] = {
            "enables": fn.get("enables", []) or [],
            "motivation": fn.get("motivation"),
            "threatens": fn.get("threatens"),
        }
    return out


def main_l6(argv: list[str] | None = None) -> int:
    """CLI: evaluate L6 causality assignment results against ground truth."""
    parser = argparse.ArgumentParser(description="FR-577 L6 evaluator")
    parser.add_argument("--results-dir", default=str(EXAMPLE_DIR / "results" / "l6"))
    parser.add_argument(
        "--ground-truth-dir", default=str(EXAMPLE_DIR / "fixtures" / "ground-truth")
    )
    parser.add_argument(
        "--out-dir", default=str(EXAMPLE_DIR / "results" / "evaluation")
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
        truth_by_id = _load_gt_causality(gt_path)
        result_path = results_dir / f"{genre}.yaml"
        predicted: list | None = None
        if result_path.exists():
            try:
                loaded = yaml.safe_load(result_path.read_text(encoding="utf-8"))
                predicted = loaded if isinstance(loaded, list) else None
            except yaml.YAMLError:
                predicted = None

        evaluation = score_l6(genre, predicted, truth_by_id, args.provider, args.model)
        evaluations.append(evaluation)
        out_path = out_dir / f"{genre}-l6-eval.yaml"
        record = {k: v for k, v in evaluation.items() if k != "_counts"}
        out_path.write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        er = evaluation["summary"]["enables_recall"]
        print(f"  {genre}: enables_recall {er}")

    if evaluations:
        summary = summarise_l6(evaluations)
        (out_dir / "l6-summary.yaml").write_text(
            yaml.safe_dump(summary, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"\nOverall enables recall: {summary['enables_recall']}")
        print(f"Enables precision: {summary['enables_precision']}")
        print(f"Verdict: {summary['verdict']}")
    else:
        print("No ground-truth files found.")
    return 0


# ---------------------------------------------------------------------------
# L7 evaluation — affects: eff_affect (AffectDelta) per beat (FR-578)
# ---------------------------------------------------------------------------


def _affect_matches(pred: dict, truth: dict) -> bool:
    """One affect delta matches another (FR-578 criteria).

    ``op`` and ``kind`` are exact (closed enums, C4); ``char`` is tolerant
    (normalized). ``toward`` is symmetric (C3): GT-null requires pred-null/absent
    (a hallucinated non-null target is a precision miss, never a free pass);
    GT-non-null requires a tolerant char match.
    """
    if not isinstance(pred, dict) or not isinstance(truth, dict):
        return False
    if _norm(pred.get("op")) != _norm(truth.get("op")):
        return False
    if _norm(pred.get("kind")) != _norm(truth.get("kind")):
        return False
    if _norm(pred.get("char")) != _norm(truth.get("char")):
        return False
    t_toward = truth.get("toward")
    p_toward = pred.get("toward")
    if t_toward is None:
        return p_toward is None  # C3: GT-null matches only pred-null/absent
    if p_toward is None:
        return False
    pt, tt = _norm(p_toward), _norm(t_toward)
    return pt == tt or pt in tt or tt in pt


def _match_count(a_deltas: list, b_deltas: list) -> int:
    """Greedy bipartite count: how many of ``a`` find a distinct match in ``b``."""
    used: set[int] = set()
    hits = 0
    for a in a_deltas:
        for j, b in enumerate(b_deltas):
            if j in used:
                continue
            if _affect_matches(a, b):
                hits += 1
                used.add(j)
                break
    return hits


def _affect_label(delta: dict) -> str:
    """Human-readable arc label for the balance report."""
    char = delta.get("char", "?")
    kind = delta.get("kind", "?")
    toward = delta.get("toward")
    return f"{char}:{kind}->{toward}" if toward else f"{char}:{kind}"


def _affect_balance(predicted: list | None) -> dict:
    """Open/close balance over a predicted plan (informational, C1 — not gating).

    Counts unresolved ``open`` arcs (same char+kind+toward never closed). Balance
    is a cross-beat plan invariant the merge node (FR-579) enforces; here it is
    only reported.
    """
    if not isinstance(predicted, list):
        return {"balanced": False, "unclosed": []}
    open_arcs: dict[tuple, list] = {}
    for item in predicted:
        if not isinstance(item, dict):
            continue
        for d in item.get("eff_affect") or []:
            if not isinstance(d, dict):
                continue
            key = (_norm(d.get("char")), _norm(d.get("kind")), _norm(d.get("toward")))
            if _norm(d.get("op")) == "open":
                open_arcs.setdefault(key, []).append(_affect_label(d))
            elif _norm(d.get("op")) == "close" and open_arcs.get(key):
                open_arcs[key].pop()
    unclosed = [label for labels in open_arcs.values() for label in labels]
    return {"balanced": len(unclosed) == 0, "unclosed": sorted(unclosed)}


def _l7_verdict(affect_recall: float) -> str:
    """GATE on affect recall: GO>=0.70, REVISE 0.50-0.70, KILL<0.50 (J:N2)."""
    if affect_recall >= 0.70:
        return "GO"
    if affect_recall >= 0.50:
        return "REVISE"
    return "KILL"


def _l7_counts(predicted: list | None, truth_by_id: dict) -> dict:
    """Tally recall/precision hits and gt/pred totals over all beats."""
    counts = {"recall_hits": 0, "gt": 0, "precision_hits": 0, "pred": 0}
    pred_by_id: dict[str, list] = {}
    if isinstance(predicted, list):
        for item in predicted:
            if isinstance(item, dict) and item.get("id"):
                ea = item.get("eff_affect")
                pred_by_id[item["id"]] = ea if isinstance(ea, list) else []

    for bid, t_deltas in truth_by_id.items():
        p_deltas = pred_by_id.get(bid, [])
        counts["gt"] += len(t_deltas)
        counts["pred"] += len(p_deltas)
        counts["recall_hits"] += _match_count(t_deltas, p_deltas)
        counts["precision_hits"] += _match_count(p_deltas, t_deltas)

    return counts


def score_l7(
    genre: str,
    predicted: list | None,
    truth_by_id: dict,
    provider: str,
    model: str,
) -> dict:
    """Build L7 evaluation record for one genre (FR-578)."""
    counts = _l7_counts(predicted, truth_by_id)
    balance = _affect_balance(predicted)
    return {
        "meta": {"genre": genre, "provider": provider, "model": model},
        "summary": {
            "affect_recall": _fraction(counts["recall_hits"], counts["gt"]),  # GATE
            "affect_precision": _fraction(counts["precision_hits"], counts["pred"]),
            "open_close_balance": balance,  # informational (C1)
            "produced_valid_yaml": isinstance(predicted, list),
        },
        "_counts": counts,  # carried for the summary aggregation
    }


def summarise_l7(evaluations: list[dict]) -> dict:
    """Aggregate L7 per-genre evaluations into an overall summary (FR-578)."""
    agg = {"recall_hits": 0, "gt": 0, "precision_hits": 0, "pred": 0}
    for e in evaluations:
        for k in agg:
            agg[k] += e["_counts"][k]

    affect_recall = (agg["recall_hits"] / agg["gt"]) if agg["gt"] else 0.0
    verdict = _l7_verdict(affect_recall)
    unclosed = sorted(
        f"{e['meta']['genre']}: {label}"
        for e in evaluations
        for label in e["summary"]["open_close_balance"]["unclosed"]
    )

    return {
        "corpus": {
            "synopses": len(evaluations),
            "isolation": "ground-truth glosses + kinds + agents (Mode 1)",
        },
        "affect_recall": _fraction(agg["recall_hits"], agg["gt"]),  # GATE
        "affect_precision": _fraction(agg["precision_hits"], agg["pred"]),
        "open_close_balance": {
            "balanced": len(unclosed) == 0,
            "unclosed": unclosed,  # informational (C1)
        },
        "per_genre": {
            e["meta"]["genre"]: {
                "recall": e["summary"]["affect_recall"],
                "precision": e["summary"]["affect_precision"],
            }
            for e in evaluations
        },
        "verdict": verdict,
        "conditions": [
            "affect recall >= 0.70 for GO",
            "borderline 0.50-0.70 defaults to REVISE (J:N2)",
            "KILL only if < 0.50 AND the confusion pattern is not a fixable prompt issue",
        ],
        "note": (
            "Gate is affect recall — does the model place the arcs the corpus "
            "authors placed (J:N2). affect_precision is the over-emission detector "
            "(C2): a low value means the model opens an arc on every emotional beat. "
            "kind/op are matched exactly (closed enums, C4); char is normalized; "
            "toward is symmetric (C3 — a hallucinated target is a precision miss). "
            "open_close_balance is INFORMATIONAL (C1): balance is a merge-node plan "
            "invariant (FR-579), not a per-layer gate. Denominators are small — read "
            "the fractions, never a bare percentage (J:C5)."
        ),
    }


def _load_gt_affects(path: Path) -> dict:
    """Load per-beat eff_affect deltas, keyed by beat id, from a ground-truth plot."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    out: dict[str, list] = {}
    for fn in data.get("functions", []):
        out[fn["id"]] = fn.get("eff_affect", []) or []
    return out


def main_l7(argv: list[str] | None = None) -> int:
    """CLI: evaluate L7 affect assignment results against ground truth."""
    parser = argparse.ArgumentParser(description="FR-578 L7 evaluator")
    parser.add_argument("--results-dir", default=str(EXAMPLE_DIR / "results" / "l7"))
    parser.add_argument(
        "--ground-truth-dir", default=str(EXAMPLE_DIR / "fixtures" / "ground-truth")
    )
    parser.add_argument(
        "--out-dir", default=str(EXAMPLE_DIR / "results" / "evaluation")
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
        truth_by_id = _load_gt_affects(gt_path)
        result_path = results_dir / f"{genre}.yaml"
        predicted: list | None = None
        if result_path.exists():
            try:
                loaded = yaml.safe_load(result_path.read_text(encoding="utf-8"))
                predicted = loaded if isinstance(loaded, list) else None
            except yaml.YAMLError:
                predicted = None

        evaluation = score_l7(genre, predicted, truth_by_id, args.provider, args.model)
        evaluations.append(evaluation)
        out_path = out_dir / f"{genre}-l7-eval.yaml"
        record = {k: v for k, v in evaluation.items() if k != "_counts"}
        out_path.write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        ar = evaluation["summary"]["affect_recall"]
        print(f"  {genre}: affect_recall {ar}")

    if evaluations:
        summary = summarise_l7(evaluations)
        (out_dir / "l7-summary.yaml").write_text(
            yaml.safe_dump(summary, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"\nOverall affect recall: {summary['affect_recall']}")
        print(f"Affect precision: {summary['affect_precision']}")
        print(f"Verdict: {summary['verdict']}")
    else:
        print("No ground-truth files found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
