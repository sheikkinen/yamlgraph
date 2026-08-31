"""Deterministic tools for the research-route demo (FR-890, FR-896).

FR-896 hardening: precedent traceability is checked in code at the
reducer boundary — committed identifiers must exist, brief echo is
demoted (never dropped), librarian citations are reconciled against
recorded tool observations, and enums replace free-text labels
(two_strike_split: mechanizable levels belong in code, not prompts).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

REQUIRED_SECTIONS = (
    "Problem statement",
    "Classification",
    "Constraints",
    "Witnessed incidents",
)

PERSONA_KEYS = (
    "os_infra_finding",
    "data_process_finding",
    "yamlgraph_native_finding",
    "subtractionist_finding",
    "librarian_finding",
)

TABLE_COLUMNS = (
    "candidate",
    "persona",
    "class",
    "verdict",
    "precedent",
    "is_this_a_graph",
    "effort-risk",
    "rationale",
)

# Closed enums (FR-896 AC-06). ``echo`` is reducer-only: no persona may
# claim it; the reducer sets it when demoting a brief-echo row.
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
MODEL_VERDICTS = frozenset({"pursue", "dissent", "duplicate"})
ECHO_MARKER = "brief-echo"

# FR-932: the honest miss. Personas may only claim it when retrieval
# genuinely returned nothing, which the reducer verifies against the
# same block the personas were shown.
NONE_RETRIEVED = "none-retrieved"
PRIOR_ART_HEADING = "### Prior art retrieved for this brief (filename-noun, IDF-ranked)"

URL_RE = re.compile(r"https?://\S+")
LIBRARIAN_ERROR_STRINGS = ("Error:", "No results")

FR_ID_RE = re.compile(r"\bFR-(\d+)\b")
CAP_ID_RE = re.compile(r"\bCAP-(\d+)\b")
REPO_PATH_RE = re.compile(
    r"(?:feature-requests|capabilities|docs|examples|scripts|tests|graphs"
    r"|prompts|reference|changelog|yamlgraph|\.github|\.chaplain)/[\w./-]+"
)
SCRIPTURE_KEY_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
_SCRIPTURE_HEADING_RE = re.compile(r"^  ([a-z][a-z0-9_]*):", re.MULTILINE)

_MAX_CONTEXT_LINES = 300
_MIN_GRAPH_SHAPES = 10


def is_librarian(persona: str) -> bool:
    """Shared librarian predicate (FR-896 AC-02) — substring, not equality."""
    return "librarian" in persona.lower()


class PersonaFinding(BaseModel):
    """One closed-input planning alternative from one persona."""

    persona: str = Field(min_length=1, max_length=400)
    candidate: str = Field(min_length=1, max_length=400)
    solution_class: str = Field(min_length=1, max_length=400)
    verdict: str = Field(min_length=1, max_length=400)
    rationale: str = Field(min_length=1, max_length=400)
    precedent: str = Field(min_length=1, max_length=400)
    is_this_a_graph: str = Field(min_length=1, max_length=400)
    effort_risk: str = Field(min_length=1, max_length=400)

    @field_validator("*", mode="before")
    @classmethod
    def _reject_blank(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("empty required cell")
            return stripped
        return value

    @field_validator("solution_class")
    @classmethod
    def _closed_class(cls, value: str) -> str:
        if value not in SOLUTION_CLASSES:
            raise ValueError(
                f"solution_class must be one of {sorted(SOLUTION_CLASSES)}, "
                f"got {value!r}"
            )
        return value

    @field_validator("verdict")
    @classmethod
    def _closed_verdict(cls, value: str) -> str:
        if value == "echo":
            raise ValueError(
                "verdict 'echo' is reducer-only — personas may not claim it"
            )
        if value not in MODEL_VERDICTS:
            raise ValueError(
                f"verdict must be one of {sorted(MODEL_VERDICTS)}, got {value!r}"
            )
        return value


def _state_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value[key]
    return value


def _section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^#{{1,6}}\s*{re.escape(heading)}\s*$(.*?)(?=^#{{1,6}}\s|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def load_brief(brief_path: str) -> dict:
    """Parse the four allowed problem-brief sections into graph state."""
    path = Path(_state_value(brief_path, "brief_path"))
    text = path.read_text(encoding="utf-8")

    parsed = {
        "problem_statement": _section(text, "Problem statement"),
        "classification": _section(text, "Classification"),
        "constraints": _section(text, "Constraints"),
        "witnessed_incidents": _section(text, "Witnessed incidents"),
    }
    missing = [name for name, value in parsed.items() if not value]
    if missing:
        raise ValueError(f"brief missing required sections: {', '.join(missing)}")
    return parsed


def _scripture_keys(repo_root: Path) -> frozenset[str]:
    scripture = repo_root / ".github" / "copilot-instructions.md"
    if not scripture.is_file():
        raise ValueError(f"Scripture not found: {scripture}")
    return frozenset(_SCRIPTURE_HEADING_RE.findall(scripture.read_text("utf-8")))


def _graph_shape_lines(root: Path, patterns: list[str]) -> list[str]:
    lines: list[str] = []
    for pattern in patterns:
        for graph_path in sorted(root.glob(pattern)):
            with graph_path.open(encoding="utf-8") as handle:
                config = yaml.safe_load(handle) or {}
            if not isinstance(config, dict) or "nodes" not in config:
                continue
            name = str(config.get("name") or graph_path.parent.name).strip()
            description = " ".join(str(config.get("description") or "").split())
            rel = graph_path.relative_to(root)
            lines.append(f"{name} ({rel}): {description}")
    return lines


def collect_graph_shapes(root_dir: str = ".") -> str:
    """One line per committed graph across demos, graphs/, .chaplain/graphs/.

    FR-896 AC-05: inventory drift is caught by a count threshold, not a
    named-demo canary.
    """
    raw = root_dir.get("root_dir", ".") if isinstance(root_dir, dict) else root_dir
    root = Path(raw)
    if not root.is_absolute():
        root = Path.cwd() / root
    if not root.is_dir():
        raise ValueError(f"graph inventory root not found: {root}")

    if (root / "examples" / "demos").is_dir():
        patterns = [
            "examples/demos/*/graph.yaml",
            "graphs/*/*.yaml",
            ".chaplain/graphs/*/graph.yaml",
        ]
    else:
        patterns = ["*/graph.yaml"]  # called with a demos dir directly

    lines = _graph_shape_lines(root, patterns)
    if len(lines) < _MIN_GRAPH_SHAPES:
        raise ValueError(
            f"graph shape inventory suspiciously small ({len(lines)} < "
            f"{_MIN_GRAPH_SHAPES}) — inventory drift at {root}"
        )
    return "\n".join(lines)


def _cap_one_liners(repo_root: Path) -> list[str]:
    entries: list[str] = []
    for cap_path in sorted((repo_root / "capabilities").glob("CAP-*.yaml")):
        with cap_path.open(encoding="utf-8") as handle:
            cap = yaml.safe_load(handle) or {}
        entries.append(f"{cap.get('id', cap_path.stem)} {cap.get('name', '')}".strip())
    return [" | ".join(entries[i : i + 6]) for i in range(0, len(entries), 6)]


def _load_prior_art_builder():
    """Load the FR-737 hook retrieval module by path (it is not importable)."""
    import importlib.util

    path = (
        Path(__file__).resolve().parents[4]
        / ".github"
        / "hooks"
        / "scripts"
        / "checks"
        / "prior_art.py"
    )
    spec = importlib.util.spec_from_file_location("prior_art_fr932", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_prior_art


def _prior_art_lines(repo_root: Path, brief_path: str) -> list[str]:
    """Retrieve FR-corpus prior art for the brief (FR-932).

    The query path is synthetic: build_prior_art scopes its corpus to the
    query file's parent, so a brief living in research-briefs/ must ask as
    though it were an FR. rare_floor=False because this grounds a context
    window rather than interrupting an author.
    """
    if not brief_path:
        return [PRIOR_ART_HEADING, NONE_RETRIEVED]
    stem = Path(brief_path).stem
    query = repo_root / "feature-requests" / f"{stem}.md"
    try:
        block = _load_prior_art_builder()(query, rare_floor=False)
    except (OSError, ValueError):
        block = ""
    # FR-890 R-2 closure: the brief's own FR states the author's proposed
    # solution. The synthetic query path hides it from build_prior_art's
    # self-exclusion, so drop it here by FR number.
    own_fr = re.match(r"(fr-\d+)", stem, re.IGNORECASE)
    own_prefix = f"{own_fr.group(1).upper()}-" if own_fr else None
    hits = [
        line
        for line in block.splitlines()
        if line.startswith("  ")
        and not line.startswith("  Disposition")
        and not (own_prefix and line.strip().upper().startswith(own_prefix))
    ]
    return [PRIOR_ART_HEADING, *(hits or [NONE_RETRIEVED])]


def extract_prior_art_block(committed_context: str) -> str:
    """Slice the prior-art subsection out of the block the personas saw.

    FR-932 R-5: one computation, copied. The reducer never re-runs
    retrieval, so the artifact cannot disagree with the context window.
    """
    lines = committed_context.splitlines()
    try:
        start = lines.index(PRIOR_ART_HEADING)
    except ValueError:
        return ""
    end = start + 1
    while end < len(lines) and not lines[end].startswith("### "):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def collect_committed_context(repo_root: str = ".", brief_path: str = "") -> str:
    """Deterministic committed-state grounding block (FR-896 AC-05).

    No LLM, no author narrative: CAP registry one-liners, ARCHITECTURE.md
    headings, Scripture trap/cure keys, and (FR-932) prior art retrieved
    from the feature-request corpus for this brief — the same block for
    every persona, bounded.
    """
    root = Path(_state_value(repo_root, "repo_root"))
    # FR-932: python nodes call func(effective_state) — ONE positional dict with
    # declared `variables` merged in, never keywords. brief_path therefore
    # arrives inside that dict at runtime and only as an argument in tests.
    if isinstance(repo_root, dict) and not brief_path:
        brief_path = repo_root.get("brief_path", "")
    arch = root / "ARCHITECTURE.md"
    headings = [
        line.lstrip("#").strip()
        for line in arch.read_text("utf-8").splitlines()
        if re.match(r"^#{1,2}\s", line)
    ]
    keys = sorted(_scripture_keys(root))
    key_lines = [", ".join(keys[i : i + 10]) for i in range(0, len(keys), 10)]

    lines = [
        "## Committed context (deterministic, author-independent)",
        "",
        "### Capability registry (CAP one-liners)",
        *_cap_one_liners(root),
        "",
        *_prior_art_lines(root, _state_value(brief_path, "brief_path")),
        "",
        "### ARCHITECTURE.md headings",
        *headings,
        "",
        "### Scripture trap/cure keys",
        *key_lines,
    ]
    if len(lines) > _MAX_CONTEXT_LINES:
        raise ValueError(
            f"committed-context block exceeds bound: {len(lines)} > "
            f"{_MAX_CONTEXT_LINES} lines"
        )
    return "\n".join(lines)


def _normalize_finding(value: Any, key: str) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if not isinstance(value, dict):
        raise ValueError(f"persona output {key!r} is not a dict")
    return value


def _as_error_record(entry: Any) -> dict[str, Any] | None:
    """Normalize a PipelineError object or dict; None if unstructured."""
    if hasattr(entry, "model_dump"):
        entry = entry.model_dump()
    if not isinstance(entry, dict):
        return None
    if not any(entry.get(field) for field in ("node", "type", "message")):
        return None
    return entry


def _format_recorded_errors(errors: Any) -> str:
    """Render the error channel the retry handler already populated."""
    lines = []
    for entry in errors or []:
        record = _as_error_record(entry)
        if record is None:
            continue
        category = record.get("type")
        category = getattr(category, "value", category) or "unknown_error"
        exception_type = (record.get("details") or {}).get("exception_type")
        origin = record.get("node") or "unknown_node"
        suffix = f" ({exception_type})" if exception_type else ""
        lines.append(f"\n  {origin}: {category}{suffix}: {record.get('message', '')}")
    return "".join(lines)


def gather_findings(state: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Gather the five persona findings without deduplication."""
    missing = [key for key in PERSONA_KEYS if key not in state]
    if missing:
        # FR-926: the cause is already recorded one key away — cite it.
        detail = _format_recorded_errors(state.get("errors"))
        raise ValueError(
            f"missing persona findings: {', '.join(missing)}"
            + (f"\nrecorded node errors:{detail}" if detail else "")
        )
    return {"findings": [_normalize_finding(state[key], key) for key in PERSONA_KEYS]}


