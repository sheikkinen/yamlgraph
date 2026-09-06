"""FR-1013 — doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010).

Witnesses that no live doctrine or reference document still describes the
retired Chaplain runtime as the process, that the Scripture edit is limited to
the heading and the sources clause, and that the judge-doctrine ramp mirror is
byte-identical. The residual grep is frozen against the R-1 inventory taken at
BASE 36591389 (docs/census/fr1013-inventory-at-base-36591389.txt).
"""

from __future__ import annotations

import filecmp
import hashlib
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = (
    pytest.mark.process
)  # FR-756: the module names .chaplain/ and scripts/ paths

REPO = Path(__file__).resolve().parents[2]
SCRIPTURE = REPO / ".github" / "copilot-instructions.md"
DEV_PROCESS = REPO / "docs" / "development-process.md"
AUDIT_INDEX = REPO / "reference" / "audit-index.md"
INVENTORY = REPO / "docs" / "census" / "fr1013-inventory-at-base-36591389.txt"

# Frozen at BASE 36591389 (see FR-1013 § Inventory at BASE).
KG_SHA256_AT_BASE = "e3c43f103341b88e2737ceb11483aebbb19e0d3142bb20091e4e68a31aa04628"
SERMON_STEPS_AT_BASE = [
    "Research",
    "Plan",
    "Judge",
    "Enforce",
    "Purge",
    "Submit",
    "Distill",
]
MEASUREMENT_SENTENCE_AT_BASE = (
    "Measured\nover May–July 2026: **~568 commits on main, of which ~94 (17%) arrived via PR (chaplain path)\n"
    "and ~474 (83%) were direct pushes**"
)

GREP = re.compile(
    r"\.chaplain|Chaplain|chaplain|watcher2?\b|Inquisitor|inquisitor|label: chaplain|`chaplain` label"
)
EXCLUDE = re.compile(
    r"^(feature-requests|changelog|docs/diary|docs/memento|docs/ebook|docs/archive)/|^docs/research-|^docs/context/fr-698\.md$|^ramp/curation-diffs\.md$"
)
SUFFIXES = (".md", ".py", ".sh", ".yaml", ".yml")

# Route-critical strings: after the sweep, none may appear in an edit-set file.
RETIRED_ROUTE = ("Sermon of the Chaplain", ".chaplain/inbox", "start-system.sh")
EDIT_SET = [
    ".github/copilot-instructions.md",
    "reference/onepager-development-process.md",
    "reference/audit-index.md",
    "reference/graph-yaml.md",
    "reference/command-book.md",
    "reference/patterns/fsm-as-conductor.md",
    "examples/README.md",
    ".github/skills/graph-authoring/doctrine.md",
    ".github/skills/graph-authoring/SKILL.md",
    ".github/skills/judge-fr/doctrine.md",
    "ramp/assets/tier2/github/skills/judge-fr/doctrine.md",
]


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [
        f for f in out.splitlines() if f.endswith(SUFFIXES) and not EXCLUDE.search(f)
    ]


def _frozen_files() -> set[str]:
    return {
        ln.rsplit(":", 1)[0]
        for ln in INVENTORY.read_text(encoding="utf-8").splitlines()
        if ln and not ln.startswith("#")
    }


def _section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


# --- residual grep (AC-08) --------------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-666")
def test_residual_matches_stay_within_the_frozen_inventory():
    matched = {
        f
        for f in _tracked_files()
        if GREP.search((REPO / f).read_text(encoding="utf-8", errors="replace"))
    }
    new = (
        matched
        - _frozen_files()
        - {"docs/census/fr1013-inventory-at-base-36591389.dispositions.md"}
    )
    assert not new, f"files naming the retired runtime that were not in the BASE inventory: {sorted(new)}"


