"""FR-1126 — ramp_rtm is the FR-1125 showcase: the refused shape and the filled one.

RED before GREEN: the README assertions fail until the showcase section exists.
The before/after assertions pass from day one and stay as the rot guard: the
demo's pre-FR-1125 schema (kept here as a string, never committed as a prompt)
must remain refused by lint with the complete E017 message the README quotes,
and the committed prompt must remain clean and keep its five declared item
fields. Provider-sensitive witnesses set PROVIDER=anthropic explicitly
(judgement C-2); the host's environment and .env never decide the outcome.
"""

from __future__ import annotations

import copy
import re
import shutil
from pathlib import Path

import pytest

from yamlgraph.linter.graph_linter import lint_graph
from yamlgraph.schema_loader import load_schema_from_yaml

pytestmark = pytest.mark.process

REQ = "REQ-YG-712"
ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "examples" / "demos" / "ramp_rtm"
README = DEMO / "README.md"
PROMPT = DEMO / "prompts" / "derive_reqs.yaml"
ENTRY_FIELDS = {"req_id", "statement", "witness_tests", "confidence", "status"}
HEADING = "## Anthropic and open objects (FR-1125)"

# The demo's schema as committed before FR-1125 (git 2b62085e^): the `fields`
# form with an open object. Lives here so no open-object prompt sits under
# examples/ on an Anthropic-bound demo.
BEFORE_SCHEMA = """\
schema:
  name: RtmFileRequirements
  fields:
    path:
      type: str
      description: The test file path exactly as provided.
    entries:
      type: list[dict]
      description: >
        Requirement candidates supported by this file. Each item is an
        RtmEntry-shaped object with exactly these keys: req_id (neutral
        REQ-XXX-NNN placeholder), statement (test-derived requirement),
        witness_tests (list of provided test function names only),
        confidence (0.0 to 1.0), and status (exactly proposed).
      default: []
"""


@pytest.fixture(autouse=True)
def _explicit_anthropic(monkeypatch):
    """Judgement C-2: provider-sensitive witnesses set PROVIDER explicitly."""
    monkeypatch.setenv("PROVIDER", "anthropic")


def _before_copy(tmp_path: Path) -> Path:
    """A scratch copy of the demo with the pre-FR-1125 schema put back."""
    copy_dir = tmp_path / "ramp_rtm"
    shutil.copytree(DEMO, copy_dir, ignore=shutil.ignore_patterns("demo-output.log"))
    prompt = copy_dir / "prompts" / "derive_reqs.yaml"
    text = prompt.read_text(encoding="utf-8")
    head = text[: text.index("output_schema:")]
    prompt.write_text(head + BEFORE_SCHEMA, encoding="utf-8")
    return copy_dir / "graph.yaml"


def _codes(graph: Path) -> list[tuple[str, str]]:
    issues = lint_graph(graph, project_root=graph.parent).issues
    return [(i.code, i.message) for i in issues]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# README --------------------------------------------------------------------


@pytest.mark.req(REQ)
def test_readme_has_the_showcase_section() -> None:
    text = README.read_text(encoding="utf-8")
    assert HEADING in text
    for needle in (
        "E017",
        "list[dict]",
        "output_schema",
        "demo-output.log",
        "PROVIDER=anthropic yamlgraph graph lint",
        "PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 yamlgraph graph run",
        "reference/prompt-yaml.md",
    ):
        assert needle in text, f"README lacks {needle!r}"


@pytest.mark.req(REQ)
def test_readme_e017_diagnostic_equals_the_linter_message(tmp_path) -> None:
    """Judgement R-3: the README quotes the COMPLETE diagnostic; equality after
    whitespace normalisation, never a prefix and never an ellipsis."""
    text = README.read_text(encoding="utf-8")
    block = re.search(r"```text\n(\[E017\].*?)\n```", text, re.S)
    assert block, "README must quote the E017 diagnostic in a text block"
    quoted = _normalize(block.group(1))
    # The diagnostic itself contains "{...}" legitimately; truncation is caught by
    # the equality below, and an ellipsis at the END is the one shape to forbid.
    assert not quoted.endswith(("…", "..."))
    messages = [m for c, m in _codes(_before_copy(tmp_path)) if c == "E017"]
    assert len(messages) == 1
    assert quoted == _normalize("[E017] " + messages[0])


# Before is refused -----------------------------------------------------------


@pytest.mark.req(REQ)
def test_before_form_is_refused_with_e017(tmp_path) -> None:
    issues = _codes(_before_copy(tmp_path))
    e017 = [m for c, m in issues if c == "E017"]
    assert len(e017) == 1, issues
    assert "derive/node" in e017[0] and "entries.items" in e017[0]
    assert "output_schema" in e017[0]


# After is clean and full --------------------------------------------------------


@pytest.mark.req(REQ)
def test_committed_demo_is_clean() -> None:
    codes = {c for c, _ in _codes(DEMO / "graph.yaml")}
    assert not codes & {"E016", "E017", "W028", "W029"}, codes


@pytest.mark.req(REQ)
def test_committed_prompt_keeps_its_five_entry_fields() -> None:
    transform_schema = pytest.importorskip("anthropic").transform_schema
    model = load_schema_from_yaml(PROMPT)
    assert model is not None
    transformed = transform_schema(copy.deepcopy(model.model_json_schema()))
    entries = transformed["properties"]["entries"]
    if (
        "anyOf" in entries
    ):  # `default: []` makes the field optional: anyOf [array, null]
        entries = next(v for v in entries["anyOf"] if v.get("type") == "array")
    items = entries["items"]
    if "$ref" in items:
        items = transformed["$defs"][items["$ref"].rsplit("/", 1)[-1]]
    assert set(items["properties"]) == ENTRY_FIELDS
    assert set(items.get("required", [])) == ENTRY_FIELDS
    assert items.get("additionalProperties") is False
