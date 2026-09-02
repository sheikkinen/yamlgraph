"""FR-733 NVD-gold crosscheck harness (REQ-YG-560) — LLM-free evaluation.

Copy-adapted from examples/icpc-2-rfe/nodes/crosscheck.py. Evaluates
archived classifier results (``logs/cwe-classifier/*.result.json``)
against committed NVD-labeled fixtures in ``data/labeled/``. Pure
instrumentation: raw k-of-n counts only, no significance.

Judgement-addendum protocol: NVD gold labels are analyst opinions and
two of eleven committed labels are codes MITRE itself marks
Mapping-Discouraged. Disagreements therefore partition mechanically by
the catalog's Mapping_Notes usage:

- miss on an Allowed / Allowed-with-Review gold code → ``our_miss``
  (fails the run);
- miss on a Discouraged / Prohibited gold code → ``label_questionable``
  (recorded, never fails alone);
- EVERY gold code guidance-violating → ``gold_unscoreable``
  (passed=None; our primary is reported for the human read — a more
  specific Allowed code than NVD's Discouraged label is a success
  narrative, not a miss).

Usage is computed from the GENERATED catalog at evaluation time; the
committed label files stay raw provenance (cve_id + nvd_cwes only).

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
CATALOG_PATH = EXAMPLE_DIR / "data" / "cwe_catalog.yaml"
ARCHIVE_DIR = EXAMPLE_DIR.parents[1] / "logs" / "cwe-classifier"

_GUIDANCE_VIOLATING = {"Discouraged", "Prohibited"}


def load_labels(labeled_dir: Path = LABELED_DIR) -> dict[str, dict]:
    """Load labels; rationale is the leading comment block — labels
    without one are rejected."""
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


def load_usage(catalog_path: Path = CATALOG_PATH) -> dict[str, str]:
    """Mapping_Notes usage per code, from the generated catalog."""
    if not catalog_path.exists():
        raise FileNotFoundError(
            f"Catalog not found: {catalog_path}. Generate it first: "
            "python examples/cwe-classifier/nodes/build_catalog.py"
        )
    payload = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    return {row["code"]: row["mapping_usage"] for row in payload["rows"]}


def _surfaced_codes(classification: dict) -> set[str]:
    """Codes visible anywhere in the output."""
    codes: set[str] = set()
    primary = classification.get("primary")
    if primary:
        codes.add(primary["code"])
    for entry in classification.get("secondary", []):
        codes.add(entry["code"])
    for entry in classification.get("best_partial", []):
        codes.add(entry["code"])
    return codes


def evaluate_result(label: dict, result: dict, usage: dict[str, str]) -> dict:
    """Evaluate one archived result against one NVD gold label,
    partitioned by MITRE usage (addendum protocol)."""
    classification = result["classification"]
    primary = classification.get("primary")
    our_primary = primary["code"] if primary else None
    surfaced = _surfaced_codes(classification)

    gold = list(label["nvd_cwes"])
    scoreable = [c for c in gold if usage.get(c, "Allowed") not in _GUIDANCE_VIOLATING]
    questionable_missed = [
        c
        for c in gold
        if usage.get(c, "Allowed") in _GUIDANCE_VIOLATING and c not in surfaced
    ]

    if not scoreable:
        return {
            "passed": None,
            "gold_unscoreable": True,
            "our_miss": [],
            "label_questionable": questionable_missed,
            "our_primary": our_primary,
        }

    our_miss = [c for c in scoreable if c not in surfaced]
    return {
        "passed": not our_miss,
        "gold_unscoreable": False,
        "our_miss": our_miss,
        "label_questionable": questionable_missed,
        "our_primary": our_primary,
    }


def attribute_archives(
    archive_dir: Path, fixture_names: set[str]
) -> dict[str, list[Path]]:
    """Join archives to fixtures by exact `<name>-<timestamp>` stem
    (timestamp-anchored — icpc prefix-misattribution finding)."""
    stamp = re.compile(r"-\d{8}_\d{6}$")
    attributed: dict[str, list[Path]] = {}
    for path in sorted(archive_dir.glob("*.result.json")):
        stem = path.name.removesuffix(".result.json")
        base = stamp.sub("", stem)
        if base in fixture_names:
            attributed.setdefault(base, []).append(path)
    return attributed


def agreement(results: list[dict]) -> dict:
    """Raw k-of-n primary agreement (counts, never significance)."""
    primaries = [(r["classification"]["primary"] or {}).get("code") for r in results]
    counts = Counter(primaries)
    mode, k = counts.most_common(1)[0]
    return {"n": len(results), "primary_mode": mode, "k": k}


def _run_fixtures(runs: int) -> None:
    classify = EXAMPLE_DIR / "classify.sh"
    for description in sorted(LABELED_DIR.glob("*.md")):
        for i in range(runs):
            print(f"▶ {description.stem} run {i + 1}/{runs}", file=sys.stderr)
            proc = subprocess.run(
                [str(classify), str(description)],
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
    usage = load_usage()
    archives = attribute_archives(ARCHIVE_DIR, set(labels))
    report: dict = {
        "fixtures": {},
        "totals": {"pass": 0, "fail": 0, "unscoreable": 0},
    }

    for name, label in labels.items():
        paths = archives.get(name, [])
        results = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
        evaluations = [evaluate_result(label, r, usage) for r in results]
        scored = [e for e in evaluations if e["passed"] is not None]
        entry: dict = {
            "runs": len(results),
            "nvd_label_usage": {c: usage.get(c, "?") for c in label["nvd_cwes"]},
            "passed": sum(1 for e in scored if e["passed"]),
            "failed": sum(1 for e in scored if not e["passed"]),
            "unscoreable": sum(1 for e in evaluations if e["gold_unscoreable"]),
            "our_miss": sorted({c for e in evaluations for c in e["our_miss"]}),
            "label_questionable": sorted(
                {c for e in evaluations for c in e["label_questionable"]}
            ),
        }
        if entry["unscoreable"]:
            entry["our_primaries"] = sorted(
                {e["our_primary"] for e in evaluations if e["gold_unscoreable"]},
                key=str,
            )
        if results:
            entry["agreement"] = agreement(results)
        report["fixtures"][name] = entry
        report["totals"]["pass"] += entry["passed"]
        report["totals"]["fail"] += entry["failed"]
        report["totals"]["unscoreable"] += entry["unscoreable"]

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
            f" {entry['unscoreable']} unscoreable{agr_txt}"
        )
        for code in entry["our_miss"]:
            print(f"    ✗ our_miss: {code}")
        for code in entry["label_questionable"]:
            print(
                f"    ⚖ label_questionable (MITRE-{entry['nvd_label_usage'][code]}): {code}"
            )
        if entry.get("our_primaries"):
            print(f"    → our primaries (gold unscoreable): {entry['our_primaries']}")
    totals = report["totals"]
    print(
        f"TOTAL: {totals['pass']} pass / {totals['fail']} fail / "
        f"{totals['unscoreable']} unscoreable"
    )


if __name__ == "__main__":
    main()
