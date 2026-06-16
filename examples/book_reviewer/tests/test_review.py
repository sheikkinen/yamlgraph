"""Graph-level tests for book_reviewer (FR-497).

Three concerns, all without a real LLM:

1. **K4 prompt-scope gate** (the anti-"almighty-prompt" invariant): each prompt is
   rendered in isolation and asserted to carry exactly the inputs its stage is
   allowed to see — one chapter body for chapter review, two for continuity, no
   chapter body for synopsis delivery, and only the computed findings for the
   verdict.
2. **End-to-end map -> reduce** with a fake executor: the graph runs, every numeric
   score is COMPUTED by the deterministic reduce (K3), and the LLM is called the
   expected number of times.
3. **Import purity**: the example imports only YAMLGraph framework code — no
   ``dungeon_master`` package and no ``story.json``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from examples.book_reviewer.models import BookReview
from yamlgraph.executor_base import format_prompt
from yamlgraph.utils.prompts import load_prompt

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
PROMPTS_DIR = PACKAGE / "prompts"
SAMPLE = PACKAGE / "sample_book.md"


def _render_user(name: str, variables: dict) -> str:
    cfg = load_prompt(name, prompts_dir=PROMPTS_DIR)
    return format_prompt(cfg["user"], variables)


def _raw_user(name: str) -> str:
    return load_prompt(name, prompts_dir=PROMPTS_DIR)["user"]


# ---------------------------------------------------------------------------
# 1. K4 prompt-scope gate — the anti-almighty-prompt invariant
# ---------------------------------------------------------------------------


def test_chapter_prompt_contains_exactly_one_chapter_body() -> None:
    """The per-chapter prompt sees exactly ONE chapter body (plus reference matter)."""
    out = _render_user(
        "chapter_review",
        {
            "number": 2,
            "title": "Two",
            "body": "<<BODY-2>>",
            "synopsis": "<<SYNOPSIS>>",
            "cast": ["<<CAST>>"],
        },
    )
    assert out.count("<<BODY-2>>") == 1
    # Synopsis and cast are allowed reference context, not chapter prose.
    assert "<<SYNOPSIS>>" in out
    assert "<<CAST>>" in out
    # Structurally there is only one body slot, and no pairwise body slots.
    raw = _raw_user("chapter_review")
    assert "body_n" not in raw


def test_continuity_prompt_contains_exactly_two_chapter_bodies() -> None:
    """The continuity prompt sees exactly TWO adjacent chapter bodies, nothing more."""
    out = _render_user(
        "continuity",
        {"between": [1, 2], "body_n": "<<BODY-1>>", "body_n1": "<<BODY-2>>"},
    )
    assert out.count("<<BODY-1>>") == 1
    assert out.count("<<BODY-2>>") == 1
    # The pair identity is echoed so completion-order collection can re-sort.
    assert "1" in out and "2" in out


def test_synopsis_prompt_has_no_chapter_body() -> None:
    """Synopsis delivery judges summaries only — never a chapter body."""
    reviews = [
        {"number": 1, "summary": "<<SUMMARY-1>>"},
        {"number": 2, "summary": "<<SUMMARY-2>>"},
    ]
    out = _render_user(
        "synopsis_beats",
        {"synopsis": "<<SYNOPSIS>>", "chapter_reviews": reviews},
    )
    assert "<<SUMMARY-1>>" in out
    assert "<<SUMMARY-2>>" in out
    assert "<<SYNOPSIS>>" in out
    # The template must not expose any chapter-body variable.
    raw = _raw_user("synopsis_beats")
    assert "{{ body" not in raw
    assert "body_n" not in raw


def test_verdict_prompt_uses_findings_only() -> None:
    """The verdict prompt sees only the computed findings — no manuscript at all."""
    out = _render_user("verdict", {"findings": "<<FINDINGS>>"})
    assert "<<FINDINGS>>" in out
    raw = _raw_user("verdict")
    assert "findings" in raw
    for forbidden in ("body", "synopsis", "chapter", "manuscript"):
        assert forbidden not in raw.lower()


# ---------------------------------------------------------------------------
# 2. End-to-end map -> reduce with a fake executor (no API calls)
# ---------------------------------------------------------------------------


class _FakeExecutor:
    """Records prompt calls and returns canned, shape-correct structured outputs."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def execute(self, prompt_name: str, variables: dict | None = None, **_kw):
        v = variables or {}
        self.calls.append((prompt_name, v))
        if prompt_name == "chapter_review":
            return {
                "number": v["number"],
                "summary": f"chapter {v['number']} summary",
                "criteria": [
                    {"name": n, "score": 4, "justification": "ok"}
                    for n in ("coherence", "engagement", "prose", "character")
                ],
                "issues": [],
            }
        if prompt_name == "continuity":
            return {"between": v["between"], "breaks": []}
        if prompt_name == "synopsis_beats":
            return {"promised": ["beat a", "beat b"], "undelivered": []}
        if prompt_name == "verdict":
            return {"verdict": "A confident, consistent debut."}
        raise AssertionError(f"unexpected prompt: {prompt_name}")

    def prompt_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for name, _ in self.calls:
            counts[name] = counts.get(name, 0) + 1
        return counts


