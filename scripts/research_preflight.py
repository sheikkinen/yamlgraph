"""FR-890/FR-896: deterministic closure checks for the research sole route.

Stdlib-only checks, no LLM in this path (FR-890 R-2/R-3, FR-896 C-6):

1. ``check_brief``: a problem brief is closed input — it must carry the
   four required headings (problem statement, closed-enum
   classification, constraints, witnessed incidents) and none of the
   forbidden solution-shaped sections (Proposed Solution, Candidates,
   Alternatives, Design, or candidate bullet lists). The brief is the
   contamination boundary: a draft solution in the brief anchors every
   persona (C-3).
2. ``verify_artifact``: shape check for ``tmp/draft-alternatives.md`` —
   frozen columns, no empty required cells, closed class/verdict enums
   (echo permitted only as the reducer's demotion), at least 3 non-echo
   rows, and a librarian row whose citation carries a URL and is not an
   error string. Distinct-class count is advisory, never blocking
   (FR-896 R-2). The wrapper checks shape; the Judge checks substance.
   FR-1005: a short run carries JSON persona accounting whose keys are
   conserved against the five canonical persona keys.
3. ``verify_promotion``: integrity check for a promoted research record
   against the committed run log (FR-896 R-3) — recomputes the brief and
   table-body hashes and reports matching / missing / mismatched. This
   proves hash consistency, not execution.

Exit codes: 64 brief violation, 65 artifact or promotion violation.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

EXIT_BRIEF = 64
EXIT_ARTIFACT = 65

REQUIRED_HEADINGS = (
    "Problem statement",
    "Classification",
    "Constraints",
    "Witnessed incidents",
)

FORBIDDEN_HEADINGS = re.compile(
    r"^#{1,6}\s*(proposed solution|candidates?|alternatives?|design)\b",
    re.IGNORECASE | re.MULTILINE,
)

# Bullet lists naming candidates are solution contamination (R-2).
CANDIDATE_BULLET = re.compile(r"^\s*[-*]\s*(candidate|option)\b[:.]?", re.IGNORECASE)

CLASSIFICATION_ENUM = frozenset(
    {
        "enforcement/latency-critical",
        "judgement/analysis/generation",
        "prediction-over-undecidable-input",
        "measurement",
    }
)

COLUMNS = (
    "candidate",
    "persona",
    "class",
    "verdict",
    "precedent",
    "is_this_a_graph",
    "effort-risk",
    "rationale",
)

# Closed enums — must mirror research_tools.py (witnessed by a test).
SOLUTION_CLASSES = frozenset(
    {
        "os-permissions",
        "process-boundary",
        "schema-data",
        "graph-pipeline",
        "subtraction",
        "external-method",
        "boundary-enforcement",
    }
)
ARTIFACT_VERDICTS = frozenset({"pursue", "dissent", "duplicate", "echo"})
CONVERGENT_SUFFIX = re.compile(r"\s*\(convergent x\d+\)$")

# FR-1005: mirrors research_tools (witnessed by a test); short runs must account.
_PERSONAS = "os_infra data_process yamlgraph_native subtractionist librarian"
PERSONA_KEYS = tuple(f"{p}_finding" for p in _PERSONAS.split())
PERSONA_COUNT = len(PERSONA_KEYS)
LIBRARIAN_KEY = "librarian_finding"
MIN_ROWS = 4
EXECUTED_HEADER = "- persona keys executed:"
FAILED_HEADER = "- personas failed:"

URL_RE = re.compile(r"https?://\S+")

# FR-938: mirrors research_tools. Shape only — the reducer resolves each
# token against the filesystem; this checks that a resolvable shape was
# offered at all. The shapes are the reducer's: registry identifiers,
# snake_case Scripture keys, repo paths, and URLs.
COMMITTED_ID_RE = re.compile(r"\b(?:FR|NC|CAP|REQ)-[A-Z]*-?\d+", re.IGNORECASE)
SCRIPTURE_KEY_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
REPO_PATH_RE = re.compile(r"\b[\w.-]+/[\w./-]+")
ECHO_MARKER = "brief-echo"
CLASSIFICATION_DELIMITERS = "—-:(–"
NONE_RETRIEVED = "none-retrieved"
PRIOR_ART_HEADING = "### Prior art retrieved for this brief (filename-noun, IDF-ranked)"
ERROR_STRINGS = ("Error:", "No results")


def is_librarian(persona: str) -> bool:
    """Shared librarian predicate (FR-896 AC-02) — substring, not equality."""
    return "librarian" in persona.lower()


def _section(text: str, heading: str) -> str:
    """Return the body of a ``## heading`` section, empty if absent."""
    pattern = re.compile(
        rf"^#{{1,6}}\s*{re.escape(heading)}\s*$(.*?)(?=^#{{1,6}}\s|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def check_brief(text: str) -> list[str]:
    """Return closure violations for a problem brief (empty = clean)."""
    violations: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if not _section(text, heading):
            violations.append(f"missing or empty required heading: ## {heading}")

    for match in FORBIDDEN_HEADINGS.finditer(text):
        violations.append(
            f"forbidden solution-shaped heading: {match.group(0).strip()!r}"
        )

    for line in text.splitlines():
        if CANDIDATE_BULLET.match(line):
            violations.append(f"forbidden candidate bullet: {line.strip()!r}")

    classification = _section(text, "Classification")
    if classification:
        violations.extend(_check_classification_claim(classification))

    return violations


def _check_classification_claim(classification: str) -> list[str]:
    """FR-937: the claim is the leading token, not any enum name in prose; a
    brief may explain why a class does *not* apply without claiming it."""
    line = next(
        (ln.strip() for ln in classification.splitlines() if ln.strip()),
        "",
    )
    claimed = [value for value in CLASSIFICATION_ENUM if line.startswith(value)]
    expected = "classification must name exactly one of: " + ", ".join(
        sorted(CLASSIFICATION_ENUM)
    )
    if len(claimed) != 1:
        return [expected]
    remainder = line[len(claimed[0]) :].strip()
    if remainder and remainder[0] not in CLASSIFICATION_DELIMITERS:
        return [
            f"{expected} — the claim line must end after the class or "
            f"continue with one of {''.join(CLASSIFICATION_DELIMITERS)!r}: "
            f"{line!r}"
        ]
    return []


def _table_rows(text: str) -> tuple[list[str], list[list[str]]]:
    """Parse the first markdown table into (header, data rows)."""
    header: list[str] | None = None
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if all(set(c) <= {"-", ":", " "} for c in cells):
            continue  # separator row
        rows.append(cells)
    return header or [], rows


def _prior_art_is_empty(text: str) -> bool:
    """Did the retrieval the personas saw actually come back empty?"""
    lines = text.splitlines()
    if PRIOR_ART_HEADING not in lines:
        return False
    start = lines.index(PRIOR_ART_HEADING) + 1
    for line in lines[start:]:
        if line.startswith("### ") or line.startswith("|"):
            break
        if line.strip():
            return NONE_RETRIEVED in line
    return False


def is_marker_claim(citation: str, marker: str) -> bool:
    """FR-937: a marker is claimed, not mentioned.

    The cell must *be* the marker or open with ``<marker>:``. An occurrence
    anywhere else is prose about the marker, and prose is not a claim.
    """
    stripped = citation.strip()
    return stripped == marker or stripped.startswith(f"{marker}:")


def _check_precedent(citation: str, prior_art_empty: bool) -> list[str]:
    """FR-938: a non-librarian cell offers an identifier, a URL, or the miss.

    FR-937: identifier and URL shapes resolve first, matching the reducer's
    ``_classify_precedent``. A cell citing real precedent stays traceable
    whatever else its prose happens to name.
    """
    if any(
        pattern.search(citation)
        for pattern in (
            COMMITTED_ID_RE,
            URL_RE,
            SCRIPTURE_KEY_RE,
            REPO_PATH_RE,
        )
    ):
        return []
    if is_marker_claim(citation, ECHO_MARKER):
        return [
            f"{ECHO_MARKER!r} is not precedent — the brief cannot cite "
            f"itself: {citation!r}"
        ]
    if is_marker_claim(citation, NONE_RETRIEVED):
        if prior_art_empty:
            return []
        return [
            f"{NONE_RETRIEVED!r} claimed but prior-art retrieval returned "
            f"hits: {citation!r}"
        ]
    return [
        "precedent carries no committed identifier, no URL and no "
        f"{NONE_RETRIEVED!r} token: {citation!r}"
    ]


def _header_value(text: str, label: str) -> str | None:
    for line in text.splitlines():
        if line.strip().startswith(label):
            return line.strip()[len(label) :].strip()
    return None


def _json_header(raw: str, label: str, kind: type) -> tuple[object, str | None]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        value = exc.msg  # not the kind → reported as the shape violation below
    if isinstance(value, kind):
        return value, None
    return None, f"persona accounting: '{label}' must be valid JSON {kind.__name__}"


def _check_persona_accounting(text: str, row_count: int) -> list[str]:
    """FR-1005 R-4: re-derive the reducer's accounting; short run: both lines
    and every invariant; full run: no failure line, executed = all keys."""
    executed_raw = _header_value(text, EXECUTED_HEADER)
    failed_raw = _header_value(text, FAILED_HEADER)
    short = row_count < PERSONA_COUNT
    if not short and failed_raw is not None:
        return ["persona accounting: failure metadata on a full five-row run"]
    if not short and executed_raw is None:
        return []
    missing = [
        f"persona accounting: {row_count} rows but no '{label}' line"
        for label, raw in ((EXECUTED_HEADER, executed_raw), (FAILED_HEADER, failed_raw))
        if short and raw is None
    ]
    if missing:
        return missing
    executed, bad_exec = _json_header(executed_raw, EXECUTED_HEADER, list)
    failed, bad_fail = (
        _json_header(failed_raw, FAILED_HEADER, dict)
        if failed_raw is not None
        else ({}, None)
    )
    if bad_exec or bad_fail:
        return [v for v in (bad_exec, bad_fail) if v]
    executed = [str(key) for key in executed]
    failed = {str(key): value for key, value in failed.items()}
    checks = (
        (len(set(executed)) != len(executed), "duplicate executed key"),
        (any(k not in PERSONA_KEYS for k in executed + list(failed)), "unknown key"),
        (bool(set(executed) & set(failed)), "executed and failed keys overlap"),
        (set(executed) | set(failed) != set(PERSONA_KEYS), "keys not conserved"),
        (len(executed) != row_count, f"{row_count} rows, {len(executed)} executed"),
        (any(not str(c).strip() for c in failed.values()), "empty failure cause"),
        (len(failed) > 1, "more than one failed persona"),
        (LIBRARIAN_KEY in failed, "the librarian may not fail"),
    )
    return [f"persona accounting: {msg}" for hit, msg in checks if hit]


def verify_artifact(text: str) -> list[str]:
    """Return schema/shape violations for a draft-alternatives artifact."""
    violations: list[str] = []
    header, rows = _table_rows(text)

    for column in COLUMNS:
        if column not in header:
            violations.append(f"missing required column: {column}")
    if violations:
        return violations

    if len(rows) < MIN_ROWS:
        violations.append(f"expected >= {MIN_ROWS} rows, found {len(rows)}")
    violations.extend(_check_persona_accounting(text, len(rows)))

    idx = {name: header.index(name) for name in COLUMNS}
    prior_art_empty = _prior_art_is_empty(text)
    non_echo_rows = 0
    librarian_rows = 0
    for row in rows:
        if len(row) < len(header):
            violations.append(f"short row: {row!r}")
            continue
        for name in COLUMNS:
            if not row[idx[name]]:
                violations.append(f"empty required cell {name!r} in row: {row!r}")
        class_cell = CONVERGENT_SUFFIX.sub("", row[idx["class"]])
        if class_cell and class_cell not in SOLUTION_CLASSES:
            violations.append(f"unknown solution class: {class_cell!r}")
        verdict = row[idx["verdict"]]
        if verdict and verdict not in ARTIFACT_VERDICTS:
            violations.append(f"unknown verdict: {verdict!r}")
        if verdict != "echo":
            non_echo_rows += 1
        if is_librarian(row[idx["persona"]]):
            librarian_rows += 1
            citation = row[idx["precedent"]]
            if any(err in citation for err in ERROR_STRINGS):
                violations.append(
                    f"librarian citation is an error string: {citation!r}"
                )
            elif not URL_RE.search(citation):
                violations.append(f"librarian citation carries no URL: {citation!r}")
        else:
            violations.extend(_check_precedent(row[idx["precedent"]], prior_art_empty))

    # Distinct-class count is advisory (FR-896 R-2): convergence is
    # information, never a gate. The gate is non-echo grounding.
    if rows and non_echo_rows < 3:
        violations.append(
            f"fewer than 3 non-echo rows: {non_echo_rows} — too little "
            "committed-state grounding"
        )
    if librarian_rows == 0:
        violations.append("no librarian row present")

    return violations


def verify_promotion(record_text: str, log_text: str, repo_root: str = ".") -> str:
    """Integrity verdict for a promoted research record (FR-896 R-3):
    ``matching`` (a run-log line reproduces the table-body and brief hashes),
    ``missing`` (no log lines) or ``mismatched``. Same-actor log: this proves
    hash consistency, not that the graph executed."""
    records = [json.loads(line) for line in log_text.splitlines() if line.strip()]
    if not records:
        return "missing"

    start = record_text.find("# Draft alternatives")
    if start == -1:
        return "mismatched"
    body_sha = hashlib.sha256(record_text[start:].encode("utf-8")).hexdigest()

    for entry in records:
        if entry.get("artifact_sha256") != body_sha:
            continue
        brief = Path(entry.get("brief_path", ""))
        if not brief.is_absolute():
            brief = Path(repo_root) / brief
        if brief.is_file() and hashlib.sha256(
            brief.read_bytes()
        ).hexdigest() == entry.get("brief_sha256"):
            return "matching"
        return "mismatched"
    return "mismatched"


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--verify-promotion":
        if len(argv) not in (3, 4):
            print(
                "usage: research_preflight.py --verify-promotion "
                "<record.md> <research-runs.jsonl> [repo_root]",
                file=sys.stderr,
            )
            return 2
        record = Path(argv[1]).read_text(encoding="utf-8")
        log = Path(argv[2]).read_text(encoding="utf-8")
        root = argv[3] if len(argv) == 4 else "."
        status = verify_promotion(record, log, root)
        print(f"research_preflight: promotion {status}")
        return 0 if status == "matching" else EXIT_ARTIFACT
    if argv and argv[0] == "--verify-artifact":
        if len(argv) != 2:
            print(
                "usage: research_preflight.py --verify-artifact <artifact.md>",
                file=sys.stderr,
            )
            return 2
        violations = verify_artifact(Path(argv[1]).read_text(encoding="utf-8"))
        exit_code = EXIT_ARTIFACT
        label = "artifact"
    else:
        if len(argv) != 1:
            print("usage: research_preflight.py <problem-brief.md>", file=sys.stderr)
            return 2
        violations = check_brief(Path(argv[0]).read_text(encoding="utf-8"))
        exit_code = EXIT_BRIEF
        label = "brief"

    if violations:
        for violation in violations:
            print(f"research_preflight: {label}: {violation}", file=sys.stderr)
        return exit_code
    print(f"research_preflight: {label} ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
