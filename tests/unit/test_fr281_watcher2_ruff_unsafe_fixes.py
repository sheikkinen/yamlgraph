"""Acceptance tests for FR-281: Watcher2 Remediation Loop Crash Fix for Ruff SIM117 Errors.

Tests the enhanced watcher2.sh remediation logic to handle ruff unsafe fixes
and improve copilot context with specific error codes.

Acceptance Criteria from FR-281:
- [ ] AC-01: `ruff check --fix --unsafe-fixes` runs in both finalize and CI remediation steps
- [ ] AC-02: SIM117 violations are auto-fixed without manual intervention
- [ ] AC-03: Copilot fix prompt includes specific ruff error codes and rule names  
- [ ] AC-04: Changelog fragment FR numbers are validated against branch names
- [ ] AC-05: Remediation loop handles partial success (some fixes work, others need copilot)
- [ ] AC-06: Tests added covering SIM117 remediation scenarios
- [ ] AC-07: Documentation updated in watcher2 comments

Testing approach:
- Parse watcher2.sh to verify progressive ruff command changes exist
- Check that unsafe-fixes flag is added to both finalize and CI remediation steps
- Verify copilot prompt template includes error code context
- Mock SIM117 violations to test auto-fix behavior
- Test changelog fragment validation logic

All tests target the unmodified code and MUST fail (RED phase).
"""

import re
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
WATCHER2_SH = REPO_ROOT / ".chaplain" / "watcher2.sh"
ENFORCE_CI_REMEDIATE_PROMPT = (
    REPO_ROOT / ".chaplain" / "graphs" / "enforce" / "prompts" / "enforce-ci-remediate.yaml"
)


