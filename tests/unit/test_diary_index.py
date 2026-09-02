"""FR-254 Diary Index Graph — unit tests.

Tests for the diary-index demo: aggregate_index() ground-truth fixture,
graph YAML loading/linting, list_diary_files() structure, write_index() output.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
import pytest
import yaml

pytestmark = pytest.mark.process

DEMO_DIR = Path("examples/demos/diary_index")
GRAPH_PATH = DEMO_DIR / "graph.yaml"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Ground-truth fixture: 5 diary entries with known extractions
# ---------------------------------------------------------------------------
FIXTURE_EXTRACTIONS = [
    {
        "filename": "2026-01-10-reflection.md",
        "date": "2026-01-10",
        "title": "Quick Confidence Trap",
        "traps": ["quick_confidence", "downstream_fix"],
        "heuristics": ["test_before_reading"],
        "seeds": ["Can we auto-detect quick_confidence in PR reviews?"],
        "fr_references": ["FR-100"],
        "category": "reflection",
    },
    {
        "filename": "2026-01-15-audit.md",
        "date": "2026-01-15",
        "title": "Audit of Error Handling",
        "traps": ["downstream_fix", "symptom_patch"],
        "heuristics": ["test_before_reading", "tolerant_matching"],
        "seeds": [],
        "fr_references": ["FR-100", "FR-110"],
        "category": "audit",
    },
    {
        "filename": "2026-02-01-git-report.md",
        "date": "2026-02-01",
        "title": "Git Report Analysis",
        "traps": [],
        "heuristics": [],
        "seeds": ["Could git reports feed into auto-scheduling?"],
        "fr_references": ["FR-120"],
        "category": "git-report",
    },
    {
        "filename": "2026-02-10-reflection.md",
        "date": "2026-02-10",
        "title": "Intent Drift Observed",
        "traps": ["intent_drift", "quick_confidence"],
        "heuristics": ["three_reads"],
        "seeds": ["Can we auto-detect quick_confidence in PR reviews?"],
        "fr_references": [],
        "category": "reflection",
    },
    {
        "filename": "2026-03-01-chaplain.md",
        "date": "2026-03-01",
        "title": "Chaplain Process Review",
        "traps": ["downstream_fix"],
        "heuristics": [],
        "seeds": [],
        "fr_references": ["FR-100", "FR-130"],
        "category": "chaplain",
    },
]


# ---------------------------------------------------------------------------
# 1. aggregate_index() — deterministic ground-truth test
# ---------------------------------------------------------------------------
class TestAggregateIndex:
    """Test aggregate_index() against ground-truth fixture (AC #10)."""

    @pytest.mark.req("REQ-YG-257")
    def test_aggregate_returns_all_sections(self):
        """Index must contain entries, traps_index, seeds_index, fr_index,
        heuristics_candidates, and statistics."""
        from examples.demos.diary_index.tools import aggregate_index

        result = aggregate_index({"extractions": FIXTURE_EXTRACTIONS})
        index = result["index"]

        assert "entries" in index
        assert "traps_index" in index
        assert "seeds_index" in index
        assert "fr_index" in index
        assert "heuristics_candidates" in index
        assert "statistics" in index

    @pytest.mark.req("REQ-YG-257")
    def test_entries_count(self):
        """Index entries must match extraction count."""
        from examples.demos.diary_index.tools import aggregate_index

        result = aggregate_index({"extractions": FIXTURE_EXTRACTIONS})
        assert len(result["index"]["entries"]) == 5

    @pytest.mark.req("REQ-YG-257")
    def test_traps_index_sorted_by_frequency(self):
        """Traps index sorted by occurrence count descending."""
        from examples.demos.diary_index.tools import aggregate_index

        result = aggregate_index({"extractions": FIXTURE_EXTRACTIONS})
        traps = result["index"]["traps_index"]

        # downstream_fix appears in 3 entries (most frequent)
        assert traps[0]["trap"] == "downstream_fix"
        assert traps[0]["count"] == 3
        assert len(traps[0]["filenames"]) == 3

        # quick_confidence appears in 2 entries
        assert traps[1]["trap"] == "quick_confidence"
        assert traps[1]["count"] == 2

    @pytest.mark.req("REQ-YG-257")
    def test_seeds_index_with_deduplication(self):
        """Seeds index groups identical seeds across entries."""
        from examples.demos.diary_index.tools import aggregate_index

        result = aggregate_index({"extractions": FIXTURE_EXTRACTIONS})
        seeds = result["index"]["seeds_index"]

        # The repeated seed appears in 2 entries
        recurring = [s for s in seeds if s["count"] >= 2]
        assert len(recurring) == 1
        assert recurring[0]["count"] == 2
        assert "auto-detect quick_confidence" in recurring[0]["seed"]

    @pytest.mark.req("REQ-YG-257")
    def test_fr_reverse_index(self):
        """FR index maps FR-XXX to diary entry filenames."""
        from examples.demos.diary_index.tools import aggregate_index

        result = aggregate_index({"extractions": FIXTURE_EXTRACTIONS})
        fr_index = result["index"]["fr_index"]

        # FR-100 appears in 3 entries
        fr100 = [f for f in fr_index if f["fr"] == "FR-100"]
        assert len(fr100) == 1
        assert fr100[0]["count"] == 3
        assert len(fr100[0]["filenames"]) == 3

    @pytest.mark.req("REQ-YG-257")
    def test_heuristics_candidates(self):
        """Heuristics appearing 2+ times are graduation candidates."""
        from examples.demos.diary_index.tools import aggregate_index

        result = aggregate_index({"extractions": FIXTURE_EXTRACTIONS})
        candidates = result["index"]["heuristics_candidates"]

        # test_before_reading appears in 2 entries
        tbr = [c for c in candidates if c["heuristic"] == "test_before_reading"]
        assert len(tbr) == 1
        assert tbr[0]["count"] == 2

    @pytest.mark.req("REQ-YG-257")
    def test_statistics(self):
        """Statistics section has correct totals."""
        from examples.demos.diary_index.tools import aggregate_index

        result = aggregate_index({"extractions": FIXTURE_EXTRACTIONS})
        stats = result["index"]["statistics"]

        assert stats["total_entries"] == 5
        assert (
            stats["total_unique_traps"] == 4
        )  # downstream_fix, quick_confidence, symptom_patch, intent_drift
        assert stats["total_unique_seeds"] == 2
        assert stats["total_unique_frs"] == 4  # FR-100, FR-110, FR-120, FR-130
        assert stats["entries_by_category"]["reflection"] == 2
        assert stats["entries_by_category"]["audit"] == 1
        assert stats["entries_by_category"]["git-report"] == 1
        assert stats["entries_by_category"]["chaplain"] == 1


# ---------------------------------------------------------------------------
# 2. write_index() — writes valid YAML
# ---------------------------------------------------------------------------
class TestWriteIndex:
    """Test write_index() produces valid YAML file (AC #5)."""

    @pytest.mark.req("REQ-YG-257")
    def test_write_index_produces_valid_yaml(self, tmp_path):
        """write_index() writes parseable YAML to the specified path."""
        from examples.demos.diary_index.tools import aggregate_index, write_index

        agg = aggregate_index({"extractions": FIXTURE_EXTRACTIONS})
        output_file = tmp_path / "diary-index.yaml"

        result = write_index(
            {
                "index": agg["index"],
                "output_path": str(output_file),
            }
        )

        assert result["output_path"] == str(output_file)
        assert output_file.exists()

        # Must be valid YAML
        parsed = yaml.safe_load(output_file.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict)
        assert "entries" in parsed
        assert "traps_index" in parsed


# ---------------------------------------------------------------------------
# 3. list_diary_files() — structure test
# ---------------------------------------------------------------------------
class TestListDiaryFiles:
    """Test list_diary_files() returns expected structure."""

    @pytest.mark.req("REQ-YG-257")
    def test_returns_list_of_dicts_with_filename_and_content(self, tmp_path):
        """Each entry has filename and content keys."""
        from examples.demos.diary_index.tools import list_diary_files

        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-01-01-test.md").write_text("# Test\nContent here", encoding="utf-8")
        (diary_dir / "2026-01-02-test.md").write_text("# Another\nMore content", encoding="utf-8")

        with patch(
            "examples.demos.diary_index.tools.DIARY_DIR",
            diary_dir,
        ):
            result = list_diary_files({})

        files = result["diary_files"]
        assert len(files) == 2
        assert all("filename" in f and "content" in f for f in files)
        assert files[0]["filename"].endswith(".md")
        assert (
            "Content here" in files[0]["content"]
            or "More content" in files[0]["content"]
        )


# ---------------------------------------------------------------------------
# 4. Graph YAML — loads and lints clean
# ---------------------------------------------------------------------------
class TestGraphYaml:
    """Test graph.yaml structure (AC #1, #2, #11)."""

    @pytest.mark.req("REQ-YG-257")
    def test_graph_loads(self):
        """Graph YAML loads via load_graph_config."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(str(GRAPH_PATH))
        assert config.name == "diary-index"

    @pytest.mark.req("REQ-YG-257")
    def test_graph_lints_clean(self):
        """Graph passes yamlgraph graph lint with no errors."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(GRAPH_PATH)
        errors = [i for i in result.issues if i.severity == "error"]
        assert len(errors) == 0, f"Lint errors: {errors}"

    @pytest.mark.req("REQ-YG-257")
    def test_aggregate_node_is_python_type(self):
        """AC #4: aggregate node must be type: python, not type: llm."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(str(GRAPH_PATH))
        agg_node = config.nodes["aggregate"]
        assert agg_node["type"] == "python"

    @pytest.mark.req("REQ-YG-257")
    def test_write_index_node_is_python_type(self):
        """AC #5: write_index node must be type: python."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(str(GRAPH_PATH))
        write_node = config.nodes["write_index"]
        assert write_node["type"] == "python"

    @pytest.mark.req("REQ-YG-257")
    def test_defaults_model_is_haiku(self):
        """AC #14: defaults.model set to claude-haiku for cost control."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(str(GRAPH_PATH))
        assert "haiku" in config.defaults.get("model", "").lower()

    @pytest.mark.req("REQ-YG-257")
    def test_extract_prompt_has_inline_schema(self):
        """AC #12: extraction prompt uses inline schema."""
        prompt_path = DEMO_DIR / "prompts" / "extract_entry.yaml"
        prompt = yaml.safe_load(prompt_path.read_text(encoding="utf-8"))
        assert "schema" in prompt
        assert "name" in prompt["schema"]
        assert prompt["schema"]["name"] == "DiaryExtraction"

    @pytest.mark.req("REQ-YG-257")
    def test_tools_py_no_hardcoded_prompts(self):
        """AC #13: tools.py contains no hardcoded prompts."""
        tools_path = DEMO_DIR / "tools.py"
        content = tools_path.read_text(encoding="utf-8")
        # No prompt strings — check for common prompt patterns
        assert "system:" not in content.lower() or "system:" in content.split('"""')[1]
        assert "You are" not in content

    @pytest.mark.req("REQ-YG-257")
    def test_map_node_max_items(self):
        """Map node must support 500 items for full diary corpus."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(str(GRAPH_PATH))
        extract_node = config.nodes["extract_all"]
        assert extract_node["max_items"] == 500


# ---------------------------------------------------------------------------
# 5. README and demo-output.log existence
# ---------------------------------------------------------------------------
class TestDemoFiles:
    """Test demo directory has required files (AC #15, #16)."""

    @pytest.mark.req("REQ-YG-257")
    def test_readme_exists(self):
        """README.md exists in demo directory."""
        assert (DEMO_DIR / "README.md").exists()

    @pytest.mark.req("REQ-YG-257")
    def test_demo_output_log_exists(self):
        """demo-output.log exists (FR-206 demo-gate)."""
        assert (DEMO_DIR / "demo-output.log").exists()
