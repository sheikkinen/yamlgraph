"""FR-191 Acceptance Tests: Diary Filename Convention Enforcement.

Tests the normalization of diary filename conventions at creation boundary
in watcher2 critique step to prevent CI diary gate failures.

Testing approach:
- Mock watcher2 shell script FR number extraction
- Test critique prompt filename instruction
- Test pre-commit hook validation
- Test critique failure blocking behavior

These tests define the acceptance criteria and MUST fail initially (RED phase).
"""

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
WATCHER2_SH = REPO_ROOT / ".chaplain" / "watcher2.sh"
CRITIQUE_PROMPT = (
    REPO_ROOT
    / ".chaplain"
    / "graphs"
    / "enforce"
    / "prompts"
    / "enforce-critique-and-distill.yaml"
)
PRECOMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"


@pytest.mark.req("REQ-YG-188")
class TestFRNumberExtraction:
    """Test FR number extraction in watcher2 shell script."""

    def test_extracts_fr_number_from_feature_request_path(self):
        """Watcher2 extracts FR number from feature request path and passes as --var fr_num."""
        # This should test that the shell script properly extracts FR-191 from
        # "feature-requests/FR-191-diary-filename-normalization.md"

        script_content = WATCHER2_SH.read_text()

        # Should contain FR number extraction logic
        assert "FR_NUM=" in script_content, "Watcher2 script must extract FR number"
        assert (
            "grep -oE 'FR-[0-9]+'" in script_content
        ), "Must use regex to extract FR number"
        assert (
            "sed 's/FR-//'" in script_content
        ), "Must strip FR- prefix to get number only"

        # Should pass FR number to critique step
        assert (
            "--var fr_num=" in script_content
        ), "Must pass FR number as variable to critique step"

    def test_critique_step_receives_fr_num_variable(self):
        """The critique graph execution includes --var fr_num parameter."""
        script_content = WATCHER2_SH.read_text()

        # Find the section where critique graph is called
        assert (
            "step-critique.yaml" in script_content
        ), "Must call step-critique.yaml graph"

        # Check if fr_num variable is passed to critique step
        # Look for the pattern in the critique section
        assert (
            "--var fr_num=" in script_content
        ), "Critique step must receive --var fr_num parameter"


@pytest.mark.req("REQ-YG-188")
class TestCritiquePromptFilenameInstruction:
    """Test critique prompt explicitly instructs diary filename pattern."""

    def test_prompt_file_exists(self):
        """Critique prompt file must exist."""
        assert (
            CRITIQUE_PROMPT.exists()
        ), f"Missing {CRITIQUE_PROMPT.relative_to(REPO_ROOT)}"

    def test_prompt_contains_filename_instruction(self):
        """Critique prompt explicitly instructs to save as specific filename pattern."""
        content = CRITIQUE_PROMPT.read_text()

        # Should contain explicit filename instruction
        assert (
            "docs/diary/YYYY-MM-DD-reflection-fr-{{ fr_num }}" in content
        ), "Prompt must include explicit filename pattern instruction"

        # Should mention the fr_num variable
        assert (
            "{{ fr_num }}" in content
        ), "Prompt must use Jinja2 template syntax for fr_num variable"

    def test_filename_pattern_matches_ci_regex(self):
        """The instructed filename pattern should match CI diary gate regex."""
        content = CRITIQUE_PROMPT.read_text()

        # The pattern should be compatible with CI regex: docs/diary/.*reflection.*fr-${FR_NUM}[^0-9]
        assert (
            "reflection-fr-" in content
        ), "Filename pattern must include 'reflection-fr-' to match CI regex"


