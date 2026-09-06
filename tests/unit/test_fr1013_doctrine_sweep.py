"""FR-1013 — doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010).

Witnesses that no live doctrine or reference document still describes the
retired Chaplain runtime as the process, that the Scripture edit is limited to
the heading and the sources clause, and that the judge-doctrine ramp mirror is
byte-identical. The residual census is match-level (round-3 R-3): outside the
match-bearing edit set every file's matching lines must equal BASE's; inside it
every remaining match must be an exact listed residual line.
"""

from __future__ import annotations

import filecmp
import hashlib
import re
import subprocess
from collections import Counter
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
DISPOSITIONS = INVENTORY.with_name("fr1013-inventory-at-base-36591389.dispositions.md")

BASE = "36591389e2fdfedf9ba5ae6362effad1c64cd06e"  # FR-1012 merge SHA (PR #623)

# Frozen at BASE (see FR-1013 § Inventory at BASE).
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

# Route-critical strings: after the sweep, none may appear in a match-bearing file.
RETIRED_ROUTE = ("Sermon of the Chaplain", ".chaplain/inbox", "start-system.sh")

# Clause 2 — the BASE match-bearing source set; value = exact residual lines
# permitted at HEAD (historical sentences and archive links only). Empty = zero.
# docs/context/chaplain-system.md is the 13th member; it is asserted moved.
RESIDUAL: dict[str, list[str]] = {
    ".github/copilot-instructions.md": [
        "  - audit        # Inquisitor findings → enforcement gates",
        '  inquisitor_auto_escalation: "Auto-create FR when audit pattern hits threshold"',
    ],
    ".github/skills/graph-authoring/SKILL.md": [],
    ".github/skills/graph-authoring/doctrine.md": [],
    ".github/skills/judge-fr/doctrine.md": [
        "- Verdict vocabulary note: chaplain-era prompts used APPROVE/AMEND;",
        "- The retired Chaplain runtime is the historical origin of this",
        "  doctrine (FR-084→257→305; archived: `docs/archive/chaplain.md`).",
    ],
    "docs/development-process.md": [
        "An autonomous FSM (the Chaplain) ran the same rite unattended from February to July 2026 and was",
        "[docs/archive/chaplain-system.md](archive/chaplain-system.md) and its source in",
        "[docs/archive/chaplain.md](archive/chaplain.md).",
        "over May–July 2026: **~568 commits on main, of which ~94 (17%) arrived via PR (chaplain path)",
        "[docs/archive/chaplain.md](archive/chaplain.md)):",
        "  ([docs/archive/chaplain.md](archive/chaplain.md)); its lesson stands: detection authority ≠",
        "- *Self-exemption risk*: meta-tooling (hooks, chaplain scripts) historically drifted from the",
    ],
    "examples/README.md": [],
    "ramp/assets/tier2/github/skills/judge-fr/doctrine.md": [
        "- Verdict vocabulary note: chaplain-era prompts used APPROVE/AMEND;",
        "- The retired Chaplain runtime is the historical origin of this",
        "  doctrine (FR-084→257→305; archived: `docs/archive/chaplain.md`).",
    ],
    "reference/audit-index.md": [
        "| Inquisitor audits | `docs/diary/inquisitor-audit-*` | 200+ commit audits against Scripture |",
        "| Chaplain (archived) | [docs/archive/chaplain.md](../docs/archive/chaplain.md) | Retired FSM runtime (FR-1010–FR-1013): archive tag, replacement table, design note |",
    ],
    "reference/command-book.md": [],
    "reference/graph-yaml.md": [],
    "reference/onepager-development-process.md": [
        "*Sources: `CLAUDE.md`, `.pre-commit-config.yaml`, `docs/ebook/v3/`, `docs/archive/chaplain-system.md`*",
    ],
    "reference/patterns/fsm-as-conductor.md": [
        "| **Chaplain** (automation) | 9+3 | 1–4 node graphs | subprocess¹ | minutes |",
        "> ¹ The Chaplain's `yamlgraph_async_action` is a misnomer — it invokes `yamlgraph graph run` as a subprocess and `await`s completion, returning the event string directly. There is no `asyncio.create_task`, no guard key, and no socket dispatch. Event routing uses substring matching against stdout rather than structured state inspection. This works because the pipeline FSM's per-action timeouts (600–3600s) absorb the blocking call. The fsm-router and voicebot implementations are the true fire-and-forget variants.",
        "### Chaplain — Development Lifecycle Automation",
        "- Location: archived — `docs/archive/chaplain.md` (retired 2026-09)",
        "- Context: `docs/archive/chaplain-system.md`",
        "| **Horizontal** (graph nodes) | More LLM steps per invocation | Chaplain enforce: 1 → 4 nodes with context planning |",
        "| **Chaplain** | ~60s | CI operations | timeout, stop | CI/CD automation |",
        "- [docs/archive/chaplain-system.md](../../docs/archive/chaplain-system.md) — Chaplain architecture (archived)",
    ],
}

