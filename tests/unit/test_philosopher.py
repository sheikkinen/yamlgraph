"""FR-184/FR-185/FR-196: Philosopher Daemon tests.

TDD RED phase: Tests for scan_diary_markers(), write_proposals(),
and FR-185 copilot node migration (extract_json, Pydantic models).

FR-196: Updated to use path-based loading for graphs/philosopher/tools.py
"""

import importlib.util
from pathlib import Path
from unittest.mock import patch

# =============================================================================
# FR-196: Load tools.py from graphs/philosopher/ via spec_from_file_location
# =============================================================================
import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_PATH = REPO_ROOT / "graphs" / "philosopher" / "tools.py"


def _load_philosopher_tools():
    """Load philosopher tools module from path (FR-196)."""
    spec = importlib.util.spec_from_file_location("philosopher_tools", TOOLS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Module-level imports from the loaded module
_tools = _load_philosopher_tools()
scan_diary_markers = _tools.scan_diary_markers
write_proposals = _tools.write_proposals
get_today = _tools.get_today
extract_json = _tools.extract_json
Proposal = _tools.Proposal
ProposalList = _tools.ProposalList
ChallengeVerdict = _tools.ChallengeVerdict
DiaryEntry = _tools.DiaryEntry
unwrap_distill = _tools.unwrap_distill
unwrap_challenge = _tools.unwrap_challenge
load_world_context = _tools.load_world_context


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def mock_today():
    """Mock get_today() to return 2026-03-11 for all tests."""
    # FR-196: Patch the loaded module's get_today, not examples.philosopher.tools
    with patch.object(_tools, "get_today", return_value="2026-03-11"):
        yield


@pytest.fixture
def diary_fixture_dir(tmp_path):
    """Create a temp diary directory with fixture files."""
    diary_dir = tmp_path / "diary"
    diary_dir.mkdir()
    return diary_dir


@pytest.fixture
def empty_diary(diary_fixture_dir):
    """Diary with no entries."""
    return diary_fixture_dir


@pytest.fixture
def diary_no_markers(diary_fixture_dir):
    """Diary entries without any markers."""
    (diary_fixture_dir / "diary-2026-03-01.md").write_text(
        "# Session\nJust some notes without markers.\n"
    , encoding="utf-8")
    return diary_fixture_dir


@pytest.fixture
def diary_below_threshold(diary_fixture_dir):
    """Diary with markers appearing below threshold (less than 3 times)."""
    (diary_fixture_dir / "diary-2026-03-01.md").write_text(
        "**Trap:** quick_confidence\n**Heuristic:** Judge when certain\n"
    , encoding="utf-8")
    (diary_fixture_dir / "diary-2026-03-02.md").write_text(
        "**Trap:** quick_confidence\n"
    , encoding="utf-8")
    return diary_fixture_dir


@pytest.fixture
def diary_at_threshold(diary_fixture_dir):
    """Diary with markers appearing exactly at threshold (3 times)."""
    (diary_fixture_dir / "diary-2026-03-01.md").write_text(
        "**Trap:** quick_confidence\n"
    , encoding="utf-8")
    (diary_fixture_dir / "diary-2026-03-02.md").write_text(
        "**Trap:** quick_confidence\n"
    , encoding="utf-8")
    (diary_fixture_dir / "diary-2026-03-03.md").write_text(
        "**Trap:** quick_confidence\n"
    , encoding="utf-8")
    return diary_fixture_dir


@pytest.fixture
def diary_above_threshold(diary_fixture_dir):
    """Diary with markers appearing above threshold (more than 3 times)."""
    for i in range(5):
        (diary_fixture_dir / f"diary-2026-03-0{i + 1}.md").write_text(
            f"**Trap:** intent_drift\n**Seed:** Question {i}?\n"
        , encoding="utf-8")
    return diary_fixture_dir


@pytest.fixture
def diary_mixed_markers(diary_fixture_dir):
    """Diary with multiple marker types: traps, heuristics, seeds."""
    # File 1: trap + heuristic
    (diary_fixture_dir / "diary-2026-03-01.md").write_text(
        "**Trap:** quick_confidence\n"
        "**Heuristic:** Judge when certain\n"
        "**Seed:** Can we automate judgement?\n"
    , encoding="utf-8")
    # File 2: same trap + different heuristic
    (diary_fixture_dir / "diary-2026-03-02.md").write_text(
        "**Trap:** quick_confidence\n**Heuristic:** Test before assuming\n"
    , encoding="utf-8")
    # File 3: same trap again (now at threshold)
    (diary_fixture_dir / "diary-2026-03-03.md").write_text(
        "**Trap:** quick_confidence\n**Heuristic:** Judge when certain\n"
    , encoding="utf-8")
    return diary_fixture_dir


# =============================================================================
# Test: scan_diary_markers()
# =============================================================================


class TestScanDiaryMarkers:
    """Tests for scan_diary_markers() function."""

    @pytest.mark.req("REQ-YG-184")
    def test_empty_diary_returns_empty_counts(self, empty_diary):
        """Empty diary should return empty marker dicts."""
        # FR-196: Using module-level import

        state = {"diary_dir": str(empty_diary), "lookback_days": 30}
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert scan_result["heuristics"] == {}
        assert scan_result["traps"] == {}
        assert scan_result["seeds"] == {}
        assert scan_result["file_count"] == 0

    @pytest.mark.req("REQ-YG-184")
    def test_no_markers_returns_empty_counts(self, diary_no_markers):
        """Files without markers should return empty marker dicts."""
        # FR-196: Using module-level import

        state = {"diary_dir": str(diary_no_markers), "lookback_days": 30}
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert scan_result["heuristics"] == {}
        assert scan_result["traps"] == {}
        assert scan_result["seeds"] == {}
        assert scan_result["file_count"] == 1

    @pytest.mark.req("REQ-YG-184")
    def test_extracts_trap_markers(self, diary_below_threshold):
        """Should extract **Trap:** markers with file locations."""
        # FR-196: Using module-level import

        state = {"diary_dir": str(diary_below_threshold), "lookback_days": 30}
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert "quick_confidence" in scan_result["traps"]
        assert len(scan_result["traps"]["quick_confidence"]) == 2
        assert scan_result["file_count"] == 2

    @pytest.mark.req("REQ-YG-184")
    def test_extracts_heuristic_markers(self, diary_below_threshold):
        """Should extract **Heuristic:** markers with file locations."""
        # FR-196: Using module-level import

        state = {"diary_dir": str(diary_below_threshold), "lookback_days": 30}
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert "Judge when certain" in scan_result["heuristics"]
        assert len(scan_result["heuristics"]["Judge when certain"]) == 1

    @pytest.mark.req("REQ-YG-184")
    def test_extracts_seed_markers(self, diary_above_threshold):
        """Should extract **Seed:** markers with file locations."""
        # FR-196: Using module-level import

        state = {"diary_dir": str(diary_above_threshold), "lookback_days": 30}
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert len(scan_result["seeds"]) == 5  # 5 unique seeds

    @pytest.mark.req("REQ-YG-184")
    def test_respects_lookback_window(self, diary_fixture_dir):
        """Should only scan files within lookback_days window."""
        # FR-196: Using module-level import

        # Create recent file
        (diary_fixture_dir / "diary-2026-03-10.md").write_text(
            "**Trap:** recent_trap\n"
        , encoding="utf-8")
        # Create old file (~70 days ago with today=2026-03-11)
        (diary_fixture_dir / "diary-2026-01-01.md").write_text("**Trap:** old_trap\n", encoding="utf-8")

        state = {"diary_dir": str(diary_fixture_dir), "lookback_days": 30}
        # autouse fixture mocks get_today() to return "2026-03-11"
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert "recent_trap" in scan_result["traps"]
        assert "old_trap" not in scan_result["traps"]

    @pytest.mark.req("REQ-YG-184")
    def test_returns_file_count(self, diary_mixed_markers):
        """Should return count of scanned files."""
        # FR-196: Using module-level import

        state = {"diary_dir": str(diary_mixed_markers), "lookback_days": 30}
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert scan_result["file_count"] == 3


# =============================================================================
# Test: write_proposals()
# =============================================================================


class TestWriteProposals:
    """Tests for write_proposals() function."""

    @pytest.mark.req("REQ-YG-184")
    def test_no_proposals_when_below_threshold(self, tmp_path):
        """Should not write proposals when counts below threshold."""
        # FR-196: Using module-level import

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": [{"type": "trap", "name": "quick_confidence", "count": 2}],
        }
        result = write_proposals(state)

        assert result["written_count"] == 0
        assert list(inbox.glob("*.md")) == []

    @pytest.mark.req("REQ-YG-184")
    def test_writes_proposal_at_threshold(self, tmp_path):
        """Should write proposal when count equals threshold."""
        # FR-196: Using module-level import

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": [{"type": "trap", "name": "quick_confidence", "count": 3}],
        }
        result = write_proposals(state)

        assert result["written_count"] == 1
        files = list(inbox.glob("*.md"))
        assert len(files) == 1
        assert "graduate" in files[0].name
        assert "quick_confidence" in files[0].name

    @pytest.mark.req("REQ-YG-184")
    def test_writes_multiple_proposals(self, tmp_path):
        """Should write multiple proposals when all meet threshold."""
        # FR-196: Using module-level import

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": [
                {"type": "trap", "name": "quick_confidence", "count": 3},
                {"type": "heuristic", "name": "Judge when certain", "count": 4},
            ],
        }
        result = write_proposals(state)

        assert result["written_count"] == 2
        files = list(inbox.glob("*.md"))
        assert len(files) == 2

    @pytest.mark.req("REQ-YG-184")
    def test_excludes_already_graduated(self, tmp_path):
        """Should not write proposals for patterns already in Scripture."""
        # FR-196: Using module-level import

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        # Mock Scripture content that already has this trap
        scripture_content = """
traps:
  quick_confidence: "When I feel certain → Judge instead"
"""
        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": [{"type": "trap", "name": "quick_confidence", "count": 5}],
            "scripture_content": scripture_content,
        }
        result = write_proposals(state)

        assert result["written_count"] == 0
        assert result["excluded_already_graduated"] == 1

    @pytest.mark.req("REQ-YG-184")
    def test_proposal_file_format(self, tmp_path):
        """Proposal files should be markdown consumable by Chaplain."""
        # FR-196: Using module-level import

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": [
                {
                    "type": "trap",
                    "name": "intent_drift",
                    "count": 4,
                    "files": ["diary-1.md", "diary-2.md", "diary-3.md", "diary-4.md"],
                }
            ],
        }
        write_proposals(state)

        files = list(inbox.glob("*.md"))
        content = files[0].read_text(encoding="utf-8")

        # Should be markdown with description
        assert "intent_drift" in content
        assert "4" in content or "four" in content.lower()  # occurrence count


