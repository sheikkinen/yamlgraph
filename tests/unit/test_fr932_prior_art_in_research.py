"""FR-932: prior-art retrieval reaches the personas, and the record says so.

The route validated that a cited FR *exists*, never that it was *found*.
Across all thirteen research runs before this FR, 20 of 35 cited repo
identifiers were already written in the brief by the author and 11 more
were CAP ids from committed_context — four novel FR identifiers total,
because the personas were never shown the directory FRs live in.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NODES = REPO_ROOT / "examples" / "demos" / "research-route" / "nodes"


def _load_research_tools():
    spec = importlib.util.spec_from_file_location(
        "research_tools_fr932", NODES / "research_tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rt = _load_research_tools()


def _fake_repo(tmp_path: Path, fr_files: dict[str, str]) -> Path:
    """Minimal repo root satisfying collect_committed_context's readers."""
    (tmp_path / "capabilities").mkdir()
    (tmp_path / "capabilities" / "CAP-01-thing.yaml").write_text(
        "id: CAP-01\nname: Thing\n", encoding="utf-8"
    )
    (tmp_path / "ARCHITECTURE.md").write_text(
        "# Architecture\n## State\n", encoding="utf-8"
    )
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "copilot-instructions.md").write_text(
        'traps:\n  some_trap: "x"\ncures:\n  some_cure: "y"\n', encoding="utf-8"
    )
    fr_dir = tmp_path / "feature-requests"
    fr_dir.mkdir()
    for name, body in fr_files.items():
        (fr_dir / name).write_text(body, encoding="utf-8")
    briefs = fr_dir / "research-briefs"
    briefs.mkdir()
    return tmp_path


@pytest.mark.req("REQ-YG-623")
def test_context_carries_prior_art_section(tmp_path: Path) -> None:
    """AC-03: the personas are shown the FR corpus, not just CAP one-liners."""
    root = _fake_repo(
        tmp_path,
        {
            "FR-700-precedent-retrieval-grounding.md": (
                "# FR-700 Precedent Retrieval\n**Status:** Completed\n"
                "## Summary\nPrecedent retrieval grounding.\n"
            ),
            "FR-701-unrelated-widget.md": "# FR-701\n**Status:** Completed\nWidget.\n",
        },
    )
    brief = root / "feature-requests" / "research-briefs" / "precedent-retrieval.md"
    brief.write_text("# brief\n", encoding="utf-8")

    out = rt.collect_committed_context(str(root), str(brief))

    assert "### Prior art retrieved" in out
    assert "FR-700-precedent-retrieval-grounding.md" in out
    assert "[Completed]" in out


@pytest.mark.req("REQ-YG-623")
def test_prior_art_searches_fr_corpus_not_brief_directory(tmp_path: Path) -> None:
    """AC-03: the synthetic query path scopes retrieval to feature-requests/."""
    root = _fake_repo(
        tmp_path,
        {"FR-700-precedent-retrieval.md": "# FR-700\n**Status:** Completed\nx\n"},
    )
    briefs = root / "feature-requests" / "research-briefs"
    # A tempting same-noun neighbour in the brief's own directory.
    (briefs / "precedent-retrieval-decoy.md").write_text(
        "# decoy\nprecedent retrieval\n", encoding="utf-8"
    )
    brief = briefs / "precedent-retrieval.md"
    brief.write_text("# brief\n", encoding="utf-8")

    out = rt.collect_committed_context(str(root), str(brief))

    assert "FR-700-precedent-retrieval.md" in out
    assert "decoy" not in out


@pytest.mark.req("REQ-YG-623")
def test_rejected_precedent_is_visible_to_personas(tmp_path: Path) -> None:
    """AC-04: a REJECTED FR is precedent — the rule the Judge enforces."""
    root = _fake_repo(
        tmp_path,
        {
            "FR-070-gui-web-playground.md": (
                "# FR-070 Web Playground\n**Status:** Rejected\n"
                "## Summary\nA web playground.\n"
            )
        },
    )
    brief = root / "feature-requests" / "research-briefs" / "web-playground.md"
    brief.write_text("# brief\n", encoding="utf-8")

    out = rt.collect_committed_context(str(root), str(brief))

    assert "FR-070-gui-web-playground.md" in out
    assert "[REJECTED]" in out


@pytest.mark.req("REQ-YG-623")
def test_empty_retrieval_is_reported_not_omitted(tmp_path: Path) -> None:
    """AC-05: a genuine zero is stated, so `none-retrieved` rows are bounded."""
    root = _fake_repo(
        tmp_path, {"FR-700-widget.md": "# FR-700\n**Status:** Completed\nx\n"}
    )
    brief = root / "feature-requests" / "research-briefs" / "xyzzy-plugh.md"
    brief.write_text("# brief\n", encoding="utf-8")

    out = rt.collect_committed_context(str(root), str(brief))

    assert "### Prior art retrieved" in out
    assert rt.NONE_RETRIEVED in out


