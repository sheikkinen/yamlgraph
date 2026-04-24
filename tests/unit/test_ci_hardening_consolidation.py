"""Tests for CI hardening consolidation (FR-196).

Validates that GitHub Actions workflows have been hardened with:
- Concurrency control (cancel-in-progress)
- Dependency caching (pip cache)
- Workflow naming improvements
- Version validation on tags
- Security scan resilience (retry mechanism)
- Python version matrix (3.11, 3.12)
- Preserved existing behavior

Test layers:
1. YAML structure — parse workflows and verify configuration
2. Behavioral preservation — ensure existing job dependencies/triggers maintained
"""

from pathlib import Path

import pytest
import yaml

WORKFLOW_DIR = Path(".github/workflows")
EXPECTED_WORKFLOWS = ["workflow.yml", "security.yml", "commitlint.yml"]


def _load_workflow(filename: str) -> dict:
    """Load and parse a GitHub Actions workflow YAML file."""
    workflow_path = WORKFLOW_DIR / filename
    with open(workflow_path) as f:
        return yaml.safe_load(f)


def _get_all_setup_python_steps(workflow: dict) -> list[dict]:
    """Extract all setup-python steps from a workflow."""
    setup_python_steps = []

    for _job_name, job in workflow.get("jobs", {}).items():
        for step in job.get("steps", []):
            if step.get("uses", "").startswith("actions/setup-python"):
                setup_python_steps.append(step)

    return setup_python_steps


# ── AC-01: Concurrency Groups ─────────────────────────────────────────────


@pytest.mark.req("REQ-YG-277")
class TestConcurrencyGroups:
    """AC-01: All workflows have concurrency groups with cancel-in-progress."""

    def test_workflow_yml_has_concurrency_control(self) -> None:
        """Main workflow.yml should have concurrency group with cancel-in-progress."""
        workflow = _load_workflow("workflow.yml")

        assert "concurrency" in workflow, "workflow.yml missing concurrency section"
        concurrency = workflow["concurrency"]

        assert "group" in concurrency, "concurrency section missing group"
        assert (
            "cancel-in-progress" in concurrency
        ), "concurrency section missing cancel-in-progress"
        assert (
            concurrency["cancel-in-progress"] is True
        ), "cancel-in-progress should be true"

    def test_security_yml_has_concurrency_control(self) -> None:
        """Security workflow should have concurrency group with cancel-in-progress."""
        workflow = _load_workflow("security.yml")

        assert "concurrency" in workflow, "security.yml missing concurrency section"
        concurrency = workflow["concurrency"]

        assert "group" in concurrency, "concurrency section missing group"
        assert (
            "cancel-in-progress" in concurrency
        ), "concurrency section missing cancel-in-progress"
        assert (
            concurrency["cancel-in-progress"] is True
        ), "cancel-in-progress should be true"

    def test_commitlint_yml_has_concurrency_control(self) -> None:
        """Commitlint workflow should have concurrency group with cancel-in-progress."""
        workflow = _load_workflow("commitlint.yml")

        assert "concurrency" in workflow, "commitlint.yml missing concurrency section"
        concurrency = workflow["concurrency"]

        assert "group" in concurrency, "concurrency section missing group"
        assert (
            "cancel-in-progress" in concurrency
        ), "concurrency section missing cancel-in-progress"
        assert (
            concurrency["cancel-in-progress"] is True
        ), "cancel-in-progress should be true"


# ── AC-02: Pip Caching ────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-277")
class TestPipCaching:
    """AC-02: All setup-python steps include cache: pip."""

    def test_workflow_yml_setup_python_has_cache(self) -> None:
        """All setup-python steps in workflow.yml should have cache: pip."""
        workflow = _load_workflow("workflow.yml")
        setup_python_steps = _get_all_setup_python_steps(workflow)

        assert (
            len(setup_python_steps) > 0
        ), "workflow.yml should have at least one setup-python step"

        for step in setup_python_steps:
            with_section = step.get("with", {})
            assert "cache" in with_section, f"setup-python step missing cache: {step}"
            assert (
                with_section["cache"] == "pip"
            ), f"cache should be 'pip', got: {with_section.get('cache')}"

    def test_security_yml_setup_python_has_cache(self) -> None:
        """All setup-python steps in security.yml should have cache: pip."""
        workflow = _load_workflow("security.yml")
        setup_python_steps = _get_all_setup_python_steps(workflow)

        assert (
            len(setup_python_steps) > 0
        ), "security.yml should have at least one setup-python step"

        for step in setup_python_steps:
            with_section = step.get("with", {})
            assert "cache" in with_section, f"setup-python step missing cache: {step}"
            assert (
                with_section["cache"] == "pip"
            ), f"cache should be 'pip', got: {with_section.get('cache')}"

    def test_commitlint_yml_setup_python_has_cache(self) -> None:
        """All setup-python steps in commitlint.yml should have cache: pip."""
        workflow = _load_workflow("commitlint.yml")
        setup_python_steps = _get_all_setup_python_steps(workflow)

        # commitlint.yml may not have setup-python steps, so this test should pass if none exist
        for step in setup_python_steps:
            with_section = step.get("with", {})
            assert "cache" in with_section, f"setup-python step missing cache: {step}"
            assert (
                with_section["cache"] == "pip"
            ), f"cache should be 'pip', got: {with_section.get('cache')}"


