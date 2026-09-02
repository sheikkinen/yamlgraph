"""FR-725 labeled crosscheck harness (REQ-YG-554) — LLM-free evaluation.

Evaluates archived classifier results (``logs/icpc2-rfe/*.result.json``)
against committed labels in ``data/labeled/``. Pure instrumentation:
never changes classifier behavior, never computes significance — raw
k-of-n counts only (Judgement F3).

Label schema (``<fixture>.label.yaml`` beside ``<fixture>.md``):
    valid_for_components: [1, ..., 7]   # F4 coverage guard
    primary_any_of: [code, ...]          # rank-tolerant primary
    must_include: [code, ...]            # any surfaced slot counts
    must_not_include: [code, ...]        # blocked from primary/secondary
    low_confidence_expected: true|false|null   # null = either outcome
    # rationale: taken from the leading YAML comment block

Usage:
    python nodes/crosscheck.py                 # evaluate existing archives
    python nodes/crosscheck.py --runs 5        # generate N fresh runs first (slow, keys)
    python nodes/crosscheck.py --json          # machine-readable report
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

EXAMPLE_DIR = Path(__file__).resolve().parents[1]
LABELED_DIR = EXAMPLE_DIR / "data" / "labeled"
ARCHIVE_DIR = EXAMPLE_DIR.parents[1] / "logs" / "icpc2-rfe"


def load_labels(labeled_dir: Path = LABELED_DIR) -> dict[str, dict]:
    """Load labels; file-based fixtures only (F2). Rationale is the
    leading comment block — labels without one are rejected."""
    labels: dict[str, dict] = {}
    for label_path in sorted(labeled_dir.glob("*.label.yaml")):
        name = label_path.name.removesuffix(".label.yaml")
        text = label_path.read_text(encoding="utf-8")
        rationale = " ".join(
            line.lstrip("# ").strip()
            for line in text.splitlines()
            if line.startswith("#")
        )
        label = yaml.safe_load(text)
        label["rationale"] = rationale
        if not rationale:
            raise ValueError(f"{name}: label has no rationale comment")
        labels[name] = label
    return labels


def _surfaced_codes(classification: dict) -> set[str]:
    """Codes visible anywhere in the output (must_include scope)."""
    codes: set[str] = set()
    primary = classification.get("primary")
    if primary:
        codes.add(primary["code"])
        context = primary.get("chapter_context")
        if context:
            codes.add(context["code"])
    for entry in classification.get("secondary", []):
        codes.add(entry["code"])
    for entry in classification.get("best_partial", []):
        codes.add(entry["code"])
    return codes


def evaluate_result(label: dict, result: dict) -> dict:
    """Evaluate one archived result against one label."""
    components = result["meta"]["catalog_coverage"]["components"]
    if components != label["valid_for_components"]:
        return {
            "passed": None,
            "skipped": True,
            "reason": (
                f"label valid_for_components {label['valid_for_components']} "
                f"!= result components {components}"
            ),
        }

    classification = result["classification"]
    primary = classification.get("primary")
    primary_code = primary["code"] if primary else None
    failures: list[str] = []

    expected_low = label.get("low_confidence_expected", False)
    if expected_low is None:
        low_conf_ok = True
    else:
        low_conf_ok = classification["low_confidence"] == expected_low
    if not low_conf_ok:
        failures.append(
            f"low_confidence={classification['low_confidence']}, "
            f"expected {expected_low}"
        )

    if label["primary_any_of"] and not classification["low_confidence"]:
        if primary_code not in label["primary_any_of"]:
            failures.append(
                f"primary {primary_code!r} not in {label['primary_any_of']}"
            )
    elif (
        label["primary_any_of"]
        and classification["low_confidence"]
        and expected_low is False
    ):
        failures.append("no primary (low_confidence)")

    surfaced = _surfaced_codes(classification)
    for code in label.get("must_include", []):
        if code not in surfaced:
            failures.append(f"must_include {code} not surfaced")

    blocked_slots = {primary_code} | {
        e["code"] for e in classification.get("secondary", [])
    }
    for code in label.get("must_not_include", []):
        if code in blocked_slots:
            failures.append(f"must_not_include {code} in primary/secondary")

    return {"passed": not failures, "skipped": False, "failures": failures}


def attribute_archives(
    archive_dir: Path, fixture_names: set[str]
) -> dict[str, list[Path]]:
    """Join archives to fixtures by exact `<name>-<timestamp>` stem (F2).
    Timestamp-anchored: a bare prefix match would misattribute fixtures
    whose names are prefixes of other fixtures (hp36-renewal-behalf vs
    hp36-renewal-behalf-en — found by the language-invariance runs).
    Unknown and stdin archives are never attributed."""
    stamp = re.compile(r"-\d{8}_\d{6}$")
    attributed: dict[str, list[Path]] = {}
    for path in sorted(archive_dir.glob("*.result.json")):
        stem = path.name.removesuffix(".result.json")
        base = stamp.sub("", stem)
        if base in fixture_names:
            attributed.setdefault(base, []).append(path)
    return attributed


def agreement(results: list[dict]) -> dict:
    """Raw k-of-n primary agreement (F3: counts, never significance)."""
    primaries = [(r["classification"]["primary"] or {}).get("code") for r in results]
    counts = Counter(primaries)
    mode, k = counts.most_common(1)[0]
    return {"n": len(results), "primary_mode": mode, "k": k}


def _run_fixtures(runs: int) -> None:
    classify = EXAMPLE_DIR / "classify.sh"
    for transcript in sorted(LABELED_DIR.glob("*.md")):
        for i in range(runs):
            print(f"▶ {transcript.stem} run {i + 1}/{runs}", file=sys.stderr)
            proc = subprocess.run(
                [str(classify), str(transcript)],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                # A failed run is DATA for a measurement tool, not a
                # crash: it simply produces no archive to attribute.
                print(
                    f"  ✗ run failed (recorded): {proc.stderr.strip()[-160:]}",
                    file=sys.stderr,
                )


def main() -> None:
    args = sys.argv[1:]
    as_json = "--json" in args
    if "--runs" in args:
        _run_fixtures(int(args[args.index("--runs") + 1]))

    labels = load_labels()
    archives = attribute_archives(ARCHIVE_DIR, set(labels))
    report: dict = {"fixtures": {}, "totals": {"pass": 0, "fail": 0, "skip": 0}}

    for name, label in labels.items():
        paths = archives.get(name, [])
        results = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
        evaluations = [evaluate_result(label, r) for r in results]
        scored = [e for e in evaluations if not e.get("skipped")]
        skipped = [e for e in evaluations if e.get("skipped")]
        entry: dict = {
            "runs": len(results),
            "passed": sum(1 for e in scored if e["passed"]),
            "failed": sum(1 for e in scored if not e["passed"]),
            "skipped": len(skipped),
            "failures": [f for e in scored if not e["passed"] for f in e["failures"]],
        }
        if skipped:
            entry["skip_reasons"] = sorted({e["reason"] for e in skipped})
        if scored:
            entry["agreement"] = agreement(
                [
                    r
                    for r, e in zip(results, evaluations, strict=False)
                    if not e.get("skipped")
                ]
            )
        report["fixtures"][name] = entry
        report["totals"]["pass"] += entry["passed"]
        report["totals"]["fail"] += entry["failed"]
        report["totals"]["skip"] += entry["skipped"]

    if as_json:
        print(json.dumps(report, indent=2))
        return
    for name, entry in report["fixtures"].items():
        agr = entry.get("agreement")
        agr_txt = (
            f" | agreement {agr['k']}/{agr['n']} on {agr['primary_mode']}"
            if agr
            else ""
        )
        print(
            f"{name}: {entry['passed']} pass / {entry['failed']} fail /"
            f" {entry['skipped']} skip{agr_txt}"
        )
        for failure in entry["failures"]:
            print(f"    ✗ {failure}")
        for reason in entry.get("skip_reasons", []):
            print(f"    ⤳ skipped: {reason}")
    totals = report["totals"]
    print(
        f"TOTAL: {totals['pass']} pass / {totals['fail']} fail / "
        f"{totals['skip']} skip"
    )


if __name__ == "__main__":
    main()
