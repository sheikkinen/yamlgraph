"""Tests for CI dependency security scan workflow (FR-187).

Validates that `.github/workflows/security.yml` contains a `security` job
that runs `pip-audit --strict --desc` on every PR and tag push.

Two test layers:
1. YAML structure — parse the workflow and verify job config, triggers, steps.
2. Documentation — verify CLAUDE.md documents the `security` status check.
"""

import pytest
import yaml

WORKFLOW_PATH = ".github/workflows/security.yml"


def _load_workflow() -> dict:
    """Load and parse the security workflow YAML."""
    with open(WORKFLOW_PATH) as f:
        return yaml.safe_load(f)


# ── YAML Structure Tests ───────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-186")
class TestSecurityWorkflowExists:
    """Verify the security workflow file exists and is valid YAML."""

    def test_workflow_file_exists(self) -> None:
        """The security workflow file must exist."""
        import os

        assert os.path.isfile(
            WORKFLOW_PATH
        ), f"Missing {WORKFLOW_PATH} — FR-187 requires a security workflow"

    def test_workflow_is_valid_yaml(self) -> None:
        """The workflow must be parseable YAML."""
        wf = _load_workflow()
        assert isinstance(wf, dict), "Workflow must be a YAML mapping"


@pytest.mark.req("REQ-YG-186")
class TestSecurityWorkflowTriggers:
    """Verify the workflow triggers on PRs and version tag pushes."""

    def test_pull_request_trigger(self) -> None:
        """The workflow must trigger on pull_request events."""
        wf = _load_workflow()
        assert "pull_request" in wf.get(
            "on", wf.get(True, {})
        ), "Workflow must trigger on pull_request"

    def test_pull_request_event_types(self) -> None:
        """PR trigger must include opened, synchronize, reopened."""
        wf = _load_workflow()
        on = wf.get("on", wf.get(True, {}))
        pr_config = on["pull_request"]
        types = pr_config.get("types", [])
        for event_type in ["opened", "synchronize", "reopened"]:
            assert (
                event_type in types
            ), f"pull_request trigger must include '{event_type}'"

    def test_tag_push_trigger(self) -> None:
        """The workflow must trigger on version tag pushes (v*.*.*)."""
        wf = _load_workflow()
        on = wf.get("on", wf.get(True, {}))
        push_config = on.get("push", {})
        tags = push_config.get("tags", [])
        assert "v*.*.*" in tags, "Workflow must trigger on push tags matching 'v*.*.*'"


@pytest.mark.req("REQ-YG-186")
class TestSecurityWorkflowPermissions:
    """Verify the workflow has minimal permissions."""

    def test_contents_read_permission(self) -> None:
        """The workflow must request only contents: read permission."""
        wf = _load_workflow()
        perms = wf.get("permissions", {})
        assert (
            perms.get("contents") == "read"
        ), "Workflow must have 'contents: read' permission"


@pytest.mark.req("REQ-YG-186")
class TestSecurityJobStructure:
    """Verify the security job has the correct structure."""

    def test_security_job_exists(self) -> None:
        """The workflow must contain a 'security' job."""
        wf = _load_workflow()
        assert "security" in wf.get(
            "jobs", {}
        ), "Missing 'security' job in security.yml"

    def test_runs_on_ubuntu(self) -> None:
        """The security job must run on ubuntu-latest."""
        wf = _load_workflow()
        job = wf["jobs"]["security"]
        assert job["runs-on"] == "ubuntu-latest"

    def test_checkout_step(self) -> None:
        """The job must check out the repository."""
        wf = _load_workflow()
        steps = wf["jobs"]["security"]["steps"]
        checkout_steps = [
            s for s in steps if s.get("uses", "").startswith("actions/checkout")
        ]
        assert checkout_steps, "Must have an actions/checkout step"

    def test_python_setup_step(self) -> None:
        """The job must set up Python."""
        wf = _load_workflow()
        steps = wf["jobs"]["security"]["steps"]
        python_steps = [
            s for s in steps if s.get("uses", "").startswith("actions/setup-python")
        ]
        assert python_steps, "Must have an actions/setup-python step"

    def test_install_dependencies_step(self) -> None:
        """The job must install project dependencies and pip-audit."""
        wf = _load_workflow()
        steps = wf["jobs"]["security"]["steps"]
        install_steps = [
            s for s in steps if "run" in s and "pip-audit" in s.get("run", "")
        ]
        assert install_steps, "Must have a step that installs pip-audit"

    def test_pip_audit_step(self) -> None:
        """The job must run pip-audit with --strict and --desc flags."""
        wf = _load_workflow()
        steps = wf["jobs"]["security"]["steps"]
        audit_steps = [
            s
            for s in steps
            if "run" in s
            and "pip-audit" in s["run"]
            and "--strict" in s["run"]
            and "--desc" in s["run"]
        ]
        assert audit_steps, "Must have a step that runs 'pip-audit --strict --desc'"


# ── Documentation Tests ───────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-186")
class TestSecurityDocumentation:
    """Verify that CLAUDE.md documents the security status check."""

    def test_security_in_branch_protection_table(self) -> None:
        """The branch protection table must list 'security' as a required check."""
        with open("CLAUDE.md") as f:
            content = f.read()
        # The table row for required status checks should include 'security'
        assert "`security`" in content, "CLAUDE.md must mention `security` status check"

    def test_security_in_status_checks_list(self) -> None:
        """The required status checks list must describe the security job."""
        with open("CLAUDE.md") as f:
            content = f.read()
        assert (
            "pip-audit" in content
        ), "CLAUDE.md must describe pip-audit in the security status check entry"
        assert (
            "security.yml" in content
        ), "CLAUDE.md must reference security.yml workflow"
