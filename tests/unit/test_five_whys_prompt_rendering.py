"""Condemning test: five-whys demo prompts mix simple ``{var}`` placeholders
with Jinja2 blocks.

``format_prompt`` auto-detects Jinja2 when ``{%``/``{{`` is present, so a
bare ``{problem}`` in the same template is rendered LITERALLY — the model
never sees the problem statement. Witnessed by the FR-853 demo-gate run:
five-whys returned "Problem statement not provided." despite
``--var problem=...`` reaching state (plausible_wrong_answer, exit 0).
"""

from pathlib import Path

import pytest
import yaml

from yamlgraph.executor_base import format_prompt

PROMPTS_DIR = (
    Path(__file__).resolve().parents[2] / "examples" / "demos" / "five-whys" / "prompts"
)

PROBLEM = "The nightly backup job silently stopped running last week"


def _user_template(name: str) -> str:
    return yaml.safe_load((PROMPTS_DIR / f"{name}.yaml").read_text(encoding="utf-8"))["user"]


@pytest.mark.req("REQ-YG-013")
def test_ask_why_prompt_renders_problem_statement():
    """The rendered ask_why prompt must contain the actual problem text."""
    rendered = format_prompt(
        _user_template("ask_why"),
        {"problem": PROBLEM, "iteration": 1, "previous": None},
    )
    assert "{problem}" not in rendered, "simple placeholder leaked through Jinja2"
    assert PROBLEM in rendered


@pytest.mark.req("REQ-YG-013")
def test_summarise_prompt_renders_problem_statement():
    """The rendered summarise prompt must contain the actual problem text."""
    rendered = format_prompt(
        _user_template("summarise"),
        {
            "problem": PROBLEM,
            "analysis": {"chain": ["because reasons"], "answer": "x"},
        },
    )
    assert "{problem}" not in rendered, "simple placeholder leaked through Jinja2"
    assert PROBLEM in rendered