# Clause 2, generated/registry files and main drift merged after BASE:
# (removed matching lines, added matching lines) relative to BASE — exact — plus
# the sha256 of the resulting HEAD matching-line multiset (CI has no BASE object).
DELTA: dict[str, tuple[list[str], list[str]]] = {
    "capabilities/CAP-264-chaplain-runtime-retired.yaml": (
        [],
        [
            "      - docs/archive/chaplain-system.md",
            "      Chaplain-runtime match appears outside the frozen, dispositioned BASE",
            "      resolve to docs/archive/chaplain.md or docs/archive/chaplain-system.md;",
            "      set; non-historical Chaplain pointers in those documentation surfaces",
            "  - docs/archive/chaplain-system.md",
        ],
    ),
    "ARCHITECTURE.md": (
        [
            "| 264 | CAP-264 Chaplain runtime retired | `scripts/chaplain_census.py`, `examples/demos/corpus_census/adapters/chaplain_adapters.py`, `examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml`, `examples/demos/corpus_census/adapters/chaplain-extract.tool.yaml`, … | REQ-YG-666 |",
        ],
        [
            "| 264 | CAP-264 Chaplain runtime retired | `scripts/chaplain_census.py`, `examples/demos/corpus_census/adapters/chaplain_adapters.py`, `examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml`, `examples/demos/corpus_census/adapters/chaplain-extract.tool.yaml`, … | REQ-YG-666, 668 |",
            "| REQ-YG-668 | The post-FR-1012 tracked-text census remains reconciled: active doctrine, skill instructions, process/reference documentation, and examples describe the operator-driven author -> judge -> worktree enforcement -> review -> human-merge route; no new or reworded Chaplain-runtime match appears outside the frozen, dispositioned BASE set; non-historical Chaplain pointers in those documentation surfaces resolve to docs/archive/chaplain.md or docs/archive/chaplain-system.md; witnessed by tests/unit/test_fr1013_doctrine_sweep.py (FR-1013, Phase 3 of FR-1010). | `.github/copilot-instructions.md`, `docs/development-process.md`, `reference/audit-index.md`, `reference/onepager-development-process.md`, `.github/skills/graph-authoring/doctrine.md`, `.github/skills/judge-fr/doctrine.md`, `docs/archive/chaplain-system.md`, `tests/unit/test_fr1013_doctrine_sweep.py` |",
        ],
    ),
    "docs/confessions.md": (
        [],
        [
            "- **File**: [examples/demos/corpus_census/adapters/chaplain_adapters.py](../examples/demos/corpus_census/adapters/chaplain_adapters.py#L57)",
            "- **File**: [scripts/chaplain_census.py](../scripts/chaplain_census.py#L158)",
            "- **File**: [scripts/chaplain_census.py](../scripts/chaplain_census.py#L75)",
            "- **File**: [scripts/chaplain_census.py](../scripts/chaplain_census.py#L91)",
        ],
    ),
}

DELTA_HEAD_SHA256 = {
    "capabilities/CAP-264-chaplain-runtime-retired.yaml": "d20976227ec1e9b85b4ae88c05aa45fc1eb1950e48d65bd38d43a82ecd3cfeaf",
    "ARCHITECTURE.md": "5d5790c35a5eab27ea353174364eafe251afafd6eea9843e436c181b8edefd3a",
    "docs/confessions.md": "b53ba777cc0fae631de84e12a9bdae14e81f5cbd3e5a0a99737fcecd95687ca1",
}

