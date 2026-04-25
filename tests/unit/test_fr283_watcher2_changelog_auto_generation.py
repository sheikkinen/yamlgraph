"""Acceptance tests for FR-283: Auto-Generate Changelog Fragments in Watcher2 Pipeline.

Tests cover the acceptance criteria for watcher2 changelog fragment auto-generation:
- Shell step generates fragment with correct FR number from FR_PATH variable
- Fragment type/scope/req derived from capability registry when available
- Fragment FR number matches branch FR (no cross-wiring)
- Generated fragments follow naming convention: fr-{num}-{descriptive}.md
- Fragment content includes proper YAML frontmatter and FR reference
- Finalize step verifies changelog exists before pre-commit
- CI remediation receives FR context for correct fragment naming
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.req("REQ-YG-308")
class TestWatcher2ChangelogAutoGeneration:
    """Test auto-generation of changelog fragments in watcher2 pipeline."""

    def test_shell_changelog_generation_script_exists(self):
        """AC-1: Shell step generates fragment between critique and finalize steps.

        Verify that watcher2.sh contains changelog generation logic after the
        critique step (around line 307) and before finalize (around line 309).
        """
        watcher2_path = REPO_ROOT / ".chaplain" / "watcher2.sh"
        assert watcher2_path.exists(), "watcher2.sh must exist"

        content = watcher2_path.read_text()

        # Find critique commit line (around line 307)
        critique_commit_match = re.search(
            r'git commit -m "docs: watcher2 — critique and diary"', content
        )
        assert critique_commit_match, "Expected critique commit line not found"

        # Find finalize step start (around line 309)
        finalize_match = re.search(
            r"# ── Enforce Step 4: Finalize.*Progressive ruff fixing",
            content,
            re.DOTALL,
        )
        assert finalize_match, "Expected finalize step not found"

        # Verify changelog generation logic exists between these points
        critique_pos = critique_commit_match.end()
        finalize_pos = finalize_match.start()
        between_section = content[critique_pos:finalize_pos]

        # This should fail on unmodified code - no changelog generation exists yet
        assert (
            "CHANGELOG_FRAG=" in between_section
        ), "Missing changelog fragment generation logic between critique and finalize"

    def test_fr_number_extraction_pattern_in_watcher2(self):
        """AC-2: Changelog fragment auto-generated with correct FR number from FR_PATH variable.

        Verify that watcher2.sh can extract FR number correctly and use it for
        changelog fragment generation.
        """
        watcher2_path = REPO_ROOT / ".chaplain" / "watcher2.sh"
        content = watcher2_path.read_text()

        # Verify FR_NUM extraction exists (this should pass - it's already there)
        assert (
            "FR_NUM=$(basename \"$FR_PATH\" | grep -oE 'FR-[0-9]+' | sed 's/FR-//'"
            in content
        )

        # This should fail - changelog fragment generation using FR_NUM doesn't exist yet
        changelog_gen_pattern = r"CHANGELOG_FRAG=.*fr-\$\{FR_NUM\}"
        assert re.search(
            changelog_gen_pattern, content
        ), "Missing changelog fragment path generation using FR_NUM variable"

    def test_changelog_fragment_naming_convention(self):
        """AC-3: Generated fragments follow existing naming convention: fr-{num}-{descriptive}.md.

        Test that the shell logic generates filenames matching the established pattern.
        """
        # This test simulates the shell logic that should exist but doesn't yet
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Simulate what the shell script should do
            fr_path = (
                "feature-requests/FR-283-auto-generate-changelog-fragments-watcher2.md"
            )

            # This logic should exist in watcher2.sh but doesn't yet
            # Extract FR number
            fr_num = re.search(r"FR-(\d+)", fr_path).group(1)

            # Generate descriptive name from FR path
            basename = Path(fr_path).stem  # Remove .md
            descriptive = re.sub(r"^FR-\d+-", "", basename)  # Remove FR-283-
            descriptive = descriptive[:40]  # Truncate to 40 chars

            # Expected fragment filename
            expected_filename = f"fr-{fr_num}-{descriptive}.md"

            # This should fail - the actual generation logic doesn't exist in watcher2.sh
            changelog_dir = tmppath / "changelog" / "unreleased"
            changelog_dir.mkdir(parents=True)
            changelog_dir / expected_filename

            # Simulate checking if the logic exists in watcher2.sh
            watcher2_path = REPO_ROOT / ".chaplain" / "watcher2.sh"
            watcher2_content = watcher2_path.read_text()

            # This assertion should fail - the generation logic doesn't exist yet
            assert (
                "head -c 40" in watcher2_content
            ), "Missing descriptive name truncation logic in watcher2.sh"

    def test_capability_registry_req_derivation(self):
        """AC-4: Fragment type/scope/req derived from capability registry when available.

        Verify that the shell script can find REQ-YG-XXX from capabilities/ files
        when given an FR-XXX reference.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create mock capability registry file
            cap_dir = tmppath / "capabilities"
            cap_dir.mkdir()

            cap_file = cap_dir / "CAP-66-append-only-changelog.yaml"
            cap_content = {
                "id": "CAP-66",
                "name": "Append-Only Changelog",
                "fr": "FR-179",
                "requirements": [
                    {
                        "id": "REQ-YG-162",
                        "description": "Append-only changelog fragments",
                    }
                ],
            }
            cap_file.write_text(yaml.dump(cap_content))

            # Test the shell logic that should exist in watcher2.sh
            # This simulates: grep -l "fr: $FR_ID" capabilities/CAP-*.yaml
            fr_id = "FR-179"

            # Find files containing the FR reference
            ["grep", "-l", f"fr: {fr_id}", str(cap_dir / "CAP-*.yaml")]

            # This should work with our mock data
            try:
                result = subprocess.run(
                    ["grep", "-l", f"fr: {fr_id}", str(cap_file)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                matching_files = (
                    result.stdout.strip().split("\n") if result.stdout.strip() else []
                )
            except subprocess.CalledProcessError:
                matching_files = []

            # Verify we can extract REQ-YG-XXX from the matching file
            if matching_files:
                req_cmd = ["grep", "-oE", "REQ-YG-[0-9]+", matching_files[0]]
                try:
                    req_result = subprocess.run(
                        req_cmd, capture_output=True, text=True, check=True
                    )
                    req_ids = req_result.stdout.strip().split("\n")
                    assert "REQ-YG-162" in req_ids
                except subprocess.CalledProcessError:
                    pytest.fail("Failed to extract REQ-YG-XXX from capability file")

            # This should fail - the capability lookup logic doesn't exist in watcher2.sh yet
            watcher2_path = REPO_ROOT / ".chaplain" / "watcher2.sh"
            watcher2_content = watcher2_path.read_text()

            assert (
                'grep -l "fr: $FR_ID" capabilities/CAP-*.yaml' in watcher2_content
            ), "Missing capability registry lookup logic in watcher2.sh"

    def test_yaml_frontmatter_generation_logic(self):
        """AC-5: Fragment content includes proper YAML frontmatter and FR reference.

        Verify that the shell script generates fragments with correct YAML structure.
        """
        # Expected fragment structure

        # This should fail - the YAML generation logic doesn't exist in watcher2.sh yet
        watcher2_path = REPO_ROOT / ".chaplain" / "watcher2.sh"
        watcher2_content = watcher2_path.read_text()

        # Look for YAML frontmatter generation
        yaml_generation_indicators = [
            'echo "---"',
            'echo "type: $CHANGE_TYPE"',
            'echo "scope: $SCOPE"',
            '[[ -n "$REQ_ID" ]] && echo "req: $REQ_ID"',
        ]

        for indicator in yaml_generation_indicators:
            assert (
                indicator in watcher2_content
            ), f"Missing YAML frontmatter generation logic: {indicator}"

    def test_finalize_step_changelog_verification(self):
        """AC-6: Finalize step verifies changelog exists before pre-commit.

        Verify that enforce-finalize.yaml includes changelog verification.
        """
        finalize_prompt_path = (
            REPO_ROOT
            / ".chaplain"
            / "graphs"
            / "enforce"
            / "prompts"
            / "enforce-finalize.yaml"
        )
        assert finalize_prompt_path.exists(), "enforce-finalize.yaml must exist"

        content = finalize_prompt_path.read_text()

        # This should fail - no changelog verification logic exists yet
        changelog_verification_indicators = [
            "Part 0: Verify Changelog Fragment",
            "changelog fragment exists",
            "fr-{{ fr_num }}-*.md",
        ]

        for indicator in changelog_verification_indicators:
            assert (
                indicator in content
            ), f"Missing changelog verification logic in finalize prompt: {indicator}"

    def test_critique_prompt_changelog_generation(self):
        """AC-7: Critique prompt includes Part 3: Changelog Fragment generation.

        Verify that enforce-critique-and-distill.yaml includes changelog generation instructions.
        """
        critique_prompt_path = (
            REPO_ROOT
            / ".chaplain"
            / "graphs"
            / "enforce"
            / "prompts"
            / "enforce-critique-and-distill.yaml"
        )
        assert (
            critique_prompt_path.exists()
        ), "enforce-critique-and-distill.yaml must exist"

        content = critique_prompt_path.read_text()

        # This should fail - no Part 3 changelog section exists yet
        changelog_section_indicators = [
            "Part 3: Changelog Fragment",
            "changelog/unreleased/fr-{{ fr_num }}",
            "type: feat",
            "scope: <primary-scope>",
        ]

        for indicator in changelog_section_indicators:
            assert (
                indicator in content
            ), f"Missing changelog generation in critique prompt: {indicator}"

    def test_ci_remediation_fr_context(self):
        """AC-8: CI remediation receives FR context for correct fragment naming.

        Verify that step-ci-remediate.yaml passes fr_path variable to the prompt.
        """
        ci_remediate_step_path = (
            REPO_ROOT
            / ".chaplain"
            / "graphs"
            / "watcher-enforce"
            / "step-ci-remediate.yaml"
        )
        assert ci_remediate_step_path.exists(), "step-ci-remediate.yaml must exist"

        content = ci_remediate_step_path.read_text()

        # This should fail - fr_path variable is not passed to CI remediation yet
        fr_context_indicators = ["fr_path:", "--var fr_path=", "{{ fr_path }}"]

        found_any = any(indicator in content for indicator in fr_context_indicators)
        assert found_any, "Missing fr_path variable context in CI remediation step"

    def test_no_cross_wiring_between_fr_and_fragment(self):
        """AC-9: Fragment FR number matches branch FR (no cross-wiring like fr-276 vs fr-219).

        Verify that watcher2.sh has logic to prevent FR number cross-wiring.
        """
        watcher2_path = REPO_ROOT / ".chaplain" / "watcher2.sh"
        content = watcher2_path.read_text()

        # This should fail - no validation logic exists to prevent cross-wiring
        cross_wiring_prevention_indicators = [
            "# Validate FR_NUM matches",
            'if [[ "$FR_NUM" != "$EXPECTED_FR_NUM" ]]',
            "FR number mismatch",
            "cross-wiring",
        ]

        found_any = any(
            indicator in content for indicator in cross_wiring_prevention_indicators
        )
        assert found_any, "Missing cross-wiring prevention logic in watcher2.sh"

    def test_ruff_flow_unchanged(self):
        """AC-10: Existing ruff fix flow unchanged (lines 314-316 are already correct).

        Verify that the progressive ruff fixing logic remains intact after changelog additions.
        """
        watcher2_path = REPO_ROOT / ".chaplain" / "watcher2.sh"
        content = watcher2_path.read_text()

        # These lines should exist and remain unchanged
        expected_ruff_sequence = [
            "ruff check --fix yamlgraph/ tests/ 2>/dev/null || true",
            "ruff check --fix --unsafe-fixes yamlgraph/ tests/ 2>/dev/null || true",
            "ruff format yamlgraph/ tests/ 2>/dev/null || true",
        ]

        for ruff_cmd in expected_ruff_sequence:
            assert ruff_cmd in content, f"Missing or modified ruff command: {ruff_cmd}"

        # This should fail - changelog generation logic should be present but isn't yet
        # The test verifies that changelog logic exists AND ruff flow is preserved
        changelog_before_ruff = "CHANGELOG_FRAG=" in content and content.find(
            "CHANGELOG_FRAG="
        ) < content.find("ruff check --fix yamlgraph/")
        assert (
            changelog_before_ruff
        ), "Changelog generation logic must be added before ruff fixing begins"