def _check_committed_ids(text: str, repo_root: Path) -> bool:
    """Raise on nonexistent identifiers; return True if any resolved."""
    resolved = False
    for number in FR_ID_RE.findall(text):
        if not list((repo_root / "feature-requests").glob(f"FR-{number}[-.]*")):
            raise ValueError(f"precedent names nonexistent FR-{number}")
        resolved = True
    for number in CAP_ID_RE.findall(text):
        if not list((repo_root / "capabilities").glob(f"CAP-{number}-*.yaml")):
            raise ValueError(f"precedent names nonexistent CAP-{number}")
        resolved = True
    remaining = text
    for token in REPO_PATH_RE.findall(text):
        cleaned = token.rstrip(".,;:)")
        if not (repo_root / cleaned).exists():
            raise ValueError(f"precedent cites nonexistent path: {cleaned!r}")
        resolved = True
        remaining = remaining.replace(token, " ")
    keys = _scripture_keys(repo_root)
    for token in SCRIPTURE_KEY_RE.findall(remaining):
        if token in keys or _is_committed_dir(token, repo_root):
            resolved = True
            continue
        raise ValueError(
            f"precedent names unknown Scripture key or committed dir: {token!r}"
        )
    return resolved


def _is_committed_dir(token: str, repo_root: Path) -> bool:
    """Bare snake token naming a committed demo/graph dir is a valid citation."""
    return any(
        (repo_root / parent / token).is_dir()
        for parent in ("examples/demos", "graphs", ".chaplain/graphs")
    )


