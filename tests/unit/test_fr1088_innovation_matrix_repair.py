"""FR-1088: innovation_matrix pipeline — declared domain, bounded grid, index-joined synthesis."""

import re
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from examples.demos.innovation_matrix.nodes.cartesian import cartesian_product
from yamlgraph.executor_base import format_prompt
from yamlgraph.linter.graph_linter import lint_graph
from yamlgraph.schema_loader import build_pydantic_model

pytestmark = pytest.mark.process

DEMO = Path(__file__).parents[2] / "examples/demos/innovation_matrix"
PIPELINE = DEMO / "pipeline.yaml"
DIMENSIONS = DEMO / "prompts/generate_dimensions.yaml"
SYNTHESIZE = DEMO / "prompts/synthesize.yaml"
CARTESIAN = DEMO / "nodes/cartesian.py"

CAPS = ["cap-a", "cap-b", "cap-c", "cap-d"]
CONS = ["con-x", "con-y", "con-z"]
IDS_4X3 = [f"C{c}S{s}" for c in range(1, 5) for s in range(1, 4)]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _pairs() -> list[dict]:
    state = {"dimensions": {"capabilities": CAPS, "constraints": CONS}}
    return cartesian_product(state)["pairs"]


def _render(expansions: list[dict]) -> str:
    return format_prompt(
        _load(SYNTHESIZE)["user"],
        {"domain": "cold-chain logistics", "pairs": _pairs(), "expansions": expansions},
    )


def _segments(text: str) -> dict[str, str]:
    """Slice the render into one segment per pair ID, in pair order."""
    starts = [text.index(pid) for pid in IDS_4X3]
    ends = [*starts[1:], len(text)]
    return {pid: text[s:e] for pid, s, e in zip(IDS_4X3, starts, ends, strict=True)}


def _rows(indices: list[int]) -> list[dict]:
    return [{"_map_index": i, "value": f"idea-{i}"} for i in indices]


def _cap_matches_schema(prompt: dict, pipeline: dict) -> bool:
    fields = prompt["schema"]["fields"]
    product = (
        fields["capabilities"]["constraints"]["max_length"]
        * fields["constraints"]["constraints"]["max_length"]
    )
    return product == pipeline["nodes"]["expand_all"]["max_items"]


@pytest.mark.req("REQ-YG-690")
def test_ids_derive_from_dimension_lengths() -> None:
    pairs = _pairs()

    assert [p["id"] for p in pairs] == IDS_4X3
    assert [(p["capability"], p["constraint"]) for p in pairs] == [
        (c, s) for c in CAPS for s in CONS
    ]


@pytest.mark.req("REQ-YG-690")
def test_dimensions_schema_bounds_each_list_to_three_to_five() -> None:
    model = build_pydantic_model(_load(DIMENSIONS)["schema"])

    with pytest.raises(ValidationError):
        model(capabilities=[f"c{i}" for i in range(6)], constraints=["s1", "s2"])
    model(
        capabilities=[f"c{i}" for i in range(5)],
        constraints=[f"s{i}" for i in range(5)],
    )
    model(capabilities=["c1", "c2", "c3"], constraints=["s1", "s2", "s3", "s4"])


@pytest.mark.req("REQ-YG-690")
def test_map_cap_equals_schema_product() -> None:
    prompt, pipeline = _load(DIMENSIONS), _load(PIPELINE)
    assert _cap_matches_schema(prompt, pipeline)

    pipeline["nodes"]["expand_all"]["max_items"] = 24
    assert not _cap_matches_schema(prompt, pipeline)


@pytest.mark.req("REQ-YG-690")
@pytest.mark.parametrize(("caps", "cons"), [([], CONS), (CAPS, [])])
def test_empty_dimension_raises_with_both_lengths(caps: list, cons: list) -> None:
    state = {"dimensions": {"capabilities": caps, "constraints": cons}}

    with pytest.raises(ValueError) as excinfo:
        cartesian_product(state)
    numbers = set(re.findall(r"\d+", str(excinfo.value)))
    assert {str(len(caps)), str(len(cons))} <= numbers


@pytest.mark.req("REQ-YG-690")
def test_synthesis_renders_every_cell_when_complete() -> None:
    text = _render(_rows(list(range(12))))

    assert "12 of 12" in text
    assert "MISSING" not in text
    for i, (pid, segment) in enumerate(_segments(text).items()):
        assert f"idea-{i}" in segment, pid


@pytest.mark.req("REQ-YG-690")
def test_synthesis_marks_only_the_absent_index_missing() -> None:
    text = _render(_rows([i for i in range(12) if i != 7]))

    assert "11 of 12" in text
    segments = _segments(text)
    assert "MISSING" in segments["C3S2"]
    assert [pid for pid, seg in segments.items() if "MISSING" in seg] == ["C3S2"]
    assert "idea-8" in segments["C3S3"]


@pytest.mark.req("REQ-YG-690")
def test_synthesis_refuses_to_pick_between_duplicate_indices() -> None:
    rows = _rows(list(range(12)))
    rows[7]["value"] = "dup-a"
    rows.append({"_map_index": 7, "value": "dup-b"})
    text = _render(rows)

    segments = _segments(text)
    assert "DUPLICATE" in segments["C3S2"]
    assert "dup-a" not in text
    assert "dup-b" not in text
    assert [pid for pid, seg in segments.items() if "DUPLICATE" in seg] == ["C3S2"]


@pytest.mark.req("REQ-YG-690")
def test_no_stale_literal_cell_count() -> None:
    assert not re.search(r"\b25\b", SYNTHESIZE.read_text(encoding="utf-8"))
    assert not re.search(r"\b25\b", CARTESIAN.read_text(encoding="utf-8"))
    pipeline_25 = [
        line
        for line in PIPELINE.read_text(encoding="utf-8").splitlines()
        if re.search(r"\b25\b", line)
    ]
    assert [line.strip() for line in pipeline_25] == ["max_items: 25"]


@pytest.mark.req("REQ-YG-690")
def test_pipeline_lints_without_errors() -> None:
    result = lint_graph(PIPELINE)

    errors = [i for i in result.issues if i.severity == "error"]
    assert errors == [], [i.message for i in errors]
    assert not [i for i in result.issues if i.code == "E007"]