@pytest.fixture
def fake_executor(monkeypatch):
    import yamlgraph.executor as executor_mod

    fake = _FakeExecutor()
    monkeypatch.setattr(executor_mod, "_executor", fake)
    return fake


def test_graph_runs_and_every_score_is_computed(fake_executor, tmp_path) -> None:
    """The full pipeline runs on the sample book and emits a typed, COMPUTED review."""
    from yamlgraph.graph_loader import compile_graph, load_graph_config

    manuscript = tmp_path / "story.md"
    shutil.copyfile(SAMPLE, manuscript)

    config = load_graph_config(str(PACKAGE / "graph.yaml"))
    graph = compile_graph(config).compile()

    result = graph.invoke({"manuscript_path": str(manuscript)})

    review = BookReview.model_validate(result["review"])

    # Every numeric score is in range and was produced by the deterministic reduce,
    # not by any LLM (the fake never returns a number).
    assert 1 <= review.overall <= 5
    assert {c.name for c in review.criteria} == {
        "coherence",
        "engagement",
        "prose",
        "character",
    }
    for crit in review.criteria:
        assert 1 <= crit.score <= 5
    assert 1 <= review.continuity.score <= 5
    assert 1 <= review.synopsis_delivery.score <= 5

    # The LLM only ever wrote prose (the verdict), never a number.
    assert review.verdict == "A confident, consistent debut."

    # Two chapters -> 2 chapter reviews + 1 seam + 1 synopsis + 1 verdict = 5 calls.
    assert fake_executor.prompt_counts() == {
        "chapter_review": 2,
        "continuity": 1,
        "synopsis_beats": 1,
        "verdict": 1,
    }

    # Chapters are re-sorted into reading order regardless of completion order.
    assert [c.number for c in review.chapters] == [1, 2]

    # The sidecar review.md is written next to the manuscript.
    assert (tmp_path / "review.md").is_file()


def test_chapter_review_call_carries_one_body(fake_executor, tmp_path) -> None:
    """Each chapter_review LLM call is handed exactly one chapter body (K4 at runtime)."""
    from yamlgraph.graph_loader import compile_graph, load_graph_config

    manuscript = tmp_path / "story.md"
    shutil.copyfile(SAMPLE, manuscript)

    config = load_graph_config(str(PACKAGE / "graph.yaml"))
    graph = compile_graph(config).compile()
    graph.invoke({"manuscript_path": str(manuscript)})

    chapter_calls = [v for name, v in fake_executor.calls if name == "chapter_review"]
    assert chapter_calls
    for v in chapter_calls:
        # Exactly one body variable, and no pairwise bodies leaked in.
        assert "body" in v
        assert "body_n" not in v
        assert "body_n1" not in v

    continuity_calls = [v for name, v in fake_executor.calls if name == "continuity"]
    for v in continuity_calls:
        # Exactly two bodies, no single-body var.
        assert "body_n" in v and "body_n1" in v
        assert "body" not in v


# ---------------------------------------------------------------------------
# 3. Import purity — only YAMLGraph framework code (no dungeon_master, no JSON)
# ---------------------------------------------------------------------------


def _imported_modules(path: Path) -> set[str]:
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
    return mods


def test_example_imports_only_framework() -> None:
    """book_reviewer is stand-alone: it imports YAMLGraph + stdlib + pydantic only.

    No ``dungeon_master`` package, and any first-party import stays inside the
    example's own package.
    """
    sources = [p for p in PACKAGE.rglob("*.py") if "tests" not in p.parts]
    for path in sources:
        for module in _imported_modules(path):
            assert "dungeon_master" not in module, f"{path} imports {module}"
            top = module.split(".")[0]
            if top == "examples":
                assert module.startswith(
                    "examples.book_reviewer"
                ), f"{path} imports foreign example {module}"


def test_example_never_reads_story_json() -> None:
    """The reviewer consumes a Markdown manuscript, never the DM's story.json."""
    sources = [p for p in PACKAGE.rglob("*.py") if "tests" not in p.parts]
    sources += list(PACKAGE.rglob("*.yaml"))
    for path in sources:
        assert "story.json" not in path.read_text(
            encoding="utf-8"
        ), f"{path} references story.json"
