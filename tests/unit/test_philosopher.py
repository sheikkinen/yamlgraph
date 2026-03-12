"""FR-184: Philosopher Daemon tests.

TDD RED phase: Tests for scan_diary_markers() and write_proposals().
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

        assert result["heuristics"] == {}
        assert result["traps"] == {}
        assert result["seeds"] == {}
        assert result["file_count"] == 0

    @pytest.mark.req("REQ-YG-184")
    def test_no_markers_returns_empty_counts(self, diary_no_markers):
        """Files without markers should return empty marker dicts."""
        from examples.philosopher.tools import scan_diary_markers

        state = {"diary_dir": str(diary_no_markers), "lookback_days": 30}
        result = scan_diary_markers(state)

        assert result["heuristics"] == {}
        assert result["traps"] == {}
        assert result["seeds"] == {}
        assert result["file_count"] == 1

    @pytest.mark.req("REQ-YG-184")
    def test_extracts_trap_markers(self, diary_below_threshold):
        """Should extract **Trap:** markers with file locations."""
        from examples.philosopher.tools import scan_diary_markers

        state = {"diary_dir": str(diary_below_threshold), "lookback_days": 30}
        result = scan_diary_markers(state)

        assert "quick_confidence" in result["traps"]
        assert len(result["traps"]["quick_confidence"]) == 2
        assert result["file_count"] == 2

    @pytest.mark.req("REQ-YG-184")
    def test_extracts_heuristic_markers(self, diary_below_threshold):
        """Should extract **Heuristic:** markers with file locations."""
        from examples.philosopher.tools import scan_diary_markers

        state = {"diary_dir": str(diary_below_threshold), "lookback_days": 30}
        result = scan_diary_markers(state)

        assert "Judge when certain" in result["heuristics"]
        assert len(result["heuristics"]["Judge when certain"]) == 1

    @pytest.mark.req("REQ-YG-184")
    def test_extracts_seed_markers(self, diary_above_threshold):
        """Should extract **Seed:** markers with file locations."""
        from examples.philosopher.tools import scan_diary_markers

        state = {"diary_dir": str(diary_above_threshold), "lookback_days": 30}
        result = scan_diary_markers(state)

        assert len(result["seeds"]) == 5  # 5 unique seeds

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

        assert "recent_trap" in result["traps"]
        assert "old_trap" not in result["traps"]

    @pytest.mark.req("REQ-YG-184")
    def test_returns_file_count(self, diary_mixed_markers):
        """Should return count of scanned files."""
        from examples.philosopher.tools import scan_diary_markers

        state = {"diary_dir": str(diary_mixed_markers), "lookback_days": 30}
        result = scan_diary_markers(state)

        assert result["file_count"] == 3


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
# Test: FR-186 — to_serializable migration
# =============================================================================


class TestWriteProposalsToSerializable:
    """FR-186: write_proposals uses to_serializable for Pydantic model handling."""

    @pytest.mark.req("REQ-YG-070")
    def test_pydantic_model_proposal_items_are_serialized(self, tmp_path):
        """Category A (line 138): Pydantic model proposal items should be
        converted via to_serializable, not inline hasattr."""
        from pydantic import BaseModel

        from examples.philosopher.tools import write_proposals

        class Proposal(BaseModel):
            type: str
            name: str
            count: int
            files: list[str]

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": [
                Proposal(
                    type="trap",
                    name="intent_drift",
                    count=4,
                    files=["diary-1.md", "diary-2.md", "diary-3.md", "diary-4.md"],
                ),
            ],
        }
        result = write_proposals(state)

        assert result["written_count"] == 1
        files = list(inbox.glob("*.md"))
        assert len(files) == 1
        assert "intent_drift" in files[0].read_text()

    @pytest.mark.req("REQ-YG-070")
    def test_pydantic_wrapper_model_proposals_extracted(self, tmp_path):
        """Category B (line 122): Pydantic wrapper with model_dump().get('proposals')
        should be handled via to_serializable compose pattern."""
        from pydantic import BaseModel

        from examples.philosopher.tools import write_proposals

        class ProposalWrapper(BaseModel):
            proposals: list[dict]

        inbox = tmp_path / "inbox"
        inbox.mkdir()

        wrapper = ProposalWrapper(
            proposals=[
                {"type": "trap", "name": "quick_confidence", "count": 3, "files": []},
            ]
        )

        state = {
            "inbox_dir": str(inbox),
            "graduation_threshold": 3,
            "proposals": wrapper,
        }
        result = write_proposals(state)

        assert result["written_count"] == 1

    @pytest.mark.req("REQ-YG-070")
    def test_uses_to_serializable_import(self):
        """FR-186: philosopher/tools.py must import to_serializable from contrib."""
        import inspect

        import examples.philosopher.tools as mod

        source = inspect.getsource(mod)
        assert "from yamlgraph.contrib import to_serializable" in source
        assert "to_serializable(" in source