# ── AC-03: Workflow Naming ────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-277")
class TestWorkflowNaming:
    """AC-03: Main workflow renamed from 'Release to PyPI' to 'CI'."""

    def test_workflow_yml_renamed_to_ci(self) -> None:
        """workflow.yml name should be 'CI', not 'Release to PyPI'."""
        workflow = _load_workflow("workflow.yml")

        workflow_name = workflow.get("name", "")
        assert (
            workflow_name == "CI"
        ), f"Workflow name should be 'CI', got: '{workflow_name}'"
        assert (
            workflow_name != "Release to PyPI"
        ), "Workflow should no longer be named 'Release to PyPI'"


# ── AC-04: Version Validation ─────────────────────────────────────────────


@pytest.mark.req("REQ-YG-277")
class TestVersionValidation:
    """AC-04: Tag pushes validate version matches pyproject.toml."""

    def test_version_validation_on_tag_push(self) -> None:
        """workflow.yml should validate tag version against pyproject.toml on tag pushes."""
        workflow = _load_workflow("workflow.yml")

        # Check if there are any jobs that run on tag pushes
        tag_triggered_jobs = []
        for job_name, job in workflow.get("jobs", {}).items():
            # Look for jobs that have tag-related conditions or run unconditionally on tag pushes
            if_condition = job.get("if", "")
            if (
                "tag" in if_condition.lower()
                or "github.ref" in if_condition
                or "startsWith(github.ref, 'refs/tags/'" in if_condition
            ):
                tag_triggered_jobs.append(job_name)

        assert (
            len(tag_triggered_jobs) > 0
        ), "workflow.yml should have jobs that run on tag pushes"

        # Look for version validation steps in tag-triggered jobs
        has_version_validation = False
        for job_name in tag_triggered_jobs:
            job = workflow["jobs"][job_name]
            for step in job.get("steps", []):
                step_name = step.get("name", "").lower()
                step_run = step.get("run", "").lower()

                if ("version" in step_name and "validate" in step_name) or (
                    "pyproject" in step_run and "version" in step_run
                ):
                    has_version_validation = True
                    break

            if has_version_validation:
                break

        assert (
            has_version_validation
        ), "Tag pushes should include version validation against pyproject.toml"


# ── AC-05: Security Scan Retry ────────────────────────────────────────────


@pytest.mark.req("REQ-YG-277")
class TestSecurityScanRetry:
    """AC-05: pip-audit has retry mechanism (3 attempts, 30s intervals)."""

    def test_pip_audit_has_retry_mechanism(self) -> None:
        """security.yml should use retry action for pip-audit with 3 attempts and 30s intervals."""
        workflow = _load_workflow("security.yml")

        # Look for pip-audit steps with retry mechanism
        has_retry_pip_audit = False
        for _job_name, job in workflow.get("jobs", {}).items():
            for step in job.get("steps", []):
                uses = step.get("uses", "")
                step_run = step.get("run", "")

                # Check for retry action with pip-audit
                if "retry" in uses.lower() and "pip-audit" in step.get("with", {}).get(
                    "command", ""
                ):
                    with_section = step["with"]
                    max_attempts = with_section.get("max_attempts", 0)
                    retry_wait = with_section.get("retry_wait_seconds", 0)

                    assert (
                        max_attempts == 3
                    ), f"pip-audit retry should have 3 max_attempts, got: {max_attempts}"
                    assert (
                        retry_wait == 30
                    ), f"pip-audit retry should have 30s wait, got: {retry_wait}"
                    has_retry_pip_audit = True
                    break

                # Alternative: direct pip-audit with manual retry logic
                elif "pip-audit" in step_run and "retry" in step_run.lower():
                    has_retry_pip_audit = True
                    break

            if has_retry_pip_audit:
                break

        assert (
            has_retry_pip_audit
        ), "security.yml should use retry mechanism for pip-audit"


# ── AC-06: Python Version Matrix ──────────────────────────────────────────


@pytest.mark.req("REQ-YG-277")
class TestPythonVersionMatrix:
    """AC-06: Test matrix includes Python 3.11 and 3.12."""

    def test_workflow_yml_has_python_matrix(self) -> None:
        """workflow.yml should test against Python 3.11 and 3.12 in matrix."""
        workflow = _load_workflow("workflow.yml")

        # Look for matrix strategy with python-version
        has_python_matrix = False
        python_versions = []

        for _job_name, job in workflow.get("jobs", {}).items():
            strategy = job.get("strategy", {})
            matrix = strategy.get("matrix", {})

            if "python-version" in matrix:
                python_versions = matrix["python-version"]
                has_python_matrix = True
                break

        assert (
            has_python_matrix
        ), "workflow.yml should have a matrix strategy with python-version"
        assert "3.11" in python_versions, "Matrix should include Python 3.11"
        assert "3.12" in python_versions, "Matrix should include Python 3.12"