@pytest.mark.req("REQ-YG-666")
@pytest.mark.parametrize("rel", EDIT_SET)
def test_edit_set_files_no_longer_name_the_retired_route(rel):
    text = (REPO / rel).read_text(encoding="utf-8")
    hits = [s for s in RETIRED_ROUTE if s in text]
    assert not hits, f"{rel} still contains {hits}"


# --- Scripture (AC-03, AC-11) --------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-666")
def test_sermon_heading_renamed_and_steps_unchanged():
    text = SCRIPTURE.read_text(encoding="utf-8")
    assert text.count("Sermon of the Chaplain") == 0
    assert "\n## Sermon\n" in text
    sermon = _section(text, "\n## Sermon\n", "## Agents' prayer")
    assert re.findall(r"^\*\*([A-Z][a-z]+)\.\*\*", sermon, re.M) == SERMON_STEPS_AT_BASE


@pytest.mark.req("REQ-YG-666")
def test_sources_clause_no_longer_names_the_chaplain_pipeline():
    line = next(
        ln
        for ln in SCRIPTURE.read_text(encoding="utf-8").splitlines()
        if ln.startswith("Canonical sources:")
    )
    assert "chaplain" not in line.lower()
    assert "`docs/development-process.md` (doctrine, enforcement rings)" in line


@pytest.mark.req("REQ-YG-192")
def test_knowledge_graph_block_is_byte_identical_to_base():
    text = SCRIPTURE.read_text(encoding="utf-8")
    kg = _section(
        text, "### The Knowledge Graph of the Diary", "### Requirement Traceability"
    )
    assert hashlib.sha256(kg.encode()).hexdigest() == KG_SHA256_AT_BASE


# --- docs/development-process.md (AC-04) ---------------------------------------------------------------


@pytest.mark.req("REQ-YG-666")
def test_development_process_describes_the_operator_route():
    text = DEV_PROCESS.read_text(encoding="utf-8")
    for token in (
        "scripts/author.sh",
        "scripts/judge.sh",
        "scripts/review.sh",
        "worktree",
    ):
        assert token in text, token
    live = text.replace(
        _section(text, "### 3.1 Reality check", "## 4. The Traceability Spine"), ""
    )
    for retired in (
        "start-system.sh",
        "label: chaplain",
        ".chaplain/inbox",
        ".chaplain/failed",
        ".chaplain/inquisitor.sh",
        "stateDiagram",
    ):
        assert retired not in live, retired


@pytest.mark.req("REQ-YG-666")
def test_development_process_measurement_sentence_is_byte_identical_to_base():
    assert MEASUREMENT_SENTENCE_AT_BASE in DEV_PROCESS.read_text(encoding="utf-8")


# --- reference (AC-05) ------------------------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-666")
def test_audit_index_has_exactly_one_chaplain_row_pointing_at_the_archive():
    rows = [
        ln
        for ln in AUDIT_INDEX.read_text(encoding="utf-8").splitlines()
        if ln.startswith("|") and "Chaplain" in ln
    ]
    assert len(rows) == 1, rows
    assert "docs/archive/chaplain.md" in rows[0]


# --- archive move (AC-06) ------------------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-666")
def test_chaplain_system_doc_moved_to_archive_and_linked():
    assert (REPO / "docs" / "archive" / "chaplain-system.md").is_file()
    assert not (REPO / "docs" / "context" / "chaplain-system.md").exists()
    assert "chaplain-system.md" in (
        REPO / "docs" / "archive" / "chaplain.md"
    ).read_text(encoding="utf-8")


# --- ramp mirror (AC-07) ---------------------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-613")
def test_judge_doctrine_ramp_mirror_is_byte_identical():
    live = REPO / ".github" / "skills" / "judge-fr" / "doctrine.md"
    mirror = (
        REPO
        / "ramp"
        / "assets"
        / "tier2"
        / "github"
        / "skills"
        / "judge-fr"
        / "doctrine.md"
    )
    assert filecmp.cmp(live, mirror, shallow=False)
    assert "docs/archive/chaplain.md" in live.read_text(encoding="utf-8")
