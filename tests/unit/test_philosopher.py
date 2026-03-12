"""FR-184/FR-185: Philosopher Daemon tests.

TDD RED phase: Tests for scan_diary_markers(), write_proposals(),
and FR-185 copilot node migration (extract_json, Pydantic models).
"""

from pathlib import Path
from unittest.mock import patch

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def mock_today():
    """Mock get_today() to return 2026-03-11 for all tests."""
    with patch("examples.philosopher.tools.get_today", return_value="2026-03-11"):
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
    )
    return diary_fixture_dir


@pytest.fixture
def diary_below_threshold(diary_fixture_dir):
    """Diary with markers appearing below threshold (less than 3 times)."""
    (diary_fixture_dir / "diary-2026-03-01.md").write_text(
        "**Trap:** quick_confidence\n**Heuristic:** Judge when certain\n"
    )
    (diary_fixture_dir / "diary-2026-03-02.md").write_text(
        "**Trap:** quick_confidence\n"
    )
    return diary_fixture_dir


@pytest.fixture
def diary_at_threshold(diary_fixture_dir):
    """Diary with markers appearing exactly at threshold (3 times)."""
    (diary_fixture_dir / "diary-2026-03-01.md").write_text(
        "**Trap:** quick_confidence\n"
    )
    (diary_fixture_dir / "diary-2026-03-02.md").write_text(
        "**Trap:** quick_confidence\n"
    )
    (diary_fixture_dir / "diary-2026-03-03.md").write_text(
        "**Trap:** quick_confidence\n"
    )
    return diary_fixture_dir


@pytest.fixture
def diary_above_threshold(diary_fixture_dir):
    """Diary with markers appearing above threshold (more than 3 times)."""
    for i in range(5):
        (diary_fixture_dir / f"diary-2026-03-0{i+1}.md").write_text(
            f"**Trap:** intent_drift\n**Seed:** Question {i}?\n"
        )
    return diary_fixture_dir


@pytest.fixture
def diary_mixed_markers(diary_fixture_dir):
    """Diary with multiple marker types: traps, heuristics, seeds."""
    # File 1: trap + heuristic
    (diary_fixture_dir / "diary-2026-03-01.md").write_text(
        "**Trap:** quick_confidence\n"
        "**Heuristic:** Judge when certain\n"
        "**Seed:** Can we automate judgement?\n"
    )
    # File 2: same trap + different heuristic
    (diary_fixture_dir / "diary-2026-03-02.md").write_text(
        "**Trap:** quick_confidence\n" "**Heuristic:** Test before assuming\n"
    )
    # File 3: same trap again (now at threshold)
    (diary_fixture_dir / "diary-2026-03-03.md").write_text(
        "**Trap:** quick_confidence\n" "**Heuristic:** Judge when certain\n"
    )
    return diary_fixture_dir


# =============================================================================
# Test: scan_diary_markers()
# =============================================================================