# =============================================================================
# Test: Graph structure
# =============================================================================


class TestPhilosopherGraph:
    """Tests for philosopher graph structure."""

    @pytest.mark.req("REQ-YG-184")
    def test_graph_exists(self):
        """graphs/philosopher/graph.yaml should exist."""
        graph_path = Path("graphs/philosopher/graph.yaml")
        assert graph_path.exists(), "philosopher graph not found"

    @pytest.mark.req("REQ-YG-194")
    def test_graph_has_ten_nodes(self):
        """Graph should have 10 nodes after FR-194/FR-195: scan, analyze, distill, unwrap_distill, challenge, unwrap_challenge, propose, load_context, reflect, write_diary."""
        import yaml

        graph_path = Path("graphs/philosopher/graph.yaml")
        with open(graph_path, encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        nodes = list(graph["nodes"].keys())
        assert len(nodes) == 10
        for name in [
            "scan",
            "analyze",
            "distill",
            "unwrap_distill",
            "challenge",
            "unwrap_challenge",
            "propose",
            "load_context",
            "reflect",
            "write_diary",
        ]:
            assert name in nodes, f"Missing node: {name}"

    @pytest.mark.req("REQ-YG-184")
    def test_graph_edge_topology(self):
        """Graph should have correct edge topology with FR-195 conditional edges."""
        import yaml

        graph_path = Path("graphs/philosopher/graph.yaml")
        with open(graph_path, encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        edges = graph["edges"]
        # Unconditional edges that must exist
        for from_node, to_node in [
            ("START", "scan"),
            ("scan", "analyze"),
            ("analyze", "distill"),
            ("distill", "unwrap_distill"),
            ("challenge", "unwrap_challenge"),
            ("propose", "load_context"),
            ("load_context", "reflect"),
            ("reflect", "write_diary"),
            ("write_diary", "END"),
        ]:
            found = any(e["from"] == from_node and e["to"] == to_node for e in edges)
            assert found, f"Missing edge: {from_node} → {to_node}"


# =============================================================================
# Test: README exists
# =============================================================================


class TestPhilosopherReadme:
    """Tests for philosopher README."""

    @pytest.mark.req("REQ-YG-184")
    def test_readme_exists(self):
        """graphs/philosopher/README.md should exist."""
        readme_path = Path("graphs/philosopher/README.md")
        assert readme_path.exists(), "philosopher README not found"

    @pytest.mark.req("REQ-YG-184")
    def test_readme_documents_usage(self):
        """README should document usage."""
        readme_path = Path("graphs/philosopher/README.md")
        content = readme_path.read_text(encoding="utf-8")
        assert "usage" in content.lower() or "Usage" in content


# =============================================================================
# FR-185: Copilot Node Migration Tests
# =============================================================================


class TestExtractJson:
    """Tests for extract_json() utility (AC-11, AC-13)."""

    @pytest.mark.req("REQ-YG-185")
    def test_clean_json_array(self):
        """extract_json should return clean JSON array unchanged."""
        # FR-196: Using module-level import

        raw = '[{"type": "trap", "name": "quick_confidence", "count": 3, "files": ["d1.md"]}]'
        result = extract_json(raw, "analyze")
        assert result == raw

    @pytest.mark.req("REQ-YG-185")
    def test_clean_json_object(self):
        """extract_json should return clean JSON object unchanged."""
        # FR-196: Using module-level import

        raw = '{"theme": "Patterns", "body": "Reflection text", "seed": "What next?"}'
        result = extract_json(raw, "reflect")
        assert result == raw

    @pytest.mark.req("REQ-YG-185")
    def test_fenced_json(self):
        """extract_json should strip markdown code fences."""
        # FR-196: Using module-level import

        raw = '```json\n[{"type": "trap", "name": "x", "count": 3, "files": []}]\n```'
        result = extract_json(raw, "analyze")
        import json

        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "x"

    @pytest.mark.req("REQ-YG-185")
    def test_preamble_text(self):
        """extract_json should strip preamble text before JSON."""
        # FR-196: Using module-level import

        raw = 'Here are the results:\n\n[{"type": "heuristic", "name": "y", "count": 4, "files": ["a.md"]}]'
        result = extract_json(raw, "analyze")
        import json

        parsed = json.loads(result)
        assert parsed[0]["name"] == "y"

    @pytest.mark.req("REQ-YG-185")
    def test_malformed_json_raises_pipeline_error(self):
        """extract_json should raise ValueError on unparseable input."""
        # FR-196: Using module-level import

        with pytest.raises(ValueError):
            extract_json("This is just plain text with no JSON at all.", "analyze")

    @pytest.mark.req("REQ-YG-185")
    def test_empty_string_raises_pipeline_error(self):
        """extract_json should raise ValueError on empty input."""
        # FR-196: Using module-level import

        with pytest.raises(ValueError):
            extract_json("", "analyze")


class TestPhilosopherModels:
    """Tests for Pydantic models: Proposal, ProposalList, DiaryEntry (AC-10, AC-14)."""

    @pytest.mark.req("REQ-YG-185")
    def test_proposal_list_validates_json(self):
        """ProposalList should validate from JSON string."""
        # FR-196: Using module-level import

        json_str = '{"proposals": [{"type": "trap", "name": "quick_confidence", "count": 3, "files": ["d1.md", "d2.md", "d3.md"]}]}'
        result = ProposalList.model_validate_json(json_str)
        assert len(result.proposals) == 1
        assert result.proposals[0].name == "quick_confidence"
        assert result.proposals[0].count == 3

    @pytest.mark.req("REQ-YG-185")
    def test_proposal_list_empty(self):
        """ProposalList should accept empty proposals list."""
        # FR-196: Using module-level import

        result = ProposalList.model_validate_json('{"proposals": []}')
        assert result.proposals == []

    @pytest.mark.req("REQ-YG-185")
    def test_proposal_list_from_array(self):
        """ProposalList should wrap raw JSON array into proposals field."""

        # FR-196: Using module-level import

        raw_array = '[{"type": "trap", "name": "x", "count": 3, "files": []}]'
        wrapped = f'{{"proposals": {raw_array}}}'
        result = ProposalList.model_validate_json(wrapped)
        assert len(result.proposals) == 1

    @pytest.mark.req("REQ-YG-185")
    def test_diary_entry_validates_json(self):
        """DiaryEntry should validate from JSON string."""
        # FR-196: Using module-level import

        json_str = '{"theme": "Pattern Scanning", "body": "Today I observed...", "seed": "What patterns emerge next?"}'
        result = DiaryEntry.model_validate_json(json_str)
        assert result.theme == "Pattern Scanning"
        assert "observed" in result.body
        assert "?" in result.seed

    @pytest.mark.req("REQ-YG-185")
    def test_diary_entry_rejects_missing_fields(self):
        """DiaryEntry should reject JSON missing required fields."""
        from pydantic import ValidationError

        # FR-196: Using module-level import

        with pytest.raises(ValidationError):
            DiaryEntry.model_validate_json('{"theme": "Test"}')

    @pytest.mark.req("REQ-YG-185")
    def test_proposal_has_typed_fields(self):
        """Proposal fields should be properly typed (not Any)."""
        # FR-196: Using module-level import

        # Verify fields are strongly typed
        fields = Proposal.model_fields
        assert fields["type"].annotation is str
        assert fields["name"].annotation is str
        assert fields["count"].annotation is int
        assert fields["files"].annotation == list[str]


class TestWriteProposalsCopilot:
    """Tests for write_proposals() with CopilotResult input (AC-5, AC-8)."""

    @pytest.mark.req("REQ-YG-185")
    def test_copilot_result_parsed_through_pydantic(self, tmp_path):
        """write_proposals should parse CopilotResult.output through ProposalList."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        copilot_output = CopilotResult(
            output='[{"type": "trap", "name": "quick_confidence", "count": 3, "files": ["d1.md", "d2.md", "d3.md"]}]',
            exit_code=0,
            backend="cli",
        )

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": copilot_output,
        }
        result = write_proposals(state)

        assert result["written_count"] == 1
        files = list(inbox.glob("*.md"))
        assert len(files) == 1
        assert "quick_confidence" in files[0].name

    @pytest.mark.req("REQ-YG-185")
    def test_copilot_result_with_fenced_json(self, tmp_path):
        """write_proposals should handle CopilotResult with markdown fences."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        copilot_output = CopilotResult(
            output='```json\n[{"type": "heuristic", "name": "judge_as_junior", "count": 4, "files": ["d1.md", "d2.md", "d3.md", "d4.md"]}]\n```',
            exit_code=0,
            backend="cli",
        )

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": copilot_output,
        }
        result = write_proposals(state)

        assert result["written_count"] == 1

    @pytest.mark.req("REQ-YG-185")
    def test_copilot_result_empty_proposals(self, tmp_path):
        """write_proposals should handle CopilotResult with empty JSON array."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        copilot_output = CopilotResult(output="[]", exit_code=0, backend="cli")

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": copilot_output,
        }
        result = write_proposals(state)

        assert result["written_count"] == 0

    @pytest.mark.req("REQ-YG-185")
    def test_legacy_pydantic_model_still_works(self, tmp_path):
        """write_proposals should still work with hasattr(.proposals) objects."""
        # FR-196: Using module-level import

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        class MockProposals:
            proposals = [{"type": "trap", "name": "x", "count": 3, "files": []}]

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": MockProposals(),
        }
        result = write_proposals(state)

        assert result["written_count"] == 1


class TestWriteDiaryCopilot:
    """Tests for write_diary() with CopilotResult input."""

    @pytest.mark.req("REQ-YG-185")
    def test_copilot_result_diary_entry(self, tmp_path, monkeypatch):
        """write_diary should parse CopilotResult.output through DiaryEntry model."""
        import examples.shared.diary as diary_mod
        from examples.shared.diary import write_diary
        from yamlgraph.models.schemas import CopilotResult

        monkeypatch.setattr(diary_mod, "DIARY_DIR", tmp_path)

        copilot_output = CopilotResult(
            output='{"theme": "Pattern Scanning", "body": "Today I observed recurring traps.", "seed": "What patterns will emerge tomorrow?"}',
            exit_code=0,
            backend="cli",
        )

        state = {
            "diary_entry": copilot_output,
            "date": "2026-03-11",
            "diary_prefix": "Philosopher",
        }

        result = write_diary(state)
        assert result["written"] is True

        entry_path = tmp_path / "2026-03-11-philosopher.md"
        assert entry_path.exists()
        content = entry_path.read_text(encoding="utf-8")
        assert "Pattern Scanning" in content
        assert "recurring traps" in content
        assert "Seed:" in content

    @pytest.mark.req("REQ-YG-185")
    def test_copilot_result_fenced_diary_entry(self, tmp_path, monkeypatch):
        """write_diary should handle CopilotResult with markdown fences."""
        import examples.shared.diary as diary_mod
        from examples.shared.diary import write_diary
        from yamlgraph.models.schemas import CopilotResult

        monkeypatch.setattr(diary_mod, "DIARY_DIR", tmp_path)

        copilot_output = CopilotResult(
            output='```json\n{"theme": "Fenced Entry", "body": "Test body.", "seed": "Test seed?"}\n```',
            exit_code=0,
            backend="cli",
        )

        state = {
            "diary_entry": copilot_output,
            "date": "2026-03-11",
            "diary_prefix": "Philosopher",
        }

        result = write_diary(state)
        assert result["written"] is True

        entry_path = tmp_path / "2026-03-11-philosopher.md"
        assert entry_path.exists()
        content = entry_path.read_text(encoding="utf-8")
        assert "Fenced Entry" in content


class TestGraphCopilotNodes:
    """Tests for graph.yaml copilot node configuration (AC-1, AC-2, AC-12)."""

    @pytest.mark.req("REQ-YG-185")
    def test_analyze_node_is_copilot(self):
        """analyze node should use type: copilot."""
        import yaml

        graph_path = Path("graphs/philosopher/graph.yaml")
        with open(graph_path, encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        assert graph["nodes"]["analyze"]["type"] == "copilot"

    @pytest.mark.req("REQ-YG-185")
    def test_reflect_node_is_copilot(self):
        """reflect node should use type: copilot."""
        import yaml

        graph_path = Path("graphs/philosopher/graph.yaml")
        with open(graph_path, encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        assert graph["nodes"]["reflect"]["type"] == "copilot"

    @pytest.mark.req("REQ-YG-185")
    def test_no_cli_flags_on_copilot_nodes(self):
        """Philosopher copilot nodes should not have cli_flags: allow_all_paths."""
        import yaml

        graph_path = Path("graphs/philosopher/graph.yaml")
        with open(graph_path, encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        for node_name in ("analyze", "reflect"):
            node = graph["nodes"][node_name]
            assert "cli_flags" not in node, f"{node_name} should not have cli_flags"

    @pytest.mark.req("REQ-YG-185")
    def test_copilot_nodes_have_timeout(self):
        """Copilot nodes should have timeout configured."""
        import yaml

        graph_path = Path("graphs/philosopher/graph.yaml")
        with open(graph_path, encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        for node_name in ("analyze", "reflect"):
            node = graph["nodes"][node_name]
            assert "timeout" in node, f"{node_name} should have timeout"


class TestPromptsCopilot:
    """Tests for prompt YAML changes (AC-3, AC-4)."""

    @pytest.mark.req("REQ-YG-185")
    def test_analyze_prompt_no_schema(self):
        """analyze prompt should not have a schema: block."""
        import yaml

        prompt_path = Path("graphs/philosopher/prompts/analyze.yaml")
        with open(prompt_path, encoding="utf-8") as f:
            prompt = yaml.safe_load(f)

        assert "schema" not in prompt, "analyze.yaml should not have schema: block"

    @pytest.mark.req("REQ-YG-185")
    def test_reflect_prompt_no_schema(self):
        """reflect prompt should not have a schema: block."""
        import yaml

        prompt_path = Path("graphs/philosopher/prompts/reflect.yaml")
        with open(prompt_path, encoding="utf-8") as f:
            prompt = yaml.safe_load(f)

        assert "schema" not in prompt, "reflect.yaml should not have schema: block"

    @pytest.mark.req("REQ-YG-185")
    def test_analyze_prompt_has_json_guard(self):
        """analyze prompt should include 'output ONLY valid JSON' guard."""
        prompt_path = Path("graphs/philosopher/prompts/analyze.yaml")
        content = prompt_path.read_text(encoding="utf-8")

        assert (
            "output ONLY valid JSON" in content.upper()
            or "Output ONLY valid JSON" in content
        )

    @pytest.mark.req("REQ-YG-185")
    def test_reflect_prompt_has_json_guard(self):
        """reflect prompt should include 'output ONLY valid JSON' guard."""
        prompt_path = Path("graphs/philosopher/prompts/reflect.yaml")
        content = prompt_path.read_text(encoding="utf-8")

        assert (
            "output ONLY valid JSON" in content.upper()
            or "Output ONLY valid JSON" in content
        )


# =============================================================================
# FR-195: Philosopher Challenge Node (Devil's Advocate Gate)
# =============================================================================


class TestChallengeVerdictModel:
    """Tests for ChallengeVerdict Pydantic model."""

    @pytest.mark.req("REQ-YG-193")
    def test_approve_verdict(self):
        """ChallengeVerdict should validate an approve verdict."""
        # FR-196: Using module-level import

        v = ChallengeVerdict(
            verdict="approve",
            confidence=0.85,
            objections=["Minor phrasing overlap"],
            surviving_arguments=["Distinct root cause", "Actionable fix"],
        )
        assert v.verdict == "approve"
        assert v.confidence == 0.85
        assert len(v.objections) == 1
        assert len(v.surviving_arguments) == 2

    @pytest.mark.req("REQ-YG-193")
    def test_reject_verdict(self):
        """ChallengeVerdict should validate a reject verdict."""
        # FR-196: Using module-level import

        v = ChallengeVerdict(
            verdict="reject",
            confidence=0.92,
            objections=["False duplicate of existing trap", "Low evidence quality"],
            surviving_arguments=[],
        )
        assert v.verdict == "reject"
        assert v.confidence == 0.92
        assert len(v.objections) == 2
        assert v.surviving_arguments == []

    @pytest.mark.req("REQ-YG-193")
    def test_confidence_lower_bound(self):
        """ChallengeVerdict should reject confidence below 0.0."""
        from pydantic import ValidationError

        # FR-196: Using module-level import

        with pytest.raises(ValidationError):
            ChallengeVerdict(
                verdict="approve",
                confidence=-0.1,
                objections=[],
                surviving_arguments=[],
            )

    @pytest.mark.req("REQ-YG-193")
    def test_confidence_upper_bound(self):
        """ChallengeVerdict should reject confidence above 1.0."""
        from pydantic import ValidationError

        # FR-196: Using module-level import

        with pytest.raises(ValidationError):
            ChallengeVerdict(
                verdict="approve",
                confidence=1.1,
                objections=[],
                surviving_arguments=[],
            )

    @pytest.mark.req("REQ-YG-193")
    def test_from_json(self):
        """ChallengeVerdict should validate from JSON string."""
        # FR-196: Using module-level import

        json_str = '{"verdict": "reject", "confidence": 0.7, "objections": ["weak evidence"], "surviving_arguments": ["partial"]}'
        v = ChallengeVerdict.model_validate_json(json_str)
        assert v.verdict == "reject"
        assert v.confidence == 0.7


class TestUnwrapDistill:
    """Tests for unwrap_distill() tool function."""

    @pytest.mark.req("REQ-YG-193")
    def test_null_signal_returns_none(self):
        """unwrap_distill with {"selected": null} returns top_candidate=None."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        state = {
            "distill_result": CopilotResult(
                output='{"selected": null}',
                exit_code=0,
                backend="cli",
            )
        }
        result = unwrap_distill(state)
        assert result == {"top_candidate": None}

    @pytest.mark.req("REQ-YG-193")
    def test_valid_proposal_returns_dict(self):
        """unwrap_distill with valid proposal returns validated dict."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        proposal_json = '{"type": "trap", "name": "quick_confidence", "count": 4, "files": ["d1.md", "d2.md", "d3.md", "d4.md"]}'
        state = {
            "distill_result": CopilotResult(
                output=proposal_json,
                exit_code=0,
                backend="cli",
            )
        }
        result = unwrap_distill(state)
        assert result["top_candidate"] is not None
        assert result["top_candidate"]["name"] == "quick_confidence"
        assert result["top_candidate"]["count"] == 4
        assert len(result["top_candidate"]["files"]) == 4

    @pytest.mark.req("REQ-YG-193")
    def test_wrapped_selected_proposal(self):
        """unwrap_distill with {"selected": {...}} unwraps correctly."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        proposal_json = '{"selected": {"type": "heuristic", "name": "test_before_reading", "count": 5, "files": ["a.md", "b.md", "c.md", "d.md", "e.md"]}}'
        state = {
            "distill_result": CopilotResult(
                output=proposal_json,
                exit_code=0,
                backend="cli",
            )
        }
        result = unwrap_distill(state)
        assert result["top_candidate"]["name"] == "test_before_reading"
        assert result["top_candidate"]["type"] == "heuristic"

    @pytest.mark.req("REQ-YG-193")
    def test_missing_distill_result(self):
        """unwrap_distill with no distill_result returns None."""
        # FR-196: Using module-level import

        result = unwrap_distill({})
        assert result == {"top_candidate": None}

    @pytest.mark.req("REQ-YG-193")
    def test_non_copilot_result(self):
        """unwrap_distill with non-CopilotResult returns None."""
        # FR-196: Using module-level import

        result = unwrap_distill({"distill_result": "just a string"})
        assert result == {"top_candidate": None}

    @pytest.mark.req("REQ-YG-193")
    def test_fenced_json_proposal(self):
        """unwrap_distill handles markdown-fenced JSON."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        state = {
            "distill_result": CopilotResult(
                output='```json\n{"type": "seed", "name": "auto_escalation", "count": 3, "files": ["x.md", "y.md", "z.md"]}\n```',
                exit_code=0,
                backend="cli",
            )
        }
        result = unwrap_distill(state)
        assert result["top_candidate"]["name"] == "auto_escalation"


class TestUnwrapChallenge:
    """Tests for unwrap_challenge() tool function."""

    @pytest.mark.req("REQ-YG-193")
    def test_approve_verdict_parsed(self):
        """unwrap_challenge parses approve verdict correctly."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        verdict_json = '{"verdict": "approve", "confidence": 0.85, "objections": ["minor overlap"], "surviving_arguments": ["distinct cause", "actionable"]}'
        state = {
            "challenge_result": CopilotResult(
                output=verdict_json,
                exit_code=0,
                backend="cli",
            )
        }
        result = unwrap_challenge(state)
        assert result["challenge_parsed"]["verdict"] == "approve"
        assert result["challenge_parsed"]["confidence"] == 0.85
        assert len(result["challenge_parsed"]["objections"]) == 1
        assert len(result["challenge_parsed"]["surviving_arguments"]) == 2

    @pytest.mark.req("REQ-YG-193")
    def test_reject_verdict_parsed(self):
        """unwrap_challenge parses reject verdict correctly."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        verdict_json = '{"verdict": "reject", "confidence": 0.95, "objections": ["false duplicate", "low evidence"], "surviving_arguments": []}'
        state = {
            "challenge_result": CopilotResult(
                output=verdict_json,
                exit_code=0,
                backend="cli",
            )
        }
        result = unwrap_challenge(state)
        assert result["challenge_parsed"]["verdict"] == "reject"
        assert result["challenge_parsed"]["confidence"] == 0.95
        assert len(result["challenge_parsed"]["objections"]) == 2
        assert result["challenge_parsed"]["surviving_arguments"] == []

    @pytest.mark.req("REQ-YG-193")
    def test_missing_challenge_result(self):
        """unwrap_challenge with no challenge_result returns reject fallback."""
        # FR-196: Using module-level import

        result = unwrap_challenge({})
        assert result["challenge_parsed"]["verdict"] == "reject"
        assert result["challenge_parsed"]["confidence"] == 0.0

    @pytest.mark.req("REQ-YG-193")
    def test_fenced_verdict(self):
        """unwrap_challenge handles markdown-fenced JSON."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        state = {
            "challenge_result": CopilotResult(
                output='```json\n{"verdict": "approve", "confidence": 0.9, "objections": [], "surviving_arguments": ["strong"]}\n```',
                exit_code=0,
                backend="cli",
            )
        }
        result = unwrap_challenge(state)
        assert result["challenge_parsed"]["verdict"] == "approve"


