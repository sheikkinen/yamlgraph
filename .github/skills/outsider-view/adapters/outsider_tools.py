"""FR-995 outsider reader — typed report boundary, derived verdict, ledger.

The model's free text is a CLAIM. It is normalised here into a Pydantic
report or rejected (fail closed). The verdict is derived from the validated
report, never taken from the model. Ledger rows exist only for validated
runs against real PRs.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

MAX_S3 = 8
MAX_S4 = 10
HEDGES = ("does not say", "something called", "not stated", "cannot tell")
_HEADINGS = (
    "## 1. In my own words",
    "## 2. Could I decide whether to merge this from the description alone?",
    "## 3. Words and references I could not understand",
    "## 4. What a merge decision would still need",
)
_QUOTE = re.compile(r"[“\"`]([^”\"`]{1,200})[”\"`]")
_ITEM_START = re.compile(r"^(?:[-*]\s+|\d+\.\s+|\*\*)")


class ReportFormatError(ValueError):
    """Model text does not satisfy the report contract."""


class Item(BaseModel):
    quote: str = Field(min_length=1, max_length=200)
    question: str = ""


class OutsiderReport(BaseModel):
    restatement: str = Field(min_length=1)
    model_opinion: Literal["YES", "NO"]
    opinion_reason: str = ""
    section3: list[Item] = Field(max_length=MAX_S3)
    section4: list[str] = Field(max_length=MAX_S4)


# Resolve postponed annotations under yamlgraph's path-based tool loading (CONF-443 idiom).
Item.model_rebuild()
OutsiderReport.model_rebuild()


# ------------------------------------------------------------------ parse
def _split_sections(text: str) -> list[str]:
    positions: list[int] = []
    for heading in _HEADINGS:
        hits = [m.start() for m in re.finditer(re.escape(heading), text)]
        if len(hits) != 1:
            raise ReportFormatError(
                f"heading must appear exactly once: {heading!r} ({len(hits)})"
            )
        positions.append(hits[0])
    if positions != sorted(positions):
        raise ReportFormatError("sections out of order")
    bounds = positions + [len(text)]
    return [
        text[bounds[i] + len(_HEADINGS[i]) : bounds[i + 1]].strip() for i in range(4)
    ]


def _is_nothing(body: str) -> bool:
    return body.strip().strip("*_").casefold() in {"nothing", "nothing."}


def _items(body: str, cap: int, label: str) -> list[str]:
    if not body or _is_nothing(body):
        return []
    lines = [ln.strip() for ln in body.splitlines()]
    items: list[str] = []
    for ln in lines:
        if not ln:
            continue
        if _ITEM_START.match(ln) or not items:
            items.append(ln)
        else:
            items[-1] += " " + ln  # continuation line
    if len(items) > cap:
        raise ReportFormatError(f"{label}: {len(items)} items exceeds cap {cap}")
    return items


def parse_report(text: str) -> OutsiderReport:
    s1, s2, s3, s4 = _split_sections(text)
    if not s1:
        raise ReportFormatError("section 1 restatement is empty")
    opinion_lines = [ln.strip() for ln in s2.splitlines() if ln.strip()]
    if not opinion_lines or opinion_lines[0].strip("*").upper() not in {"YES", "NO"}:
        raise ReportFormatError("section 2 must start with YES or NO")
    opinion = opinion_lines[0].strip("*").upper()
    reason = " ".join(opinion_lines[1:])
    items3: list[Item] = []
    for raw in _items(s3, MAX_S3, "section 3"):
        m = _QUOTE.search(raw)
        if not m:
            raise ReportFormatError(
                f"section 3 item has no quoted phrase: {raw[:80]!r}"
            )
        question = (
            raw[m.end() :].split("·", 1)[-1].replace("**Question:**", "").strip(" *·")
        )
        items3.append(Item(quote=m.group(1).strip(), question=question))
    items4 = [
        re.sub(r"^(?:[-*]\s+)?(?:\[ \]\s*)?", "", i).strip()
        for i in _items(s4, MAX_S4, "section 4")
    ]
    return OutsiderReport(
        restatement=s1,
        model_opinion=opinion,
        opinion_reason=reason,
        section3=items3,
        section4=items4,  # type: ignore[arg-type]
    )


# ----------------------------------------------------------------- verdict
def derive_verdict(report: OutsiderReport) -> Literal["YES", "NO"]:
    low = report.restatement.casefold()
    if len(report.section3) <= 2 and not any(h in low for h in HEDGES):
        return "YES"
    return "NO"


def render_report(
    report: OutsiderReport, verdict: str, *, model: str, source: str
) -> str:
    lines = [
        f"**Derived verdict:** {verdict}  (rule: ≤ 2 items in section 3 and no hedge in section 1; computed in code)",
        f"<!-- outsider reader | source: {source} | model: {model} | {datetime.now(UTC).isoformat()} -->",
        "",
        _HEADINGS[0],
        "",
        report.restatement,
        "",
        _HEADINGS[1],
        "",
        report.model_opinion,
        f"(model's non-authoritative opinion) {report.opinion_reason}".strip(),
        "",
        _HEADINGS[2],
        "",
    ]
    lines += [
        f"- **“{i.quote}”** · {i.question}".rstrip(" ·") for i in report.section3
    ] or ["nothing"]
    lines += ["", _HEADINGS[3], ""]
    lines += [f"- [ ] {i}" for i in report.section4] or ["nothing"]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ ledger
def ledger_row(
    *,
    repo: str,
    pr: int,
    head_sha: str,
    input_text: str,
    model: str,
    prompt_digest: str,
    tool_sha: str,
    verdict: str,
    s3: int,
    s4: int,
    report_path: str,
) -> dict[str, Any]:
    return {
        "ts": datetime.now(UTC).isoformat(),
        "repo": repo,
        "pr": pr,
        "head_sha": head_sha,
        "input_sha256": hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
        "model": model,
        "prompt_digest": prompt_digest,
        "tool_sha": tool_sha,
        "derived_verdict": verdict,
        "s3_count": s3,
        "s4_count": s4,
        "report_path": report_path,
    }


def append_ledger(path: Path, row: dict[str, Any], *, mode: str) -> bool:
    """Only validated runs against a real PR are measurements."""
    if mode != "pr":
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return True


def distinct_pr_count(path: Path) -> int:
    if not path.is_file():
        return 0
    return len(
        {
            (json.loads(ln)["repo"], json.loads(ln)["pr"])
            for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        }
    )


# ------------------------------------------------------------- graph tools
def read_input(state: dict[str, Any]) -> str:
    path = Path(state["input_path"])
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def finalize_report(state: dict[str, Any]) -> dict[str, Any]:
    """Parse the model output, derive the verdict, write the report. Fails closed."""
    result = state.get("outsider_result")
    output = (
        result.get("output")
        if isinstance(result, dict)
        else getattr(result, "output", None)
    )
    if not isinstance(output, str) or not output.strip():
        raise ReportFormatError(f"outsider produced no output: {result!r}")
    report = parse_report(output)
    verdict = derive_verdict(report)
    out = Path(state["report_path"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render_report(
            report,
            verdict,
            model=str(state.get("model", "gpt-5.6-sol")),
            source=str(state["input_path"]),
        ),
        encoding="utf-8",
    )
    return {
        "path": str(out),
        "derived_verdict": verdict,
        "s3_count": len(report.section3),
        "s4_count": len(report.section4),
        "model_opinion": report.model_opinion,
    }
