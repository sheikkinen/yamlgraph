"""FR-191: Validate graduated plausible_wrong_answer trap description in Scripture.

The Knowledge Graph in .github/copilot-instructions.md contains trap descriptions
that are compressed signals for cognitive hazards. FR-191 graduates the
plausible_wrong_answer trap based on 4 confirmed diary occurrences, refining the
description from variant-specific ("Silent fallback") to pattern-general
("Output passes shape check but is semantically wrong").
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COPILOT_INSTRUCTIONS = REPO_ROOT / ".github" / "copilot-instructions.md"

GRADUATED_DESCRIPTION = (
    'plausible_wrong_answer: "Output passes shape check but is semantically'
    ' wrong → add assertion beyond type validation"'
)

OLD_DESCRIPTION = 'plausible_wrong_answer: "Silent fallback harder to catch than crash"'


@pytest.mark.req("REQ-YG-188")
class TestPlausibleWrongAnswerGraduation:
    """Validate the graduated plausible_wrong_answer trap in the Knowledge Graph."""

    def test_copilot_instructions_exists(self):
        assert (
            COPILOT_INSTRUCTIONS.is_file()
        ), f"Missing {COPILOT_INSTRUCTIONS.relative_to(REPO_ROOT)}"

    def test_plausible_wrong_answer_has_graduated_description(self):
        content = COPILOT_INSTRUCTIONS.read_text()
        assert GRADUATED_DESCRIPTION in content, (
            f"plausible_wrong_answer trap not updated to graduated description.\n"
            f"Expected: {GRADUATED_DESCRIPTION}\n"
            f"Hint: FR-191 requires updating the trap from variant-specific "
            f"to pattern-general language."
        )

    def test_old_description_removed(self):
        content = COPILOT_INSTRUCTIONS.read_text()
        assert OLD_DESCRIPTION not in content, (
            f"Old plausible_wrong_answer description still present.\n"
            f"Found: {OLD_DESCRIPTION}\n"
            f"FR-191 requires replacing this with the graduated description."
        )

    def test_trap_in_traps_section(self):
        """Verify the graduated trap is in the traps: section, not elsewhere."""
        content = COPILOT_INSTRUCTIONS.read_text()
        traps_start = content.index("traps:")
        cures_start = content.index("cures:")
        traps_section = content[traps_start:cures_start]
        assert "plausible_wrong_answer:" in traps_section, (
            "plausible_wrong_answer must be in the traps: section, "
            "not elsewhere in the file."
        )

    def test_no_other_traps_changed(self):
        """Verify all other trap descriptions remain unchanged."""
        content = COPILOT_INSTRUCTIONS.read_text()
        expected_traps = {
            "quick_confidence": '"When I feel certain → Judge instead"',
            "downstream_fix": (
                '"Guard added where symptom manifests'
                ' → normalize at entry boundary instead"'
            ),
            "symptom_patch": '"Verify root cause with test before designing fix"',
            "intent_drift": '"Plan says X, code does Y → re-read thrice"',
            "false_duplicate": '"Syntactic similarity ≠ semantic equivalence"',
            "regex_fourth_exclusion": (
                '"Fourth special case → switch to proper parser"'
            ),
            "partial_remediation": '"Fix all occurrences, not just cited one"',
            "audit_as_ritual": '"3+ audits without fix → ritual, not process"',
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
            "three_reads": '"surface → deep against code → mechanical simulation"',
            "streaming_xray": '"Real-time constraint exposes implicit assumptions"',
            "callsite_fix": '"Fix at the specific caller, not the shared utility"',
            "spec_kill": '"Cheapest bug is the one killed in the spec"',
            "judge_as_junior_pr": '"Assume plausible code hides subtle bugs"',
        }
        for cure_name, description in expected_cures.items():
            line = f"{cure_name}: {description}"
            assert line in content, (
                f"Cure '{cure_name}' description changed unexpectedly.\n"
                f"Expected line containing: {line}"
            )

    def test_no_process_entries_changed(self):
        """Verify all process descriptions remain unchanged."""
        content = COPILOT_INSTRUCTIONS.read_text()
        expected_process = {
            "graduation": (
                '"Heuristic appears twice → create FR;'
                ' confirmed recurrence → graduate to Scripture"'
            ),
            "conductor": '"Parallel viewpoints need Blue hat to sequence"',
            "boring_enforcement": (
                '"Boring = Judgement was good; surprise = spec had gaps"'
            ),
            "audit_gate": (
                '"Audit without blocking mechanism' ' = post-mortem before incident"'
            ),
            "demo_vs_test": (
                '"Tests prove constraints;' ' demos prove abstraction worth having"'
            ),
            "unchallenged_premise": (
                '"Judge validates execution, not intent'
                " → need Red Hat: 'Is the pain real?'\""
            ),
        }
        for entry_name, description in expected_process.items():
            line = f"{entry_name}: {description}"
            assert line in content, (
                f"Process '{entry_name}' description changed unexpectedly.\n"
                f"Expected line containing: {line}"
            )
