"""Tests for FR-237: Document Race and Pipeline Node Types.

Verifies that reference docs include dedicated sections for type: race (FR-232)
and type: pipeline (FR-235) so graph authors can discover them.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GETTING_STARTED = REPO_ROOT / "reference" / "getting-started.md"
GRAPH_YAML_REF = REPO_ROOT / "reference" / "graph-yaml.md"


# ---------------------------------------------------------------------------
# AC-1: getting-started.md node type table includes race and pipeline
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-240")
class TestGettingStartedNodeTable:
    """Verify reference/getting-started.md lists race and pipeline."""

    def test_race_row_exists(self):
        content = GETTING_STARTED.read_text(encoding="utf-8")
        assert (
            "| `race`" in content
        ), "getting-started.md node type table must include a race row"

    def test_pipeline_row_exists(self):
        content = GETTING_STARTED.read_text(encoding="utf-8")
        assert (
            "| `pipeline`" in content
        ), "getting-started.md node type table must include a pipeline row"


# ---------------------------------------------------------------------------
# AC-2: graph-yaml.md has type: race section
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-240")
class TestGraphYamlRaceSection:
    """Verify reference/graph-yaml.md has a dedicated type: race section."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = GRAPH_YAML_REF.read_text(encoding="utf-8")

    def test_race_heading_exists(self):
        assert (
            "### `type: race`" in self.content
        ), "graph-yaml.md must have a ### type: race heading"

    def test_race_candidates_documented(self):
        assert (
            "candidates" in self.content.split("### `type: race`")[1].split("###")[0]
        ), "race section must document candidates config key"

    def test_race_timeout_documented(self):
        assert (
            "timeout" in self.content.split("### `type: race`")[1].split("###")[0]
        ), "race section must document timeout config key"

    def test_race_winner_metadata_documented(self):
        assert (
            "_race_winner" in self.content.split("### `type: race`")[1].split("###")[0]
        ), "race section must document _race_winner state output"

    def test_race_error_handling_documented(self):
        race_section = self.content.split("### `type: race`")[1].split("###")[0]
        assert (
            "on_error" in race_section or "error" in race_section.lower()
        ), "race section must document error handling behavior"

    def test_race_example_yaml(self):
        race_section = self.content.split("### `type: race`")[1].split("###")[0]
        assert "type: race" in race_section, "race section must include a YAML example"


# ---------------------------------------------------------------------------
# AC-3: graph-yaml.md has type: pipeline section
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-240")
class TestGraphYamlPipelineSection:
    """Verify reference/graph-yaml.md has a dedicated type: pipeline section."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = GRAPH_YAML_REF.read_text(encoding="utf-8")

    def test_pipeline_heading_exists(self):
        assert (
            "### `type: pipeline`" in self.content
        ), "graph-yaml.md must have a ### type: pipeline heading"

    def test_pipeline_items_documented(self):
        assert (
            "items" in self.content.split("### `type: pipeline`")[1].split("###")[0]
        ), "pipeline section must document items config key"

    def test_pipeline_stages_documented(self):
        assert (
            "stages" in self.content.split("### `type: pipeline`")[1].split("###")[0]
        ), "pipeline section must document stages config key"

    def test_pipeline_expansion_documented(self):
        pipeline_section = self.content.split("### `type: pipeline`")[1].split("###")[0]
        assert (
            "expand" in pipeline_section.lower()
            or "concrete" in pipeline_section.lower()
        ), "pipeline section must document expansion semantics"

    def test_pipeline_interpolation_documented(self):
        pipeline_section = self.content.split("### `type: pipeline`")[1].split("###")[0]
        assert (
            "{item." in pipeline_section
        ), "pipeline section must document {item.field} interpolation"

    def test_pipeline_example_yaml(self):
        pipeline_section = self.content.split("### `type: pipeline`")[1].split("###")[0]
        assert (
            "type: pipeline" in pipeline_section
        ), "pipeline section must include a YAML example"


# ---------------------------------------------------------------------------
# AC-4: Examples match demo YAMLs
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-240")
class TestExamplesMatchDemos:
    """Verify doc examples match the actual demo graph YAMLs."""

    def test_race_candidates_match_demo(self):
        """Race section must include candidates from the demo YAML."""
        demo = (REPO_ROOT / "examples" / "demos" / "race" / "graph.yaml").read_text(encoding="utf-8")
        doc = GRAPH_YAML_REF.read_text(encoding="utf-8")
        race_section = doc.split("### `type: race`")[1].split("###")[0]
        # The demo uses mistral-small-latest, gpt-4o-mini, gemini-2.0-flash
        for model in ["mistral-small-latest", "gpt-4o-mini", "gemini-2.0-flash"]:
            assert (
                model in race_section or model in demo
            ), f"race example should reference demo models (missing {model})"

    def test_pipeline_items_match_demo(self):
        """Pipeline section must include items from the demo YAML."""
        doc = GRAPH_YAML_REF.read_text(encoding="utf-8")
        pipeline_section = doc.split("### `type: pipeline`")[1].split("###")[0]
        # The demo uses sun, moon items with draft/polish stages
        assert (
            "draft" in pipeline_section
        ), "pipeline example should include draft stage"
        assert (
            "polish" in pipeline_section
        ), "pipeline example should include polish stage"
