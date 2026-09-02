"""RED acceptance tests for FR-329 Agent SDK planner spike."""

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

WORKTREE = Path(__file__).resolve().parents[2]
SCRIPT_PATH = WORKTREE / "examples" / "agent-sdk-planner" / "plan.py"
README_PATH = WORKTREE / "examples" / "agent-sdk-planner" / "README.md"
TEMPLATE_PATH = WORKTREE / "feature-requests" / "TEMPLATE.md"
RUNTIME_SCOPE_FILES = [
    WORKTREE / "yamlgraph" / "node_factory" / "copilot_node.py",
    WORKTREE / ".chaplain" / "graphs" / "watcher-plan" / "step-plan-unified.yaml",
    WORKTREE / ".chaplain" / "config" / "watcher-pipeline-v2.yaml",
]


def _script_text() -> str:
    assert SCRIPT_PATH.exists(), f"Missing planner script: {SCRIPT_PATH}"
    return SCRIPT_PATH.read_text(encoding="utf-8")


@pytest.mark.req("REQ-YG-087")
class TestFR329AgentSdkPlannerSpike:
    """AC-01..AC-09 planning contract for the standalone spike."""

    def test_ac01_planner_script_exists_and_requires_topic_argument(self) -> None:
        assert SCRIPT_PATH.exists(), f"Missing planner script: {SCRIPT_PATH}"
        completed = subprocess.run(
            ["python", str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0
        assert "topic" in (completed.stdout + completed.stderr).lower()

    def test_ac03_next_fr_number_tool_contract_is_present(self) -> None:
        text = _script_text()
        assert "next_fr_number" in text
        assert "feature-requests" in text
        assert "FR-" in text

    def test_ac04_read_fr_template_tool_contract_is_present(self) -> None:
        text = _script_text()
        assert TEMPLATE_PATH.exists(), f"Missing FR template: {TEMPLATE_PATH}"
        assert "read_fr_template" in text
        assert "TEMPLATE.md" in text

    def test_ac05_output_contract_requires_draft_status(self) -> None:
        text = _script_text()
        assert "feature-requests/FR-" in text or "feature-requests" in text
        assert "Draft" in text

    def test_ac06_post_tool_use_hook_contract_is_present(self) -> None:
        text = _script_text()
        assert "PostToolUse" in text
        assert "audit" in text.lower()

    def test_ac09_scope_isolation_contract(self) -> None:
        assert SCRIPT_PATH.exists(), f"Missing planner script: {SCRIPT_PATH}"
        assert README_PATH.exists(), f"Missing usage doc: {README_PATH}"
        for path in RUNTIME_SCOPE_FILES:
            assert path.exists(), f"Missing runtime scope file: {path}"