class TestWriteProposalsTopCandidate:
    """Tests for write_proposals() with top_candidate path (FR-195)."""

    @pytest.mark.req("REQ-YG-193")
    def test_top_candidate_writes_single_proposal(self, tmp_path):
        """write_proposals with top_candidate dict writes single proposal."""
        # FR-196: Using module-level import

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": [],
            "top_candidate": {
                "type": "trap",
                "name": "quick_confidence",
                "count": 4,
                "files": ["d1.md", "d2.md", "d3.md", "d4.md"],
            },
        }
        result = write_proposals(state)
        assert result["written_count"] == 1
        files = list(inbox.glob("*.md"))
        assert len(files) == 1
        assert "quick_confidence" in files[0].name

    @pytest.mark.req("REQ-YG-193")
    def test_top_candidate_none_falls_back_to_proposals(self, tmp_path):
        """write_proposals with top_candidate=None falls back to proposals key."""
        # FR-196: Using module-level import
        from yamlgraph.models.schemas import CopilotResult

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        copilot_output = CopilotResult(
            output='[{"type": "trap", "name": "fallback_pattern", "count": 3, "files": ["a.md", "b.md", "c.md"]}]',
            exit_code=0,
            backend="cli",
        )

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": copilot_output,
            "top_candidate": None,
        }
        result = write_proposals(state)
        assert result["written_count"] == 1
        files = list(inbox.glob("*.md"))
        assert "fallback_pattern" in files[0].name

    @pytest.mark.req("REQ-YG-193")
    def test_top_candidate_below_threshold_skipped(self, tmp_path):
        """write_proposals with top_candidate below threshold writes nothing."""
        # FR-196: Using module-level import

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": [],
            "top_candidate": {
                "type": "trap",
                "name": "weak_pattern",
                "count": 2,
                "files": ["d1.md", "d2.md"],
            },
        }
        result = write_proposals(state)
        assert result["written_count"] == 0


