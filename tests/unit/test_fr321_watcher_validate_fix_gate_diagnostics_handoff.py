"""Acceptance tests for FR-321 watcher validate-fix gate diagnostics handoff."""

from pathlib import Path

import pytest
import yaml
from jinja2 import Template

pytestmark = pytest.mark.process

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
VALIDATE_SESSION_GRAPH = (
    CHAPLAIN / "graphs" / "watcher-enforce" / "validate-session.yaml"
)
VALIDATE_PROMPT = (
    CHAPLAIN / "graphs" / "watcher-enforce" / "prompts" / "validate-session.yaml"
)


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"Missing YAML file: {path}"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _transition_exists(
    transitions: list[dict], from_state: str, to_state: str, event: str
) -> bool:
    return any(
        t.get("from") == from_state
        and t.get("to") == to_state
        and t.get("event") == event
        for t in transitions
    )


@pytest.mark.req("REQ-YG-318")
class TestFR321ValidateFixGateDiagnosticsHandoff:
    """AC-01..AC-05 contracts for validate diagnostics handoff."""

    def test_ac01_validate_fix_action_passes_validate_gate_output_var(self):
        pipeline = _load_yaml(PIPELINE_V2)
        action = pipeline["actions"]["validate_fix"][0]
        assert "validate_gate_output" in action["vars"]
        assert action["vars"]["validate_gate_output"] == "{validate_gate_output}"

    def test_ac02_validate_session_graph_declares_validate_gate_output_state_and_variable(
        self,
    ):
        graph = _load_yaml(VALIDATE_SESSION_GRAPH)
        assert graph["state"]["validate_gate_output"] == "str"
        variables = graph["nodes"]["validate_fix"]["variables"]
        assert variables["validate_gate_output"] == "{state.validate_gate_output}"

    def test_ac03_validate_prompt_renders_validate_gate_diagnostics_section(self):
        prompt_yaml = _load_yaml(VALIDATE_PROMPT)
        template = Template(prompt_yaml["user"])
        rendered = template.render(
            fr_path="feature-requests/FR-321.md",
            worktree_dir="/tmp/worktree",
            branch="feat/x",
            precommit_output="ruff failed",
            validate_gate_output='{"checks":[{"name":"diary_parity","status":"failed"}],"failures":["diary_parity"]}',
        )
        assert "Validate-gate diagnostics (checks/failures)" in rendered
        assert "diary_parity" in rendered

    def test_ac04_validate_prompt_handles_literal_precommit_placeholder_as_first_pass(
        self,
    ):
        prompt_yaml = _load_yaml(VALIDATE_PROMPT)
        template = Template(prompt_yaml["user"])
        rendered = template.render(
            fr_path="feature-requests/FR-321.md",
            worktree_dir="/tmp/worktree",
            branch="feat/x",
            precommit_output="{precommit_output}",
            validate_gate_output="",
        )
        assert "first validate_fix pass — no prior gate diagnostics" in rendered
        assert "The previous validate_gate/pre-commit attempt reported:" not in rendered
        assert "{precommit_output}" not in rendered

    def test_ac05_validate_gate_retry_topology_unchanged(self):
        pipeline = _load_yaml(PIPELINE_V2)
        transitions = pipeline.get("transitions", [])
        assert _transition_exists(
            transitions, "validate_gate", "validate_fix", "fix_needed"
        )
        assert _transition_exists(transitions, "validate_gate", "done", "pass")
        assert _transition_exists(transitions, "validate_gate", "failed", "error")
        assert _transition_exists(
            transitions, "validate_fix", "sanity_check", "validate_done"
        )