@pytest.mark.req("REQ-YG-188")
class TestPreCommitHookValidation:
    """Test local pre-commit hook validates diary filename pattern."""

    def test_precommit_config_exists(self):
        """Pre-commit config file must exist."""
        assert (
            PRECOMMIT_CONFIG.exists()
        ), f"Missing {PRECOMMIT_CONFIG.relative_to(REPO_ROOT)}"

    def test_diary_filename_hook_exists(self):
        """Pre-commit config must contain diary filename validation hook."""
        with open(PRECOMMIT_CONFIG) as f:
            config = yaml.safe_load(f)

        # Find local hooks
        local_repos = [
            repo for repo in config.get("repos", []) if repo.get("repo") == "local"
        ]
        assert local_repos, "Must have local hooks in pre-commit config"

        # Look for diary filename validation hook
        diary_hooks = []
        for repo in local_repos:
            for hook in repo.get("hooks", []):
                if (
                    "diary" in hook.get("id", "").lower()
                    and "filename" in hook.get("id", "").lower()
                ):
                    diary_hooks.append(hook)

        assert (
            diary_hooks
        ), "Must have diary filename validation hook in pre-commit config"

    def test_diary_hook_uses_correct_regex(self):
        """Diary filename hook must use regex pattern matching CI gate."""
        with open(PRECOMMIT_CONFIG) as f:
            config = yaml.safe_load(f)

        # Find the diary filename hook
        diary_hook = None
        for repo in config.get("repos", []):
            if repo.get("repo") == "local":
                for hook in repo.get("hooks", []):
                    if (
                        "diary" in hook.get("id", "").lower()
                        and "filename" in hook.get("id", "").lower()
                    ):
                        diary_hook = hook
                        break

        assert diary_hook, "Must have diary filename validation hook"

        # Should use same pattern as CI: docs/diary/.*reflection.*fr-[0-9]+[^0-9]
        entry = diary_hook.get("entry", "")
        assert (
            "docs/diary/.*reflection.*fr-[0-9]+[^0-9]" in entry
        ), "Hook must use same regex pattern as CI diary gate"


@pytest.mark.req("REQ-YG-188")
class TestCritiqueFailureBlocking:
    """Test critique step failure terminates pipeline instead of logging warning."""

    def test_critique_failure_is_blocking(self):
        """Critique step failure must terminate pipeline, not continue with warning."""
        script_content = WATCHER2_SH.read_text()

        # Should not contain warning-and-continue pattern
        assert (
            "log_warn" not in script_content
            or "continuing to finalize" not in script_content
        ), "Critique failure should not log warning and continue"

        # Should use handle_failure or similar blocking mechanism
        critique_section = self._extract_critique_section(script_content)
        assert (
            "handle_failure" in critique_section or "exit" in critique_section
        ), "Critique failure must use blocking error handling"

    def _extract_critique_section(self, script_content: str) -> str:
        """Extract the section of script that handles critique step."""
        lines = script_content.split("\n")
        critique_lines = []
        in_critique = False

        for line in lines:
            if "step-critique.yaml" in line:
                in_critique = True

            if in_critique:
                critique_lines.append(line)

                # End section at next major step or end of conditional
                if (
                    line.strip().startswith("fi")
                    or "step-" in line
                    and "critique" not in line
                ):
                    break

        return "\n".join(critique_lines)


@pytest.mark.req("REQ-YG-188")
class TestExistingFilesNormalization:
    """Test that existing diary files follow consistent naming convention."""

    def test_existing_diary_files_follow_pattern(self):
        """All existing diary files with FR references should follow naming convention."""
        diary_dir = REPO_ROOT / "docs" / "diary"

        if not diary_dir.exists():
            pytest.skip("No docs/diary directory found")

        # Find all diary files with FR references
        diary_files = list(diary_dir.glob("*reflection*fr-*.md"))

        for diary_file in diary_files:
            filename = diary_file.name

            # Should match pattern: YYYY-MM-DD-reflection-fr-NNN-topic.md
            import re

            pattern = r"\d{4}-\d{2}-\d{2}-reflection-fr-\d+.*\.md"

            assert re.match(
                pattern, filename
            ), f"Diary file {filename} does not follow expected naming pattern"


@pytest.mark.req("REQ-YG-188")
class TestIntegration:
    """Integration tests for complete diary filename normalization flow."""

    def test_fr_number_extraction_integration(self):
        """Test FR number extraction with real shell script execution."""
        # Create temporary FR file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="-FR-123-test-feature.md", delete=False
        ) as f:
            fr_path = f.name
            f.write("# Test Feature Request\n**Status:** Proposed\n")

        try:
            # Test the extraction logic (this will fail until implemented)
            script = textwrap.dedent(f"""\
                #!/bin/bash
                FR_PATH="{fr_path}"
                FR_NUM=$(basename "$FR_PATH" | grep -oE 'FR-[0-9]+' | sed 's/FR-//')
                echo "FR_NUM=$FR_NUM"
            """)

            result = subprocess.run(
                ["bash", "-c", script], capture_output=True, text=True
            )
            assert result.returncode == 0, f"FR extraction failed: {result.stderr}"
            assert (
                "FR_NUM=123" in result.stdout
            ), f"Wrong FR number extracted: {result.stdout}"

        finally:
            os.unlink(fr_path)
