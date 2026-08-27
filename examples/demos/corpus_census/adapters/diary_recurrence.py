"""LLM-free diary trap recurrence aggregator (FR-893).

Consumes corpus_census JSONL ledgers, groups by canonical label with
DISTINCT-ENTRY counting (R-4), enforces the hidden-canary run gate, and
writes a public-safe recurrence table (no evidence spans, R-3) plus
draft .chaplain/inbox graduation proposals for candidates at threshold.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from examples.demos.corpus_census.adapters import census_brief

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_ERROR_MARKERS = ("Error:", "No results")
_SCRIPTURE_KEY_RE = re.compile(r"^ {0,2}([a-z0-9_]+):", re.MULTILINE)


def load_graduated_labels(scripture_path: str) -> set[str]:
    """Extract already-graduated knowledge-graph keys from the Scripture."""
    text = Path(scripture_path).read_text(encoding="utf-8", errors="replace")
    return set(_SCRIPTURE_KEY_RE.findall(text))


def _canonical(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")


def _entry_date(item_ref: str) -> str:
    match = _DATE_RE.search(Path(item_ref).name)
    return match.group(1) if match else ""


def _load_rows(ledger_paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in ledger_paths:
        with open(path, encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    if not rows:
        raise ValueError("no ledger rows loaded")
    return rows


def aggregate(
    ledger_paths: list[str],
    output_dir: str,
    *,
    threshold: int = 3,
    canaries: dict[str, int] | None = None,
    inbox_dir: str = ".chaplain/inbox",
    run_meta: dict[str, Any] | None = None,
    graduated: set[str] | None = None,
    inbox_threshold: int | None = None,
) -> dict[str, Any]:
    """Aggregate census ledgers into a recurrence table + inbox drafts.

    Raises:
        ValueError: Missing citations, or any canary label absent /
            below its required distinct-entry count (run invalid; no
            artifacts are emitted).
    """
    rows = _load_rows(ledger_paths)

    label_entries: dict[str, set[str]] = {}
    abstentions = 0
    for row in rows:
        if row.get("abstained"):
            abstentions += 1
            continue
        item_ref = str(row.get("item_ref", "")).strip()
        if not item_ref:
            raise ValueError(f"row lacks item_ref citation: {row}")
        judgement = str(row.get("judgement", ""))
        if any(m in judgement for m in _ERROR_MARKERS):
            raise ValueError(f"error-string judgement in ledger: {judgement}")
        for raw_label in judgement.split(","):
            label = _canonical(raw_label)
            if label:
                label_entries.setdefault(label, set()).add(item_ref)

    # Canary gate BEFORE any artifact emission (fail closed).
    # A canary key is a FAMILY spec: '|'-separated substrings; an entry
    # matches when any of its canonical labels contains any alternative
    # (vocabulary drifts — raw-read evidence sample 2; exact match undercounts).
    for canary, minimum in (canaries or {}).items():
        alternatives = [_canonical(a) for a in canary.split("|") if a.strip()]
        matched: set[str] = set()
        for label, entries in label_entries.items():
            if any(alt in label for alt in alternatives):
                matched |= entries
        if len(matched) < minimum:
            raise ValueError(
                f"canary family '{canary}' has {len(matched)} distinct "
                f"entries, needs >={minimum} — run invalid, no artifacts emitted"
            )

    candidates = []
    for label, entries in sorted(
        label_entries.items(), key=lambda kv: (-len(kv[1]), kv[0])
    ):
        dates = sorted(d for d in (_entry_date(e) for e in entries) if d)
        candidates.append(
            {
                "label": label,
                "entries": len(entries),
                "citations": sorted(entries),
                "first_seen": dates[0] if dates else "",
                "last_seen": dates[-1] if dates else "",
            }
        )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    table_name = f"recurrence-{stamp}.md"

    lines = [
        "# Diary Trap Recurrence Census",
        "",
        f"- rows: {len(rows)}  abstentions: {abstentions}",
        f"- ledgers: {len(ledger_paths)}",
    ]
    for key, value in (run_meta or {}).items():
        lines.append(f"- {key}: {value}")
    lines += [
        "",
        "| label | entries | first_seen | last_seen | citations |",
        "|---|---:|---|---|---|",
    ]
    for c in candidates:
        cites = "<br>".join(c["citations"])
        lines.append(
            f"| {c['label']} | {c['entries']} | {c['first_seen']} "
            f"| {c['last_seen']} | {cites} |"
        )
    (out / table_name).write_text("\n".join(lines) + "\n", encoding="utf-8")

    inbox = Path(inbox_dir)
    drafts: list[str] = []
    graduated = graduated or set()
    # Inbox drafts may use a higher bar than the table threshold: the
    # chaplain consumes inbox files on pickup, so a flood is operational.
    emit_bar = inbox_threshold if inbox_threshold is not None else threshold
    for c in candidates:
        if c["entries"] < emit_bar:
            continue
        if c["label"] in graduated:
            continue  # already in Scripture — measured, not proposable
        inbox.mkdir(parents=True, exist_ok=True)
        draft = inbox / f"diary-census-{c['label']}.md"
        cite_lines = "\n".join(f"- {e}" for e in c["citations"])
        draft.write_text(
            f"Diary trap census graduation candidate: `{c['label']}` recurs in "
            f"{c['entries']} distinct diary entries "
            f"({c['first_seen']} .. {c['last_seen']}), meeting the Scripture "
            f"recurrence bar. Citations:\n{cite_lines}\n\n"
            "Generated by the FR-893 diary census (canary-validated run). "
            "Graduation judgement remains with the chaplain/human flow — "
            "this is a measured proposal, not an auto-graduation.\n",
            encoding="utf-8",
        )
        drafts.append(str(draft))

    return {
        "table_name": table_name,
        "candidates": candidates,
        "abstentions": abstentions,
        "inbox_drafts": drafts,
        "rows": len(rows),
    }


def _default_synthesize(
    rows: list[dict[str, Any]], rubric: str
) -> list[dict[str, Any]]:
    """One pinned structured-claims call on the census prompt artifact."""
    from yamlgraph.executor import execute_prompt
    from yamlgraph.schema_loader import load_schema_from_yaml

    prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
    output_model = load_schema_from_yaml(prompts_dir / "synthesize_brief.yaml")
    result = execute_prompt(
        "synthesize_brief",
        variables={"rubric": rubric, "rows": json.dumps(rows, ensure_ascii=False)},
        output_model=output_model,
        provider="anthropic",
        model="claude-haiku-4-5",
        temperature=0.0,
        prompts_dir=prompts_dir,
    )
    payload = result.model_dump() if hasattr(result, "model_dump") else result
    if not isinstance(payload, dict) or not isinstance(payload.get("claims"), list):
        raise ValueError(f"synthesis returned no claims list: {type(payload)}")
    return payload["claims"]


def emit_diary_brief(
    candidates: list[dict[str, Any]],
    brief_path: str,
    brief_rubric: str,
    *,
    run_meta: dict[str, Any] | None = None,
    synthesize_fn: Callable[[list[dict[str, Any]], str], list[dict[str, Any]]]
    | None = None,
) -> dict[str, Any]:
    """FR-895 D-5: one synthesis call over the recurrence table.

    Bounded, allowlisted input; fail-closed citation boundary; AC-07
    top-finding family check recorded in the result and brief metadata.
    """
    synth = synthesize_fn or _default_synthesize
    rows = census_brief.build_synthesis_input(candidates)
    claims = synth(rows, brief_rubric)
    top_cited = census_brief.top_finding_cited(claims, rows)
    meta = dict(run_meta or {})
    meta["top_finding_cited"] = top_cited
    result = census_brief.emit_brief(claims, rows, brief_path, run_meta=meta)
    result["top_finding_cited"] = top_cited
    return result


def main(argv: list[str] | None = None) -> int:
    """CLI: aggregate ledgers, enforce canaries, write artifacts."""
    import argparse

    parser = argparse.ArgumentParser(description="FR-893 diary recurrence census")
    parser.add_argument("ledgers", nargs="+", help="census JSONL ledger paths")
    parser.add_argument("--output-dir", default="docs/diary/census")
    parser.add_argument("--inbox-dir", default=".chaplain/inbox")
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument(
        "--inbox-threshold",
        type=int,
        default=None,
        help="min distinct entries for inbox drafts (default: --threshold)",
    )
    parser.add_argument(
        "--canary",
        action="append",
        default=[],
        help="LABEL=MIN_ENTRIES, repeatable; run fails if unmet",
    )
    parser.add_argument(
        "--meta", action="append", default=[], help="KEY=VALUE run metadata"
    )
    parser.add_argument(
        "--exclude-scripture",
        default="",
        help="Scripture file; its knowledge-graph keys are excluded from drafts",
    )
    parser.add_argument(
        "--brief-path",
        default="",
        help="FR-895: write a citation-checked brief here (requires --brief-rubric)",
    )
    parser.add_argument(
        "--brief-rubric",
        default="",
        help="FR-895: the question the brief answers",
    )
    args = parser.parse_args(argv)

    canaries = {}
    for spec in args.canary:
        label, _, minimum = spec.partition("=")
        canaries[label] = int(minimum or "3")
    run_meta = dict(m.partition("=")[::2] for m in args.meta)
    graduated = (
        load_graduated_labels(args.exclude_scripture)
        if args.exclude_scripture
        else set()
    )

    result = aggregate(
        args.ledgers,
        args.output_dir,
        threshold=args.threshold,
        canaries=canaries,
        inbox_dir=args.inbox_dir,
        run_meta=run_meta,
        graduated=graduated,
        inbox_threshold=args.inbox_threshold,
    )
    print(
        f"census ok: {result['rows']} rows, {len(result['candidates'])} labels, "
        f"{result['abstentions']} abstentions, "
        f"{len(result['inbox_drafts'])} inbox drafts, "
        f"table {args.output_dir}/{result['table_name']}"
    )

    if bool(args.brief_path) != bool(args.brief_rubric):
        parser.error("--brief-path and --brief-rubric must be passed together")
    if args.brief_path:
        brief = emit_diary_brief(
            result["candidates"],
            args.brief_path,
            args.brief_rubric,
            run_meta=dict(
                run_meta,
                prompt_version="synthesize_brief.v1",
                rows_total=len(result["candidates"]),
            ),
        )
        print(
            f"brief: accepted={brief['accepted']} "
            f"top_finding_cited={brief['top_finding_cited']} "
            f"artifact={brief['artifact']}"
        )
        if not brief["accepted"] or not brief["top_finding_cited"]:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