def _classify_precedent(
    precedent: str, repo_root: Path, prior_art_empty: bool = False
) -> str:
    """Precedent validation (FR-932): traceable | grounded-empty | raise.

    FR-896's ``brief-echo`` demotion is gone: restating the brief as its
    own precedent is not precedent. Its replacement is bounded — a
    persona may claim ``none-retrieved`` only when the retrieval the
    personas were shown actually came back empty.
    """
    without_urls = URL_RE.sub(" ", precedent)
    if _check_committed_ids(without_urls, repo_root):
        return "traceable"
    if ECHO_MARKER in precedent:
        raise ValueError(
            f"{ECHO_MARKER!r} is not precedent — the brief cannot cite "
            f"itself; cite committed state or declare {NONE_RETRIEVED!r}: "
            f"{precedent!r}"
        )
    if NONE_RETRIEVED in precedent:
        if prior_art_empty:
            return "grounded-empty"
        raise ValueError(
            f"{NONE_RETRIEVED!r} claimed but prior-art retrieval returned "
            f"hits — cite one or explain why it does not apply: {precedent!r}"
        )
    raise ValueError(
        "precedent carries no committed identifier, no URL and no "
        f"{NONE_RETRIEVED!r} token — cite committed state or declare the "
        f"honest miss: {precedent!r}"
    )


