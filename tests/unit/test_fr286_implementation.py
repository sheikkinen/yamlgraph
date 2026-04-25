"""Implementation tests for FR-286: Watcher2 AMEND Retry Loop.

Tests that validate the AMEND retry loop functionality works correctly
with proper retry limits, feedback extraction, and commit patterns.

These tests target the implementation and should PASS (GREEN phase).
"""

import subprocess
from pathlib import Path
import tempfile
import json
import os

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
WATCHER2_SH = REPO_ROOT / ".chaplain" / "watcher2.sh"


@pytest.mark.req("REQ-YG-310")
class TestWatcher2AmendRetryImplementation:
    """Test AMEND retry loop functionality implementation."""

    def test_amend_retry_functions_exist(self):
        """Validate that AMEND retry functions are implemented."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # These functions should now exist
        required_functions = [
            "extract_judge_feedback",
            "run_revision_step", 
            "commit_revision_attempt",
            "handle_amend_verdict",
            "handle_exhausted_amend_retries"
        ]
        
        for func in required_functions:
            assert func in watcher2_content, f"Function {func} should be implemented"
            # Verify it's actually a function definition
            assert f"{func}()" in watcher2_content, f"Function {func}() definition should exist"

    def test_max_retries_constant_defined(self):
        """Validate MAX_AMEND_RETRIES is defined with correct value."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Should define MAX_AMEND_RETRIES=2
        assert "MAX_AMEND_RETRIES=2" in watcher2_content, "MAX_AMEND_RETRIES should be set to 2"

    def test_step_revise_graph_exists(self):
        """Validate step-revise.yaml graph file exists."""
        revise_graph = REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "step-revise.yaml"
        assert revise_graph.exists(), "step-revise.yaml should exist"
        
        # Verify it has the expected structure
        content = revise_graph.read_text()
        assert "name: watcher-revise" in content, "Graph should have correct name"
        assert "type: copilot" in content, "Graph should use copilot node"
        assert "prompt: revise" in content, "Graph should use revise prompt"

    def test_revise_prompt_exists(self):
        """Validate revise.yaml prompt file exists."""
        revise_prompt = REPO_ROOT / ".chaplain" / "graphs" / "copilot" / "prompts" / "revise.yaml"
        assert revise_prompt.exists(), "revise.yaml prompt should exist"
        
        # Verify it has the expected content
        content = revise_prompt.read_text()
        assert "judge_feedback" in content, "Prompt should accept judge_feedback parameter"
        assert "feature request reviser" in content.lower(), "Prompt should identify as reviser"

    def test_amend_handling_separated_from_split(self):
        """Validate AMEND and SPLIT have separate handling logic."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Should have separate AMEND condition
        assert 'if [[ "$VERDICT" == "AMEND" ]]' in watcher2_content, "AMEND should have separate condition"
        
        # Should still have SPLIT condition but separate
        assert 'if [[ "$VERDICT" == "SPLIT" ]]' in watcher2_content, "SPLIT should have separate condition"
        
        # Should NOT have combined condition anymore
        assert 'if [[ "$VERDICT" == "AMEND" || "$VERDICT" == "SPLIT" ]]' not in watcher2_content, "Combined AMEND/SPLIT condition should be removed"

    def test_amend_calls_handle_amend_verdict(self):
        """Validate AMEND verdict calls handle_amend_verdict function."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Find the main judge section where AMEND handling occurs
        # Look for the specific AMEND handling after judge verdict extraction
        judge_section_marker = "log_info \"Judge verdict: $VERDICT\""
        judge_start = watcher2_content.find(judge_section_marker)
        assert judge_start != -1, "Judge verdict section should exist"
        
        # Look for AMEND handling after the judge verdict logging
        amend_section_start = watcher2_content.find('if [[ "$VERDICT" == "AMEND" ]]', judge_start)
        assert amend_section_start != -1, "AMEND condition should exist in judge section"
        
        # Find the corresponding fi for this AMEND condition
        next_fi = watcher2_content.find("    fi", amend_section_start)  # Matching indentation
        amend_section = watcher2_content[amend_section_start:next_fi + 6]  
        
        assert "handle_amend_verdict" in amend_section, f"AMEND section should call handle_amend_verdict. Found: {amend_section}"

    def test_split_still_calls_handle_failure(self):
        """Validate SPLIT verdict still calls handle_failure (unchanged behavior)."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Find SPLIT handling section
        split_section_start = watcher2_content.find('if [[ "$VERDICT" == "SPLIT" ]]')
        assert split_section_start != -1, "SPLIT condition should exist"
        
        # Look for handle_failure call within SPLIT section
        next_fi = watcher2_content.find("fi", split_section_start)
        split_section = watcher2_content[split_section_start:next_fi + 20]
        
        assert 'handle_failure "judge $VERDICT"' in split_section, "SPLIT should still call handle_failure"

    def test_revision_commit_message_pattern(self):
        """Validate revision commit message pattern is implemented."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Should have the revision commit message pattern
        expected_pattern = "FR revision (AMEND retry"
        assert expected_pattern in watcher2_content, "Revision commit message pattern should be implemented"

    def test_extract_judge_feedback_function_implementation(self):
        """Validate extract_judge_feedback function has proper implementation."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Find the function
        func_start = watcher2_content.find("extract_judge_feedback() {")
        assert func_start != -1, "extract_judge_feedback function should exist"
        
        # Check it uses judge_result from pipeline state
        func_end = watcher2_content.find("}", func_start)
        func_body = watcher2_content[func_start:func_end]
        
        assert "judge_result" in func_body, "Function should access judge_result from state"
        assert "PIPELINE_STATE" in func_body, "Function should read from PIPELINE_STATE"

    def test_handle_amend_verdict_retry_logic(self):
        """Validate handle_amend_verdict has proper retry loop logic."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Find the function
        func_start = watcher2_content.find("handle_amend_verdict() {")
        assert func_start != -1, "handle_amend_verdict function should exist"
        
        func_end = watcher2_content.find("}", func_start)
        func_body = watcher2_content[func_start:func_end]
        
        # Should have retry loop
        assert 'while [[ "$VERDICT" == "AMEND"' in func_body, "Should have AMEND retry loop"
        assert "AMEND_RETRIES" in func_body, "Should track retry count"
        assert "MAX_AMEND_RETRIES" in func_body, "Should check max retries"
        
        # Should call revision and judge steps
        assert "run_revision_step" in func_body, "Should call revision step"
        assert "step-judge.yaml" in func_body, "Should re-run judge step"

    def test_exhausted_retries_calls_handle_failure(self):
        """Validate that exhausted retries still call handle_failure."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Should call handle_failure when retries exhausted
        assert 'handle_failure "judge AMEND (exhausted retries)"' in watcher2_content, "Exhausted retries should call handle_failure with specific message"


@pytest.mark.req("REQ-YG-310") 
class TestWatcher2AmendRetryIntegration:
    """Integration tests for AMEND retry functionality."""

    def test_functions_can_be_declared(self):
        """Test that the functions are declared properly (syntax check without sourcing)."""
        # Just check that the functions are syntactically valid by checking their definitions
        watcher2_content = WATCHER2_SH.read_text()
        
        required_functions = [
            "extract_judge_feedback() {",
            "run_revision_step() {",
            "commit_revision_attempt() {",
            "handle_amend_verdict() {",
            "handle_exhausted_amend_retries() {"
        ]
        
        for func_def in required_functions:
            assert func_def in watcher2_content, f"Function definition {func_def} should exist"
        
        # Check basic syntax by running bash -n on the script
        result = subprocess.run(
            ["bash", "-n", str(WATCHER2_SH)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script should have valid syntax. Error: {result.stderr}"

    def test_extract_judge_feedback_function_structure(self):
        """Test extract_judge_feedback function structure without execution."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Find the function
        func_start = watcher2_content.find("extract_judge_feedback() {")
        assert func_start != -1, "extract_judge_feedback function should exist"
        
        func_end = watcher2_content.find("}", func_start)
        func_body = watcher2_content[func_start:func_end]
        
        # Verify it contains the expected structure
        assert "python3 -c" in func_body, "Function should use python3 for JSON parsing"
        assert "judge_result" in func_body, "Function should access judge_result"
        assert "PIPELINE_STATE" in func_body, "Function should use PIPELINE_STATE variable"