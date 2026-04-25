"""FR-190: Validate graduated infrastructure_self_exempt trap in Scripture.

The Knowledge Graph in .github/copilot-instructions.md contains trap descriptions
that are compressed signals for cognitive hazards. FR-190 graduates the
infrastructure_self_exempt trap based on 3 confirmed diary occurrences
(audits 94, 95, 97), naming the cognitive blind spot where meta-tooling
exempts itself from the quality gates it enforces.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COPILOT_INSTRUCTIONS = REPO_ROOT / ".github" / "copilot-instructions.md"

NEW_TRAP = (
    'infrastructure_self_exempt: "Meta-tooling exempted from gates it enforces'
    ' → apply same rules to the guardrail as to what it guards"'
)


@pytest.mark.req("REQ-YG-187")
class TestInfrastructureSelfExemptGraduation:
    """Validate the new infrastructure_self_exempt trap in the Knowledge Graph."""

    def test_copilot_instructions_exists(self):
        assert (
            COPILOT_INSTRUCTIONS.is_file()
        ), f"Missing {COPILOT_INSTRUCTIONS.relative_to(REPO_ROOT)}"

    def test_infrastructure_self_exempt_trap_present(self):
        content = COPILOT_INSTRUCTIONS.read_text()
        assert NEW_TRAP in content, (
            f"infrastructure_self_exempt trap not found in Scripture.\n"
            f"Expected: {NEW_TRAP}\n"
            f"Hint: FR-190 requires adding this new trap to the traps section."
        )

    def test_trap_in_traps_section(self):
        """Verify the new trap is in the traps: section, not elsewhere."""
        content = COPILOT_INSTRUCTIONS.read_text()
        traps_start = content.index("traps:")
        cures_start = content.index("cures:")
        traps_section = content[traps_start:cures_start]
        assert "infrastructure_self_exempt:" in traps_section, (
            "infrastructure_self_exempt must be in the traps: section, "
            "not elsewhere in the file."
        )

    def test_no_other_traps_changed(self):
        """Verify all existing trap descriptions remain unchanged."""
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
            "plausible_wrong_answer": (
                '"Output passes shape check but is semantically wrong'
                ' → add assertion beyond type validation"'
            ),
            "framework_costume": (
                '"FSM wearing DAG costume'
                ' → if <50% nodes use core features, wrong tool"'
            ),
            "working_system_inertia": (
                "\"'It works' blocks seeing it clearly → inventory fit, not function\""
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
            "conductor": ('"Parallel viewpoints need Blue hat to sequence"'),
            "boring_enforcement": (
                '"Boring = Judgement was good; surprise = spec had gaps"'
            ),
            "audit_gate": (
                '"Audit without blocking mechanism = post-mortem before incident"'
            ),
            "demo_vs_test": (
                '"Tests prove constraints; demos prove abstraction worth having"'
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
