"""Tests for FR-199: FSM CLAUDE.md upgraded with full YAMLGraph doctrine.

Verifies that fsm/CLAUDE.md contains all doctrinal sections from the root
CLAUDE.md/copilot-instructions.md, adapted for FSM paths and idioms.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _find_fsm_claude_md() -> Path:
    """Find statemachine-engine/CLAUDE.md via the fsm symlink.

    In the main repo, fsm/ is a valid symlink to ../statemachine-engine.
    In a worktree, the symlink target is relative to the main repo root,
    so we use `git worktree list` to discover the main worktree path.
    """
    direct = REPO_ROOT / "fsm" / "CLAUDE.md"
    if direct.exists():
        return direct

    # Worktree: the symlink target ../statemachine-engine is relative to the
    # main repo root, not the worktree root. Use git to find the main worktree.
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=True,
        )
        for line in result.stdout.split("\n"):
            if line.startswith("worktree "):
                main_wt = Path(line.split(" ", 1)[1])
                candidate = main_wt / "fsm" / "CLAUDE.md"
                if candidate.exists():
                    return candidate
    except (subprocess.CalledProcessError, ValueError, IndexError, OSError):
        pass

    pytest.skip(
        "fsm/CLAUDE.md not accessible (symlink broken in this environment)",
        allow_module_level=True,
    )


FSM_CLAUDE_MD = _find_fsm_claude_md()


@pytest.mark.req("REQ-YG-195")
class TestFsmClaudeMdTenCommandments:
    """Verify fsm/CLAUDE.md contains all 10 Commandments verbatim."""

    def test_commandment_1_research_before_coding(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt research before coding" in content, (
            "fsm/CLAUDE.md must contain Commandment 1 (FR-199 AC-1)"
        )

    def test_commandment_2_demonstrate_with_example(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt demonstrate with example" in content, (
            "fsm/CLAUDE.md must contain Commandment 2 (FR-199 AC-1)"
        )

    def test_commandment_3_not_utter_code_in_vain(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt not utter code in vain" in content, (
            "fsm/CLAUDE.md must contain Commandment 3 (FR-199 AC-1)"
        )

    def test_commandment_4_honor_existing_patterns(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt honor existing patterns" in content, (
            "fsm/CLAUDE.md must contain Commandment 4 (FR-199 AC-1)"
        )

    def test_commandment_5_sanctify_outputs_with_types(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt sanctify thy outputs with types" in content, (
            "fsm/CLAUDE.md must contain Commandment 5 (FR-199 AC-1)"
        )

    def test_commandment_6_bear_witness_of_errors(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt bear witness of thy errors" in content, (
            "fsm/CLAUDE.md must contain Commandment 6 (FR-199 AC-1)"
        )

    def test_commandment_7_faithful_to_tdd(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt be faithful to TDD" in content, (
            "fsm/CLAUDE.md must contain Commandment 7 (FR-199 AC-1)"
        )

    def test_commandment_8_kill_entropy(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt kill all entropy and false idols" in content, (
            "fsm/CLAUDE.md must contain Commandment 8 (FR-199 AC-1)"
        )

    def test_commandment_9_operational_truth(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt define and observe operational truth" in content, (
            "fsm/CLAUDE.md must contain Commandment 9 (FR-199 AC-1)"
        )

    def test_commandment_10_preserve_doctrine(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Thou shalt preserve and improve the doctrine" in content, (
            "fsm/CLAUDE.md must contain Commandment 10 (FR-199 AC-1)"
        )

    def test_section_heading_ten_commandments(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "The 10 Commandments" in content, (
            "fsm/CLAUDE.md must have 'The 10 Commandments' section heading (FR-199 AC-1)"
        )


@pytest.mark.req("REQ-YG-195")
class TestFsmClaudeMdSermon:
    """Verify fsm/CLAUDE.md contains the Sermon of the Chaplain verbatim."""

    def test_sermon_section_heading(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Sermon of the Chaplain" in content, (
            "fsm/CLAUDE.md must contain 'Sermon of the Chaplain' (FR-199 AC-2)"
        )

    def test_sermon_contains_research(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Research.**" in content, (
            "Sermon must contain Research step (FR-199 AC-2)"
        )

    def test_sermon_contains_plan(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Plan.**" in content, "Sermon must contain Plan step (FR-199 AC-2)"

    def test_sermon_contains_judge(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Judge.**" in content, "Sermon must contain Judge step (FR-199 AC-2)"

    def test_sermon_contains_enforce(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Enforce.**" in content, (
            "Sermon must contain Enforce step (FR-199 AC-2)"
        )

    def test_sermon_contains_purge(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Purge.**" in content, "Sermon must contain Purge step (FR-199 AC-2)"

    def test_sermon_contains_submit(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Submit.**" in content, "Sermon must contain Submit step (FR-199 AC-2)"

    def test_sermon_contains_distill(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Distill.**" in content, (
            "Sermon must contain Distill step (FR-199 AC-2)"
        )


@pytest.mark.req("REQ-YG-195")
class TestFsmClaudeMdRiteOfCorrection:
    """Verify fsm/CLAUDE.md contains the Rite of Correction verbatim."""

    def test_rite_section_heading(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Rite of Correction" in content, (
            "fsm/CLAUDE.md must contain 'Rite of Correction' (FR-199 AC-3)"
        )

    def test_rite_contains_inspect(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Inspect.**" in content, "Rite must contain Inspect step (FR-199 AC-3)"

    def test_rite_contains_amend(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Amend.**" in content, "Rite must contain Amend step (FR-199 AC-3)"

    def test_rite_contains_escalate(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "**Escalate.**" in content, (
            "Rite must contain Escalate step (FR-199 AC-3)"
        )


@pytest.mark.req("REQ-YG-195")
class TestFsmClaudeMdAgentsPrayer:
    """Verify fsm/CLAUDE.md contains the Agents' prayer verbatim."""

    def test_prayer_section_heading(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Agents' prayer" in content, (
            "fsm/CLAUDE.md must contain 'Agents' prayer' section (FR-199 AC-4)"
        )

    def test_prayer_contains_callsite_fix(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "May I fix at the callsite, not the utility." in content, (
            "Prayer must contain callsite-fix heuristic (FR-199 AC-4)"
        )

    def test_prayer_contains_normalize_at_boundary(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "May I normalize at the boundary" in content, (
            "Prayer must contain boundary normalization heuristic (FR-199 AC-4)"
        )

    def test_prayer_contains_no_verify_warning(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "--no-verify" in content, (
            "Prayer/doctrine must contain --no-verify warning (FR-199 AC-4)"
        )


@pytest.mark.req("REQ-YG-195")
class TestFsmClaudeMdKnowledgeGraph:
    """Verify fsm/CLAUDE.md contains the Knowledge Graph of the Diary."""

    def test_knowledge_graph_section_heading(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Knowledge Graph" in content and "Diary" in content, (
            "fsm/CLAUDE.md must contain the Knowledge Graph of the Diary (FR-199 AC-5)"
        )

    def test_knowledge_graph_the_one_law(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "the_one_law:" in content, (
            "Knowledge Graph must contain the_one_law: entry (FR-199 AC-5)"
        )

    def test_knowledge_graph_traps_section(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "traps:" in content, (
            "Knowledge Graph must contain traps: section (FR-199 AC-5)"
        )

    def test_knowledge_graph_cures_section(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "cures:" in content, (
            "Knowledge Graph must contain cures: section (FR-199 AC-5)"
        )

    def test_knowledge_graph_process_section(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "process:" in content, (
            "Knowledge Graph must contain process: section (FR-199 AC-5)"
        )

    def test_knowledge_graph_seeds_section(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "seeds:" in content, (
            "Knowledge Graph must contain seeds: section (FR-199 AC-5)"
        )

    def test_knowledge_graph_quick_confidence_trap(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "quick_confidence:" in content, (
            "Knowledge Graph must contain quick_confidence trap (FR-199 AC-5)"
        )

    def test_knowledge_graph_downstream_fix_trap(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "downstream_fix:" in content, (
            "Knowledge Graph must contain downstream_fix trap (FR-199 AC-5)"
        )


@pytest.mark.req("REQ-YG-195")
class TestFsmClaudeMdAdaptationTable:
    """Verify fsm/CLAUDE.md contains the path/package adaptation table."""

    def test_adaptation_table_present(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "statemachine_engine" in content or "statemachine-engine" in content, (
            "fsm/CLAUDE.md must contain FSM-specific path adaptations (FR-199 AC-6)"
        )

    def test_adaptation_table_has_yamlgraph_column(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "YAMLGraph" in content and "FSM equivalent" in content, (
            "Adaptation table must have YAMLGraph and FSM equivalent columns (FR-199 AC-6)"
        )

    def test_adaptation_table_action_loader(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "ActionLoader" in content, (
            "Adaptation table must map create_llm() → ActionLoader (FR-199 AC-6)"
        )

    def test_adaptation_table_base_action(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "BaseAction" in content, (
            "Adaptation table must reference BaseAction (FR-199 AC-6)"
        )

    def test_adaptation_table_shared_paths(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "../feature-requests/" in content, (
            "Adaptation table must show shared mono-repo paths (FR-199 AC-6)"
        )


@pytest.mark.req("REQ-YG-195")
class TestFsmClaudeMdAntiPatterns:
    """Verify fsm/CLAUDE.md contains an anti-patterns table with FSM idioms."""

    def test_anti_patterns_section_present(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "Anti-Patterns" in content or "Anti-patterns" in content, (
            "fsm/CLAUDE.md must contain an anti-patterns section (FR-199 AC-7)"
        )

    def test_anti_patterns_table_format(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "❌ Wrong" in content and "✅ Correct" in content, (
            "Anti-patterns table must use ❌/✅ format (FR-199 AC-7)"
        )


@pytest.mark.req("REQ-YG-195")
class TestFsmClaudeMdExistingSectionsPreserved:
    """Verify all existing FSM-specific sections are preserved intact."""

    def test_architecture_section_preserved(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "## Architecture" in content, (
            "Existing Architecture section must be preserved (FR-199 AC-8)"
        )

    def test_core_engine_preserved(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "core/engine.py" in content, (
            "Core engine reference must be preserved (FR-199 AC-8)"
        )

    def test_usage_patterns_preserved(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "## Usage Patterns" in content, (
            "Usage Patterns section must be preserved (FR-199 AC-8)"
        )

    def test_communication_architecture_preserved(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "## Communication Architecture" in content, (
            "Communication Architecture section must be preserved (FR-199 AC-8)"
        )

    def test_troubleshooting_preserved(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "## Troubleshooting" in content, (
            "Troubleshooting section must be preserved (FR-199 AC-8)"
        )

    def test_variable_interpolation_preserved(self):
        content = FSM_CLAUDE_MD.read_text()
        assert (
            "Variable interpolation" in content or "variable interpolation" in content
        ), "Variable interpolation content must be preserved (FR-199 AC-8)"


@pytest.mark.req("REQ-YG-195")
class TestFsmClaudeMdNoLegacyPrinciples:
    """Verify the four-line YAGNI/TDD/DRY/KISS block is replaced, not duplicated."""

    def test_project_principles_section_removed(self):
        content = FSM_CLAUDE_MD.read_text()
        assert "## Project Principles" not in content, (
            "'## Project Principles' heading must be replaced by full doctrine (FR-199 AC-9)"
        )

    def test_no_standalone_yagni_bullet(self):
        content = FSM_CLAUDE_MD.read_text()
        # The old four-line block had "- **YAGNI**: Build minimal features"
        assert "**YAGNI**: Build minimal features" not in content, (
            "Old YAGNI bullet point must be removed (FR-199 AC-9)"
        )
