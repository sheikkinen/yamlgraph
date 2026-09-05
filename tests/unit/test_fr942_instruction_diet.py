"""FR-942 instruction context diet — mechanical acceptance tests.

Governs the two per-turn instruction files:
  .github/copilot-instructions.md  (doctrine surface)
  CLAUDE.md                        (thin dev-command surface)

Covers AC-03 (dedup), AC-04 (relocation), AC-05 (governed key sets),
AC-06 (40-word cap + MOMENT:), AC-07 (provenance + citation
preservation), AC-08 (combined byte ceiling). Semantic preservation of
compressed entries is a HUMAN gate (AC-13) and is deliberately not
asserted here.
"""

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.req("REQ-YG-631")

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCTRINE = REPO_ROOT / ".github" / "copilot-instructions.md"
CLAUDE = REPO_ROOT / "CLAUDE.md"
PROVENANCE = REPO_ROOT / "docs" / "scripture-provenance.md"
DEV_OPS = REPO_ROOT / "reference" / "development-operations.md"

# Frozen by FR-942 judgement R-4: baseline 56,610 bytes, ceiling 60%.
BYTE_CEILING = 33_966

# Frozen by FR-942 judgement R-3: governed collections and their exact
# key sets at compression time. Compression may not add or remove keys.
GOVERNED_KEYS = {
    "traps": {
        "architecture_as_diagram",
        "audit_as_ritual",
        "composition_bug",
        "continuation_bias",
        "downstream_fix",
        "false_duplicate",
        "framework_costume",
        "gate_checks_shape_not_substance",
        "growth_as_default",
        "infrastructure_self_exempt",
        "instruction_boundary_uncrossed",
        "intent_drift",
        "inventory_by_visibility",
        "metric_archaeology_before_reading_output",
        "mock_escape_hatch",
        "model_as_trusted_peer",
        "partial_remediation",
        "plausible_wrong_answer",
        "quick_confidence",
        "recent_changes_blindness",
        "refactor_orphans_secondary",
        "regex_fourth_exclusion",
        "research_as_inventory",
        "symptom_patch",
        "impossibly_large_sequential_task",
        "threshold_encodes_forecast",
        "vendor_default_as_help",
        "working_system_inertia",
        "workspace_is_not_boundary",
    },
    "cures": {
        "ask_before_generate",
        "assert_path_not_destination",
        "boundary_inventory",
        "callsite_fix",
        "changelog_first_diagnostic",
        "incident_density_ranking",
        "investigation_before_fix",
        "judge_as_junior_pr",
        "junk_drawer_cap",
        "map_reduce_the_corpus",
        "name_the_seam",
        "read_raw_output_first",
        "spec_kill",
        "streaming_xray",
        "substance_over_presence",
        "test_before_reading",
        "three_reads",
        "tolerant_matching",
        "two_ends_of_the_knowledge_axis",  # FR-995 graduation, PR #595
        "two_strike_split",
    },
    "questions": {
        "are_the_witnesses_one_phenomenon",
        "does_the_platform_already_do_this",
        "does_the_tool_fit_or_merely_exist",
        "is_this_a_graph",
        "what_does_the_raw_record_say",
        "what_would_the_successor_need",
        "where_is_the_repo_boundary",
        "who_reads_this_when",
        "would_you_use_this",
    },
    "process": {
        "audit_gate",
        "automation_inherits_doctrine",
        "boring_enforcement",
        "changelog_ci_gate",
        "conductor",
        "constraint_over_code",
        "cross_project_graduation",
        "demo_vs_test",
        "detection_without_enforcement",
        "enforcement_at_merge_boundary",
        "graduation",
        "mixed_commits_erode_auditability",
        "one_session_one_repo",
        "unchallenged_premise",
    },
}

# Frozen verbatim citation inventory extracted from the pre-compression
# Scripture (2026-08-31). Every token must survive — inline in the
# compressed entry or verbatim in the keyed provenance record.
CITATION_INVENTORY = {
    "traps.vendor_default_as_help": ["FR-438"],
    "traps.composition_bug": ["FR-371", "NC-141", "NC-289"],
    "traps.mock_escape_hatch": ["FR-378"],
    "traps.refactor_orphans_secondary": ["NC-203"],
    "traps.inventory_by_visibility": ["2026-05-31"],
    "traps.growth_as_default": ["FR-465", "FR-466"],
    "traps.metric_archaeology_before_reading_output": ["FR-596/597"],
    "traps.threshold_encodes_forecast": ["FR-726", "FR-727", "FR-730"],
    "cures.investigation_before_fix": ["FR-371", "FR-372"],
    "cures.assert_path_not_destination": ["NC-179"],
    "cures.name_the_seam": ["NC-131"],
    "cures.read_raw_output_first": ["FR-598", "FR-730"],
    "cures.two_strike_split": ["FR-722/727/730"],
    "cures.junk_drawer_cap": ["FR-725", "FR-727/730"],
    "questions.is_this_a_graph": ["2026-07-17", "2026-08-22", "FR-853"],
    "process.changelog_ci_gate": ["FR-149"],
    "process.one_session_one_repo": ["2026-07-14"],
}

# Content markers that must leave CLAUDE.md with their relocated blocks
# (judgement R-2 source-to-destination map). Pointers use section names
# only, never these payload strings.
RELOCATED_MARKERS = {
    "env-var table": "ANTHROPIC_API_KEY",
    "branch-protection table": "enforce_admins",
    "CI-check list": "changelog-req-gate",
    "FR-761 walkthrough": "dev-py312.txt",
}

