"""FR-1137 reconciliation, canary and rendering: model output is a claim."""

from __future__ import annotations

import re
from typing import Any

from yamlgraph.models.map_results import MapFailure

TARGETS = ("core", "linter", "examples", "scripts", "docs", "other")
TEST_TYPES = ("unit", "integration", "other")
TIE_BREAK = ("linter", "examples", "scripts", "docs", "core", "other")

_RECORD_KEYS = ("nodeid", "description", "target", "test_type")
_ABBREVIATIONS = {"e.g", "i.e", "etc", "vs", "cf"}
_SENTENCE_BREAK = re.compile(r"[.!?]\s+(?=\S)")


def validate_description(text: Any) -> str | None:
    """Return why `text` is not exactly one sentence, or None when it is."""
    if not isinstance(text, str) or not text.strip():
        return "empty description"
    value = text.strip()
    if "\n" in value or "\r" in value:
        return "multi-line description"
    if value[-1] not in ".!?" or (len(value) > 1 and value[-2] in ".!?"):
        return "description must end with exactly one of . ! ?"
    for match in _SENTENCE_BREAK.finditer(value):
        word = value[: match.start() + 1].rsplit(None, 1)[-1]
        is_abbreviation = word.rstrip(".").lower() in _ABBREVIATIONS
        if value[match.start()] == "." and is_abbreviation:
            continue
        return "more than one sentence"
    return None


def _defect(kind: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"kind": kind, "detail": detail, **extra}


def _index_results(
    parts: list[dict], findings: list, failures: list, defects: list
) -> tuple[dict[int, dict], set[int]]:
    by_index: dict[int, dict] = {}
    failed: set[int] = set()
    for finding in findings:
        index = finding.get("_map_index") if isinstance(finding, dict) else None
        if isinstance(finding, dict) and "_error" in finding:
            defects.append(_defect("map_error", str(finding["_error"]), index=index))
            failed.add(index)
        elif not isinstance(index, int) or not 0 <= index < len(parts):
            defects.append(_defect("bad_index", f"unusable map index {index!r}"))
        elif index in by_index:
            defects.append(_defect("duplicate_index", f"map index {index} twice"))
        else:
            by_index[index] = finding
    for raw in failures:
        failure = MapFailure.model_validate(raw)
        failed.add(failure.index)
        in_range = 0 <= failure.index < len(parts)
        partition = parts[failure.index]["partition_id"] if in_range else None
        defects.append(_defect("map_error", failure.message, partition_id=partition))
    for index, part in enumerate(parts):
        if index not in by_index and index not in failed:
            defects.append(
                _defect(
                    "missing_result",
                    "partition has no result",
                    partition_id=part["partition_id"],
                )
            )
    return by_index, failed


def _record_defect(record: Any) -> tuple[str, str] | None:
    if not isinstance(record, dict) or any(
        not isinstance(record.get(key), str) for key in _RECORD_KEYS
    ):
        return "malformed", "record lacks string nodeid/description/target/test_type"
    if record["target"] not in TARGETS:
        return "bad_target", f"target {record['target']!r} not in enum"
    if record["test_type"] not in TEST_TYPES:
        return "bad_type", f"test_type {record['test_type']!r} not in enum"
    reason = validate_description(record["description"])
    return ("bad_description", reason) if reason else None


def _identity_defect(
    nodeid: str, index: int, owner: dict[str, int], parts: list, accepted: dict
) -> tuple[str, str] | None:
    if nodeid not in owner:
        return "unknown", "nodeid not in the frozen corpus"
    if owner[nodeid] != index:
        return "wrong_partition", f"belongs to {parts[owner[nodeid]]['partition_id']}"
    if nodeid in accepted:
        return "duplicate", "nodeid returned twice"
    return None


