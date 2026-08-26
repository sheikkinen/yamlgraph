"""FR-890: deterministic closure checks for the research sole route.

Two stdlib-only checks, no LLM in this path (judgement R-2, R-3):

1. ``check_brief``: a problem brief is closed input — it must carry the
   four required headings (problem statement, closed-enum
   classification, constraints, witnessed incidents) and none of the
   forbidden solution-shaped sections (Proposed Solution, Candidates,
   Alternatives, Design, or candidate bullet lists). The brief is the
   contamination boundary: a draft solution in the brief anchors every
   persona (C-3).
2. ``verify_artifact``: shape check for ``tmp/draft-alternatives.md`` —
   frozen columns, no empty required cells, 4-6 distinct solution
   classes, and a librarian row whose citation carries a URL and is not
   an error string (R-4). The wrapper checks shape; the Judge checks
   substance.

Exit codes: 64 brief violation, 65 artifact violation.
"""

from __future__ import annotations

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
)

URL_RE = re.compile(r"https?://\S+")
ERROR_STRINGS = ("Error:", "No results")


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
        values = [v for v in CLASSIFICATION_ENUM if v in classification]
        if len(values) != 1:
            violations.append(
                "classification must name exactly one of: "
                + ", ".join(sorted(CLASSIFICATION_ENUM))
            )

    return violations


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


def verify_artifact(text: str) -> list[str]:
    """Return schema/shape violations for a draft-alternatives artifact."""
    violations: list[str] = []
    header, rows = _table_rows(text)

    for column in COLUMNS:
        if column not in header:
            violations.append(f"missing required column: {column}")
    if violations:
        return violations

    if len(rows) < 4:
        violations.append(f"expected >= 4 rows, found {len(rows)}")

    idx = {name: header.index(name) for name in COLUMNS}
    classes: set[str] = set()
    librarian_rows = 0
    for row in rows:
        if len(row) < len(header):
            violations.append(f"short row: {row!r}")
            continue
        for name in COLUMNS:
            if not row[idx[name]]:
                violations.append(f"empty required cell {name!r} in row: {row!r}")
        classes.add(row[idx["class"]])
        if "librarian" in row[idx["persona"]].lower():
            librarian_rows += 1
            citation = row[idx["precedent"]]
            if any(err in citation for err in ERROR_STRINGS):
                violations.append(
                    f"librarian citation is an error string: {citation!r}"
                )
            elif not URL_RE.search(citation):
                violations.append(f"librarian citation carries no URL: {citation!r}")

    if not 4 <= len(classes) <= 6:
        violations.append(
            f"expected 4-6 distinct solution classes, found {len(classes)}"
        )
    if librarian_rows == 0:
        violations.append("no librarian row present")

    return violations


def main(argv: list[str]) -> int:
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