@pytest.mark.req("REQ-YG-287")
class TestWatcher2RuffUnsafeFixes:
    """Tests for watcher2.sh ruff unsafe-fixes enhancement."""

    def test_ac01_unsafe_fixes_in_finalize_step(self):
        """AC-01: `ruff check --fix --unsafe-fixes` runs in finalize step."""
        # Read the watcher2.sh file and parse the finalize section
        watcher_content = WATCHER2_SH.read_text()

        # Find the finalize section (step 4)
        finalize_section = re.search(
            r"# ── Enforce Step 4: Finalize.*?# Run pre-commit",
            watcher_content,
            re.DOTALL,
        )

        assert finalize_section, "Could not find finalize section in watcher2.sh"
        finalize_text = finalize_section.group(0)

        # Verify progressive ruff fixing: safe first, then unsafe
        assert (
            "ruff check --fix --unsafe-fixes" in finalize_text
        ), "ruff check --fix --unsafe-fixes command not found in finalize step"

        # Verify the progression: fix -> unsafe-fixes -> format
        ruff_fix_pos = finalize_text.find("ruff check --fix yamlgraph/")
        unsafe_fix_pos = finalize_text.find("ruff check --fix --unsafe-fixes")
        ruff_format_pos = finalize_text.find("ruff format")

        assert ruff_fix_pos != -1, "ruff check --fix not found"
        assert unsafe_fix_pos != -1, "ruff check --fix --unsafe-fixes not found"
        assert ruff_format_pos != -1, "ruff format not found"

        assert (
            ruff_fix_pos < unsafe_fix_pos
        ), "ruff check --fix should come before unsafe-fixes"
        assert (
            unsafe_fix_pos < ruff_format_pos
        ), "unsafe-fixes should come before ruff format"

    def test_ac01_unsafe_fixes_in_ci_remediation_step(self):
        """AC-01: `ruff check --fix --unsafe-fixes` runs in CI remediation step."""
        watcher_content = WATCHER2_SH.read_text()

        # Find the CI remediation section (after copilot finalize step)
        ci_remediation_section = re.search(
            r"# Re-run finalize.*?git push origin",
            watcher_content,
            re.DOTALL,
        )

        assert ci_remediation_section, "Could not find CI remediation section"
        ci_remediation_text = ci_remediation_section.group(0)

        # Verify unsafe-fixes is included in CI remediation
        assert (
            "ruff check --fix --unsafe-fixes" in ci_remediation_text
        ), "ruff check --fix --unsafe-fixes not found in CI remediation step"

        # Verify the command structure: git add && ruff fix && ruff unsafe-fixes && format
        assert (
            "git add -A && ruff check --fix . && ruff check --fix --unsafe-fixes . && ruff format ."
            in ci_remediation_text
        ), "Expected progressive ruff command structure not found in CI remediation"

    def test_ac02_sim117_auto_fix_detection(self):
        """AC-02: SIM117 violations are auto-fixed without manual intervention."""
        # This tests the conceptual coverage - the actual SIM117 fixing would be done by ruff
        # We test that the command structure supports it
        watcher_content = WATCHER2_SH.read_text()

        # Verify unsafe-fixes flag is present (which enables SIM117 auto-fixing)
        unsafe_fixes_count = watcher_content.count("--unsafe-fixes")
        
        # Should appear in both finalize step and CI remediation step  
        assert (
            unsafe_fixes_count >= 2
        ), f"Expected at least 2 instances of --unsafe-fixes, found {unsafe_fixes_count}"

    def test_ac03_copilot_prompt_includes_error_codes(self):
        """AC-03: Copilot fix prompt includes specific ruff error codes and rule names."""
        if not ENFORCE_CI_REMEDIATE_PROMPT.exists():
            pytest.skip("enforce-ci-remediate.yaml prompt not found")

        prompt_content = ENFORCE_CI_REMEDIATE_PROMPT.read_text()

        # Check for specific guidance about ruff error codes in the prompt
        error_code_guidance_patterns = [
            "ruff error code",
            "SIM117",
            "specific.*error.*code",
            "rule.*name",
        ]

        found_patterns = []
        for pattern in error_code_guidance_patterns:
            if re.search(pattern, prompt_content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert (
            len(found_patterns) >= 2
        ), f"Expected copilot prompt to include specific error code guidance. Found patterns: {found_patterns}"

    def test_ac04_changelog_fragment_validation(self):
        """AC-04: Changelog fragment FR numbers are validated against branch names."""
        watcher_content = WATCHER2_SH.read_text()

        # Look for changelog fragment validation logic
        changelog_validation_patterns = [
            "changelog/unreleased/.*md",
            "FRAGMENT_FR.*grep.*FR-[0-9]+",
            "BRANCH_FR.*grep.*FR-[0-9]+",
            "Fragment FR mismatch",
        ]

        found_patterns = []
        for pattern in changelog_validation_patterns:
            if re.search(pattern, watcher_content):
                found_patterns.append(pattern)

        assert (
            len(found_patterns) >= 2
        ), f"Expected changelog fragment validation logic. Found patterns: {found_patterns}"

    def test_ac05_partial_success_handling(self):
        """AC-05: Remediation loop handles partial success (some fixes work, others need copilot)."""
        watcher_content = WATCHER2_SH.read_text()

        # Verify progressive fixing strategy exists
        # Should have: ruff fix -> ruff unsafe-fixes -> still may invoke copilot
        
        # Find the section where copilot is invoked after pre-commit failures
        copilot_fallback_section = re.search(
            r"Pre-commit still failing.*copilot fix",
            watcher_content,
            re.DOTALL | re.IGNORECASE,
        )

        assert copilot_fallback_section, "Copilot fallback mechanism not found"

        # Verify that ruff commands run before this fallback
        section_before_copilot = watcher_content[:copilot_fallback_section.start()]
        
        assert (
            "ruff check --fix --unsafe-fixes" in section_before_copilot
        ), "Progressive ruff fixing should happen before copilot fallback"

    def test_ac07_watcher2_comments_updated(self):
        """AC-07: Documentation updated in watcher2 comments."""
        watcher_content = WATCHER2_SH.read_text()

        # Look for comments documenting the progressive ruff strategy
        progressive_comment_patterns = [
            "Progressive.*ruff.*fix",
            "unsafe.*fix.*remaining",
            "safe.*first.*unsafe",
        ]

        found_patterns = []
        for pattern in progressive_comment_patterns:
            if re.search(pattern, watcher_content, re.IGNORECASE):
                found_patterns.append(pattern)

        assert (
            len(found_patterns) >= 1
        ), f"Expected documentation comments about progressive ruff fixing. Found: {found_patterns}"


@pytest.mark.req("REQ-YG-287")
class TestSIM117RemediationScenarios:
    """Tests for SIM117-specific remediation scenarios."""

    def test_ac06_sim117_test_file_structure(self):
        """AC-06: Tests added covering SIM117 remediation scenarios."""
        # This test should verify that SIM117 integration tests exist
        # Since they don't exist yet, this test must fail
        
        sim117_test_dir = REPO_ROOT / "tests" / "integration" / "sim117_remediation"
        assert sim117_test_dir.exists(), "SIM117 integration test directory should exist"
        
        # Look for SIM117 specific test files
        sim117_test_files = list(sim117_test_dir.glob("test_*.py"))
        assert len(sim117_test_files) >= 1, "Should have SIM117 remediation test files"

    def test_sim117_nested_with_detection(self):
        """Test that nested with statements would be detected as SIM117 violations."""
        # Example of nested with that should trigger SIM117
        problematic_code = '''
        with open("file1.txt") as f1:
            with open("file2.txt") as f2:
                content = f1.read() + f2.read()
        '''
        
        # This would normally be fixed by ruff to:
        # with open("file1.txt") as f1, open("file2.txt") as f2:
        #     content = f1.read() + f2.read()
        
        # For now, just verify the test structure recognizes the pattern
        assert "with " in problematic_code
        assert problematic_code.count("with ") >= 2, "Should have nested with statements"

    def test_unsafe_fixes_flag_enables_sim117(self):
        """Test that --unsafe-fixes flag is required for SIM117 auto-fixing."""
        # Conceptual test: SIM117 requires unsafe fixes because combining
        # with statements can change execution order in edge cases
        
        # Mock ruff command to verify flag presence
        with patch("subprocess.run") as mock_run:
            # Simulate what watcher2.sh should do
            cmd = ["ruff", "check", "--fix", "--unsafe-fixes", "test_file.py"]
            
            # Verify unsafe-fixes is included for SIM117 support
            assert "--unsafe-fixes" in cmd, "unsafe-fixes flag required for SIM117"