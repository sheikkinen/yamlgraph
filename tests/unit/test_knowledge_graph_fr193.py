"""FR-193: Validate mass graduation of 8 patterns into Scripture Knowledge Graph.

Graduates 5 process heuristics and 3 seeds into the Knowledge Graph in
.github/copilot-instructions.md. Process entries are confirmed workflow patterns;
seeds are forward-looking questions that have recurred 4+ times in diary analysis
but whose implementation has not yet been attempted.

Evidence: Philosopher analysis of 220+ diary entries (docs/diary/2026-03-12-philosopher.md).
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COPILOT_INSTRUCTIONS = REPO_ROOT / ".github" / "copilot-instructions.md"

# --- New process heuristics (5) ---

NEW_PROCESS_ENTRIES = {
    "automation_inherits_doctrine": (
        '"Scripts follow same rules as humans → no --no-verify bypass"'
    ),
    "changelog_ci_gate": (
        '"Require changelog fragments at CI, not documentation'
        ' → FR-149 proved advisory docs insufficient"'
    ),
    "detection_without_enforcement": (
        '"Lint without gate = advisory → add CI block or remove claim"'
    ),
    "enforcement_at_merge_boundary": (
        '"PR merge is last gate → all enforcement must block there"'
    ),
    "mixed_commits_erode_auditability": (
        '"One concern per commit → clear blame, clear revert"'
    ),
}

# --- New seed entries (3) ---

NEW_SEED_ENTRIES = {
    "inquisitor_auto_escalation": (
        '"Auto-create FR when audit pattern hits threshold"'
    ),
    "req_coverage_as_universal_gate": (
        '"Block PR merge on coverage gaps, not just report"'
    ),
    "verification_checkpoint_primitive": (
        '"Checkpoint/resume for long enforce pipelines"'
    ),
}

# --- Existing entries that must remain unchanged ---

EXISTING_PROCESS_ENTRIES = {
    "graduation": (
        '"Heuristic appears twice → create FR;'
        ' confirmed recurrence → graduate to Scripture"'
    ),
    "conductor": '"Parallel viewpoints need Blue hat to sequence"',
    "boring_enforcement": ('"Boring = Judgement was good; surprise = spec had gaps"'),
    "audit_gate": ('"Audit without blocking mechanism = post-mortem before incident"'),
    "demo_vs_test": ('"Tests prove constraints; demos prove abstraction worth having"'),
    "unchallenged_premise": (
        "\"Judge validates execution, not intent → need Red Hat: 'Is the pain real?'\""
    ),
}


@pytest.mark.req("REQ-YG-192")
class TestMassGraduationProcessEntries:
    """Validate 5 new process heuristics in the Knowledge Graph."""

    def test_copilot_instructions_exists(self):
        assert (
            COPILOT_INSTRUCTIONS.is_file()
        ), f"Missing {COPILOT_INSTRUCTIONS.relative_to(REPO_ROOT)}"

    @pytest.mark.parametrize(
        "entry_name,description",
        list(NEW_PROCESS_ENTRIES.items()),
        ids=list(NEW_PROCESS_ENTRIES.keys()),
    )
    def test_new_process_entry_present(self, entry_name, description):
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        line = f"{entry_name}: {description}"
        assert line in content, (
            f"Process entry '{entry_name}' not found in Knowledge Graph.\n"
            f"Expected: {line}\n"
            f"FR-193 requires adding this process heuristic."
        )

    @pytest.mark.parametrize(
        "entry_name,description",
        list(NEW_PROCESS_ENTRIES.items()),
        ids=list(NEW_PROCESS_ENTRIES.keys()),
    )
    def test_new_process_entry_in_process_section(self, entry_name, description):
        """Each new process entry must be within the process: section."""
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        process_start = content.index("process:")
        # Find the next section or end of YAML block
        seeds_marker = "seeds:"
        yaml_end = "```"
        if seeds_marker in content[process_start:]:
            section_end = content.index(seeds_marker, process_start)
        else:
            section_end = content.index(yaml_end, process_start)
        process_section = content[process_start:section_end]
        assert f"{entry_name}:" in process_section, (
            f"Process entry '{entry_name}' must be in the process: section, "
            f"not elsewhere in the file."
        )

    def test_changelog_ci_gate_not_in_seeds(self):
        """changelog_ci_gate describes FR-149 (already implemented) → must be
        in process, not seeds."""
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        if "seeds:" in content:
            seeds_start = content.index("seeds:")
            seeds_section = content[seeds_start:]
            assert "changelog_ci_gate:" not in seeds_section, (
                "changelog_ci_gate is an implemented pattern (FR-149) and must "
                "be in process:, not seeds:."
            )


@pytest.mark.req("REQ-YG-192")
class TestMassGraduationSeedsSection:
    """Validate the new seeds: section in the Knowledge Graph."""

    def test_seeds_section_exists(self):
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        assert "seeds:" in content, (
            "seeds: section not found in Knowledge Graph.\n"
            "FR-193 requires a new seeds: section after process:."
        )

    def test_seeds_section_has_comment(self):
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        assert "# Forward-looking patterns awaiting implementation" in content, (
            "seeds: section comment not found.\n"
            "FR-193 requires: '# Forward-looking patterns awaiting implementation'"
        )

    def test_seeds_section_after_process(self):
        """Section ordering: process comes before seeds."""
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        process_pos = content.index("process:")
        seeds_pos = content.index("seeds:")
        assert process_pos < seeds_pos, (
            "seeds: section must appear after process: section in the "
            "Knowledge Graph YAML block."
        )

    @pytest.mark.parametrize(
        "entry_name,description",
        list(NEW_SEED_ENTRIES.items()),
        ids=list(NEW_SEED_ENTRIES.keys()),
    )
    def test_seed_entry_present(self, entry_name, description):
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        line = f"{entry_name}: {description}"
        assert line in content, (
            f"Seed entry '{entry_name}' not found in Knowledge Graph.\n"
            f"Expected: {line}\n"
            f"FR-193 requires adding this seed pattern."
        )

    @pytest.mark.parametrize(
        "entry_name,description",
        list(NEW_SEED_ENTRIES.items()),
        ids=list(NEW_SEED_ENTRIES.keys()),
    )
    def test_seed_entry_in_seeds_section(self, entry_name, description):
        """Each seed entry must be within the seeds: section."""
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        seeds_start = content.index("seeds:")
        seeds_section = content[seeds_start:]
        assert f"{entry_name}:" in seeds_section, (
            f"Seed entry '{entry_name}' must be in the seeds: section, "
            f"not elsewhere in the file."
        )


@pytest.mark.req("REQ-YG-192")
class TestMassGraduationNoExistingEntriesChanged:
    """FR-193 is additive only — no existing Knowledge Graph entries may change."""

    @pytest.mark.parametrize(
        "entry_name,description",
        list(EXISTING_PROCESS_ENTRIES.items()),
        ids=list(EXISTING_PROCESS_ENTRIES.keys()),
    )
    def test_existing_process_unchanged(self, entry_name, description):
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        line = f"{entry_name}: {description}"
        assert line in content, (
            f"Existing process entry '{entry_name}' changed unexpectedly.\n"
            f"Expected: {line}\n"
            f"FR-193 is additive only — no existing entries may be modified."
        )

    def test_all_descriptions_are_one_liners(self):
        """All 8 pattern descriptions must follow key: 'trigger → redirect'
        convention (single line)."""
        content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
        all_entries = {**NEW_PROCESS_ENTRIES, **NEW_SEED_ENTRIES}
        for entry_name, description in all_entries.items():
            line = f"{entry_name}: {description}"
            assert line in content, (
                f"Pattern '{entry_name}' not found as single-line entry.\n"
                f"Expected: {line}"
            )
