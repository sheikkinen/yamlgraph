"""RED acceptance tests for FR-421 built-in questionnaire gap utilities."""

from pathlib import Path

import pytest

from yamlgraph.compile.graph_loader import load_and_compile


@pytest.mark.req("REQ-YG-409")
class TestFR421DetectGaps:
    """Acceptance tests for detect_gaps utility contract."""

    def test_ac02_detect_gaps_returns_required_missing_ids(self) -> None:
        from yamlgraph.tools.questionnaire import detect_gaps

        state = {
            "schema": {
                "fields": [
                    {"id": "age", "required": True},
                    {"id": "name", "required": True},
                    {"id": "notes", "required": False},
                ]
            },
            "extracted": {"name": "Ada"},
        }

        result = detect_gaps(state)

        assert result == {"gaps": ["age"], "has_gaps": True}

    def test_ac03_detect_gaps_treats_none_and_empty_string_as_missing(self) -> None:
        from yamlgraph.tools.questionnaire import detect_gaps

        state = {
            "schema": {
                "fields": [
                    {"id": "a", "required": True},
                    {"id": "b", "required": True},
                ]
            },
            "extracted": {"a": None, "b": ""},
        }

        result = detect_gaps(state)

        assert result == {"gaps": ["a", "b"], "has_gaps": True}

    def test_ac04_detect_gaps_ignores_optional_and_sorts_ids(self) -> None:
        from yamlgraph.tools.questionnaire import detect_gaps

        state = {
            "schema": {
                "fields": [
                    {"id": "zeta", "required": True},
                    {"id": "alpha", "required": True},
                    {"id": "beta", "required": False},
                ]
            },
            "extracted": {},
        }

        result = detect_gaps(state)

        assert result == {"gaps": ["alpha", "zeta"], "has_gaps": True}

    def test_ac05_detect_gaps_returns_empty_when_all_required_present(self) -> None:
        from yamlgraph.tools.questionnaire import detect_gaps

        state = {
            "schema": {
                "fields": [
                    {"id": "name", "required": True},
                    {"id": "city", "required": True},
                ]
            },
            "extracted": {"name": "Ada", "city": "Helsinki"},
        }

        result = detect_gaps(state)

        assert result == {"gaps": [], "has_gaps": False}


@pytest.mark.req("REQ-YG-410")
class TestFR421NormalizeExtracted:
    """Acceptance tests for normalize_extracted utility contract."""

    def test_ac06_normalize_extracted_returns_noop_when_already_dict(self) -> None:
        from yamlgraph.tools.questionnaire import normalize_extracted

        result = normalize_extracted({"extracted": {"name": "Ada"}})

        assert result == {}

    @pytest.mark.parametrize("value", [None, "text", 123, 1.5, [], ("a",), False])
    def test_ac07_normalize_extracted_resets_when_non_dict(self, value: object) -> None:
        from yamlgraph.tools.questionnaire import normalize_extracted

        result = normalize_extracted({"extracted": value})

        assert result == {"extracted": {}}

    def test_ac08_yaml_module_wiring_compiles_and_runs_python_tool(
        self, tmp_path: Path
    ) -> None:
        graph_path = tmp_path / "graph.yaml"
        graph_path.write_text(
            """
version: "1.0"
name: fr421_questionnaire_tool_wiring

state:
  schema: dict
  extracted: dict
  gaps: list
  has_gaps: bool

tools:
  check_gaps:
    type: python
    module: yamlgraph.tools.questionnaire
    function: detect_gaps

nodes:
  detect:
    type: python
    tool: check_gaps
    state_key: gaps

edges:
  - from: START
    to: detect
  - from: detect
    to: END
""".strip()
        )

        compiled = load_and_compile(graph_path).compile()
        result = compiled.invoke(
            {
                "schema": {
                    "fields": [
                        {"id": "name", "required": True},
                        {"id": "age", "required": True},
                    ]
                },
                "extracted": {"name": "Ada"},
            }
        )

        assert result["gaps"] == ["age"]
        assert result["has_gaps"] is True


@pytest.mark.req("REQ-YG-409", "REQ-YG-410")
def test_ac01_module_exports_detect_gaps_and_normalize_extracted() -> None:
    from yamlgraph.tools.questionnaire import detect_gaps, normalize_extracted

    assert callable(detect_gaps)
    assert callable(normalize_extracted)
