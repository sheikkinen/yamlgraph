"""Tests for CI conventional commit enforcement workflow.

FR-127: Validates that .github/workflows/commitlint.yml enforces
Conventional Commits on PR titles with type parity against local hooks.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "commitlint.yml"
PRECOMMIT_PATH = REPO_ROOT / ".pre-commit-config.yaml"

EXPECTED_TYPES = sorted(
    [
        "feat",
        "fix",
        "chore",
        "docs",
        "refactor",
        "test",
        "ci",
        "perf",
        "style",
        "build",
        "revert",
    ]
)


def _load_workflow() -> dict:
    """Load and parse the commitlint workflow YAML."""
    assert WORKFLOW_PATH.exists(), f"Workflow file missing: {WORKFLOW_PATH}"
    return yaml.safe_load(WORKFLOW_PATH.read_text())


def _load_precommit() -> dict:
    """Load and parse the pre-commit config YAML."""
    return yaml.safe_load(PRECOMMIT_PATH.read_text())


def _get_precommit_conventional_types() -> list[str]:
    """Extract the conventional-pre-commit args from .pre-commit-config.yaml."""
    config = _load_precommit()
    for repo in config["repos"]:
        if isinstance(repo.get("repo"), str) and "conventional-pre-commit" in repo.get(
            "repo", ""
        ):
            for hook in repo["hooks"]:
                if hook["id"] == "conventional-pre-commit":
                    return sorted(hook["args"])
    raise AssertionError("conventional-pre-commit hook not found in .pre-commit-config.yaml")


@pytest.mark.req("REQ-YG-002")
class TestCommitlintWorkflowExists:
    """Verify the workflow file exists and is valid YAML."""

    def test_workflow_file_exists(self) -> None:
        """commitlint.yml must exist in .github/workflows/."""
        assert WORKFLOW_PATH.exists(), (
            f"Missing: {WORKFLOW_PATH.relative_to(REPO_ROOT)}"
        )

    def test_workflow_is_valid_yaml(self) -> None:
        """The workflow file must be parseable YAML."""
        wf = _load_workflow()
        assert isinstance(wf, dict), "Workflow must be a YAML mapping"


@pytest.mark.req("REQ-YG-002")
class TestWorkflowTrigger:
    """Verify the workflow triggers on correct PR events."""

    def test_triggers_on_pull_request(self) -> None:
        """Workflow must trigger on pull_request events."""
        wf = _load_workflow()
        assert "pull_request" in wf.get("on", wf.get(True, {})), (
            "Workflow must trigger on pull_request"
        )

    def test_triggers_on_required_event_types(self) -> None:
        """Workflow must trigger on opened, edited, synchronize, reopened."""
        wf = _load_workflow()
        pr_config = wf.get("on", wf.get(True, {})).get("pull_request", {})
        event_types = set(pr_config.get("types", []))
        required = {"opened", "edited", "synchronize", "reopened"}
        assert required <= event_types, (
            f"Missing PR event types: {required - event_types}"
        )


@pytest.mark.req("REQ-YG-002")
class TestWorkflowTypes:
    """Verify allowed commit types match expectations."""

    def test_workflow_allows_all_expected_types(self) -> None:
        """The semantic PR action must allow all expected conventional types."""
        wf = _load_workflow()
        steps = wf["jobs"]["commitlint"]["steps"]
        semantic_step = next(
            s for s in steps if "action-semantic-pull-request" in s.get("uses", "")
        )
        types_str = semantic_step["with"]["types"]
        workflow_types = sorted(t.strip() for t in types_str.strip().split("\n") if t.strip())
        assert workflow_types == EXPECTED_TYPES, (
            f"Workflow types {workflow_types} != expected {EXPECTED_TYPES}"
        )

    def test_revert_type_included(self) -> None:
        """The 'revert' type must be in the allowed types list."""
        wf = _load_workflow()
        steps = wf["jobs"]["commitlint"]["steps"]
        semantic_step = next(
            s for s in steps if "action-semantic-pull-request" in s.get("uses", "")
        )
        types_str = semantic_step["with"]["types"]
        types_list = [t.strip() for t in types_str.strip().split("\n") if t.strip()]
        assert "revert" in types_list, "revert must be in allowed types"


@pytest.mark.req("REQ-YG-002")
class TestTypeParity:
    """Verify CI and local hook type lists are in sync."""

    def test_ci_types_match_local_hook_types(self) -> None:
        """Workflow types must match .pre-commit-config.yaml conventional-pre-commit args."""
        wf = _load_workflow()
        steps = wf["jobs"]["commitlint"]["steps"]
        semantic_step = next(
            s for s in steps if "action-semantic-pull-request" in s.get("uses", "")
        )
        types_str = semantic_step["with"]["types"]
        ci_types = sorted(t.strip() for t in types_str.strip().split("\n") if t.strip())

        local_types = _get_precommit_conventional_types()
        assert ci_types == local_types, (
            f"CI types {ci_types} != local hook types {local_types}"
        )

    def test_precommit_includes_revert(self) -> None:
        """The local conventional-pre-commit hook must include 'revert' type."""
        local_types = _get_precommit_conventional_types()
        assert "revert" in local_types, (
            "revert must be in conventional-pre-commit args for parity"
        )


@pytest.mark.req("REQ-YG-002")
class TestFeatFREnforcement:
    """Verify the feat FR-XXX enforcement step."""

    def test_feat_fr_step_exists(self) -> None:
        """A step enforcing FR-XXX on feat PRs must exist."""
        wf = _load_workflow()
        steps = wf["jobs"]["commitlint"]["steps"]
        fr_steps = [s for s in steps if "FR-XXX" in s.get("name", "")]
        assert len(fr_steps) == 1, "Exactly one FR-XXX enforcement step expected"

    def test_feat_fr_step_uses_env_not_inline(self) -> None:
        """The FR-XXX step must use env block (not inline ${{ }}) for security."""
        wf = _load_workflow()
        steps = wf["jobs"]["commitlint"]["steps"]
        fr_step = next(s for s in steps if "FR-XXX" in s.get("name", ""))
        run_script = fr_step.get("run", "")
        assert "$PR_TITLE" in run_script, (
            "Script must reference $PR_TITLE from env block"
        )
        assert "${{" not in run_script, (
            "Script must NOT use ${{ }} inline interpolation (injection risk)"
        )

    def test_feat_fr_step_has_conditional(self) -> None:
        """The FR-XXX step must only run for feat PRs (if condition)."""
        wf = _load_workflow()
        steps = wf["jobs"]["commitlint"]["steps"]
        fr_step = next(s for s in steps if "FR-XXX" in s.get("name", ""))
        assert "if" in fr_step, "FR-XXX step must have an 'if' condition"
        assert "feat" in fr_step["if"], "if condition must check for 'feat'"

    def test_feat_fr_step_checks_fr_pattern(self) -> None:
        """The FR-XXX step script must grep for FR-[0-9]+ pattern."""
        wf = _load_workflow()
        steps = wf["jobs"]["commitlint"]["steps"]
        fr_step = next(s for s in steps if "FR-XXX" in s.get("name", ""))
        run_script = fr_step.get("run", "")
        assert "FR-[0-9]" in run_script, (
            "Script must check for FR-[0-9]+ pattern"
        )


@pytest.mark.req("REQ-YG-002")
class TestWorkflowPermissions:
    """Verify the workflow has minimal required permissions."""

    def test_has_pull_requests_read_permission(self) -> None:
        """Workflow must declare pull-requests: read permission."""
        wf = _load_workflow()
        perms = wf.get("permissions", {})
        assert perms.get("pull-requests") == "read", (
            "Workflow must have pull-requests: read permission"
        )
