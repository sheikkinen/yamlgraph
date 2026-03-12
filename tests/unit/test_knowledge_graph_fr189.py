"""FR-189: Validate graduated downstream_fix trap description in Scripture.

The Knowledge Graph in .github/copilot-instructions.md contains trap descriptions
that are compressed signals for cognitive hazards. FR-189 graduates the
downstream_fix trap based on 3 confirmed diary occurrences, refining the
description from incident-specific to pattern-general.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COPILOT_INSTRUCTIONS = REPO_ROOT / ".github" / "copilot-instructions.md"

GRADUATED_DESCRIPTION = (
    'downstream_fix: "Guard added where symptom manifests'
    ' → normalize at entry boundary instead"'
)

OLD_DESCRIPTION = (
    'downstream_fix: "Fix at callsite, not utility → avoid double-stripping"'
)


@pytest.mark.req("REQ-YG-184")
class TestDownstreamFixGraduation:
    """Validate the graduated downstream_fix trap in the Knowledge Graph."""

    def test_copilot_instructions_exists(self):
        assert (
            COPILOT_INSTRUCTIONS.is_file()
        ), f"Missing {COPILOT_INSTRUCTIONS.relative_to(REPO_ROOT)}"

    def test_downstream_fix_has_graduated_description(self):
        content = COPILOT_INSTRUCTIONS.read_text()
        assert GRADUATED_DESCRIPTION in content, (
            f"downstream_fix trap not updated to graduated description.\n"
            f"Expected: {GRADUATED_DESCRIPTION}\n"
            f"Hint: FR-189 requires updating the trap from incident-specific "
            f"to pattern-general language."
        )

    def test_old_description_removed(self):
        content = COPILOT_INSTRUCTIONS.read_text()
        assert OLD_DESCRIPTION not in content, (
            f"Old downstream_fix description still present.\n"
            f"Found: {OLD_DESCRIPTION}\n"
            f"FR-189 requires replacing this with the graduated description."
        )

    def test_no_other_traps_changed(self):
        """Verify all other trap descriptions remain unchanged."""
        content = COPILOT_INSTRUCTIONS.read_text()
        expected_traps = {
            "quick_confidence": '"When I feel certain → Judge instead"',
            "symptom_patch": '"Verify root cause with test before designing fix"',
            "intent_drift": '"Plan says X, code does Y → re-read thrice"',
            "false_duplicate": '"Syntactic similarity ≠ semantic equivalence"',
            "regex_fourth_exclusion": '"Fourth special case → switch to proper parser"',
            "partial_remediation": '"Fix all occurrences, not just cited one"',
            "audit_as_ritual": '"3+ audits without fix → ritual, not process"',
            "plausible_wrong_answer": '"Silent fallback harder to catch than crash"',
            "framework_costume": (
                '"FSM wearing DAG costume'
                ' → if <50% nodes use core features, wrong tool"'
            ),
            "working_system_inertia": (
                "\"'It works' blocks seeing it clearly"
                ' → inventory fit, not function"'
            ),
            "infrastructure_self_exempt": (
                '"Meta-tooling exempted from gates it enforces'
                " → apply same rules to the guardrail"
                ' as to what it guards"'
            ),
        }
        for trap_name, description in expected_traps.items():
            line = f"{trap_name}: {description}"
            assert line in content, (
                f"Trap '{trap_name}' description changed unexpectedly.\n"
                f"Expected line containing: {line}"
            )

    def test_no_cures_changed(self):
        """Verify all cure descriptions remain unchanged."""
        content = COPILOT_INSTRUCTIONS.read_text()
        expected_cures = {
            "test_before_reading": '"Write question as test → if passes, stop"',
            "tolerant_matching": (
                '"prefix/contains/regex, not exact equality for LLM"'
            ),
            "three_reads": ('"surface → deep against code → mechanical simulation"'),
            "streaming_xray": ('"Real-time constraint exposes implicit assumptions"'),
            "callsite_fix": ('"Fix at the specific caller, not the shared utility"'),
            "spec_kill": '"Cheapest bug is the one killed in the spec"',
            "judge_as_junior_pr": ('"Assume plausible code hides subtle bugs"'),
        }
        for cure_name, description in expected_cures.items():
            line = f"{cure_name}: {description}"
            assert line in content, (
                f"Cure '{cure_name}' description changed unexpectedly.\n"
                f"Expected line containing: {line}"
            )