# ── AC-07: Preserve Job Dependencies ──────────────────────────────────────


@pytest.mark.req("REQ-YG-277")
class TestJobDependenciesPreserved:
    """AC-07: All existing jobs maintain their current dependencies and triggers."""

    def test_workflow_yml_job_dependencies(self) -> None:
        """workflow.yml should maintain existing job dependency structure."""
        workflow = _load_workflow("workflow.yml")
        jobs = workflow.get("jobs", {})

        # Verify key job dependencies still exist
        if "build" in jobs and "test" in jobs:
            build_job = jobs["build"]
            assert "needs" in build_job, "build job should have 'needs' dependency"
            needs = build_job["needs"]
            if isinstance(needs, str):
                needs = [needs]
            assert "test" in needs, "build job should depend on test job"

        if "publish" in jobs and "build" in jobs:
            publish_job = jobs["publish"]
            assert "needs" in publish_job, "publish job should have 'needs' dependency"
            needs = publish_job["needs"]
            if isinstance(needs, str):
                needs = [needs]
            assert "build" in needs, "publish job should depend on build job"

    def test_workflow_yml_trigger_conditions(self) -> None:
        """workflow.yml should maintain existing trigger conditions."""
        workflow = _load_workflow("workflow.yml")

        # Should still trigger on pull requests and tag pushes
        on_triggers = workflow.get("on", {})
        assert "pull_request" in on_triggers, "Should still trigger on pull_request"
        assert "push" in on_triggers, "Should still trigger on push"

        push_triggers = on_triggers.get("push", {})
        if "tags" in push_triggers:
            tags = push_triggers["tags"]
            assert any(
                "v*" in tag for tag in tags
            ), "Should still trigger on version tags"


# ── AC-08: Security Scan Blocking ─────────────────────────────────────────


@pytest.mark.req("REQ-YG-277")
class TestSecurityScanBlocking:
    """AC-08: Security scan still blocks on vulnerabilities found."""

    def test_pip_audit_still_uses_strict_mode(self) -> None:
        """security.yml should still use pip-audit --strict to block on vulnerabilities."""
        workflow = _load_workflow("security.yml")

        # Look for pip-audit with --strict flag
        has_strict_pip_audit = False
        for _job_name, job in workflow.get("jobs", {}).items():
            for step in job.get("steps", []):
                step_run = step.get("run", "")
                command = step.get("with", {}).get("command", "")

                if (
                    "pip-audit" in step_run
                    and "--strict" in step_run
                    or "pip-audit" in command
                    and "--strict" in command
                ):
                    has_strict_pip_audit = True
                    break

            if has_strict_pip_audit:
                break

        assert has_strict_pip_audit, "security.yml should still use pip-audit --strict"


# ── AC-09: Release Process Unchanged ──────────────────────────────────────


@pytest.mark.req("REQ-YG-277")
class TestReleaseProcessUnchanged:
    """AC-09: Release process remains unchanged (tag push → test → build → publish → release)."""

    def test_release_job_sequence_preserved(self) -> None:
        """workflow.yml should maintain the release job sequence."""
        workflow = _load_workflow("workflow.yml")
        jobs = workflow.get("jobs", {})

        # Verify release jobs still exist
        expected_release_jobs = ["test", "build", "publish", "create-release"]
        existing_release_jobs = [job for job in expected_release_jobs if job in jobs]

        assert (
            len(existing_release_jobs) >= 3
        ), f"Most release jobs should exist, found: {existing_release_jobs}"

        # Verify job sequencing if jobs exist
        if "build" in jobs and "test" in jobs:
            build_needs = jobs["build"].get("needs")
            if isinstance(build_needs, str):
                build_needs = [build_needs]
            assert build_needs and "test" in build_needs, "build should depend on test"

        if "publish" in jobs and "build" in jobs:
            publish_needs = jobs["publish"].get("needs")
            if isinstance(publish_needs, str):
                publish_needs = [publish_needs]
            assert (
                publish_needs and "build" in publish_needs
            ), "publish should depend on build"

    def test_tag_triggered_release_conditions(self) -> None:
        """Release jobs should still trigger only on version tags."""
        workflow = _load_workflow("workflow.yml")
        jobs = workflow.get("jobs", {})

        tag_conditional_jobs = ["build", "publish", "create-release"]

        for job_name in tag_conditional_jobs:
            if job_name in jobs:
                job = jobs[job_name]
                if_condition = job.get("if", "")

                # Should have tag-related conditions
                assert (
                    "tag" in if_condition.lower() or "refs/tags/" in if_condition
                ), f"{job_name} should only run on tags"