@pytest.mark.req("REQ-YG-623")
def test_context_stays_within_bound_with_full_block(tmp_path: Path) -> None:
    """AC-06: the existing overflow guard still fires with the block added."""
    root = _fake_repo(
        tmp_path,
        {
            f"FR-{700 + i}-precedent-retrieval-note.md": (
                f"# FR-{700 + i} Precedent Retrieval\n**Status:** Completed\nx\n"
            )
            for i in range(8)
        },
    )
    brief = root / "feature-requests" / "research-briefs" / "precedent-retrieval.md"
    brief.write_text("# brief\n", encoding="utf-8")

    out = rt.collect_committed_context(str(root), str(brief))
    assert len(out.splitlines()) <= rt._MAX_CONTEXT_LINES

    huge = "\n".join(f"## H{i}" for i in range(rt._MAX_CONTEXT_LINES + 10))
    (root / "ARCHITECTURE.md").write_text(huge, encoding="utf-8")
    with pytest.raises(ValueError, match="exceeds bound"):
        rt.collect_committed_context(str(root), str(brief))


@pytest.mark.req("REQ-YG-623")
def test_prior_art_section_is_extracted_verbatim() -> None:
    """AC-07: one computation, copied — never recomputed at reduce time."""
    context = (
        "## Committed context (deterministic, author-independent)\n"
        "\n"
        "### Capability registry (CAP one-liners)\n"
        "CAP-01 Thing\n"
        "\n"
        "### Prior art retrieved for this brief (filename-noun, IDF-ranked)\n"
        "  FR-700-thing.md  [Completed]  matches: thing\n"
        "\n"
        "### Scripture trap/cure keys\n"
        "some_trap\n"
    )

    block = rt.extract_prior_art_block(context)

    assert block == (
        "### Prior art retrieved for this brief (filename-noun, IDF-ranked)\n"
        "  FR-700-thing.md  [Completed]  matches: thing"
    )


def _finding(persona: str, precedent: str) -> dict:
    return {
        "candidate": f"candidate for {persona}",
        "persona": persona,
        "solution_class": "process-boundary",
        "verdict": "pursue",
        "precedent": precedent,
        "is_this_a_graph": "no - single deterministic step",
        "effort_risk": "low / low",
        "rationale": "a rationale long enough to be meaningful",
    }


@pytest.mark.req("REQ-YG-623")
def test_none_retrieved_requires_an_empty_retrieval_header(tmp_path: Path) -> None:
    """AC-08: the honest-miss token is bounded by what retrieval actually did."""
    root = _fake_repo(tmp_path, {})

    assert (
        rt._classify_precedent(rt.NONE_RETRIEVED, root, prior_art_empty=True)
        == "grounded-empty"
    )
    with pytest.raises(ValueError, match="none-retrieved"):
        rt._classify_precedent(rt.NONE_RETRIEVED, root, prior_art_empty=False)


@pytest.mark.req("REQ-YG-623")
def test_brief_echo_is_rejected_in_new_artifacts(tmp_path: Path) -> None:
    """AC-08: restating the brief as its own precedent no longer passes."""
    root = _fake_repo(tmp_path, {})

    with pytest.raises(ValueError, match="brief-echo"):
        rt._classify_precedent(
            f"{rt.ECHO_MARKER}: the brief says so", root, prior_art_empty=True
        )


@pytest.mark.req("REQ-YG-623")
def test_grounded_empty_counts_toward_the_grounding_threshold(tmp_path: Path) -> None:
    """AC-08: an honest no-hit run must not be pushed into fabrication.

    FR-896 raises below three non-echo findings. If `none-retrieved` were
    treated as an echo, a genuinely empty corpus would fail the run and
    make inventing a citation the cheaper option.
    """
    root = _fake_repo(tmp_path, {})
    findings = [
        _finding("os-infra-primitivist", rt.NONE_RETRIEVED),
        _finding("data-process-planner", rt.NONE_RETRIEVED),
        _finding("yamlgraph-native-planner", rt.NONE_RETRIEVED),
    ]

    rows, statuses = rt._validate_findings(findings, root, None, prior_art_empty=True)

    assert len(rows) == 3
    assert statuses == ["grounded-empty"] * 3


@pytest.mark.req("REQ-YG-623")
def test_prose_only_precedent_still_fails(tmp_path: Path) -> None:
    """AC-08: the three permitted forms are exhaustive."""
    root = _fake_repo(tmp_path, {})

    with pytest.raises(ValueError):
        rt._classify_precedent(
            "we looked and there is definitely prior work", root, prior_art_empty=True
        )


@pytest.mark.req("REQ-YG-623")
def test_frozen_schema_is_untouched() -> None:
    """AC-09: no new column, no widened enum."""
    assert rt.TABLE_COLUMNS == (
        "candidate",
        "persona",
        "class",
        "verdict",
        "precedent",
        "is_this_a_graph",
        "effort-risk",
        "rationale",
    )
    assert frozenset({"pursue", "dissent", "duplicate"}) == rt.MODEL_VERDICTS