# Clause 3 — matching files absent from BASE that this FR creates (self-referential).
NEW_ARTIFACTS = {
    "tests/unit/test_fr1013_doctrine_sweep.py",
    "docs/census/fr1013-inventory-at-base-36591389.dispositions.md",
}

# Clause 4 — keep-out-of-scope-code: stale defaults, unchanged, not historical.
OUT_OF_SCOPE_CODE = (
    "examples/demos/research-route/nodes/research_tools.py",
    "examples/demos/corpus_census/adapters/diary_recurrence.py",
    "examples/demos/cap_journey_census/extract.py",
)


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


def _matches(text: str) -> Counter[str]:
    return Counter(ln for ln in text.splitlines() if GREP.search(ln))


def _head_matches(rel: str) -> Counter[str]:
    path = REPO / rel
    if not path.is_file():
        return Counter()
    return _matches(path.read_text(encoding="utf-8", errors="replace"))


def _sha(lines: Counter[str]) -> str:
    return hashlib.sha256(
        "\n".join(sorted(lines.elements())).encode("utf-8")
    ).hexdigest()


_ROW = re.compile(r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \| ")


def _baseline() -> dict[str, tuple[int, str]]:
    """Committed BASE baseline: per file, match count and sha256 of the sorted
    matching lines (docs/census/…dispositions.md). CI checks out depth 1, so the
    BASE object itself is not available there; the record is."""
    rows = {}
    for ln in DISPOSITIONS.read_text(encoding="utf-8").splitlines():
        m = _ROW.match(ln)
        if m:
            rows[m.group(1)] = (int(m.group(2)), m.group(3))
    return rows


def _base_lines_if_available(rel: str) -> Counter[str] | None:
    """Diagnostics only: the BASE blob when history is present (never in CI)."""
    r = subprocess.run(
        ["git", "cat-file", "-p", f"{BASE}:{rel}"], cwd=REPO, capture_output=True
    )
    if r.returncode != 0:
        return None
    return _matches(r.stdout.decode("utf-8", errors="replace"))


def _explain(rel: str, head: Counter[str]) -> str:
    base = _base_lines_if_available(rel)
    if base is None:
        return f"{rel}: matching lines differ from BASE ({len(list(head.elements()))} at HEAD; BASE object not available)"
    return f"{rel}: removed {sorted((base - head).elements())} added {sorted((head - base).elements())}"


def _section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


# --- residual census (AC-09; round-3 R-3 clauses 1–4) -----------------------------------------------------


@pytest.mark.req("REQ-YG-668")
def test_baseline_record_is_complete_and_agrees_with_the_raw_inventory():
    baseline = _baseline()
    inventory = Counter(
        ln.rsplit(":", 1)[0]
        for ln in INVENTORY.read_text(encoding="utf-8").splitlines()
        if ln and not ln.startswith("#")
    )
    assert set(baseline) == set(inventory), "baseline rows != inventory files"
    assert {p: c for p, (c, _) in baseline.items()} == dict(inventory)
    assert len(baseline) == 261


@pytest.mark.req("REQ-YG-668")
def test_residual_clause1_files_outside_the_edit_set_match_base_line_for_line():
    baseline = _baseline()
    frozen = sorted(
        set(baseline) - set(RESIDUAL) - set(DELTA) - {"docs/context/chaplain-system.md"}
    )
    drift = [
        _explain(p, _head_matches(p))
        for p in frozen
        if _sha(_head_matches(p)) != baseline[p][1]
    ]
    assert not drift, "matching lines changed outside the edit set: " + "\n".join(drift)


@pytest.mark.req("REQ-YG-668")
@pytest.mark.parametrize("rel", sorted(RESIDUAL))
def test_residual_clause2_edit_set_files_carry_only_listed_lines(rel):
    extra = _head_matches(rel) - Counter(RESIDUAL[rel])
    missing = Counter(RESIDUAL[rel]) - _head_matches(rel)
    assert not extra, f"{rel}: unlisted residual lines {sorted(extra)}"
    assert not missing, f"{rel}: listed residual lines gone {sorted(missing)}"


@pytest.mark.req("REQ-YG-668")
@pytest.mark.parametrize("rel", sorted(DELTA))
def test_residual_clause2_generated_and_drift_files_match_exact_delta(rel):
    removed, added = DELTA[rel]
    head = _head_matches(rel)
    assert _sha(head) == DELTA_HEAD_SHA256[rel], _explain(rel, head)
    assert all(ln in head for ln in added), rel
    assert not any(ln in head for ln in removed), rel


@pytest.mark.req("REQ-YG-668")
def test_residual_clause3_no_unenumerated_matching_file():
    matched = {f for f in _tracked_files() if _head_matches(f)}
    new = matched - _frozen_files() - NEW_ARTIFACTS
    assert not new, f"files naming the retired runtime that were not in the BASE inventory: {sorted(new)}"


@pytest.mark.req("REQ-YG-668")
@pytest.mark.parametrize("rel", OUT_OF_SCOPE_CODE)
def test_residual_clause4_out_of_scope_code_defaults_unchanged(rel):
    count, sha = _baseline()[rel]
    assert count, f"{rel} had no .chaplain default at BASE — reclassify"
    head = _head_matches(rel)
    assert _sha(head) == sha, _explain(rel, head)


@pytest.mark.req("REQ-YG-668")
@pytest.mark.parametrize("rel", sorted(RESIDUAL))
def test_edit_set_files_no_longer_name_the_retired_route(rel):
    text = (REPO / rel).read_text(encoding="utf-8")
    hits = [s for s in RETIRED_ROUTE if s in text]
    assert not hits, f"{rel} still contains {hits}"


# --- Scripture (AC-04) ---------------------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-668")
def test_sermon_heading_renamed_and_steps_unchanged():
    text = SCRIPTURE.read_text(encoding="utf-8")
    assert text.count("Sermon of the Chaplain") == 0
    assert "\n## Sermon\n" in text
    sermon = _section(text, "\n## Sermon\n", "## Agents' prayer")
    assert re.findall(r"^\*\*([A-Z][a-z]+)\.\*\*", sermon, re.M) == SERMON_STEPS_AT_BASE


@pytest.mark.req("REQ-YG-668")
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


# --- docs/development-process.md (AC-05) ---------------------------------------------------------------


@pytest.mark.req("REQ-YG-668")
def test_development_process_describes_the_operator_route():
    text = DEV_PROCESS.read_text(encoding="utf-8")
    for token in (
        "scripts/author.sh",
        "scripts/judge.sh",
        "scripts/review.sh",
        "worktree",
    ):
        assert token in text, token
    for retired in (
        "start-system.sh",
        "label: chaplain",
        ".chaplain/inbox",
        ".chaplain/failed",
        ".chaplain/inquisitor.sh",
        "stateDiagram",
        "chaplain-ops",
        "Chaplain/Watcher",
        "The Inquisitor is",
    ):
        assert retired not in text, retired


@pytest.mark.req("REQ-YG-668")
def test_development_process_measurement_sentence_is_byte_identical_to_base():
    assert MEASUREMENT_SENTENCE_AT_BASE in DEV_PROCESS.read_text(encoding="utf-8")


# --- reference (AC-06) ------------------------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-668")
def test_audit_index_has_exactly_one_chaplain_row_pointing_at_the_archive():
    rows = [
        ln
        for ln in AUDIT_INDEX.read_text(encoding="utf-8").splitlines()
        if ln.startswith("|") and "Chaplain" in ln
    ]
    assert len(rows) == 1, rows
    assert "docs/archive/chaplain.md" in rows[0]


# --- archive move (AC-07) ------------------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-668")
def test_chaplain_system_doc_moved_to_archive_and_linked():
    assert (REPO / "docs" / "archive" / "chaplain-system.md").is_file()
    assert not (REPO / "docs" / "context" / "chaplain-system.md").exists()
    assert "chaplain-system.md" in (
        REPO / "docs" / "archive" / "chaplain.md"
    ).read_text(encoding="utf-8")


# --- ramp mirror (AC-08) ---------------------------------------------------------------------------------------


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