def _check_librarian_row(row: PersonaFinding, tool_results: Any) -> None:
    if any(marker in row.precedent for marker in LIBRARIAN_ERROR_STRINGS):
        raise ValueError("librarian precedent is an error string")
    match = URL_RE.search(row.precedent)
    if not match:
        raise ValueError("librarian precedent must contain a URL")
    url = match.group(0).rstrip(".,;:)")
    if not tool_results or url not in str(tool_results):
        raise ValueError(
            f"librarian citation URL not found in librarian_tool_results: {url!r}"
        )


def _validate_findings(
    findings: list[dict],
    repo_root: Path,
    librarian_tool_results: Any,
    prior_art_empty: bool = False,
) -> tuple[list[PersonaFinding], list[str]]:
    """Validate rows; return (rows, per-row status: traceable|grounded-empty)."""
    validated: list[PersonaFinding] = []
    for index, finding in enumerate(findings, start=1):
        try:
            row = PersonaFinding.model_validate(finding)
        except ValidationError as exc:
            raise ValueError(
                f"empty or invalid required cell in finding {index}: {exc}"
            ) from exc
        validated.append(row)

    statuses: list[str] = []
    for row in validated:
        if is_librarian(row.persona):
            _check_librarian_row(row, librarian_tool_results)
            statuses.append("traceable")
        else:
            statuses.append(
                _classify_precedent(row.precedent, repo_root, prior_art_empty)
            )

    # FR-932: every surviving row is grounded — traceable or an honest,
    # verified miss. Counting the miss against the floor would make a
    # fabricated citation the cheaper option.
    if len(statuses) < 3:
        raise ValueError(
            f"fewer than 3 grounded findings: {len(statuses)} — "
            "the run carries too little committed-state grounding"
        )
    return validated, statuses