def reconcile(
    corpus: dict, findings: list, failures: list
) -> tuple[list[dict], list[dict]]:
    """Join model claims to AST rows; return (rows, defects)."""
    parts = corpus["partitions"]
    owner = {nodeid: i for i, part in enumerate(parts) for nodeid in part["nodeids"]}
    defects: list[dict] = []
    by_index, failed = _index_results(parts, findings, failures, defects)
    accepted: dict[str, dict] = {}
    for index in sorted(by_index):
        partition = parts[index]["partition_id"]
        records = by_index[index].get("records")
        if not isinstance(records, list):
            defects.append(
                _defect("malformed", "records is not a list", partition_id=partition)
            )
            continue
        for record in records:
            problem = _record_defect(record)
            if problem and problem[0] == "malformed":
                defects.append(_defect(*problem, partition_id=partition, raw=record))
                continue
            nodeid = record["nodeid"]
            problem = _identity_defect(nodeid, index, owner, parts, accepted) or problem
            if problem:
                bad_text = problem[0] == "bad_description"
                raw = record["description"] if bad_text else record
                defects.append(
                    _defect(*problem, partition_id=partition, nodeid=nodeid, raw=raw)
                )
                continue
            accepted[nodeid] = {key: record[key] for key in _RECORD_KEYS[1:]}
    rows = []
    for row in corpus["rows"]:
        claim = accepted.get(row["nodeid"])
        if claim is None:
            index = owner[row["nodeid"]]
            if index in by_index and index not in failed:
                defects.append(
                    _defect("missing", "no valid record", nodeid=row["nodeid"])
                )
            continue
        keep = ("nodeid", "file", "line", "reqs", "markers")
        rows.append({**{key: row[key] for key in keep}, **claim})
    return rows, defects


def check_canary(rows: list[dict], canary: list[dict]) -> tuple[list[dict], dict]:
    """Compare withheld expected classifications with accepted rows."""
    by_id = {row["nodeid"]: row for row in rows}
    defects = []
    for entry in canary:
        row = by_id.get(entry["nodeid"])
        if row is None:
            defects.append(
                _defect("canary_absent", "not in map", nodeid=entry["nodeid"])
            )
            continue
        got = (row["target"], row["test_type"])
        want = (entry["target"], entry["test_type"])
        if got != want:
            defects.append(
                _defect(
                    "canary_mismatch",
                    f"got {'/'.join(got)}, want {'/'.join(want)}",
                    nodeid=entry["nodeid"],
                )
            )
    return defects, {"checked": len(canary), "passed": len(canary) - len(defects)}


def _cell(value: Any) -> str:
    text = ", ".join(value) if isinstance(value, list) else str(value)
    return text.replace("|", "\\|")


def render_markdown(doc: dict) -> str:
    """Render the canonical JSON; the only source of the Markdown."""
    prov, rows = doc["provenance"], doc["rows"]
    counts = prov["counts"]
    out = [
        "# Test corpus map",
        "",
        f"- commit: `{prov['commit_sha']}`; run: `{prov['run_id']}`",
        f"- model: {prov['provider']} / {prov['model']} @ {prov['temperature']}",
        f"- files {counts['files']}, tests {counts['tests']}, "
        f"partitions {counts['partitions']}",
        f"- corpus hash `{prov['corpus_hash']}`; "
        f"artifact hash `{prov['artifact_hash']}`",
        "",
        "## Target × type",
        "",
        "| target | test_type | count |",
        "|---|---|---|",
    ]
    for target in TARGETS:
        for ttype in TEST_TYPES:
            n = sum(1 for r in rows if (r["target"], r["test_type"]) == (target, ttype))
            if n:
                out.append(f"| {target} | {ttype} | {n} |")
    current = None
    for row in rows:
        if row["file"] != current:
            current = row["file"]
            out += [
                "",
                f"## {current}",
                "",
                "| test | line | target | type | reqs | description |",
                "|---|---|---|---|---|---|",
            ]
        out.append(
            f"| `{row['nodeid']}` | {row['line']} | {row['target']} "
            f"| {row['test_type']} | {_cell(row['reqs'])} "
            f"| {_cell(row['description'])} |"
        )
    return "\n".join(out) + "\n"
