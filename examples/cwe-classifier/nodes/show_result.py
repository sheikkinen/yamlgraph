"""FR-733 result extractor — pretty-print the classification from a run.

Reads `yamlgraph graph run ... --full` output on stdin (or a log file as
argv[1]) and prints only the answer: primary, secondary, best partials,
coverage. Copy-adapted from examples/icpc-2-rfe/nodes/show_result.py.

Usage:
    yamlgraph graph run graph.yaml --var description="..." --full \
        2>/dev/null | python nodes/show_result.py
    python nodes/show_result.py logs/run.log
    python nodes/show_result.py --json logs/run.log   # machine-readable
"""

import ast
import json
import sys
from pathlib import Path


def _extract(text: str, key: str):
    marker = f"  {key}: "
    i = text.find(marker)
    if i < 0:
        return None
    j = text.find("\n", i)
    return ast.literal_eval(text[i + len(marker) : j])


def _line(entry: dict) -> str:
    spans = "; ".join(f'"{s}"' for s in entry.get("evidence_spans", []))
    code = entry["code"]
    if entry.get("review"):
        code += "  [REVIEW: MITRE Allowed-with-Review]"
    out = (
        f"  {code}  {entry['title']}"
        f"  [{entry['verdict']}, {entry['confidence']:.2f}]"
    )
    if entry.get("reasoning_short"):
        out += f"\n      {entry['reasoning_short']}"
    if spans:
        out += f"\n      evidence: {spans}"
    return out


def main() -> None:
    args = sys.argv[1:]
    as_json = "--json" in args
    paths = [a for a in args if a != "--json"]
    text = Path(paths[0]).read_text() if paths else sys.stdin.read()
    classification = _extract(text, "classification")
    meta = _extract(text, "meta")
    if classification is None:
        for pattern in ("Error:", "error"):
            i = text.find(pattern)
            if i >= 0:
                print(text[i : i + 300].split("\n")[0])
                raise SystemExit(1)
        raise SystemExit("No classification found in input")

    if as_json:
        print(
            json.dumps(
                {"classification": classification, "meta": meta},
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    primary = classification["primary"]
    print("PRIMARY")
    print(_line(primary) if primary else "  — none (low confidence)")
    if classification["secondary"]:
        print("SECONDARY")
        for entry in classification["secondary"]:
            print(_line(entry))
    if classification["low_confidence"] and classification["best_partial"]:
        print("BEST PARTIAL (no code reached 'match')")
        for entry in classification["best_partial"]:
            print(_line(entry))
    if meta:
        cov = meta["catalog_coverage"]
        print(
            f"coverage: {meta['catalog_version']}, view {cov['view']}, "
            f"{cov['candidates']} candidates "
            f"({cov['excluded_prohibited']} Prohibited excluded), "
            f"{cov['clusters_evaluated']} clusters, "
            f"{meta['candidates_total']} candidates surfaced"
        )


if __name__ == "__main__":
    main()