def _cell(value: str) -> str:
    return " ".join(value.split()).replace("|", "/")


def reduce_findings(
    findings: list[dict],
    brief_path: str,
    base_dir: str = ".",
    librarian_tool_results: Any = None,
    repo_root: str = ".",
    prior_art_block: str = "",
) -> dict:
    """Validate persona findings and write tmp/draft-alternatives.md."""
    root = Path(repo_root)
    prior_art_empty = NONE_RETRIEVED in prior_art_block
    rows, statuses = _validate_findings(
        findings, root, librarian_tool_results, prior_art_empty
    )
    artifact = Path(base_dir) / "tmp" / "draft-alternatives.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)

    class_counts: dict[str, int] = {}
    for row in rows:
        class_counts[row.solution_class] = class_counts.get(row.solution_class, 0) + 1

    personas = ", ".join(row.persona for row in rows)
    run_date = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Draft alternatives",
        "",
        f"- brief: {Path(brief_path).name}",
        f"- run date: {run_date}",
        f"- personas executed: {personas}",
        "",
        # FR-932: copied from the block the personas saw, never recomputed.
        *([prior_art_block, ""] if prior_art_block else []),
        "| " + " | ".join(TABLE_COLUMNS) + " |",
        "|" + "---|" * len(TABLE_COLUMNS),
    ]
    for row in rows:
        class_cell = row.solution_class
        count = class_counts.get(row.solution_class, 0)
        if count >= 2:
            class_cell = f"{class_cell} (convergent x{count})"
        lines.append(
            "| "
            + " | ".join(
                (
                    _cell(row.candidate),
                    _cell(row.persona),
                    _cell(class_cell),
                    _cell(row.verdict),
                    _cell(row.precedent),
                    _cell(row.is_this_a_graph),
                    _cell(row.effort_risk),
                    _cell(row.rationale),
                )
            )
            + " |"
        )
    lines.append("")
    artifact.write_text("\n".join(lines), encoding="utf-8")
    return {
        "artifact": str(artifact),
        "rows": len(rows),
        "non_echo_rows": statuses.count(
            "traceable"
        ),  # Advisory only (FR-896 R-2): distinct classes reported, never gated.
        "classes": len(class_counts),
    }


def write_alternatives(state: dict[str, Any]) -> dict[str, dict]:
    """Graph node wrapper for reduce_findings."""
    return {
        "result": reduce_findings(
            state["findings"],
            state["brief_path"],
            base_dir=state.get("base_dir", "."),
            librarian_tool_results=state.get("librarian_tool_results"),
            repo_root=state.get("repo_root", "."),
            prior_art_block=extract_prior_art_block(state.get("committed_context", "")),
        )
    }
