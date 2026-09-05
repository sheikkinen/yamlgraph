"""FR-995 outsider reader — typed report boundary, derived verdict, observation.

The model's free text is a CLAIM. It is normalised here into a Pydantic
report or rejected (fail closed). The verdict is derived from the validated
report, never taken from the model. Every rendered report carries one typed
observation marker (FR-1004); the durable measurement record is the PR comment
the wrapper posts — nothing is written under the repository.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

MAX_S3 = 8
MAX_S4 = 10
HEDGES = ("does not say", "something called", "not stated", "cannot tell")
PLACEHOLDER = "-"  # repo / pr / head_sha of a report that is not about a real PR
_HEADINGS = (
    "## 1. In my own words",
    "## 2. Could I decide whether to merge this from the description alone?",
    "## 3. Words and references I could not understand",
    "## 4. What a merge decision would still need",
)
_QUOTE = re.compile(r"[“\"`]([^”\"`]{1,200})[”\"`]")
_ITEM_START = re.compile(r"^(?:[-*]\s+|\d+\.\s+|\*\*)")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_MARKER_PREFIX = "<!-- outsider reader | "
_MARKER_LINE = re.compile(r"^<!-- outsider reader \| (.*) -->$", re.MULTILINE)
# marker key -> Observation field, in marker order
_MARKER_FIELDS = (
    ("ts", "ts"),
    ("repo", "repo"),
    ("pr", "pr"),
    ("head", "head_sha"),
    ("input", "input_sha256"),
    ("model", "model"),
    ("prompt", "prompt_digest"),
    ("tool", "tool_sha"),
    ("verdict", "derived_verdict"),
    ("s3", "s3"),
    ("s4", "s4"),
)


class ReportFormatError(ValueError):
    """Model text does not satisfy the report contract."""


class Item(BaseModel):
    quote: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=1)


class OutsiderReport(BaseModel):
    restatement: str = Field(min_length=1)
    model_opinion: Literal["YES", "NO"]
    opinion_reason: str = Field(min_length=1)
    section3: list[Item] = Field(max_length=MAX_S3)
    section4: list[str] = Field(max_length=MAX_S4)


class Observation(BaseModel):
    """The typed measurement carried by the report's HTML marker (FR-1004 S-2).

    Countable only when the report is successfully posted as a PR comment.
    ``--input`` / ``--selftest`` reports carry ``-`` for repo, pr and head_sha
    and are never posted.
    """

    ts: str
    repo: str = Field(min_length=1)
    pr: int | Literal["-"]
    head_sha: str
    input_sha256: str
    model: str = Field(min_length=1)
    prompt_digest: str = Field(min_length=1)
    tool_sha: str = Field(min_length=1)
    derived_verdict: Literal["YES", "NO"]
    s3: int = Field(ge=0)
    s4: int = Field(ge=0)

    @field_validator("ts")
    @classmethod
    def _utc_z(cls, v: str) -> str:
        if not _TS.match(v):
            raise ValueError("ts must be UTC ISO-8601 with a Z suffix")
        return v

    @field_validator("head_sha")
    @classmethod
    def _full_head(cls, v: str) -> str:
        if v != PLACEHOLDER and not _HEX40.match(v):
            raise ValueError("head_sha must be the full 40-hex SHA or '-'")
        return v

    @field_validator("input_sha256")
    @classmethod
    def _full_input(cls, v: str) -> str:
        if not _HEX64.match(v):
            raise ValueError("input_sha256 must be the full 64-hex digest")
        return v


# Resolve postponed annotations under yamlgraph's path-based tool loading (CONF-443 idiom).
Item.model_rebuild()
OutsiderReport.model_rebuild()
Observation.model_rebuild()


# ------------------------------------------------------------------ parse
def _split_sections(text: str) -> list[str]:
    positions: list[int] = []
    for heading in _HEADINGS:
        # Headings must be complete lines, not prefixes of a longer line.
        hits = [
            m.start()
            for m in re.finditer(rf"^{re.escape(heading)}[ \t]*$", text, re.MULTILINE)
        ]
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
    reason = " ".join(opinion_lines[1:]).strip()
    if not reason:
        raise ReportFormatError("section 2 opinion has no reason")
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
        if not question:
            raise ReportFormatError(f"section 3 item has no question: {raw[:80]!r}")
        items3.append(Item(quote=m.group(1).strip(), question=question))
    items4 = [
        re.sub(r"^(?:[-*]\s+)?(?:\[ \]\s*)?", "", i).strip()
        for i in _items(s4, MAX_S4, "section 4")
    ]
    if any(not i for i in items4):
        raise ReportFormatError("section 4 has an empty item")
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


# ------------------------------------------------------------- observation
def render_marker(obs: Observation) -> str:
    """One HTML comment line: the typed observation, searchable on GitHub."""
    body = " | ".join(f"{key}: {getattr(obs, attr)}" for key, attr in _MARKER_FIELDS)
    return f"{_MARKER_PREFIX}{body} -->"


def parse_observation(report_text: str) -> Observation:
    """Round-trip the marker back into an Observation. Fails closed."""
    hits = _MARKER_LINE.findall(report_text)
    if len(hits) != 1:
        raise ReportFormatError(
            f"observation marker must appear exactly once ({len(hits)})"
        )
    fields: dict[str, str] = {}
    for part in hits[0].split(" | "):
        key, sep, value = part.partition(": ")
        if not sep:
            raise ReportFormatError(f"malformed marker field: {part!r}")
        fields[key] = value
    expected = [key for key, _ in _MARKER_FIELDS]
    if list(fields) != expected:
        raise ReportFormatError(f"marker fields {list(fields)} != {expected}")
    return Observation(**{attr: fields[key] for key, attr in _MARKER_FIELDS})


def render_report(report: OutsiderReport, obs: Observation) -> str:
    lines = [
        f"**Derived verdict:** {obs.derived_verdict}  (rule: ≤ 2 items in section 3 and no hedge in section 1; computed in code)",
        render_marker(obs),
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


# ------------------------------------------------------------- graph tools
def read_input(state: dict[str, Any]) -> str:
    path = Path(state["input_path"])
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def finalize_report(state: dict[str, Any]) -> dict[str, Any]:
    """Parse the model output, derive the verdict, write the report. Fails closed.

    The wrapper supplies the base observation fields as graph state (FR-1004
    S-3: repo, pr, head_sha, prompt_digest, tool_sha, model); verdict and
    counts come from the validated report; the input digest is taken over the
    exact bytes the reader saw.
    """
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
    obs = Observation(
        ts=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        repo=str(state["repo"]),
        pr=str(state["pr"]),
        head_sha=str(state["head_sha"]),
        input_sha256=hashlib.sha256(Path(state["input_path"]).read_bytes()).hexdigest(),
        model=str(state["model"]),
        prompt_digest=str(state["prompt_digest"]),
        tool_sha=str(state["tool_sha"]),
        derived_verdict=verdict,
        s3=len(report.section3),
        s4=len(report.section4),
    )
    out = Path(state["report_path"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(report, obs), encoding="utf-8")
    return {
        "path": str(out),
        "derived_verdict": verdict,
        "s3_count": obs.s3,
        "s4_count": obs.s4,
        "model_opinion": report.model_opinion,
    }