class TestScanDiaryMarkers:
    """Tests for scan_diary_markers() function."""

    @pytest.mark.req("REQ-YG-184")
    def test_empty_diary_returns_empty_counts(self, empty_diary):
        """Empty diary should return empty marker dicts."""
        from examples.philosopher.tools import scan_diary_markers

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
        from examples.philosopher.tools import scan_diary_markers

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
        from examples.philosopher.tools import scan_diary_markers

        state = {"diary_dir": str(diary_below_threshold), "lookback_days": 30}
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert "quick_confidence" in scan_result["traps"]
        assert len(scan_result["traps"]["quick_confidence"]) == 2
        assert scan_result["file_count"] == 2

    @pytest.mark.req("REQ-YG-184")
    def test_extracts_heuristic_markers(self, diary_below_threshold):
        """Should extract **Heuristic:** markers with file locations."""
        from examples.philosopher.tools import scan_diary_markers

        state = {"diary_dir": str(diary_below_threshold), "lookback_days": 30}
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert "Judge when certain" in scan_result["heuristics"]
        assert len(scan_result["heuristics"]["Judge when certain"]) == 1

    @pytest.mark.req("REQ-YG-184")
    def test_extracts_seed_markers(self, diary_above_threshold):
        """Should extract **Seed:** markers with file locations."""
        from examples.philosopher.tools import scan_diary_markers

        state = {"diary_dir": str(diary_above_threshold), "lookback_days": 30}
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert len(scan_result["seeds"]) == 5  # 5 unique seeds

    @pytest.mark.req("REQ-YG-184")
    def test_respects_lookback_window(self, diary_fixture_dir):
        """Should only scan files within lookback_days window."""
        from examples.philosopher.tools import scan_diary_markers

        # Create recent file
        (diary_fixture_dir / "diary-2026-03-10.md").write_text(
            "**Trap:** recent_trap\n"
        )
        # Create old file (~70 days ago with today=2026-03-11)
        (diary_fixture_dir / "diary-2026-01-01.md").write_text("**Trap:** old_trap\n")

        state = {"diary_dir": str(diary_fixture_dir), "lookback_days": 30}
        # autouse fixture mocks get_today() to return "2026-03-11"
        result = scan_diary_markers(state)
        scan_result = result["scan_result"]

        assert "recent_trap" in scan_result["traps"]
        assert "old_trap" not in scan_result["traps"]

    @pytest.mark.req("REQ-YG-184")
    def test_returns_file_count(self, diary_mixed_markers):
        """Should return count of scanned files."""
        from examples.philosopher.tools import scan_diary_markers

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
        from examples.philosopher.tools import write_proposals

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
        from examples.philosopher.tools import write_proposals

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
        from examples.philosopher.tools import write_proposals

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
        from examples.philosopher.tools import write_proposals

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
        from examples.philosopher.tools import write_proposals

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
        content = files[0].read_text()

        # Should be markdown with description
        assert "intent_drift" in content
        assert "4" in content or "four" in content.lower()  # occurrence count


# =============================================================================
# Test: philosopher.sh exists and is executable
# =============================================================================


class TestPhilosopherDaemon:
    """Tests for philosopher.sh daemon script."""

    @pytest.mark.req("REQ-YG-184")
    def test_daemon_script_exists(self):
        """philosopher.sh should exist in .chaplain/."""
        daemon_path = Path(".chaplain/philosopher.sh")
        assert daemon_path.exists(), "philosopher.sh daemon not found"

    @pytest.mark.req("REQ-YG-184")
    def test_daemon_script_executable(self):
        """philosopher.sh should have executable permissions."""
        import stat

        daemon_path = Path(".chaplain/philosopher.sh")
        mode = daemon_path.stat().st_mode
        assert mode & stat.S_IXUSR, "philosopher.sh is not executable"


# =============================================================================
# Test: Graph structure
# =============================================================================


class TestPhilosopherGraph:
    """Tests for philosopher graph structure."""

    @pytest.mark.req("REQ-YG-184")
    def test_graph_exists(self):
        """examples/philosopher/graph.yaml should exist."""
        graph_path = Path("examples/philosopher/graph.yaml")
        assert graph_path.exists(), "philosopher graph not found"

    @pytest.mark.req("REQ-YG-184")
    def test_graph_has_five_nodes(self):
        """Graph should have exactly 5 nodes: scan, analyze, propose, reflect, write_diary."""
        import yaml

        graph_path = Path("examples/philosopher/graph.yaml")
        with open(graph_path) as f:
            graph = yaml.safe_load(f)

        nodes = list(graph["nodes"].keys())
        assert len(nodes) == 5
        assert "scan" in nodes
        assert "analyze" in nodes
        assert "propose" in nodes
        assert "reflect" in nodes
        assert "write_diary" in nodes

    @pytest.mark.req("REQ-YG-184")
    def test_graph_is_linear(self):
        """Graph should have linear edges: scan → analyze → propose → reflect → write_diary."""
        import yaml

        graph_path = Path("examples/philosopher/graph.yaml")
        with open(graph_path) as f:
            graph = yaml.safe_load(f)

        edges = graph["edges"]
        expected_sequence = [
            ("START", "scan"),
            ("scan", "analyze"),
            ("analyze", "propose"),
            ("propose", "reflect"),
            ("reflect", "write_diary"),
            ("write_diary", "END"),
        ]

        for from_node, to_node in expected_sequence:
            found = any(e["from"] == from_node and e["to"] == to_node for e in edges)
            assert found, f"Missing edge: {from_node} → {to_node}"


# =============================================================================
# Test: README exists
# =============================================================================


