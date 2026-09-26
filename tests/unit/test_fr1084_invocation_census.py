"""FR-1084 AC-08..AC-10: documented `graph run` invocations vs compiled input schemas."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "fr1084" / "census.py"
_SPEC = importlib.util.spec_from_file_location("fr1084_census", _PATH)
census = importlib.util.module_from_spec(_SPEC)
sys.modules["fr1084_census"] = census
_SPEC.loader.exec_module(census)

FR_PATTERN = re.compile(r"^FR-\d+$")

pytestmark = pytest.mark.process


@pytest.fixture(scope="module")
def rows() -> list[census.Row]:
    return census.resolve(census.extract())


@pytest.mark.req("REQ-YG-697")
def test_ac08_census_matches_committed_extracted_list(rows):
    committed = census.INVOCATIONS_PATH.read_text(encoding="utf-8")
    assert census.render(rows) == committed, (
        "stale evidence: run python tests/fixtures/fr1084/census.py"
    )


@pytest.mark.req("REQ-YG-697")
def test_ac08_scope_covers_the_four_frozen_surfaces():
    scope = {p.relative_to(census.REPO_ROOT).as_posix() for p in census.scope_files()}
    assert {"README.md", "examples/demos/demo.sh"} <= scope
    assert any(s.startswith("reference/") for s in scope)
    assert any(s.startswith("examples/") and s.endswith("/README.md") for s in scope)


@pytest.mark.req("REQ-YG-697")
def test_ac08_row_shape_continuations_repeats_and_mechanical_reasons():
    text = "yamlgraph graph run examples/.../graph.yaml \\\n  --var a=1 --var a=2 --var $K=x\n"
    joined = census._joined_lines(text)
    assert joined[0][0] == 1
    assert "--var a=2" in joined[0][1]

    rows = census._rows_for("doc.md", 1, joined[0][1].split("graph run", 1)[1])
    assert [(r.kind, r.key, r.reason) for r in rows] == [
        ("--var", "a", "placeholder"),
        ("--var", "$K", "placeholder"),
    ]
    assert census.COLUMNS == (
        "source",
        "line",
        "graph",
        "kind",
        "key",
        "status",
        "reason",
        "fr",
    )

    shell = census._rows_for("doc.md", 3, " examples/demos/hello/graph.yaml --var $K=x")
    assert [r.reason for r in shell] == ["shell-variable"]
    missing = census._rows_for(
        "doc.md", 4, " examples/demos/hello/graph.yaml --var-file nope.yaml"
    )
    assert [(r.key, r.reason) for r in missing] == [("-", "missing-var-file")]
    gone = census._rows_for("doc.md", 5, " no/such/graph.yaml --var name=x")
    assert [r.reason for r in gone] == ["unresolvable-graph"]


@pytest.mark.req("REQ-YG-697")
def test_ac09_every_row_passes_or_is_excluded_with_reason_and_filed_fr(rows):
    feature_requests = census.REPO_ROOT / "feature-requests"
    unresolved = [r for r in rows if r.status not in ("PASS", "EXCLUDED")]
    assert unresolved == []
    for row in rows:
        if row.status != "EXCLUDED":
            continue
        assert row.reason, row
        if row.reason in census.MECHANICAL_REASONS:
            assert row.fr == "", row
            continue
        assert FR_PATTERN.match(row.fr), row
        assert list(feature_requests.glob(f"{row.fr}-*.md")), row


@pytest.mark.req("REQ-YG-697")
def test_ac09_exclusion_manifest_has_no_stale_entries(rows):
    used = {(r.source, r.graph, r.key) for r in rows if r.fr}
    assert set(census.load_exclusions()) == used


@pytest.mark.req("REQ-YG-697")
def test_ac10_innovation_matrix_domain_row_tracks_the_compiled_schema(rows):
    graph = "examples/demos/innovation_matrix/pipeline.yaml"
    domain_rows = [r for r in rows if r.graph == graph and r.key == "domain"]
    assert domain_rows
    accepted = census._accepted_keys(graph, ())
    for row in domain_rows:
        if isinstance(accepted, frozenset) and "domain" in accepted:
            assert row.status == "PASS"
        else:
            assert (row.status, row.fr) == ("EXCLUDED", "FR-1088")