DEV_OPS_HEADINGS = [
    "## Key Environment Variables",
    "## Branch Protection",
    "## CI Checks",
    "## Dependency Governance (FR-761)",
]


def _scripture() -> dict:
    m = re.search(r"```yaml\n(.*?)```", DOCTRINE.read_text(encoding="utf-8"), re.S)
    assert m, "Knowledge Graph yaml block missing from doctrine"
    return yaml.safe_load(m.group(1))


def _sentences(path: Path) -> list[str]:
    """Normalization algorithm (AC-03, stated per judgement R-4):

    1. lowercase the file text
    2. collapse every whitespace run to a single space
    3. split into sentences at ``[.!?]`` followed by a space
    4. drop sentences shorter than 30 characters (table rules,
       fragments, and headings would otherwise produce noise matches)
    """
    text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8").lower())
    return [s.strip() for s in re.split(r"(?<=[.!?]) ", text) if len(s.strip()) >= 30]


def test_combined_instruction_bytes_within_ceiling():
    """AC-08: combined size of both instruction files ≤ 33,966 bytes."""
    a, b = DOCTRINE.stat().st_size, CLAUDE.stat().st_size
    assert a > 0 and b > 0, "instruction file empty"
    assert (
        a + b <= BYTE_CEILING
    ), f"combined instruction bytes {a + b} exceed ceiling {BYTE_CEILING}"


def test_submitting_proposals_removed_everywhere():
    """AC-03 (amended by operator 2026-08-31): the chaplain runtime is not
    running — the Submitting Proposals section is deleted from BOTH
    instruction files, not deduplicated into the doctrine."""
    assert "Submitting Proposals" not in DOCTRINE.read_text(encoding="utf-8")
    assert "Submitting Proposals" not in CLAUDE.read_text(encoding="utf-8")


def test_no_identical_three_sentence_run_across_files():
    """AC-03: no identical normalized three-sentence run in both files."""

    def runs(sents):
        return {tuple(sents[i : i + 3]) for i in range(len(sents) - 2)}

    shared = runs(_sentences(DOCTRINE)) & runs(_sentences(CLAUDE))
    assert not shared, f"duplicated three-sentence run(s): {sorted(shared)[:2]}"


def test_relocated_blocks_absent_from_claude():
    """AC-04: relocated payloads no longer ride in CLAUDE.md."""
    text = CLAUDE.read_text(encoding="utf-8")
    present = [name for name, marker in RELOCATED_MARKERS.items() if marker in text]
    assert not present, f"relocated blocks still in CLAUDE.md: {present}"


def test_relocation_pointers_resolve():
    """AC-04: every relocation pointer resolves to a committed section."""
    assert "reference/development-operations.md" in CLAUDE.read_text(encoding="utf-8")
    assert DEV_OPS.is_file(), "reference/development-operations.md missing"
    dev_ops = DEV_OPS.read_text(encoding="utf-8")
    missing = [h for h in DEV_OPS_HEADINGS if h not in dev_ops]
    assert not missing, f"destination sections missing: {missing}"


def test_governed_key_sets_frozen():
    """AC-05: compression changed values only — never keys or collections."""
    data = _scripture()
    for coll, expected in GOVERNED_KEYS.items():
        assert set(data[coll].keys()) == expected, f"{coll} key set drifted"
    for untouched in ("the_one_law", "boundaries", "generative_methods", "seeds"):
        assert data.get(untouched), f"non-governed collection {untouched} missing"


def test_governed_entries_within_word_cap():
    """AC-06: every governed scalar ≤ 40 whitespace-delimited words."""
    data = _scripture()
    over = {
        f"{coll}.{k}": len(v.split())
        for coll in GOVERNED_KEYS
        for k, v in data[coll].items()
        if len(v.split()) > 40
    }
    assert not over, f"entries over 40-word cap: {over}"


def test_questions_retain_moment():
    """AC-06: every question keeps its MOMENT: firing condition."""
    data = _scripture()
    missing = [k for k, v in data["questions"].items() if "MOMENT:" not in v]
    assert not missing, f"questions without MOMENT:: {missing}"


def test_provenance_records_keyed_and_complete():
    """AC-07: one keyed record per compressed entry, valid keys, no dupes."""
    assert PROVENANCE.is_file(), "docs/scripture-provenance.md missing"
    keys = re.findall(
        r"^### `((?:traps|cures|questions|process)\.\w+)`",
        PROVENANCE.read_text(encoding="utf-8"),
        re.M,
    )
    assert keys, "no keyed records in provenance file"
    assert len(keys) == len(set(keys)), "duplicate provenance keys"
    valid = {f"{c}.{k}" for c, ks in GOVERNED_KEYS.items() for k in ks}
    bad = [k for k in keys if k not in valid]
    assert not bad, f"provenance keys not in governed set: {bad}"


def test_citations_preserved_verbatim():
    """AC-07: every pre-compression citation survives — inline or in the
    keyed provenance record."""
    data = _scripture()
    prov = PROVENANCE.read_text(encoding="utf-8") if PROVENANCE.is_file() else ""
    lost = []
    for dotted, tokens in CITATION_INVENTORY.items():
        coll, key = dotted.split(".", 1)
        inline = data[coll][key]
        record = re.search(
            rf"^### `{re.escape(dotted)}`\n(.*?)(?=^### |\Z)", prov, re.M | re.S
        )
        haystack = inline + (record.group(1) if record else "")
        lost += [f"{dotted}:{t}" for t in tokens if t not in haystack]
    assert not lost, f"citations lost in compression: {lost}"