class TestPhilosopherReadme:
    """Tests for philosopher README."""

    @pytest.mark.req("REQ-YG-184")
    def test_readme_exists(self):
        """examples/philosopher/README.md should exist."""
        readme_path = Path("examples/philosopher/README.md")
        assert readme_path.exists(), "philosopher README not found"

    @pytest.mark.req("REQ-YG-184")
    def test_readme_documents_usage(self):
        """README should document usage."""
        readme_path = Path("examples/philosopher/README.md")
        content = readme_path.read_text()
        assert "usage" in content.lower() or "Usage" in content


# =============================================================================
# FR-185: Copilot Node Migration Tests
# =============================================================================


class TestExtractJson:
    """Tests for extract_json() utility (AC-11, AC-13)."""

    @pytest.mark.req("REQ-YG-185")
    def test_clean_json_array(self):
        """extract_json should return clean JSON array unchanged."""
        from examples.philosopher.models import extract_json

        raw = '[{"type": "trap", "name": "quick_confidence", "count": 3, "files": ["d1.md"]}]'
        result = extract_json(raw, "analyze")
        assert result == raw

    @pytest.mark.req("REQ-YG-185")
    def test_clean_json_object(self):
        """extract_json should return clean JSON object unchanged."""
        from examples.philosopher.models import extract_json

        raw = '{"theme": "Patterns", "body": "Reflection text", "seed": "What next?"}'
        result = extract_json(raw, "reflect")
        assert result == raw

    @pytest.mark.req("REQ-YG-185")
    def test_fenced_json(self):
        """extract_json should strip markdown code fences."""
        from examples.philosopher.models import extract_json

        raw = '```json\n[{"type": "trap", "name": "x", "count": 3, "files": []}]\n```'
        result = extract_json(raw, "analyze")
        import json

        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "x"

    @pytest.mark.req("REQ-YG-185")
    def test_preamble_text(self):
        """extract_json should strip preamble text before JSON."""
        from examples.philosopher.models import extract_json

        raw = 'Here are the results:\n\n[{"type": "heuristic", "name": "y", "count": 4, "files": ["a.md"]}]'
        result = extract_json(raw, "analyze")
        import json

        parsed = json.loads(result)
        assert parsed[0]["name"] == "y"

    @pytest.mark.req("REQ-YG-185")
    def test_malformed_json_raises_pipeline_error(self):
        """extract_json should raise ValueError on unparseable input."""
        from examples.philosopher.models import extract_json

        with pytest.raises(ValueError):
            extract_json("This is just plain text with no JSON at all.", "analyze")

    @pytest.mark.req("REQ-YG-185")
    def test_empty_string_raises_pipeline_error(self):
        """extract_json should raise ValueError on empty input."""
        from examples.philosopher.models import extract_json

        with pytest.raises(ValueError):
            extract_json("", "analyze")


class TestPhilosopherModels:
    """Tests for Pydantic models: Proposal, ProposalList, DiaryEntry (AC-10, AC-14)."""

    @pytest.mark.req("REQ-YG-185")
    def test_proposal_list_validates_json(self):
        """ProposalList should validate from JSON string."""
        from examples.philosopher.models import ProposalList

        json_str = '{"proposals": [{"type": "trap", "name": "quick_confidence", "count": 3, "files": ["d1.md", "d2.md", "d3.md"]}]}'
        result = ProposalList.model_validate_json(json_str)
        assert len(result.proposals) == 1
        assert result.proposals[0].name == "quick_confidence"
        assert result.proposals[0].count == 3

    @pytest.mark.req("REQ-YG-185")
    def test_proposal_list_empty(self):
        """ProposalList should accept empty proposals list."""
        from examples.philosopher.models import ProposalList

        result = ProposalList.model_validate_json('{"proposals": []}')
        assert result.proposals == []

    @pytest.mark.req("REQ-YG-185")
    def test_proposal_list_from_array(self):
        """ProposalList should wrap raw JSON array into proposals field."""

        from examples.philosopher.models import ProposalList

        raw_array = '[{"type": "trap", "name": "x", "count": 3, "files": []}]'
        wrapped = f'{{"proposals": {raw_array}}}'
        result = ProposalList.model_validate_json(wrapped)
        assert len(result.proposals) == 1

    @pytest.mark.req("REQ-YG-185")
    def test_diary_entry_validates_json(self):
        """DiaryEntry should validate from JSON string."""
        from examples.philosopher.models import DiaryEntry

        json_str = '{"theme": "Pattern Scanning", "body": "Today I observed...", "seed": "What patterns emerge next?"}'
        result = DiaryEntry.model_validate_json(json_str)
        assert result.theme == "Pattern Scanning"
        assert "observed" in result.body
        assert "?" in result.seed

    @pytest.mark.req("REQ-YG-185")
    def test_diary_entry_rejects_missing_fields(self):
        """DiaryEntry should reject JSON missing required fields."""
        from pydantic import ValidationError

        from examples.philosopher.models import DiaryEntry

        with pytest.raises(ValidationError):
            DiaryEntry.model_validate_json('{"theme": "Test"}')

    @pytest.mark.req("REQ-YG-185")
    def test_proposal_has_typed_fields(self):
        """Proposal fields should be properly typed (not Any)."""
        from examples.philosopher.models import Proposal

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
        from examples.philosopher.tools import write_proposals
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
        from examples.philosopher.tools import write_proposals
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
        from examples.philosopher.tools import write_proposals
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
        from examples.philosopher.tools import write_proposals

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
        content = entry_path.read_text()
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
        content = entry_path.read_text()
        assert "Fenced Entry" in content