class TestPhilosopherGraphFR195:
    """Tests for graph.yaml structure changes (FR-195)."""

    @pytest.mark.req("REQ-YG-193")
    def test_graph_has_distill_node(self):
        """Graph should have a distill copilot node."""
        import yaml

        with open("graphs/philosopher/graph.yaml", encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        assert "distill" in graph["nodes"]
        assert graph["nodes"]["distill"]["type"] == "copilot"

    @pytest.mark.req("REQ-YG-193")
    def test_graph_has_challenge_node(self):
        """Graph should have a challenge copilot node."""
        import yaml

        with open("graphs/philosopher/graph.yaml", encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        assert "challenge" in graph["nodes"]
        assert graph["nodes"]["challenge"]["type"] == "copilot"

    @pytest.mark.req("REQ-YG-193")
    def test_graph_has_unwrap_nodes(self):
        """Graph should have unwrap_distill and unwrap_challenge Python nodes."""
        import yaml

        with open("graphs/philosopher/graph.yaml", encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        assert "unwrap_distill" in graph["nodes"]
        assert graph["nodes"]["unwrap_distill"]["type"] == "python"
        assert "unwrap_challenge" in graph["nodes"]
        assert graph["nodes"]["unwrap_challenge"]["type"] == "python"

    @pytest.mark.req("REQ-YG-193")
    def test_graph_state_has_new_keys(self):
        """Graph state should declare distill_result, top_candidate, challenge_result, challenge_parsed."""
        import yaml

        with open("graphs/philosopher/graph.yaml", encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        state = graph["state"]
        for key in [
            "distill_result",
            "top_candidate",
            "challenge_result",
            "challenge_parsed",
        ]:
            assert key in state, f"Missing state key: {key}"

    @pytest.mark.req("REQ-YG-193")
    def test_graph_has_conditional_edges(self):
        """Graph should have conditional edges from unwrap nodes."""
        import yaml

        with open("graphs/philosopher/graph.yaml", encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        edges = graph["edges"]
        # Find conditional edges from unwrap_distill
        unwrap_distill_edges = [e for e in edges if e["from"] == "unwrap_distill"]
        assert len(unwrap_distill_edges) == 2
        conditions = {e.get("condition", ""): e["to"] for e in unwrap_distill_edges}
        assert "top_candidate != None" in conditions
        assert "top_candidate == None" in conditions

        # Find conditional edges from unwrap_challenge
        unwrap_challenge_edges = [e for e in edges if e["from"] == "unwrap_challenge"]
        assert len(unwrap_challenge_edges) == 2
        conditions = {e.get("condition", ""): e["to"] for e in unwrap_challenge_edges}
        assert "challenge_parsed.verdict == 'approve'" in conditions
        assert "challenge_parsed.verdict != 'approve'" in conditions

    @pytest.mark.req("REQ-YG-193")
    def test_graph_tool_declarations(self):
        """Graph should declare unwrap tool functions."""
        import yaml

        with open("graphs/philosopher/graph.yaml", encoding="utf-8") as f:
            graph = yaml.safe_load(f)

        tools = graph["tools"]
        assert "unwrap_distill_tool" in tools
        assert tools["unwrap_distill_tool"]["function"] == "unwrap_distill"
        assert "unwrap_challenge_tool" in tools
        assert tools["unwrap_challenge_tool"]["function"] == "unwrap_challenge"


class TestPhilosopherPromptsFR195:
    """Tests for new prompt YAML files (FR-195)."""

    @pytest.mark.req("REQ-YG-193")
    def test_distill_prompt_exists(self):
        """distill.yaml prompt should exist."""
        assert Path("graphs/philosopher/prompts/distill.yaml").exists()

    @pytest.mark.req("REQ-YG-193")
    def test_challenge_prompt_exists(self):
        """challenge.yaml prompt should exist."""
        assert Path("graphs/philosopher/prompts/challenge.yaml").exists()

    @pytest.mark.req("REQ-YG-193")
    def test_distill_prompt_has_json_guard(self):
        """distill prompt should include JSON output guard."""
        content = Path("graphs/philosopher/prompts/distill.yaml").read_text(encoding="utf-8")
        assert (
            "Output ONLY valid JSON" in content
            or "output ONLY valid JSON" in content.upper()
        )

    @pytest.mark.req("REQ-YG-193")
    def test_challenge_prompt_has_json_guard(self):
        """challenge prompt should include JSON output guard."""
        content = Path(
            "graphs/philosopher/prompts/challenge.yaml"
        ).read_text(encoding="utf-8")
        assert (
            "Output ONLY valid JSON" in content
            or "output ONLY valid JSON" in content.upper()
        )

    @pytest.mark.req("REQ-YG-193")
    def test_distill_prompt_no_schema(self):
        """distill prompt should not have a schema: block (validation in Python)."""
        import yaml

        with open("graphs/philosopher/prompts/distill.yaml", encoding="utf-8") as f:
            prompt = yaml.safe_load(f)
        assert "schema" not in prompt

    @pytest.mark.req("REQ-YG-193")
    def test_challenge_prompt_has_five_axes(self):
        """challenge prompt should mention all 5 challenge axes."""
        content = (
            Path("graphs/philosopher/prompts/challenge.yaml")
            .read_text(encoding="utf-8")
            .lower()
        )
        for axis in [
            "recurrence",
            "actionability",
            "specificity",
            "false duplicate",
            "evidence",
        ]:
            assert axis in content, f"Missing challenge axis: {axis}"

    @pytest.mark.req("REQ-YG-193")
    def test_reflect_prompt_includes_challenge_context(self):
        """reflect prompt should include challenge_parsed variable."""
        content = Path("graphs/philosopher/prompts/reflect.yaml").read_text(encoding="utf-8")
        assert "challenge" in content.lower()


class TestConditionalRouting:
    """Tests for conditional edge evaluation (FR-195 routing logic)."""

    @pytest.mark.req("REQ-YG-193")
    def test_approve_verdict_routes_to_propose(self):
        """approve verdict condition evaluates to True."""
        from yamlgraph.utils.conditions import evaluate_condition

        state = {"challenge_parsed": {"verdict": "approve", "confidence": 0.85}}
        assert (
            evaluate_condition("challenge_parsed.verdict == 'approve'", state) is True
        )

    @pytest.mark.req("REQ-YG-193")
    def test_reject_verdict_skips_propose(self):
        """reject verdict condition for propose evaluates to False."""
        from yamlgraph.utils.conditions import evaluate_condition

        state = {"challenge_parsed": {"verdict": "reject", "confidence": 0.9}}
        assert (
            evaluate_condition("challenge_parsed.verdict == 'approve'", state) is False
        )

    @pytest.mark.req("REQ-YG-193")
    def test_reject_routes_to_reflect(self):
        """reject verdict routes to reflect via != condition."""
        from yamlgraph.utils.conditions import evaluate_condition

        state = {"challenge_parsed": {"verdict": "reject", "confidence": 0.9}}
        assert (
            evaluate_condition("challenge_parsed.verdict != 'approve'", state) is True
        )

    @pytest.mark.req("REQ-YG-193")
    def test_null_top_candidate_routes_to_reflect(self):
        """null top_candidate routes to reflect."""
        from yamlgraph.utils.conditions import evaluate_condition

        state = {"top_candidate": None}
        assert evaluate_condition("top_candidate == None", state) is True

    @pytest.mark.req("REQ-YG-193")
    def test_present_top_candidate_routes_to_challenge(self):
        """present top_candidate routes to challenge."""
        from yamlgraph.utils.conditions import evaluate_condition

        state = {"top_candidate": {"name": "test_pattern"}}
        assert evaluate_condition("top_candidate != None", state) is True
