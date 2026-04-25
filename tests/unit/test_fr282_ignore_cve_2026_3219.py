"""Acceptance tests for FR-282: Temporary ignore CVE-2026-3219 in pip-audit.

This feature modifies .github/workflows/security.yml to temporarily ignore
CVE-2026-3219 until a pip fix is available. The tests verify:

1. The pip-audit command includes --ignore-vuln CVE-2026-3219 flag
2. Comment explains the ignore with CVE reference and date added  
3. TODO marker documents removal condition when pip fix is released
4. Security gate structure remains intact (still validates other vulnerabilities)
5. Proper documentation and rationale are present

These tests MUST FAIL on the unmodified codebase to demonstrate that the
acceptance criteria are not yet satisfied.
"""

import pytest
import yaml

WORKFLOW_PATH = ".github/workflows/security.yml"


def _load_workflow() -> dict:
    """Load and parse the security workflow YAML."""
    with open(WORKFLOW_PATH) as f:
        return yaml.safe_load(f)


@pytest.mark.req("REQ-YG-186")
class TestFR282CVEIgnore:
    """Test that CVE-2026-3219 is ignored in pip-audit command."""

    def test_pip_audit_includes_ignore_vuln_flag(self) -> None:
        """AC-01: pip-audit command includes --ignore-vuln CVE-2026-3219 flag."""
        wf = _load_workflow()
        steps = wf["jobs"]["security"]["steps"]
        
        # Find the pip-audit step (could be direct run or retry action)
        pip_audit_commands = []
        
        for step in steps:
            # Direct run command (exclude install steps)
            if "run" in step and "pip-audit" in step["run"] and "install" not in step["run"]:
                pip_audit_commands.append(step["run"])
            # Retry action with command
            elif "uses" in step and "retry" in step["uses"] and "with" in step:
                if "command" in step["with"] and "pip-audit" in step["with"]["command"]:
                    pip_audit_commands.append(step["with"]["command"])
        
        assert pip_audit_commands, "Must find at least one pip-audit execution command"
        
        # Check that at least one command includes the CVE ignore flag
        has_ignore_flag = any(
            "--ignore-vuln CVE-2026-3219" in cmd 
            for cmd in pip_audit_commands
        )
        
        assert has_ignore_flag, (
            "pip-audit command must include '--ignore-vuln CVE-2026-3219' flag. "
            f"Found commands: {pip_audit_commands}"
        )

    def test_comment_explains_cve_ignore_with_date(self) -> None:
        """AC-02: Comment explains the ignore with CVE reference and date added."""
        with open(WORKFLOW_PATH) as f:
            content = f.read()
        
        # Must contain CVE reference in comment
        assert "CVE-2026-3219" in content, (
            "Workflow must contain CVE-2026-3219 reference in comments"
        )
        
        # Must contain date when added
        assert "2026-04-25" in content, (
            "Workflow must document when the ignore was added (2026-04-25)"
        )
        
        # Must explain the vulnerability
        vulnerability_keywords = [
            "pip", "tar+ZIP", "concatenated", "vulnerability"
        ]
        content_lower = content.lower()
        found_keywords = [kw for kw in vulnerability_keywords if kw.lower() in content_lower]
        
        assert len(found_keywords) >= 2, (
            f"Comment must explain the CVE nature. Expected at least 2 of {vulnerability_keywords}, "
            f"found: {found_keywords}"
        )

    def test_todo_marker_documents_removal_condition(self) -> None:
        """AC-03: TODO marker documents removal condition when pip fix is released."""
        with open(WORKFLOW_PATH) as f:
            content = f.read()
        
        # Must have TODO marker
        assert "TODO" in content, "Must contain TODO marker for removal"
        
        # TODO should mention removal/fix
        todo_lines = [line for line in content.split('\n') if 'TODO' in line]
        assert todo_lines, "Must have at least one TODO line"
        
        # Check that TODO is related to CVE and removal
        todo_content = ' '.join(todo_lines).lower()
        
        removal_keywords = ["remove", "when", "fix", "available", "pip"]
        found_removal_keywords = [kw for kw in removal_keywords if kw in todo_content]
        
        assert len(found_removal_keywords) >= 3, (
            f"TODO must document removal condition. Expected at least 3 of {removal_keywords}, "
            f"found: {found_removal_keywords} in TODO lines: {todo_lines}"
        )

    def test_security_gate_structure_preserved(self) -> None:
        """AC-04: Security gate passes on a clean PR (no other vulnerabilities).
        
        This test verifies that the security gate structure is preserved - 
        it still runs pip-audit with --strict and --desc flags, just with
        the additional ignore flag.
        """
        wf = _load_workflow()
        steps = wf["jobs"]["security"]["steps"]
        
        # Find pip-audit command
        pip_audit_commands = []
        for step in steps:
            # Look for pip-audit in run commands, but skip install steps
            if "run" in step and "pip-audit" in step["run"] and "install" not in step["run"]:
                pip_audit_commands.append(step["run"])
            elif "uses" in step and "retry" in step["uses"] and "with" in step:
                if "command" in step["with"] and "pip-audit" in step["with"]["command"]:
                    pip_audit_commands.append(step["with"]["command"])
        
        assert pip_audit_commands, "Must find pip-audit command"
        
        # Verify critical flags are still present
        found_valid_cmd = False
        for cmd in pip_audit_commands:
            if "pip-audit" in cmd and "install" not in cmd:
                assert "--strict" in cmd, f"pip-audit must retain --strict flag: {cmd}"
                assert "--desc" in cmd, f"pip-audit must retain --desc flag: {cmd}"
                found_valid_cmd = True
                break
        
        assert found_valid_cmd, f"No pip-audit execution command found with required flags in: {pip_audit_commands}"

    def test_proper_yaml_structure_after_modification(self) -> None:
        """AC-05: Admin bypass no longer required for CVE-2026-3219-only failures.
        
        This test ensures the YAML structure is valid and the workflow
        can still execute properly after the modification.
        """
        # This test should pass once implemented, verifying YAML is valid
        wf = _load_workflow()
        
        # Basic structure checks
        assert "jobs" in wf, "Workflow must have jobs section"
        assert "security" in wf["jobs"], "Must have security job"
        assert "steps" in wf["jobs"]["security"], "Security job must have steps"
        
        # Verify the workflow is still valid GitHub Actions YAML
        assert wf.get("name") == "Dependency Security Scan", "Workflow name must be preserved"
        assert "pull_request" in wf.get("on", {}), "Must still trigger on PRs"

    def test_ignore_flag_is_specific_to_cve_2026_3219(self) -> None:
        """Verify that only CVE-2026-3219 is ignored, not all vulnerabilities."""
        wf = _load_workflow()
        steps = wf["jobs"]["security"]["steps"]
        
        pip_audit_commands = []
        for step in steps:
            if "run" in step and "pip-audit" in step["run"]:
                pip_audit_commands.append(step["run"])
            elif "uses" in step and "retry" in step["uses"] and "with" in step:
                if "command" in step["with"] and "pip-audit" in step["with"]["command"]:
                    pip_audit_commands.append(step["with"]["command"])
        
        for cmd in pip_audit_commands:
            if "pip-audit" in cmd and "--ignore-vuln" in cmd:
                # Should not have generic ignore patterns
                assert "--ignore-vuln *" not in cmd, "Must not ignore all vulns"
                assert "--ignore-vuln CVE-" not in cmd or "CVE-2026-3219" in cmd, (
                    "Must only ignore the specific CVE-2026-3219"
                )