class TestGraphCopilotNodes:
    """Tests for graph.yaml copilot node configuration (AC-1, AC-2, AC-12)."""

    @pytest.mark.req("REQ-YG-185")
    def test_analyze_node_is_copilot(self):
        """analyze node should use type: copilot."""
        import yaml

        graph_path = Path("examples/philosopher/graph.yaml")
        with open(graph_path) as f:
            graph = yaml.safe_load(f)

        assert graph["nodes"]["analyze"]["type"] == "copilot"

    @pytest.mark.req("REQ-YG-185")
    def test_reflect_node_is_copilot(self):
        """reflect node should use type: copilot."""
        import yaml

        graph_path = Path("examples/philosopher/graph.yaml")
        with open(graph_path) as f:
            graph = yaml.safe_load(f)

        assert graph["nodes"]["reflect"]["type"] == "copilot"

    @pytest.mark.req("REQ-YG-185")
    def test_no_cli_flags_on_copilot_nodes(self):
        """Philosopher copilot nodes should not have cli_flags: allow_all_paths."""
        import yaml

        graph_path = Path("examples/philosopher/graph.yaml")
        with open(graph_path) as f:
            graph = yaml.safe_load(f)

        for node_name in ("analyze", "reflect"):
            node = graph["nodes"][node_name]
            assert "cli_flags" not in node, f"{node_name} should not have cli_flags"

    @pytest.mark.req("REQ-YG-185")
    def test_copilot_nodes_have_timeout(self):
        """Copilot nodes should have timeout configured."""
        import yaml

        graph_path = Path("examples/philosopher/graph.yaml")
        with open(graph_path) as f:
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

        prompt_path = Path("examples/philosopher/prompts/analyze.yaml")
        with open(prompt_path) as f:
            prompt = yaml.safe_load(f)

        assert "schema" not in prompt, "analyze.yaml should not have schema: block"

    @pytest.mark.req("REQ-YG-185")
    def test_reflect_prompt_no_schema(self):
        """reflect prompt should not have a schema: block."""
        import yaml

        prompt_path = Path("examples/philosopher/prompts/reflect.yaml")
        with open(prompt_path) as f:
            prompt = yaml.safe_load(f)

        assert "schema" not in prompt, "reflect.yaml should not have schema: block"

    @pytest.mark.req("REQ-YG-185")
    def test_analyze_prompt_has_json_guard(self):
        """analyze prompt should include 'output ONLY valid JSON' guard."""
        prompt_path = Path("examples/philosopher/prompts/analyze.yaml")
        content = prompt_path.read_text()

        assert (
            "output ONLY valid JSON" in content.upper()
            or "Output ONLY valid JSON" in content
        )

    @pytest.mark.req("REQ-YG-185")
    def test_reflect_prompt_has_json_guard(self):
        """reflect prompt should include 'output ONLY valid JSON' guard."""
        prompt_path = Path("examples/philosopher/prompts/reflect.yaml")
        content = prompt_path.read_text()

        assert (
            "output ONLY valid JSON" in content.upper()
            or "Output ONLY valid JSON" in content
        )
