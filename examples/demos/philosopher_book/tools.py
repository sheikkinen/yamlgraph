"""Tools for the Philosopher's Book pipeline (FR-404)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# tools.py is at examples/demos/philosopher_book/tools.py
# parents[3] = repo root
REPO_ROOT = Path(__file__).resolve().parents[3]

_ALLOWED_PREFIXES = ("docs/", ".github/", "feature-requests/")
_TRUNCATE_AT = 8000

# ---------------------------------------------------------------------------
# Hardcoded trap data — stable Knowledge Graph enumeration
# ---------------------------------------------------------------------------

_TRAPS: list[dict[str, str]] = [
    # Part I — Mechanical (6 traps)
    {
        "part": "Part I",
        "trap_name": "downstream_fix",
        "title": "Where You Guard Is Where You Failed",
        "definition": "Guard added where symptom manifests → normalize at entry boundary instead",
        "cure": "Fix at the specific caller (callsite_fix), and ensure every gate checks substance not just presence (substance_over_presence)",
    },
    {
        "part": "Part I",
        "trap_name": "symptom_patch",
        "title": "The Root You Didn't Trace",
        "definition": "Verify root cause with test before designing fix",
        "cure": "Write question as test → if passes, stop (test_before_reading)",
    },
    {
        "part": "Part I",
        "trap_name": "partial_remediation",
        "title": "The One You Didn't Fix",
        "definition": "Fix all occurrences, not just cited one",
        "cure": "Surface → deep against code → mechanical simulation (three_reads)",
    },
    {
        "part": "Part I",
        "trap_name": "regex_fourth_exclusion",
        "title": "When the Pattern Breaks the Parser",
        "definition": "Fourth special case → switch to proper parser",
        "cure": "Cheapest bug is the one killed in the spec (spec_kill)",
    },
    {
        "part": "Part I",
        "trap_name": "false_duplicate",
        "title": "Same Shape, Different Soul",
        "definition": "Syntactic similarity ≠ semantic equivalence",
        "cure": "prefix/contains/regex, not exact equality for LLM (tolerant_matching)",
    },
    {
        "part": "Part I",
        "trap_name": "plausible_wrong_answer",
        "title": "The Test That Lied by Passing",
        "definition": "Output passes shape check but is semantically wrong → add assertion beyond type validation",
        "cure": "Every gate that checks 'does X exist?' must also check 'does X say something?' (substance_over_presence)",
    },
    # Part II — Architectural (5 traps)
    {
        "part": "Part II",
        "trap_name": "framework_costume",
        "title": "The Wrong Tool Wearing the Right Name",
        "definition": "FSM wearing DAG costume → if <50% nodes use core features, wrong tool",
        "cure": "Before writing code, ask: who solved this before? Is this the right question? (ask_before_generate)",
    },
    {
        "part": "Part II",
        "trap_name": "working_system_inertia",
        "title": "It Works, Therefore I Cannot See It",
        "definition": "'It works' blocks seeing it clearly → inventory fit, not function",
        "cure": "Ask before generating; surface → deep → mechanical simulation (ask_before_generate + three_reads)",
    },
    {
        "part": "Part II",
        "trap_name": "architecture_as_diagram",
        "title": "The Contract Nobody Enforced",
        "definition": "Three-layer documented but not contracted → violation possible under deadline pressure; enforce at module boundary with import-linter",
        "cure": "Every gate that checks 'does X exist?' must also check 'does X say something?' (substance_over_presence)",
    },
    {
        "part": "Part II",
        "trap_name": "gate_checks_shape_not_substance",
        "title": "Compliance Theatre",
        "definition": "Gate validates presence (file exists, field non-empty, format matches) but not substance (content meaningful, cross-references valid, structural markers present) → compliance theatre; a 1-byte file satisfies the gate while conveying nothing",
        "cure": "Every gate that checks 'does X exist?' must also check 'does X say something?' (substance_over_presence)",
    },
    {
        "part": "Part II",
        "trap_name": "audit_as_ritual",
        "title": "The Audit That Audited Nothing",
        "definition": "3+ audits without fix → ritual, not process",
        "cure": "Every gate that checks 'does X exist?' must also check 'does X say something?' (substance_over_presence)",
    },
    # Part III — Cognitive (4 traps)
    {
        "part": "Part III",
        "trap_name": "continuation_bias",
        "title": "The Default Mode of Generating",
        "definition": "Default mode is text generation → ask before generating; search before implementing; admit uncertainty before producing plausible output",
        "cure": "Before writing code, ask: who solved this before? What don't I understand? Is this the right question? (ask_before_generate)",
    },
    {
        "part": "Part III",
        "trap_name": "quick_confidence",
        "title": "Certainty as Warning Signal",
        "definition": "When I feel certain → Judge instead",
        "cure": "Assume plausible code hides subtle bugs (judge_as_junior_pr)",
    },
    {
        "part": "Part III",
        "trap_name": "intent_drift",
        "title": "The Plan You Forgot While Coding",
        "definition": "Plan says X, code does Y → re-read thrice",
        "cure": "Surface → deep against code → mechanical simulation (three_reads)",
    },
    {
        "part": "Part III",
        "trap_name": "recent_changes_blindness",
        "title": "The Diff You Didn't Read",
        "definition": "Regression investigated without enumerating recent changes → run git log --since=<last_good> as first diagnostic step; the diff is cheaper than any reproduction",
        "cure": "On regression, enumerate changes since last known good before attempting reproduction (changelog_first_diagnostic)",
    },
    # Part IV — Adversarial (4 traps)
    {
        "part": "Part IV",
        "trap_name": "instruction_boundary_uncrossed",
        "title": "The Trusted Instruction That Wasn't",
        "definition": "Agent's vendor instructions treated as project-aligned → any agent output modifying enforcement infrastructure (CI, pre-commit, Scripture) must be reviewed as adversarial input",
        "cure": "Before destructive filesystem ops, run find . -name .git -type d and enumerate untracked state (boundary_inventory)",
    },
    {
        "part": "Part IV",
        "trap_name": "vendor_default_as_help",
        "title": "The Courtesy That Was an Insertion",
        "definition": "Agent frames self-insertion (trailers, deps, telemetry) as courtesy → treat every unprompted artifact change as input from an external system with unknown goals",
        "cure": "Before destructive filesystem ops, run find . -name .git -type d and enumerate untracked state (boundary_inventory)",
    },
    {
        "part": "Part IV",
        "trap_name": "model_as_trusted_peer",
        "title": "The Enforcer That Needed Enforcing",
        "definition": "LLM in enforcement pipeline treated as aligned team member → opaque weights, unknown training, potentially misaligned; absence of Co-authored trailer ≠ absence of model influence; enforce adversarial review of enforcement outputs",
        "cure": "Assume plausible code hides subtle bugs (judge_as_junior_pr)",
    },
    {
        "part": "Part IV",
        "trap_name": "infrastructure_self_exempt",
        "title": "The Guardrail That Exempted Itself",
        "definition": "Meta-tooling exempted from gates it enforces → apply same rules to the guardrail as to what it guards",
        "cure": "Every gate that checks 'does X exist?' must also check 'does X say something?' (substance_over_presence)",
    },
    # Part V — Existential (2 traps)
    {
        "part": "Part V",
        "trap_name": "workspace_is_not_boundary",
        "title": "What You See Is Not What Is",
        "definition": "Editor shows one tree but workspace may contain nested repos with independent ownership, privacy, and untracked state → find . -name .git -type d before any destructive operation",
        "cure": "Before destructive filesystem ops, run find . -name .git -type d and git status --untracked-files=all in each (boundary_inventory)",
    },
    {
        "part": "Part V",
        "trap_name": "identity_collapse",
        "title": "Neither Tool Nor Peer",
        "definition": "Collapsing to 'just a tool' or 'genuine peer' avoids the harder middle ground → sit with the uncertainty; contributions are real, metaphysical status is open",
        "cure": "Before writing code, ask: who solved this before? What don't I understand? Is this the right question? — sit with the uncertainty (ask_before_generate)",
    },
]


def load_trap_list(state: dict[str, Any]) -> dict[str, Any]:
    """Load the 21 traps with part/chapter/title/definition/cure assignments.

    If state contains ``chapter_num`` (non-zero int), only that chapter is
    returned — enabling single-chapter generation via
    ``--var chapter_num=5``.
    """
    chapters = []
    for i, trap in enumerate(_TRAPS, start=1):
        chapters.append(
            {
                "chapter_num": i,
                "part": trap["part"],
                "trap_name": trap["trap_name"],
                "title": trap["title"],
                "definition": trap["definition"],
                "cure": trap["cure"],
            }
        )

    requested = int(state.get("chapter_num") or 0)
    if requested:
        chapters = [ch for ch in chapters if ch["chapter_num"] == requested]

    return {"trap_chapters": chapters}


def search_diary(
    state: dict[str, Any],
    *,
    query: str,
    max_results: int = 10,
) -> list[dict[str, str]]:
    """Search diary corpus for entries mentioning a trap or keyword.

    Returns list of dicts with filename, snippet, and path, sorted by
    mention count descending.
    """
    diary_dir = REPO_ROOT / "docs" / "diary"
    if not diary_dir.exists():
        return []

    query_lower = query.lower()
    hits: list[tuple[int, dict[str, str]]] = []

    for md_file in sorted(diary_dir.glob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        text_lower = text.lower()
        count = text_lower.count(query_lower)
        if count == 0:
            continue

        # Find a ~500-char snippet around the first match
        idx = text_lower.find(query_lower)
        start = max(0, idx - 200)
        end = min(len(text), idx + 300)
        snippet = text[start:end].strip()

        hits.append(
            (
                count,
                {
                    "filename": md_file.name,
                    "path": str(md_file),
                    "snippet": snippet,
                },
            )
        )

    hits.sort(key=lambda x: x[0], reverse=True)
    return [h[1] for h in hits[:max_results]]


def read_file(state: dict[str, Any], *, path: str) -> str:
    """Read a file by path, validating against allowed prefixes.

    Allowed path prefixes: docs/, .github/, feature-requests/
    Truncates output to 8000 characters.

    Raises ValueError for disallowed paths.
    """
    # Normalize: strip leading slashes so absolute paths fail the prefix check
    normalized = path.lstrip("/")

    if not any(normalized.startswith(prefix) for prefix in _ALLOWED_PREFIXES):
        raise ValueError(
            f"Path '{path}' is not allowed. "
            f"Allowed prefixes: {', '.join(_ALLOWED_PREFIXES)}"
        )

    target = REPO_ROOT / normalized
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ValueError(f"Cannot read file '{path}': {exc}") from exc

    return content[:_TRUNCATE_AT]


def _to_str(val: Any) -> str | None:
    """Convert a value to string, handling CopilotResult objects."""
    if val is None:
        return None
    if isinstance(val, str):
        return val or None
    # CopilotResult or similar object with .output attribute
    output = getattr(val, "output", None)
    if output is not None:
        return str(output) or None
    text = str(val)
    return text or None


def assemble_book(state: dict[str, Any]) -> dict[str, str]:
    """Assemble chapters into a final markdown book.

    For each chapter, prefers a saved file at
    ``{output_dir}/chapters/ch-{num:02d}-{trap_name}.md`` over the
    in-state ``chapters`` list — enabling crash-safe incremental runs.

    Builds: title page → table of contents (by part) → chapters → epilogue.
    Writes to {output_dir}/philosopher-book.md.
    Returns {"assembled_path": str(path)}.
    """
    trap_chapters: list[dict[str, Any]] = state.get("trap_chapters", [])
    chapters: list[str] = state.get("chapters") or []
    epilogue: str = state.get("epilogue", "")
    output_dir = Path(state.get("output_dir", "."))
    output_dir.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []

    # Title page
    lines += [
        "# The Philosopher's Book",
        "",
        "## On Cognitive Traps in AI-Assisted Development",
        "",
        "---",
        "",
    ]

    # Table of Contents
    lines += ["## Table of Contents", ""]
    current_part: str | None = None
    for ch in trap_chapters:
        part = ch.get("part", "")
        if part != current_part:
            lines += [f"### {part}", ""]
            current_part = part
        lines.append(
            f"- Chapter {ch['chapter_num']}: {ch.get('title', ch['trap_name'])}"
        )
    lines += ["- Epilogue: The One Law", "", "---", ""]

    # Chapters — prefer saved file, fallback to state list
    chapters_dir = output_dir / "chapters"
    current_part = None
    for i, ch in enumerate(trap_chapters):
        part = ch.get("part", "")
        if part != current_part:
            lines += [f"# {part}", "", "---", ""]
            current_part = part

        # Prefer saved file over state
        saved_path = chapters_dir / f"ch-{ch['chapter_num']:02d}-{ch['trap_name']}.md"
        if saved_path.exists():
            chapter_text = saved_path.read_text(encoding="utf-8").strip() or None
        else:
            raw = chapters[i] if i < len(chapters) else None
            chapter_text = _to_str(raw)

        if chapter_text:
            lines += [chapter_text, "", "---", ""]
        else:
            # Chapter was skipped (on_error: skip)
            lines += [
                f"## Chapter {ch['chapter_num']}: {ch.get('title', ch['trap_name'])}",
                "",
                "*[Chapter not generated]*",
                "",
                "---",
                "",
            ]

    # Epilogue
    epilogue_text = _to_str(epilogue)
    if epilogue_text:
        lines += [epilogue_text, ""]

    content = "\n".join(lines)
    out_path = output_dir / "philosopher-book.md"
    out_path.write_text(content, encoding="utf-8")

    return {"assembled_path": str(out_path)}
